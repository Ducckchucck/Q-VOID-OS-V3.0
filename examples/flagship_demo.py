"""Flagship Q-VOID OS demo pipeline.

Flow:
attacker command -> honeypot detection -> event bus -> polymorph mutation ->
AI prediction -> RAG-style response recommendation -> JSON report.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.qvoid_core import EventBus, ForensicLogger
from polymorphic.polymorph_engine import PolymorphEngine
from precog.precog_engine import PrecogEngine
from rag.rag_engine import RAGEngine
from trap.illusion_shell import SolipsismTrap, TrapSession


def run_demo(output_path: str | os.PathLike = "examples/demo_report.json") -> dict:
    """Run the flagship event-driven simulation and write a report."""
    with tempfile.TemporaryDirectory(prefix="qvoid-demo-") as temp_dir:
        logger = ForensicLogger(log_dir=str(Path(temp_dir) / "logs"))
        bus = EventBus(logger)
        events: list[dict] = []
        for event_type in [
            "THREAT_DETECTED",
            "POLYMORPH_EMERGENCY",
            "POLYMORPH_MUTATION",
            "PRECOG_PREDICTION",
            "RAG_QUERY",
        ]:
            bus.subscribe(event_type, lambda event, et=event_type: events.append({"type": et, "event": event}))

        polymorph = PolymorphEngine(bus, mutation_interval=3600)
        trap = SolipsismTrap(bus)
        precog = PrecogEngine(bus)
        rag = RAGEngine(bus)

        session = TrapSession("203.0.113.10", 4444, "demo-001")
        attacker_command = "cat /etc/shadow"
        trap_output = trap.process_command(session, attacker_command)
        prediction = precog.predict_vector("port 445 open smb windows", top_n=3)
        response = rag.query("suspicious credential access and SMB exposure", top_k=3)

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "flow": "attacker -> honeypot -> event bus -> polymorph -> AI -> report",
            "attacker_command": attacker_command,
            "trap_output_preview": trap_output[:160],
            "session": session.to_report(),
            "polymorph": polymorph.get_status(),
            "precog_prediction": prediction,
            "rag_response": response,
            "forensic_chain_intact": logger.verify_chain(),
            "events_observed": [{"type": item["type"], "event_id": item["event"].get("event_id")} for item in events],
        }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run_demo()
    print(json.dumps({
        "status": "SUCCESS",
        "report": "examples/demo_report.json",
        "events": len(result["events_observed"]),
        "top_prediction": result["precog_prediction"][0]["vector"],
    }, indent=2))
