"""
╔══════════════════════════════════════════════════════════════════╗
║  DIGITAL FORGE v3.0 — Hypervisor & Sandbox Manager               ║
║  Instant VM spin-up/destroy, malware sandboxes, red team labs.   ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, time, uuid, hashlib, threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

VM_TEMPLATES = {
    "malware-sandbox": {"os": "Linux-Minimal", "ram_mb": 512, "cpu": 1, "disk_gb": 5,
                        "network": "isolated", "description": "Isolated malware analysis sandbox"},
    "red-team-kali": {"os": "Kali-Linux", "ram_mb": 2048, "cpu": 2, "disk_gb": 20,
                      "network": "nat", "description": "Red team attack simulation"},
    "forensics-lab": {"os": "SIFT-Workstation", "ram_mb": 4096, "cpu": 4, "disk_gb": 50,
                      "network": "bridged", "description": "Digital forensics workstation"},
    "honeypot-node": {"os": "Ubuntu-Server", "ram_mb": 256, "cpu": 1, "disk_gb": 2,
                      "network": "dmz", "description": "Lightweight honeypot deployment"},
    "windows-target": {"os": "Windows-10", "ram_mb": 4096, "cpu": 2, "disk_gb": 40,
                       "network": "isolated", "description": "Windows target for exploit testing"},
}

class VirtualMachine:
    def __init__(self, vm_id: str, name: str, template: dict):
        self.vm_id = vm_id
        self.name = name
        self.os_type = template.get("os", "unknown")
        self.ram_mb = template.get("ram_mb", 512)
        self.cpu = template.get("cpu", 1)
        self.disk_gb = template.get("disk_gb", 10)
        self.network = template.get("network", "isolated")
        self.status = "STOPPED"  # STOPPED, RUNNING, PAUSED, DESTROYED
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.snapshots: List[dict] = []
        self.logs: List[str] = []
    def to_dict(self):
        return {"vm_id": self.vm_id, "name": self.name, "os": self.os_type,
                "ram_mb": self.ram_mb, "cpu": self.cpu, "disk_gb": self.disk_gb,
                "network": self.network, "status": self.status,
                "created": self.created_at.isoformat(),
                "started": self.started_at.isoformat() if self.started_at else None,
                "snapshots": len(self.snapshots)}

class DigitalForge:
    """
    Hypervisor manager for virtual machine lifecycle.
    Simulates VM creation, destruction, snapshotting for
    malware analysis, red team labs, and forensics.
    """
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self._vms: Dict[str, VirtualMachine] = {}
        self._lock = threading.Lock()

    def list_templates(self) -> List[dict]:
        return [{"name": k, **v} for k, v in VM_TEMPLATES.items()]

    def create_vm(self, name: str, template_name: str = "malware-sandbox") -> dict:
        template = VM_TEMPLATES.get(template_name)
        if not template:
            return {"status": "ERROR", "message": f"Template '{template_name}' not found"}
        vm_id = str(uuid.uuid4())[:8]
        vm = VirtualMachine(vm_id, name, template)
        with self._lock:
            self._vms[vm_id] = vm
        self.bus.publish("FORGE_VM_CREATED", {"vm_id": vm_id, "name": name, "template": template_name})
        return {"status": "CREATED", "vm_id": vm_id, **vm.to_dict()}

    def start_vm(self, vm_id: str) -> dict:
        with self._lock:
            vm = self._vms.get(vm_id)
            if not vm:
                return {"status": "ERROR", "message": "VM not found"}
            if vm.status == "RUNNING":
                return {"status": "ALREADY_RUNNING"}
            vm.status = "RUNNING"
            vm.started_at = datetime.now(timezone.utc)
            vm.logs.append(f"[{vm.started_at.isoformat()}] VM started")
        self.bus.publish("FORGE_VM_STARTED", {"vm_id": vm_id, "name": vm.name})
        return {"status": "STARTED", **vm.to_dict()}

    def stop_vm(self, vm_id: str) -> dict:
        with self._lock:
            vm = self._vms.get(vm_id)
            if not vm:
                return {"status": "ERROR", "message": "VM not found"}
            vm.status = "STOPPED"
            vm.logs.append(f"[{datetime.now(timezone.utc).isoformat()}] VM stopped")
        self.bus.publish("FORGE_VM_STOPPED", {"vm_id": vm_id})
        return {"status": "STOPPED", "vm_id": vm_id}

    def destroy_vm(self, vm_id: str) -> dict:
        with self._lock:
            vm = self._vms.pop(vm_id, None)
            if not vm:
                return {"status": "ERROR", "message": "VM not found"}
            vm.status = "DESTROYED"
        self.bus.publish("FORGE_VM_DESTROYED", {"vm_id": vm_id, "name": vm.name})
        return {"status": "DESTROYED", "vm_id": vm_id}

    def snapshot(self, vm_id: str, label: str = "") -> dict:
        with self._lock:
            vm = self._vms.get(vm_id)
            if not vm:
                return {"status": "ERROR", "message": "VM not found"}
            snap = {"snap_id": str(uuid.uuid4())[:8], "label": label or f"snap-{len(vm.snapshots)+1}",
                    "timestamp": datetime.now(timezone.utc).isoformat(), "vm_status": vm.status}
            vm.snapshots.append(snap)
        self.bus.publish("FORGE_SNAPSHOT", {"vm_id": vm_id, "snap_id": snap["snap_id"]})
        return {"status": "SNAPSHOT_CREATED", **snap}

    def list_vms(self) -> List[dict]:
        with self._lock:
            return [vm.to_dict() for vm in self._vms.values()]

    def get_host_resources(self) -> dict:
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            return {"cpu_count": psutil.cpu_count(), "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "ram_total_gb": round(mem.total / (1024**3), 1),
                    "ram_used_gb": round(mem.used / (1024**3), 1),
                    "ram_percent": mem.percent}
        return {"note": "psutil not available", "cpu_count": os.cpu_count() or 1}

    def deploy_honeypot(self, threat_type: str, code: str) -> dict:
        """Dynamically deploys a deceptive honeypot environment tailored to a threat."""
        vm_name = f"honeypot-{threat_type.lower()}-{str(uuid.uuid4())[:6]}"
        result = self.create_vm(vm_name, "honeypot-node")
        if result["status"] == "CREATED":
            vm_id = result["vm_id"]
            self.start_vm(vm_id)
            with self._lock:
                vm = self._vms.get(vm_id)
                if vm:
                    vm.logs.append(f"[{datetime.now(timezone.utc).isoformat()}] Injected honeypot payload: {len(code)} bytes")
            self.bus.publish("HONEYPOT_DEPLOYED", {"vm_id": vm_id, "threat": threat_type, "payload_size": len(code)})
            return {"status": "DEPLOYED", "vm_id": vm_id, "threat": threat_type}
        return {"status": "FAILED", "reason": "Could not create VM"}

    def get_status(self):
        vms = self.list_vms()
        return {"total_vms": len(vms), "running": len([v for v in vms if v["status"] == "RUNNING"]),
                "templates": len(VM_TEMPLATES), "host": self.get_host_resources()}

if __name__ == "__main__":
    print("[DIGITAL FORGE] Self-test...")
    bus = EventBus(ForensicLogger())
    forge = DigitalForge(bus)
    templates = forge.list_templates()
    print(f"  ✓ Templates: {len(templates)}")
    r = forge.create_vm("test-sandbox", "malware-sandbox")
    vm_id = r["vm_id"]
    print(f"  ✓ Created VM: {vm_id}")
    forge.start_vm(vm_id)
    assert forge.list_vms()[0]["status"] == "RUNNING"
    print(f"  ✓ VM running")
    forge.snapshot(vm_id, "clean-state")
    forge.stop_vm(vm_id)
    forge.destroy_vm(vm_id)
    assert len(forge.list_vms()) == 0
    print(f"  ✓ VM destroyed")
    print(f"  ✓ Host: {forge.get_host_resources()}")
    print("[DIGITAL FORGE] All tests passed.")
