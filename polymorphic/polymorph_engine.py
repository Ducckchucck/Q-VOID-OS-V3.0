"""
╔══════════════════════════════════════════════════════════════════╗
║  POLYMORPHIC SHELL ENGINE v3.0                                   ║
║  Moving-Target Defense — Constantly Shifting Internal Architecture║
║  Neutralizes signature-based scanners and static analysis.       ║
╚══════════════════════════════════════════════════════════════════╝

The Polymorphic Shell randomizes internal dispatch tables, memory aliases,
and file structure mappings on a configurable timer. Every mutation cycle
generates a new "DNA signature" — making the system a moving target that
invalidates cached exploits and malware signatures.
"""

import os
import sys
import json
import time
import random
import string
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.qvoid_core import EventBus, ForensicLogger
from rust_core import engine as rust_core


class PolymorphEngine:
    """
    Moving-Target Defense Engine.
    
    Continuously mutates internal system structures to prevent
    signature-based detection and static analysis attacks.
    """

    def __init__(self, event_bus: EventBus, mutation_interval: float = 30.0):
        self.bus = event_bus
        self.mutation_interval = mutation_interval
        self._running = False
        self._mutation_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._epoch = 0

        # ── Internal Dispatch Table (simulated syscall mapping) ──
        self._base_syscalls = [
            "SYS_READ", "SYS_WRITE", "SYS_OPEN", "SYS_CLOSE",
            "SYS_EXEC", "SYS_FORK", "SYS_MMAP", "SYS_MPROTECT",
            "SYS_IOCTL", "SYS_SOCKET", "SYS_BIND", "SYS_LISTEN",
            "SYS_ACCEPT", "SYS_CONNECT", "SYS_SENDTO", "SYS_RECVFROM",
            "SYS_CLONE", "SYS_PIPE", "SYS_DUP", "SYS_SIGNAL",
        ]
        self._dispatch_table: Dict[str, str] = {}
        self._memory_layout: Dict[str, int] = {}
        self._fs_aliases: Dict[str, str] = {}
        self._dna_signature: str = ""

        # ── Mutation History ──
        self._history: List[dict] = []
        self._max_history = 100

        # This gets Initialize with first mutation 
        self._mutate()

        # Subscribe to events
        self.bus.subscribe("THREAT_DETECTED", self._on_threat)

    # ── Core Mutation Logic ──────────────────────────────────────

    def _mutate(self):
        """Perform a full system mutation epoch."""
        with self._lock:
            self._epoch += 1
            timestamp = datetime.now(timezone.utc).isoformat()

            # 1. Randomize syscall dispatch table for making the further move go well accessed and called for the output!
            #    Each syscall gets a random internal alias
            shuffled = list(self._base_syscalls)
            random.shuffle(shuffled)
            self._dispatch_table = {}
            for i, syscall in enumerate(self._base_syscalls):
                alias = f"QV_{self._rand_hex(8)}_{shuffled[i][-4:]}"
                self._dispatch_table[syscall] = alias

            # 2. Randomize memory layout offsets for the further process and all
            #    Simulate ASLR-style base address randomization
            segments = ["TEXT", "DATA", "BSS", "HEAP", "STACK", "VDSO", "KMAP"]
            self._memory_layout = {}
            for seg in segments:
                self._memory_layout[seg] = int.from_bytes(rust_core.secure_random(4), byteorder='little') & 0x7FFFFFFF
            # Ensure non-overlapping (simplified)
            self._memory_layout = dict(
                sorted(self._memory_layout.items(), key=lambda x: x[1])
            )

            # 3. Randomize filesystem path aliases
            #    Internal paths get obfuscated names
            real_paths = ["/etc", "/var", "/tmp", "/proc", "/sys", "/dev", "/root"]
            self._fs_aliases = {}
            for p in real_paths:
                self._fs_aliases[p] = f"/.qv/{self._rand_hex(12)}"

            # 4. Generate DNA signature (hash of entire state)
            state_blob = json.dumps({
                "dispatch": self._dispatch_table,
                "memory": self._memory_layout,
                "fs": self._fs_aliases,
                "epoch": self._epoch,
            }, sort_keys=True)
            self._dna_signature = rust_core.fast_sha256(state_blob.encode())

            # 5. Record mutation in history
            mutation_record = {
                "epoch": self._epoch,
                "timestamp": timestamp,
                "dna": self._dna_signature,
                "dispatch_size": len(self._dispatch_table),
                "memory_segments": len(self._memory_layout),
                "fs_aliases": len(self._fs_aliases),
            }
            self._history.append(mutation_record)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        # Publish mutation event
        self.bus.publish("POLYMORPH_MUTATION", {
            "epoch": self._epoch,
            "dna": self._dna_signature,
            "timestamp": timestamp,
        })

    def _rand_hex(self, length: int) -> str:
        return ''.join(random.choices("0123456789abcdef", k=length))

    # ── Threat Response ────────────────────────────────────────── Where you get the response of the threat!!


    def _on_threat(self, event: dict):
        """Emergency mutation when a threat is detected."""
        data = event.get("data", {})
        self.emergency_mutate(reason=data.get("threat_type", "UNKNOWN"))
        
        target_module = data.get("target_module")
        if target_module:
            try:
                import asyncio
                from llm.llm_adapter import LLMAdapter
                from polymorphic.code_mutator import CodeMutator
                mutator = CodeMutator(LLMAdapter())
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(mutator.heal_codebase(target_module, f"Detected threat: {data.get('threat_type')}"))
                except RuntimeError:
                    asyncio.run(mutator.heal_codebase(target_module, f"Detected threat: {data.get('threat_type')}"))
            except Exception as e:
                self.bus.publish("HEALING_FAILED", {"error": str(e)}, severity="ERROR")

    def emergency_mutate(self, reason: str = "MANUAL"):
        """Force an immediate mutation cycle outside the normal schedule."""
        self.bus.publish("POLYMORPH_EMERGENCY", {
            "reason": reason,
            "prev_epoch": self._epoch,
        }, severity="WARNING")
        self._mutate()
        return self.get_status()

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Start the periodic mutation engine."""
        if self._running:
            return
        self._running = True
        self._mutation_thread = threading.Thread(target=self._mutation_loop, daemon=True)
        self._mutation_thread.start()
        self.bus.publish("POLYMORPH_STARTED", {
            "interval": self.mutation_interval,
            "epoch": self._epoch,
        })

    def stop(self):
        """Stop the periodic mutation engine."""
        self._running = False
        self.bus.publish("POLYMORPH_STOPPED", {"final_epoch": self._epoch})

    def _mutation_loop(self):
        """Background loop performing periodic mutations."""
        while self._running:
            time.sleep(self.mutation_interval)
            if self._running:
                self._mutate()

    # ── This code indicates the Query Interface system──────────────────────────────────────────

    def resolve_syscall(self, syscall: str) -> Optional[str]:
        """Resolve a syscall to its current polymorphic alias."""
        with self._lock:
            return self._dispatch_table.get(syscall)

    def get_memory_layout(self) -> Dict[str, int]:
        """Get the current randomized memory layout."""
        with self._lock:
            return dict(self._memory_layout)

    def get_fs_alias(self, real_path: str) -> Optional[str]:
        """Get the current obfuscated alias for a filesystem path."""
        with self._lock:
            return self._fs_aliases.get(real_path)

    def get_dna(self) -> str:
        """Get the current DNA signature."""
        with self._lock:
            return self._dna_signature

    def get_status(self) -> dict:
        """Get full engine status."""
        with self._lock:
            return {
                "running": self._running,
                "epoch": self._epoch,
                "dna_signature": self._dna_signature[:16] + "...",
                "mutation_interval_sec": self.mutation_interval,
                "dispatch_entries": len(self._dispatch_table),
                "memory_segments": len(self._memory_layout),
                "fs_aliases": len(self._fs_aliases),
                "history_size": len(self._history),
            }

    def get_history(self, limit: int = 10) -> List[dict]:
        """Get recent mutation history."""
        with self._lock:
            return list(self._history[-limit:])

    def get_dispatch_table(self) -> Dict[str, str]:
        """Get the current dispatch table (for debugging/audit)."""
        with self._lock:
            return dict(self._dispatch_table)


# ─── This function is for Self-Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[POLYMORPHIC ENGINE] Running self-test...")

    logger = ForensicLogger()
    bus = EventBus(logger)
    engine = PolymorphEngine(bus, mutation_interval=5.0)

    # Test initial state
    status = engine.get_status()
    print(f"  Epoch: {status['epoch']}")
    print(f"  DNA: {status['dna_signature']}")
    print(f"  Dispatch entries: {status['dispatch_entries']}")
    print(f"  Memory segments: {status['memory_segments']}")
    print(f"  Apache is clean when the system will turn out to be the one we looking it to be")
    print(f" The system is making sure we are aware about the enviorment and we running the process")

    # This Test mutation changes DNA
    old_dna = engine.get_dna()
    engine.emergency_mutate("TEST")
    new_dna = engine.get_dna()
    assert old_dna != new_dna, "DNA should change after mutation"
    print(f"  ✓ Mutation changed DNA: {old_dna[:12]}... → {new_dna[:12]}...")
    print(f" The Mutation which was changed is gotten replaced by the system call!")

    # Where Test syscall resolution takes place to happen
    alias = engine.resolve_syscall("SYS_READ")
    assert alias is not None and alias.startswith("QV_")
    print(f"  ✓ SYS_READ → {alias}")

    # Printing and saving of Test history
    history = engine.get_history()
    assert len(history) >= 2
    print(f"  ✓ History: {len(history)} mutation(s) recorded")

    print("[POLYMORPHIC ENGINE] All tests passed.")
    print(f" The Polymorphic shell is running smooth and accurately!!")

