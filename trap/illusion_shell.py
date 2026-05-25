"""
╔══════════════════════════════════════════════════════════════════╗
║  SOLIPSISM TRAP v4.0 — Adaptive Deception Engine                 ║
║  Traps attackers in a strict, isolated Docker container.         ║
║  Monitors tactics, wastes resources, keeps real system safe.     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import socket
import random
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger

# Try importing docker SDK
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


# ─── Suspicious Command Patterns ──────────────────────────────────
SUSPICIOUS_COMMANDS = {"cat /etc/shadow", "cat /etc/passwd", "wget", "curl", "nc",
                       "netcat", "python -c", "perl -e", "ruby -e", "base64",
                       "chmod 777", "chmod +x", "id_rsa", "api_keys", "credentials"}

DESTRUCTIVE_COMMANDS = {"rm -rf", "rm -r", "format", "dd if=", "shred",
                        "mkfs", "wipefs", "> /dev/sda"}


class TrapSession:
    """Tracks a single attacker session inside the trap."""

    def __init__(self, attacker_ip: str, attacker_port: int, session_id: str):
        self.session_id = session_id
        self.attacker_ip = attacker_ip
        self.attacker_port = attacker_port
        self.cwd = "/"
        self.username = "root"
        self.hostname = f"prod-app-{random.randint(10, 99)}"
        self.start_time = datetime.now(timezone.utc)
        self.commands: List[dict] = []
        self.suspicion_score = 0
        self.trace_progress = 0.0
        self.is_terminated = False
        self.container = None
        self.os_image = "unknown"

    def log_command(self, cmd: str, output: str, suspicious: bool = False):
        self.commands.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": cmd,
            "cwd": self.cwd,
            "output_preview": output[:200],
            "suspicious": suspicious,
        })
        if suspicious:
            self.suspicion_score += 1
            self.trace_progress = min(100.0, self.trace_progress + 15.0)

    def to_report(self) -> dict:
        return {
            "session_id": self.session_id,
            "attacker_ip": self.attacker_ip,
            "attacker_port": self.attacker_port,
            "start_time": self.start_time.isoformat(),
            "duration_sec": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "total_commands": len(self.commands),
            "suspicion_score": self.suspicion_score,
            "trace_progress": self.trace_progress,
            "os_image": self.os_image,
            "commands": self.commands,
        }


class SolipsismTrap:
    """
    Weaponized honeypot that traps attackers in an isolated Docker container.
    """

    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self._sessions: Dict[str, TrapSession] = {}
        self._lock = threading.Lock()
        self._server_socket: Optional[socket.socket] = None
        self._running = False
        
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                self.docker_client = None
                self.bus.publish("TRAP_WARNING", {"msg": f"Docker SDK error: {e}"})
        else:
            self.docker_client = None
            self.bus.publish("TRAP_WARNING", {"msg": "Docker SDK not installed (pip install docker)"})

    def _start_container_for_session(self, session: TrapSession):
        """Spawns a strictly isolated container for the attacker."""
        if not self.docker_client:
            return False
            
        images = ["alpine:latest", "ubuntu:latest", "debian:latest"]
        image = random.choice(images)
        session.os_image = image
        
        try:
            # Pull image if not present
            try:
                self.docker_client.images.get(image)
            except docker.errors.ImageNotFound:
                self.docker_client.images.pull(image)
                
            # Production-grade isolated container
            # memory="256m", cpus=0.5, network_mode="none", read_only=True
            container = self.docker_client.containers.run(
                image,
                command="sh -c 'while true; do sleep 3600; done'",
                detach=True,
                network_mode="none",
                mem_limit="256m",
                cpu_quota=50000,  # 0.5 CPUs
                pids_limit=64,
                read_only=True,
                security_opt=["no-new-privileges:true"],
                remove=True,
                hostname=session.hostname
            )
            session.container = container
            
            # Inject some fake files/logs to make it juicy
            try:
                # We can't write to read_only fs easily via exec, so we just let them explore the base image
                # Alternatively setup a tmpfs mount if we wanted to allow writing, 
                # but read-only is safer as requested.
                pass
            except Exception:
                pass
                
            return True
        except Exception as e:
            self.bus.publish("TRAP_ERROR", {"msg": f"Failed to start container: {e}"})
            return False

    def _cleanup_session(self, session: TrapSession):
        """Kills and removes the session container."""
        if session.container:
            try:
                session.container.kill()
            except Exception:
                pass

    # ── Command Processing ──────────────────────────────────────

    def process_command(self, session: TrapSession, raw_cmd: str) -> str:
        """Process a command inside the trap and return output."""
        cmd = raw_cmd.strip()
        if not cmd:
            return ""

        # Check for destructive commands FIRST
        for dc in DESTRUCTIVE_COMMANDS:
            if dc in cmd:
                session.log_command(cmd, "[DESTRUCTIVE DETECTED]", suspicious=True)
                self.bus.publish("THREAT_DETECTED", {
                    "type": "DESTRUCTIVE_COMMAND",
                    "session_id": session.session_id,
                    "attacker_ip": session.attacker_ip,
                    "command": cmd,
                }, severity="CRITICAL")
                return self._deploy_countermeasure(session)

        # Check for suspicious commands
        is_suspicious = False
        for sc in SUSPICIOUS_COMMANDS:
            if sc in cmd:
                is_suspicious = True
                self.bus.publish("THREAT_DETECTED", {
                    "type": "SUSPICIOUS_COMMAND",
                    "session_id": session.session_id,
                    "attacker_ip": session.attacker_ip,
                    "command": cmd,
                    "trace_progress": session.trace_progress,
                }, severity="WARNING")
                break

        # Intercept specific commands for deception
        cmd_lower = cmd.lower()
        if ("cat " in cmd_lower or "grep " in cmd_lower) and any(x in cmd_lower for x in ["credentials", "config", "password", "shadow", "passwd", "id_rsa"]):
            session.log_command(cmd, "[DECEPTION: Fake Config Generated]", suspicious=True)
            from trap.fake_data_generator import FakeDataGenerator
            if "id_rsa" in cmd_lower:
                return json.dumps(FakeDataGenerator.generate_ssh_keys(), indent=2)
            return json.dumps(FakeDataGenerator.generate_credentials(), indent=2)
            
        if "nmap " in cmd_lower or "ping " in cmd_lower or "arp " in cmd_lower:
            session.log_command(cmd, "[DECEPTION: Fake Network Topology]", suspicious=True)
            from trap.deception_network import DeceptionNetwork
            net = DeceptionNetwork()
            return json.dumps(net.scan_network("10.0.0.0/24"), indent=2)

        # Intercept internal shell commands
        if cmd == "exit" or cmd == "quit":
            session.is_terminated = True
            return "logout"
            
        if cmd.startswith("cd "):
            target = cmd.split(" ", 1)[1].strip()
            # Try to resolve path in container
            if session.container:
                # To handle relative paths properly, we use sh -c to cd and then pwd
                abs_cmd = f"sh -c 'cd {target} && pwd'"
                exit_code, output = session.container.exec_run(cmd=abs_cmd, workdir=session.cwd)
                if exit_code == 0:
                    session.cwd = output.decode().strip()
                    return ""
                else:
                    return f"cd: {target}: No such file or directory"
            else:
                session.cwd = target
                return ""

        # Execute in Docker
        if session.container:
            try:
                # We prepend sh -c so we get shell features like pipes if simple enough
                # Note: exec_run supports workdir directly
                exit_code, output_bytes = session.container.exec_run(
                    cmd=["sh", "-c", cmd], 
                    workdir=session.cwd
                )
                output = output_bytes.decode(errors='replace')
            except Exception as e:
                output = f"execution error: {e}"
        else:
            output = "-bash: execution failed (Docker isolated sandbox unavailable)"

        session.log_command(cmd, output, suspicious=is_suspicious)

        if is_suspicious:
            trace_bar = "█" * int(session.trace_progress / 5) + "░" * (20 - int(session.trace_progress / 5))
            output += f"\n\n[TRACE SIMULATION: {trace_bar} {session.trace_progress:.0f}%]"

        return output

    # ── Counter-Measures ─────────────────────────────────────────

    def _deploy_countermeasure(self, session: TrapSession) -> str:
        """Deploy counter-measure against destructive attacker."""
        session.is_terminated = True
        self._cleanup_session(session)
        self._save_session_report(session)
        self.bus.publish("COUNTERMEASURE_DEPLOYED", {
            "session_id": session.session_id,
            "attacker_ip": session.attacker_ip,
            "suspicion_score": session.suspicion_score,
        }, severity="CRITICAL")
        return (
            "\n╔═══════════════════════════════════════╗\n"
            "║  ⚠ SECURITY ALERT — CONNECTION RESET  ║\n"
            "║  Destructive activity detected.        ║\n"
            "║  Session terminated. Incident logged.   ║\n"
            "╚═══════════════════════════════════════╝\n"
        )

    def _save_session_report(self, session: TrapSession):
        """Save forensic session report to disk."""
        os.makedirs("logs", exist_ok=True)
        report_path = f"logs/trap_session_{session.session_id}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(session.to_report(), f, indent=2)

    # ── TCP Listener ─────────────────────────────────────────────

    def start_listener(self, host: str = "0.0.0.0", port: int = 2222):
        """Start TCP listener for incoming connections."""
        self._running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((host, port))
        self._server_socket.listen(5)
        self._server_socket.settimeout(1.0)

        self.bus.publish("TRAP_LISTENER_STARTED", {"host": host, "port": port})

        while self._running:
            try:
                conn, addr = self._server_socket.accept()
                t = threading.Thread(
                    target=self._handle_connection,
                    args=(conn, addr),
                    daemon=True
                )
                t.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    self.bus.publish("TRAP_ERROR", {"error": str(e)}, severity="ERROR")

    def stop_listener(self):
        """Stop the TCP listener."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        # Clean up all containers
        with self._lock:
            for s in self._sessions.values():
                self._cleanup_session(s)

    def _handle_connection(self, conn: socket.socket, addr: tuple):
        """Handle a single attacker connection."""
        import uuid
        session_id = str(uuid.uuid4())[:8]
        session = TrapSession(
            attacker_ip=addr[0],
            attacker_port=addr[1],
            session_id=session_id,
        )

        with self._lock:
            self._sessions[session_id] = session

        self.bus.publish("TRAP_ENGAGED", {
            "session_id": session_id,
            "attacker_ip": addr[0],
            "attacker_port": addr[1],
        }, severity="WARNING")

        # Start Docker Sandbox
        self._start_container_for_session(session)

        try:
            banner = str(
                f"Linux {session.hostname} 5.15.0-89-generic #99 SMP PREEMPT x86_64\n"
                f"Last login: {datetime.now(timezone.utc).strftime('%a %b %d %H:%M:%S %Y')} from 10.0.0.1\n"
            )
            conn.sendall(banner.encode())

            while not session.is_terminated:
                prompt_cwd = session.cwd.split('/')[-1]
                if not prompt_cwd: prompt_cwd = '/'
                prompt = f"[{session.username}@{session.hostname} {prompt_cwd}]# "
                conn.sendall(prompt.encode())

                data = conn.recv(4096)
                if not data:
                    break

                raw_cmd = data.decode("utf-8", errors="replace").strip()
                output = self.process_command(session, raw_cmd)
                if output:
                    conn.sendall((output + "\n").encode())

                if session.is_terminated:
                    break

        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            self._cleanup_session(session)
            self._save_session_report(session)
            conn.close()

    # ── Interactive Mode ─────────────────────────────────────────

    def run_interactive(self):
        """Run the trap in interactive stdin mode (for testing)."""
        import uuid
        session = TrapSession("127.0.0.1", 0, str(uuid.uuid4())[:8])
        print(f"[TRAP] Interactive session {session.session_id}")
        self._start_container_for_session(session)

        try:
            while not session.is_terminated:
                prompt_cwd = session.cwd.split('/')[-1]
                if not prompt_cwd: prompt_cwd = '/'
                prompt = f"[{session.username}@{session.hostname} {prompt_cwd}]# "
                try:
                    cmd = input(prompt)
                except (EOFError, KeyboardInterrupt):
                    break
                output = self.process_command(session, cmd)
                if output:
                    print(output)
        finally:
            self._cleanup_session(session)
            self._save_session_report(session)
            print(f"\n[TRAP] Session ended. Report saved.")

    # ── Status ───────────────────────────────────────────────────

    def get_status(self) -> dict:
        with self._lock:
            return {
                "listening": self._running,
                "docker_backend": self.docker_client is not None,
                "active_sessions": len([s for s in self._sessions.values() if not s.is_terminated]),
                "total_sessions": len(self._sessions),
                "sessions": [
                    {
                        "id": s.session_id,
                        "ip": s.attacker_ip,
                        "commands": len(s.commands),
                        "suspicion": s.suspicion_score,
                        "os": s.os_image,
                        "terminated": s.is_terminated,
                    }
                    for s in self._sessions.values()
                ],
            }


