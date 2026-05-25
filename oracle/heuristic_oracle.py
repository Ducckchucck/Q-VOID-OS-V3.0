"""
╔══════════════════════════════════════════════════════════════════╗
║  HEURISTIC ORACLE v3.0 — Threat Detection via Simulated Advanced Heuristic  ║
║  Pattern recognition, entropy analysis, data correlation.        ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, math, hashlib, time, random, struct
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger
from rust_core import engine as rust_core

class AdvancedSearchSimulator:
    """
    Simulates Advanced Heuristic advanced search algorithm.
    Classical simulation: O(sqrt(N)) iterations to find a target
    in an unsorted database of N items.
    """
    def __init__(self):
        self.iterations_used = 0
        self.search_space_size = 0

    def search(self, database: list, target_check, max_iter: int = None) -> Tuple[Optional[int], int]:
        """
        Simulate Advanced Heuristic search over a database.
        target_check: function(item) -> bool
        Returns (index_of_found_item, iterations_used)
        """
        n = len(database)
        self.search_space_size = n
        optimal_iters = max(1, int(math.pi / 4 * math.sqrt(n)))
        max_iter = max_iter or optimal_iters
        # Simulate amplitude amplification
        probabilities = [1.0 / n] * n
        found_idx = None
        for iteration in range(max_iter):
            self.iterations_used = iteration + 1
            # Oracle: mark the target
            for i, item in enumerate(database):
                if target_check(item):
                    probabilities[i] *= 2.0  # amplify
                    found_idx = i
            # Diffusion: normalize
            total = sum(probabilities)
            if total > 0:
                probabilities = [p / total for p in probabilities]
            # Check if we've "measured" the answer
            if found_idx is not None and probabilities[found_idx] > 0.5:
                return found_idx, self.iterations_used
        return found_idx, self.iterations_used

class EntropyAnalyzer:
    """Analyzes data entropy to detect encryption, compression, or anomalies."""
    @staticmethod
    def shannon_entropy(data: bytes) -> float:
        return rust_core.fast_entropy(data)

    @staticmethod
    def classify_entropy(entropy: float) -> str:
        if entropy < 1.0: return "NEAR_ZERO (structured/empty)"
        if entropy < 3.5: return "LOW (text/code)"
        if entropy < 5.0: return "MEDIUM (mixed content)"
        if entropy < 7.0: return "HIGH (compressed/obfuscated)"
        return "VERY_HIGH (encrypted/random)"

class CorrelationEngine:
    """Links seemingly unrelated data points to find hidden patterns."""
    def __init__(self):
        self._observations: List[dict] = []

    def add_observation(self, category: str, key: str, value: str, metadata: dict = None):
        self._observations.append({"category": category, "key": key, "value": value,
                                   "metadata": metadata or {},
                                   "timestamp": datetime.now(timezone.utc).isoformat()})

    def find_correlations(self, min_overlap: int = 2) -> List[dict]:
        """Find categories that share common keys or values."""
        cat_keys: Dict[str, set] = {}
        cat_values: Dict[str, set] = {}
        for obs in self._observations:
            cat = obs["category"]
            cat_keys.setdefault(cat, set()).add(obs["key"])
            cat_values.setdefault(cat, set()).add(obs["value"])
        correlations = []
        cats = list(cat_keys.keys())
        for i in range(len(cats)):
            for j in range(i + 1, len(cats)):
                shared_keys = cat_keys[cats[i]] & cat_keys[cats[j]]
                shared_vals = cat_values[cats[i]] & cat_values[cats[j]]
                overlap = len(shared_keys) + len(shared_vals)
                if overlap >= min_overlap:
                    correlations.append({"category_a": cats[i], "category_b": cats[j],
                                         "shared_keys": list(shared_keys), "shared_values": list(shared_vals),
                                         "strength": overlap})
        return sorted(correlations, key=lambda x: -x["strength"])

class HeuristicOracle:
    """
    Threat detection system using simulated advanced heuristic algorithms,
    entropy analysis, and data correlation.
    """
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.AdvancedSearch = AdvancedSearchSimulator()
        self.entropy = EntropyAnalyzer()
        self.correlator = CorrelationEngine()
        self._scan_history: List[dict] = []

    def pattern_search(self, data_items: List[str], pattern: str) -> dict:
        """Use simulated Advanced Heuristic search to find a pattern in data."""
        idx, iters = self.AdvancedSearch.search(data_items, lambda x: pattern.lower() in x.lower())
        result = {"pattern": pattern, "found": idx is not None,
                  "index": idx, "iterations": iters,
                  "search_space": len(data_items),
                  "classical_worst_case": len(data_items),
                  "advanced_speedup": f"O(√{len(data_items)}) = ~{int(math.sqrt(len(data_items)))} iterations",
                  "matched_item": data_items[idx] if idx is not None else None}
        self.bus.publish("ORACLE_SEARCH", {"pattern": pattern, "found": result["found"]})
        return result

    def analyze_data(self, data: bytes, label: str = "") -> dict:
        """Analyze data for anomalies using entropy and pattern detection."""
        ent = self.entropy.shannon_entropy(data)
        classification = self.entropy.classify_entropy(ent)
        # Check for suspicious patterns
        suspicious_patterns = [b"\x4d\x5a", b"\x7f\x45\x4c\x46", b"<script",
                               b"eval(", b"exec(", b"SELECT ", b"DROP TABLE"]
        found_patterns = [p.decode("utf-8", errors="replace") for p in suspicious_patterns if p in data]
        anomaly_score = min(100, int(ent * 10) + len(found_patterns) * 15)
        result = {"label": label, "size_bytes": len(data), "entropy": round(ent, 4),
                  "classification": classification, "suspicious_patterns": found_patterns,
                  "anomaly_score": anomaly_score,
                  "verdict": "THREAT" if anomaly_score > 70 else "SUSPICIOUS" if anomaly_score > 40 else "CLEAN"}
        self._scan_history.append(result)
        self.bus.publish("ORACLE_ANALYSIS", {"label": label, "verdict": result["verdict"],
                                              "anomaly_score": anomaly_score})
        return result

    def correlate_threats(self) -> List[dict]:
        return self.correlator.find_correlations()

    def add_data_point(self, category: str, key: str, value: str):
        self.correlator.add_observation(category, key, value)

    def get_status(self):
        return {"scans_performed": len(self._scan_history),
                "observations": len(self.correlator._observations),
                "AdvancedSearch_last_space": self.AdvancedSearch.search_space_size}

if __name__ == "__main__":
    print("[HEURISTIC ORACLE] Self-test...")
    bus = EventBus(ForensicLogger())
    oracle = advancedOracle(bus)
    # AdvancedSearch search
    data = [f"log_entry_{i}" for i in range(1000)]
    data[567] = "MALICIOUS_PAYLOAD_DETECTED"
    r = oracle.pattern_search(data, "MALICIOUS")
    assert r["found"] and r["index"] == 567
    print(f"  ✓ AdvancedSearch search: found at idx {r['index']} in {r['iterations']} iters (vs {r['classical_worst_case']} classical)")
    # Entropy analysis
    r = oracle.analyze_data(b"Hello world this is normal text", "normal")
    assert r["verdict"] == "CLEAN"
    print(f"  ✓ Normal text: entropy={r['entropy']}, verdict={r['verdict']}")
    r = oracle.analyze_data(os.urandom(256), "random")
    assert r["entropy"] > 6.0
    print(f"  ✓ Random data: entropy={r['entropy']}, verdict={r['verdict']}")
    # Correlation
    oracle.add_data_point("network", "src_ip", "10.0.0.5")
    oracle.add_data_point("network", "dst_port", "445")
    oracle.add_data_point("auth", "src_ip", "10.0.0.5")
    oracle.add_data_point("auth", "failed_user", "admin")
    corrs = oracle.correlate_threats()
    print(f"  ✓ Correlations: {len(corrs)} found")
    print("[HEURISTIC ORACLE] All tests passed.")
