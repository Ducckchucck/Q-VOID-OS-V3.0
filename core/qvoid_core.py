"""
╔══════════════════════════════════════════════════════════════════╗
║  Q-VOID OS — SOVEREIGN CORE v3.0                                ║
║  Central Event Bus • Forensic Logger • Module Loader             ║
║  All subsystems communicate exclusively through this bus.        ║
╚══════════════════════════════════════════════════════════════════╝

Architecture: Publish/Subscribe Event Bus Pattern
Every module publishes events (e.g., THREAT_DETECTED, CRYPTO_OP, SCAN_RESULT)
and subscribes to events it cares about. This decouples all modules.
"""

import os
import sys
import json
import time
import uuid
import hashlib
import threading
import asyncio
import inspect
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict

# ─── Version ───────────────────────────────────────────────────────
QVOID_VERSION = "3.0.0"
CODENAME = "VOID_SOVEREIGN"

# ─── Forensic Logger ──────────────────────────────────────────────
class ForensicLogger:
    """
    Tamper-proof audit trail logger.
    Every event is hashed with the previous event's hash (blockchain-style chain).
    Logs are written to disk in append-only JSON-lines format.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "forensic_audit.jsonl")
        self._lock = threading.Lock()
        self._prev_hash = "GENESIS"
        self._event_count = 0

        # Load previous hash from existing log if present
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last = json.loads(lines[-1])
                        self._prev_hash = last.get("hash", "GENESIS")
                        self._event_count = len(lines)
            except Exception:
                pass

    def log(self, event_type: str, data: dict, severity: str = "INFO") -> dict:
        """
        Log a forensic event with tamper-proof chaining.
        Returns the log entry dict.
        """
        with self._lock:
            self._event_count += 1
            entry = {
                "id": str(uuid.uuid4()),
                "seq": self._event_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "severity": severity,
                "data": data,
                "prev_hash": self._prev_hash,
            }
            # Chain hash: SHA-256 of (prev_hash + serialized entry)
            raw = self._prev_hash + json.dumps(entry, sort_keys=True)
            entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
            self._prev_hash = entry["hash"]

            # Append to log file
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                print(f"[FORENSIC] Write error: {e}")

            return entry

    def verify_chain(self) -> bool:
        """Verify the entire forensic log chain integrity."""
        if not os.path.exists(self.log_file):
            return True
        prev = "GENESIS"
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                if entry["prev_hash"] != prev:
                    return False
                stored_hash = entry.pop("hash")
                raw = prev + json.dumps(entry, sort_keys=True)
                computed = hashlib.sha256(raw.encode()).hexdigest()
                if computed != stored_hash:
                    return False
                prev = stored_hash
                entry["hash"] = stored_hash  # restore
        return True

    def get_entries(self, event_type: str = None, limit: int = 50) -> list:
        """Retrieve recent log entries, optionally filtered by type."""
        entries = []
        if not os.path.exists(self.log_file):
            return entries
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                    if event_type is None or e["type"] == event_type:
                        entries.append(e)
                except Exception:
                    pass
        return entries[-limit:]


# ─── Event Bus ─────────────────────────────────────────────────────
class EventBus:
    """
    Reliable Publish/Subscribe Event Bus.
    
    Modules subscribe to event types. When an event is published,
    all subscribers are notified in separate threads to prevent blocking.
    Dead-letter queue captures failed deliveries.
    """

    def __init__(self, logger: ForensicLogger = None):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
        self._dead_letters: List[dict] = []
        self.logger = logger or ForensicLogger()
        self._event_count = 0

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe a callback to an event type."""
        with self._lock:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Remove a callback from an event type."""
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, data: dict = None, severity: str = "INFO"):
        """
        Publish an event to all subscribers.
        Each subscriber is called in its own thread for non-blocking delivery.
        Failed deliveries go to dead-letter queue.
        """
        data = data or {}
        self._event_count += 1
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": str(uuid.uuid4()),
        }

        # Forensic log every event
        self.logger.log(event_type, data, severity)

        with self._lock:
            callbacks = list(self._subscribers.get(event_type, []))

        for cb in callbacks:
            t = threading.Thread(target=self._safe_deliver, args=(cb, event), daemon=True)
            t.start()

    def _safe_deliver(self, callback: Callable, event: dict):
        """Deliver event to callback with error handling."""
        try:
            callback(event)
        except Exception as e:
            dead = {
                "event": event,
                "error": str(e),
                "callback": str(callback),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.logger.log("DEAD_LETTER", dead, severity="ERROR")

    async def publish_async(self, event_type: str, data: dict = None, severity: str = "INFO"):
        """Publish event and await callbacks if they are async."""
        data = data or {}
        self._event_count += 1
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": str(uuid.uuid4()),
            "priority": severity
        }
        self.logger.log(event_type, data, severity)
        
        with self._lock:
            callbacks = list(self._subscribers.get(event_type, []))
            
        tasks = []
        for cb in callbacks:
            if inspect.iscoroutinefunction(cb):
                tasks.append(asyncio.create_task(self._safe_deliver_async(cb, event)))
            else:
                threading.Thread(target=self._safe_deliver, args=(cb, event), daemon=True).start()
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_deliver_async(self, callback: Callable, event: dict):
        try:
            await callback(event)
        except Exception as e:
            dead = {
                "event": event,
                "error": str(e),
                "callback": str(callback),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._dead_letters.append(dead)
            self.logger.log("DEAD_LETTER", dead, severity="ERROR")

    def replay_events(self, start_seq: int = 0, event_type: str = None):
        """Replay events from forensic log."""
        entries = self.logger.get_entries(event_type=event_type, limit=1000)
        for e in entries:
            if e["seq"] >= start_seq:
                self.publish(e["type"], e["data"], e["severity"])

    def get_dead_letters(self) -> list:
        return list(self._dead_letters)

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "total_events_published": self._event_count,
                "subscriber_count": sum(len(v) for v in self._subscribers.values()),
                "event_types": list(self._subscribers.keys()),
                "dead_letters": len(self._dead_letters),
            }


# ─── Module Registry ──────────────────────────────────────────────
class ModuleRegistry:
    """
    Central registry of all Q-Void OS subsystems.
    Tracks module status, handles initialization order, and provides
    a unified interface for the controller.
    """

    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self._modules: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def register(self, name: str, module_obj: Any, description: str = ""):
        with self._lock:
            self._modules[name] = {
                "object": module_obj,
                "description": description,
                "status": "REGISTERED",
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }
        self.bus.publish("MODULE_REGISTERED", {"module": name, "description": description})

    def get(self, name: str) -> Optional[Any]:
        with self._lock:
            mod = self._modules.get(name)
            return mod["object"] if mod else None

    def set_status(self, name: str, status: str):
        with self._lock:
            if name in self._modules:
                self._modules[name]["status"] = status

    def list_modules(self) -> Dict[str, dict]:
        with self._lock:
            return {
                k: {"description": v["description"], "status": v["status"]}
                for k, v in self._modules.items()
            }


# ─── Boot Sequence ─────────────────────────────────────────────────
def create_system() -> tuple:
    """
    Factory function to create a fully wired Q-Void OS core.
    Returns (event_bus, forensic_logger, module_registry).
    """
    logger = ForensicLogger()
    bus = EventBus(logger)
    registry = ModuleRegistry(bus)

    bus.publish("SYSTEM_BOOT", {
        "version": QVOID_VERSION,
        "codename": CODENAME,
        "pid": os.getpid(),
    }, severity="CRITICAL")

    return bus, logger, registry


def create_system_v2(precog, mcp, rag, llm_adapter) -> tuple:
    """
    Factory function for v4 Agentic Architecture.
    Returns (event_bus, forensic_logger, module_registry, threat_pipeline).
    """
    bus, logger, registry = create_system()
    from core.threat_pipeline import ThreatPipeline
    pipeline = ThreatPipeline(precog, mcp, rag, llm_adapter, bus)
    return bus, logger, registry, pipeline


# ─── Self-Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[Q-VOID CORE] v{QVOID_VERSION} — {CODENAME}")
    print("[Q-VOID CORE] Running self-test...")

    bus, logger, registry = create_system()

    # Test event subscription
    received = []
    bus.subscribe("TEST_EVENT", lambda e: received.append(e))
    bus.publish("TEST_EVENT", {"msg": "hello from core"})
    time.sleep(0.1)

    assert len(received) == 1, "Event delivery failed"
    print(f"  ✓ Event bus: delivered {len(received)} event(s)")

    # Test forensic chain
    assert logger.verify_chain(), "Chain integrity check failed"
    print(f"  ✓ Forensic chain: integrity verified ({logger._event_count} entries)")

    # Test module registry
    registry.register("test_module", object(), "A test module")
    mods = registry.list_modules()
    assert "test_module" in mods
    print(f"  ✓ Module registry: {len(mods)} module(s) registered")

    print("[Q-VOID CORE] All tests passed. Core is operational.")
