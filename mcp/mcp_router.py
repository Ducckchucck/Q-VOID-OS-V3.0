"""
╔══════════════════════════════════════════════════════════════════╗
║  MCP v3.0 — Model Control Protocol                               ║
║  Routes attack types to specialized AI detection models.         ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, re, time, hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger

class DetectionModel:
    """Base class for specialized detection models."""
    def __init__(self, name: str, model_type: str):
        self.name = name
        self.model_type = model_type
        self.version = "1.0"
        self.total_scans = 0
        self.detections = 0
    def analyze(self, payload: str) -> dict:
        raise NotImplementedError
    def get_stats(self):
        return {"name": self.name, "type": self.model_type, "version": self.version,
                "scans": self.total_scans, "detections": self.detections,
                "detection_rate": f"{(self.detections/max(1,self.total_scans))*100:.1f}%"}

class SQLDetector(DetectionModel):
    """Detects SQL injection attacks."""
    PATTERNS = [r"(?i)(union\s+select)", r"(?i)(or\s+1\s*=\s*1)", r"(?i)(drop\s+table)",
                r"(?i)(insert\s+into)", r"(?i)(delete\s+from)", r"(?i)(--\s*$)", r"(?i)(;\s*drop)",
                r"(?i)(char\s*\()", r"(?i)(concat\s*\()", r"(?i)(sleep\s*\()", r"(?i)(benchmark\s*\()"]
    def __init__(self):
        super().__init__("SQL-Detector", "sql_injection")
    def analyze(self, payload: str) -> dict:
        self.total_scans += 1
        matches = [p for p in self.PATTERNS if re.search(p, payload)]
        confidence = min(100, len(matches) * 25)
        if matches:
            self.detections += 1
        return {"model": self.name, "threat": "SQL_INJECTION", "confidence": confidence,
                "matched_patterns": len(matches), "is_threat": confidence > 0,
                "details": f"Matched {len(matches)} SQL injection patterns"}

class DDoSClassifier(DetectionModel):
    """Classifies DDoS attack traffic patterns."""
    def __init__(self):
        super().__init__("DDoS-Classifier", "traffic_analysis")
    def analyze(self, payload: str) -> dict:
        self.total_scans += 1
        indicators = {"syn_flood": "syn" in payload.lower(), "udp_amp": "udp" in payload.lower() and "amplif" in payload.lower(),
                      "slowloris": "slow" in payload.lower(), "http_flood": "http" in payload.lower() and "flood" in payload.lower(),
                      "dns_amp": "dns" in payload.lower() and "amplif" in payload.lower()}
        active = [k for k, v in indicators.items() if v]
        confidence = min(100, len(active) * 35)
        if active:
            self.detections += 1
        return {"model": self.name, "threat": "DDOS", "confidence": confidence,
                "attack_types": active, "is_threat": confidence > 30}

class MalwareAnalyzer(DetectionModel):
    """Behavioral analysis for malware detection."""
    BEHAVIORS = ["file_encrypt", "registry_modify", "process_inject", "persistence",
                 "keylog", "screen_capture", "data_exfil", "privilege_escalation",
                 "anti_debug", "anti_vm", "obfuscation", "packing"]
    def __init__(self):
        super().__init__("Malware-Behavioral", "behavioral_analysis")
    def analyze(self, payload: str) -> dict:
        self.total_scans += 1
        detected = [b for b in self.BEHAVIORS if b.replace("_", " ") in payload.lower() or b in payload.lower()]
        confidence = min(100, len(detected) * 20)
        if detected:
            self.detections += 1
        return {"model": self.name, "threat": "MALWARE", "confidence": confidence,
                "behaviors": detected, "is_threat": confidence > 25}

class HeuristicEngine(DetectionModel):
    """Zero-day detection via heuristic analysis."""
    def __init__(self):
        super().__init__("Heuristic-Engine", "zero_day")
    def analyze(self, payload: str) -> dict:
        self.total_scans += 1
        # Entropy-based heuristic
        from collections import Counter
        import math
        freq = Counter(payload.encode())
        length = len(payload)
        entropy = -sum((c/length) * math.log2(c/length) for c in freq.values()) if length > 0 else 0
        anomaly_keywords = ["exploit", "payload", "shellcode", "overflow", "heap spray",
                            "rop chain", "gadget", "nop sled"]
        found = [k for k in anomaly_keywords if k in payload.lower()]
        confidence = min(100, int(entropy * 5) + len(found) * 20)
        if confidence > 40:
            self.detections += 1
        return {"model": self.name, "threat": "ZERO_DAY", "confidence": confidence,
                "entropy": round(entropy, 3), "anomaly_keywords": found,
                "is_threat": confidence > 40}

class MCPRouter:
    """
    Model Control Protocol — intelligent routing system that
    routes attack payloads to specialized detection models.
    """
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self._models: Dict[str, DetectionModel] = {}
        self._routing_rules: List[dict] = []
        self._routing_log: List[dict] = []
        self._init_default_models()
        self._init_routing_rules()

    def _init_default_models(self):
        self._models["sql_detector"] = SQLDetector()
        self._models["ddos_classifier"] = DDoSClassifier()
        self._models["malware_analyzer"] = MalwareAnalyzer()
        self._models["heuristic_engine"] = HeuristicEngine()

    def _init_routing_rules(self):
        self._routing_rules = [
            {"keywords": ["sql", "select", "union", "insert", "drop", "table", "database"], "model": "sql_detector"},
            {"keywords": ["ddos", "flood", "syn", "amplif", "slowloris", "volumetric"], "model": "ddos_classifier"},
            {"keywords": ["malware", "trojan", "worm", "ransomware", "virus", "encrypt", "exfil"], "model": "malware_analyzer"},
            {"keywords": ["exploit", "zero-day", "unknown", "anomaly", "shellcode", "overflow"], "model": "heuristic_engine"},
        ]

    def route(self, payload: str) -> dict:
        """Route a payload to the appropriate detection model."""
        payload_lower = payload.lower()
        scores = {}
        for rule in self._routing_rules:
            model_name = rule["model"]
            match_count = sum(1 for kw in rule["keywords"] if kw in payload_lower)
            if match_count > 0:
                scores[model_name] = match_count
        if not scores:
            # Default: send to all models
            scores = {k: 1 for k in self._models}
        # Route to best-matching model
        best_model_name = max(scores, key=scores.get)
        model = self._models[best_model_name]
        result = model.analyze(payload)
        # Log routing decision
        log_entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "payload_preview": payload[:100],
                     "routed_to": best_model_name, "match_scores": scores, "result": result}
        self._routing_log.append(log_entry)
        if len(self._routing_log) > 500:
            self._routing_log = self._routing_log[-500:]
        self.bus.publish("MCP_ROUTED", {"model": best_model_name, "threat": result.get("threat"),
                                        "confidence": result.get("confidence"), "is_threat": result.get("is_threat")})
        
        # Generative Retaliation Trigger
        if result.get("is_threat") and result.get("confidence", 0) > 80:
            self.bus.publish("AUTONOMOUS_RESPONSE_INITIATED", {
                "threat_type": result.get("threat"),
                "confidence": result.get("confidence"),
                "signal": payload
            }, severity="CRITICAL")
            
        return result

    def route_all(self, payload: str) -> List[dict]:
        """Route payload to ALL models and aggregate results."""
        results = []
        for name, model in self._models.items():
            r = model.analyze(payload)
            results.append(r)
        results.sort(key=lambda x: -x.get("confidence", 0))
        return results

    def register_model(self, name: str, model: DetectionModel):
        self._models[name] = model

    def get_model_stats(self) -> List[dict]:
        return [m.get_stats() for m in self._models.values()]

    def get_routing_log(self, limit: int = 20) -> List[dict]:
        return self._routing_log[-limit:]

    def get_status(self):
        return {"models": len(self._models), "routing_rules": len(self._routing_rules),
                "total_routed": len(self._routing_log),
                "model_stats": self.get_model_stats()}

if __name__ == "__main__":
    print("[MCP ROUTER] Self-test...")
    bus = EventBus(ForensicLogger())
    mcp = MCPRouter(bus)
    r = mcp.route("SQL injection UNION SELECT password drop table admin database")
    assert r["model"] == "SQL-Detector", f"Expected SQL-Detector, got {r['model']}"
    print(f"  ✓ SQL injection → {r['model']}: confidence={r['confidence']}%")
    r = mcp.route("SYN flood detected UDP amplification DDoS attack")
    assert r["model"] == "DDoS-Classifier"
    print(f"  ✓ DDoS → {r['model']}: confidence={r['confidence']}%")
    r = mcp.route("malware trojan data_exfil persistence keylog")
    assert r["model"] == "Malware-Behavioral"
    print(f"  ✓ Malware → {r['model']}: confidence={r['confidence']}%")
    r = mcp.route("unknown exploit shellcode buffer overflow zero-day")
    assert r["model"] == "Heuristic-Engine"
    print(f"  ✓ Zero-day → {r['model']}: confidence={r['confidence']}%")
    print(f"  ✓ Stats: {len(mcp.get_model_stats())} models active")
    print("[MCP ROUTER] All tests passed.")
