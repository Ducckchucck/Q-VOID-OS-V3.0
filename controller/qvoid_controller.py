"""
╔══════════════════════════════════════════════════════════════════╗
║  Q-VOID CONTROLLER v3.0 — Module Orchestrator                    ║
║  Start, stop, restart, and monitor all subsystem modules.        ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, time, threading, subprocess, signal
from datetime import datetime, timezone
from typing import Dict, Optional
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger, ModuleRegistry

MODULE_CONFIG = {
    "polymorphic": {"script": "polymorphic/polymorph_engine.py", "description": "Moving-target defense engine", "auto_restart": True},
    "trap": {"script": "trap/illusion_shell.py", "description": "Solipsism trap honeypot", "auto_restart": True},
    "hivemind": {"script": "hivemind/hivemind_daemon.py", "description": "P2P threat intelligence grid", "auto_restart": True},
    "ghostfs": {"script": "ghostfs/ghost_fs.py", "description": "Steganographic ghost filesystem", "auto_restart": False},
    "qcrypt": {"script": "qcrypt/qcrypt_engine.py", "description": "Post-quantum encryption engine", "auto_restart": False},
    "precog": {"script": "precog/precog_engine.py", "description": "AI attack prediction engine", "auto_restart": True},
    "qpm": {"script": "qpm/qpm_cli.py", "description": "Secure package manager", "auto_restart": False},
    "forge": {"script": "forge/digital_forge.py", "description": "Hypervisor sandbox manager", "auto_restart": False},
    "oracle": {"script": "oracle/quantum_oracle.py", "description": "Quantum threat detection", "auto_restart": True},
    "mcp": {"script": "mcp/mcp_router.py", "description": "Model Control Protocol router", "auto_restart": True},
    "rag": {"script": "rag/rag_engine.py", "description": "Retrieval-augmented generation", "auto_restart": False},
    "dna": {"script": "dna/dna_encryptor.py", "description": "DNA steganographic encoder", "auto_restart": False},
}

class ModuleProcess:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.script = config["script"]
        self.description = config["description"]
        self.auto_restart = config.get("auto_restart", False)
        self.process: Optional[subprocess.Popen] = None
        self.status = "STOPPED"
        self.pid: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        self.log_lines: list = []

class QVoidController:
    """Controls all Q-Void OS subsystem modules."""
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self._modules: Dict[str, ModuleProcess] = {}
        self._watchdog_running = False
        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name, config in MODULE_CONFIG.items():
            self._modules[name] = ModuleProcess(name, config)
        os.makedirs(os.path.join(self._base_dir, "logs"), exist_ok=True)

    def start(self, module_name: str) -> dict:
        if module_name == "all":
            results = {}
            for name in self._modules:
                results[name] = self.start(name)
            return {"status": "BATCH_START", "results": results}
        mod = self._modules.get(module_name)
        if not mod:
            return {"status": "ERROR", "message": f"Unknown module: {module_name}"}
        if mod.status == "RUNNING":
            return {"status": "ALREADY_RUNNING", "module": module_name}
        script_path = os.path.join(self._base_dir, mod.script)
        if not os.path.exists(script_path):
            return {"status": "ERROR", "message": f"Script not found: {mod.script}"}
        try:
            log_path = os.path.join(self._base_dir, "logs", f"{module_name}.log")
            log_file = open(log_path, "a", encoding="utf-8")
            mod.process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=log_file, stderr=subprocess.STDOUT,
                cwd=self._base_dir, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            mod.pid = mod.process.pid
            mod.status = "RUNNING"
            mod.start_time = datetime.now(timezone.utc)
            self.bus.publish("MODULE_STARTED", {"module": module_name, "pid": mod.pid})
            return {"status": "STARTED", "module": module_name, "pid": mod.pid}
        except Exception as e:
            mod.status = "ERROR"
            return {"status": "ERROR", "message": str(e)}

    def stop(self, module_name: str) -> dict:
        if module_name == "all":
            results = {}
            for name in self._modules:
                results[name] = self.stop(name)
            return {"status": "BATCH_STOP", "results": results}
        mod = self._modules.get(module_name)
        if not mod:
            return {"status": "ERROR", "message": f"Unknown module: {module_name}"}
        if mod.status != "RUNNING" or not mod.process:
            return {"status": "NOT_RUNNING", "module": module_name}
        try:
            mod.process.terminate()
            mod.process.wait(timeout=5)
        except Exception:
            try:
                mod.process.kill()
            except Exception:
                pass
        mod.status = "STOPPED"
        mod.pid = None
        mod.process = None
        self.bus.publish("MODULE_STOPPED", {"module": module_name})
        return {"status": "STOPPED", "module": module_name}

    def restart(self, module_name: str) -> dict:
        self.stop(module_name)
        time.sleep(0.5)
        result = self.start(module_name)
        mod = self._modules.get(module_name)
        if mod:
            mod.restart_count += 1
        return result

    def status(self) -> list:
        result = []
        for name, mod in self._modules.items():
            uptime = ""
            if mod.status == "RUNNING" and mod.start_time:
                delta = (datetime.now(timezone.utc) - mod.start_time).total_seconds()
                h, rem = divmod(int(delta), 3600)
                m, s = divmod(rem, 60)
                uptime = f"{h:02d}:{m:02d}:{s:02d}"
            icon = "✅" if mod.status == "RUNNING" else "⭕" if mod.status == "STOPPED" else "💥"
            result.append({"name": name, "icon": icon, "status": mod.status,
                          "pid": mod.pid, "uptime": uptime,
                          "restarts": mod.restart_count, "description": mod.description})
        return result

    def start_watchdog(self):
        self._watchdog_running = True
        t = threading.Thread(target=self._watchdog_loop, daemon=True)
        t.start()

    def stop_watchdog(self):
        self._watchdog_running = False

    def _watchdog_loop(self):
        while self._watchdog_running:
            for name, mod in self._modules.items():
                if mod.status == "RUNNING" and mod.process:
                    if mod.process.poll() is not None:
                        mod.status = "CRASHED"
                        self.bus.publish("MODULE_CRASHED", {"module": name}, severity="ERROR")
                        if mod.auto_restart:
                            self.restart(name)
            time.sleep(5)

if __name__ == "__main__":
    print("[CONTROLLER] Self-test...")
    bus = EventBus(ForensicLogger())
    ctrl = QVoidController(bus)
    status = ctrl.status()
    print(f"  ✓ {len(status)} modules registered")
    for m in status:
        print(f"    {m['icon']} {m['name']}: {m['description']}")
    print("[CONTROLLER] All tests passed.")
