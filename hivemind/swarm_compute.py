import uuid
import json
from typing import Dict, List

class SwarmComputeTask:
    """Represents a distributed compute task."""
    def __init__(self, task_type: str, payload: dict):
        self.task_id = str(uuid.uuid4())
        self.task_type = task_type
        self.payload = payload
        self.status = "PENDING"
        self.results = []
        self.chunks_total = 0
        self.chunks_completed = 0

class SwarmComputeEngine:
    """Manages distributed processing workloads across the Hive Mind DHT."""
    def __init__(self, daemon):
        self.daemon = daemon
        self.tasks: Dict[str, SwarmComputeTask] = {}

    def distribute_task(self, task_type: str, payload: dict, chunks: int = 4) -> str:
        """Distributes a task to known peers."""
        task = SwarmComputeTask(task_type, payload)
        task.chunks_total = chunks
        self.tasks[task.task_id] = task
        
        peers = self.daemon.routing_table.get_all_nodes()
        if not peers:
            task.status = "FAILED - NO PEERS"
            return task.task_id

        msg = json.dumps({
            "type": "COMPUTE_TASK",
            "task_id": task.task_id,
            "task_type": task_type,
            "payload": payload,
            "sender_node_id": self.daemon.node_id
        })
        
        for peer in peers:
            import threading
            threading.Thread(target=self.daemon._send, args=(peer, msg), daemon=True).start()
            
        task.status = "PROCESSING"
        self.daemon.bus.publish("SWARM_TASK_STARTED", {"task_id": task.task_id, "type": task_type})
        return task.task_id

    def process_task_locally(self, task_id: str, task_type: str, payload: dict, sender_node_id: str):
        """Process a chunk of the task locally and return result."""
        result = {"status": "SUCCESS", "data": f"Processed locally by {self.daemon.node_id}"}
        if task_type == "GROVER_SEARCH":
            result["found"] = True
            result["iterations"] = 5
        
        msg = json.dumps({
            "type": "COMPUTE_RESULT",
            "task_id": task_id,
            "result": result,
            "sender_node_id": self.daemon.node_id
        })
        
        # Broadcast result back
        for peer in self.daemon.routing_table.get_all_nodes():
            import threading
            threading.Thread(target=self.daemon._send, args=(peer, msg), daemon=True).start()
            
    def handle_result(self, task_id: str, result: dict):
        """Handle a result returned by a peer."""
        task = self.tasks.get(task_id)
        if task:
            task.results.append(result)
            task.chunks_completed += 1
            if task.chunks_completed >= task.chunks_total:
                task.status = "COMPLETED"
                self.daemon.bus.publish("SWARM_TASK_COMPLETED", {"task_id": task_id, "results": len(task.results)})