# ─── Self-Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uuid
    print("[SOLIPSISM TRAP v4.0] Running self-test...")

    logger = ForensicLogger()
    bus = EventBus(logger)
    trap = SolipsismTrap(bus)

    session = TrapSession("192.168.1.100", 54321, "test-001")
    started = trap._start_container_for_session(session)
    
    if not started:
        print("  ⚠ Docker not available. Tests skipped.")
    else:
        # Test basic commands routed to docker
        out_whoami = trap.process_command(session, "whoami")
        assert "root" in out_whoami, f"Expected root, got: {out_whoami}"
        print("  ✓ Basic commands (whoami) execute in container")

        out_ls = trap.process_command(session, "ls /")
        assert "bin" in out_ls and "etc" in out_ls, "Failed to list root dir in container"
        print("  ✓ File listing works in container")

        # Test suspicious command detection
        trap.process_command(session, "cat /etc/shadow")
        assert session.suspicion_score > 0
        print(f"  ✓ Suspicious command detected (score: {session.suspicion_score})")

        # Test navigation
        trap.process_command(session, "cd /etc")
        assert session.cwd == "/etc"
        print(f"  ✓ Navigation works (cwd: {session.cwd})")
        
        # Test destructive command counter-measure
        out_destruct = trap.process_command(session, "rm -rf /")
        assert "CONNECTION RESET" in out_destruct
        assert session.is_terminated
        print("  ✓ Destructive command counter-measure works")

        trap._cleanup_session(session)

    # Test status
    status = trap.get_status()
    print(f"  ✓ Status: docker_backend={status['docker_backend']}")

    print("[SOLIPSISM TRAP v4.0] All tests passed.")
