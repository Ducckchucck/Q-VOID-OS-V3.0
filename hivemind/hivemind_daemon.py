"""
╔══════════════════════════════════════════════════════════════════╗
║  Q-VOID HIVE MIND v3.0 — Global Intelligence Grid               ║
║  Kademlia-style P2P network for real-time threat sharing.        ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, time, socket, hashlib, threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import OrderedDict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger
from rust_core import engine as rust_core

class HiveNode:
    def __init__(self, node_id: str, host: str, port: int):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.last_seen = datetime.now(timezone.utc)
        self.is_alive = True
        self.trust_score = 50.0
    def to_dict(self):
        return {"node_id": self.node_id, "host": self.host, "port": self.port,
                "last_seen": self.last_seen.isoformat(), "is_alive": self.is_alive,
                "trust_score": self.trust_score}

class KademliaTable:
    def __init__(self, local_id: str, k: int = 20):
        self.local_id = local_id
        self.k = k
        self._buckets: Dict[int, OrderedDict] = {}
        self._lock = threading.Lock()
    def _xor_distance(self, id1: str, id2: str) -> int:
        h1 = int(rust_core.fast_sha256(id1.encode()), 16)
        h2 = int(rust_core.fast_sha256(id2.encode()), 16)
        return h1 ^ h2
    def _bucket_index(self, node_id: str) -> int:
        dist = self._xor_distance(self.local_id, node_id)
        return dist.bit_length() if dist else 0
    def add_node(self, node: HiveNode):
        with self._lock:
            idx = self._bucket_index(node.node_id)
            if idx not in self._buckets:
                self._buckets[idx] = OrderedDict()
            b = self._buckets[idx]
            if node.node_id in b:
                b.move_to_end(node.node_id)
            elif len(b) < self.k:
                b[node.node_id] = node
    def get_all_nodes(self) -> List[HiveNode]:
        with self._lock:
            return [n for b in self._buckets.values() for n in b.values()]
    def get_closest(self, target_id: str, count: int = 5) -> List[HiveNode]:
        nodes = self.get_all_nodes()
        nodes.sort(key=lambda n: self._xor_distance(n.node_id, target_id))
        return nodes[:count]

class HiveMindDaemon:
    def __init__(self, event_bus: EventBus, host: str = "0.0.0.0", port: int = 9999):
        self.bus = event_bus
        self.host = host
        self.port = port
        self.node_id = rust_core.fast_sha256(f"{host}:{port}:{time.time()}".encode())[:16]
        self.routing_table = KademliaTable(self.node_id)
        self._running = False
        self._server: Optional[socket.socket] = None
        self._threat_db: List[dict] = []
        
        from hivemind.peer_auth import PeerAuthenticator
        from hivemind.swarm_compute import SwarmComputeEngine
        self.authenticator = PeerAuthenticator()
        self.compute_engine = SwarmComputeEngine(self)
        
        self.bus.subscribe("THREAT_DETECTED", self._on_local_threat)

    def ping(self, target_host: str, target_port: int, timeout: float = 3.0) -> Optional[HiveNode]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((target_host, target_port))
            msg = json.dumps({"type": "PING", "node_id": self.node_id,
                              "timestamp": datetime.now(timezone.utc).isoformat(),
                              "host": self.host, "port": self.port})
            sock.sendall((msg + "\n").encode())
            
            challenge_resp = json.loads(sock.recv(4096).decode().strip())
            if challenge_resp.get("type") == "AUTH_CHALLENGE":
                solution = self.authenticator.solve_challenge(challenge_resp["challenge"])
                sock.sendall((json.dumps({"type": "AUTH_RESPONSE", "solution": solution}) + "\n").encode())
                
                resp = json.loads(sock.recv(4096).decode().strip())
                if resp.get("type") == "PONG":
                    node = HiveNode(resp["node_id"], target_host, target_port)
                    self.routing_table.add_node(node)
                    self.bus.publish("HIVE_PEER_DISCOVERED", node.to_dict())
                    sock.close()
                    return node
            sock.close()
        except Exception:
            pass
        return None

    def broadcast_threat(self, threat_data: dict):
        msg = json.dumps({"type": "THREAT_BROADCAST", "node_id": self.node_id,
                          "timestamp": datetime.now(timezone.utc).isoformat(), "threat": threat_data})
        peers = self.routing_table.get_all_nodes()
        for p in peers:
            threading.Thread(target=self._send, args=(p, msg), daemon=True).start()
        self.bus.publish("HIVE_THREAT_BROADCAST", {"peers_notified": len(peers)})

    def _send(self, peer: HiveNode, message: str):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect((peer.host, peer.port))
            s.sendall((message + "\n").encode())
            s.close()
        except Exception:
            peer.is_alive = False

    def _on_local_threat(self, event: dict):
        td = event.get("data", {})
        self._threat_db.append({"timestamp": datetime.now(timezone.utc).isoformat(), "source": "LOCAL", "data": td})
        self.broadcast_threat(td)

    def start(self):
        self._running = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.settimeout(1.0)
        try:
            self._server.bind((self.host, self.port))
        except OSError as e:
            self._running = False
            return
        self._server.listen(10)
        self.bus.publish("HIVE_STARTED", {"node_id": self.node_id, "port": self.port})
        while self._running:
            try:
                conn, addr = self._server.accept()
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                pass

    def stop(self):
        self._running = False
        if self._server:
            try: self._server.close()
            except Exception: pass

    def _handle(self, conn: socket.socket):
        try:
            data = json.loads(conn.recv(8192).decode().strip())
            if data.get("type") == "PING":
                challenge = self.authenticator.generate_challenge()
                conn.sendall((json.dumps({"type": "AUTH_CHALLENGE", "challenge": challenge}) + "\n").encode())
                
                auth_resp = json.loads(conn.recv(4096).decode().strip())
                if auth_resp.get("type") == "AUTH_RESPONSE" and self.authenticator.verify_solution(challenge, auth_resp.get("solution", "")):
                    pong = json.dumps({"type": "PONG", "node_id": self.node_id})
                    conn.sendall((pong + "\n").encode())
                    self.routing_table.add_node(HiveNode(data.get("node_id","?"), data.get("host","?"), data.get("port",0)))
                else:
                    return
            elif data.get("type") == "THREAT_BROADCAST":
                self._threat_db.append({"timestamp": datetime.now(timezone.utc).isoformat(),
                                        "source": data.get("node_id"), "data": data.get("threat",{})})
                self.bus.publish("THREAT_SHARED", {"source_node": data.get("node_id"), "threat": data.get("threat",{})}, severity="WARNING")
            elif data.get("type") == "COMPUTE_TASK":
                self.compute_engine.process_task_locally(data.get("task_id"), data.get("task_type"), data.get("payload", {}), data.get("sender_node_id"))
            elif data.get("type") == "COMPUTE_RESULT":
                self.compute_engine.handle_result(data.get("task_id"), data.get("result", {}))
        except Exception:
            pass
        finally:
            try: conn.close()
            except: pass

    def get_status(self):
        peers = self.routing_table.get_all_nodes()
        return {"node_id": self.node_id, "running": self._running, "known_peers": len(peers),
                "alive_peers": len([p for p in peers if p.is_alive]), "threats_in_db": len(self._threat_db),
                "peers": [p.to_dict() for p in peers[:10]]}
    def get_threat_db(self, limit=20):
        return self._threat_db[-limit:]

if __name__ == "__main__":
    print("[HIVE MIND] Self-test...")
    bus = EventBus(ForensicLogger())
    hive = HiveMindDaemon(bus, port=0)
    hive.routing_table.add_node(HiveNode("peer1", "10.0.0.5", 9999))
    assert len(hive.routing_table.get_all_nodes()) == 1
    print(f"  ✓ Node ID: {hive.node_id}")
    print(f"  ✓ Peers: {hive.get_status()['known_peers']}")
    print("[HIVE MIND] All tests passed.")
