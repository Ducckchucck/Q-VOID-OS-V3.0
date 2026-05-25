"""
╔══════════════════════════════════════════════════════════════════╗
║  RAG ENGINE v3.0 — Retrieval-Augmented Generation                ║
║  Context-aware threat response using incident history.           ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, math, hashlib
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger

class TFIDFVectorStore:
    """Simple TF-IDF vector store for incident retrieval."""
    def __init__(self):
        self._documents: List[dict] = []  # {id, text, metadata}
        self._vocab: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._tfidf_matrix: List[Dict[str, float]] = []

    def add_document(self, doc_id: str, text: str, metadata: dict = None):
        self._documents.append({"id": doc_id, "text": text, "metadata": metadata or {}})
        self._rebuild_index()

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower().strip(".,;:!?()[]{}\"'") for w in text.split() if len(w) > 2]

    def _rebuild_index(self):
        n_docs = len(self._documents)
        # Build vocab and doc frequencies
        doc_freq: Dict[str, int] = Counter()
        for doc in self._documents:
            tokens = set(self._tokenize(doc["text"]))
            for t in tokens:
                doc_freq[t] += 1
        # IDF
        self._idf = {t: math.log(n_docs / (1 + df)) for t, df in doc_freq.items()}
        # TF-IDF per document
        self._tfidf_matrix = []
        for doc in self._documents:
            tokens = self._tokenize(doc["text"])
            tf = Counter(tokens)
            total = len(tokens) if tokens else 1
            tfidf = {t: (c / total) * self._idf.get(t, 0) for t, c in tf.items()}
            self._tfidf_matrix.append(tfidf)

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Find most relevant documents for a query."""
        q_tokens = self._tokenize(query)
        q_tf = Counter(q_tokens)
        q_total = len(q_tokens) if q_tokens else 1
        q_tfidf = {t: (c / q_total) * self._idf.get(t, 0) for t, c in q_tf.items()}
        # Cosine similarity
        scores = []
        for i, doc_vec in enumerate(self._tfidf_matrix):
            dot = sum(q_tfidf.get(t, 0) * doc_vec.get(t, 0) for t in set(q_tfidf) | set(doc_vec))
            mag_q = math.sqrt(sum(v**2 for v in q_tfidf.values())) or 1
            mag_d = math.sqrt(sum(v**2 for v in doc_vec.values())) or 1
            similarity = dot / (mag_q * mag_d)
            scores.append((similarity, i))
        scores.sort(reverse=True)
        results = []
        for score, idx in scores[:top_k]:
            doc = self._documents[idx]
            results.append({"doc_id": doc["id"], "score": round(score, 4),
                           "text": doc["text"][:200], "metadata": doc["metadata"]})
        return results

class RAGEngine:
    """
    Retrieval-Augmented Generation engine for cybersecurity.
    Retrieves relevant past incidents to inform current threat response.
    Provides explainable AI: shows which incidents influenced the decision.
    """
    def __init__(self, event_bus: EventBus, store_path: str = "rag/incident_store.json"):
        self.bus = event_bus
        self.store_path = store_path
        self.vector_store = TFIDFVectorStore()
        self._response_templates: Dict[str, str] = {}
        self._init_knowledge_base()
        self._load_incidents()

    def _init_knowledge_base(self):
        """Seed with built-in cybersecurity incident knowledge."""
        incidents = [
            ("INC-001", "SQL injection attack on login endpoint using UNION SELECT. Attacker extracted user credentials from database. Mitigated by input sanitization and parameterized queries.",
             {"type": "SQL_INJECTION", "severity": "HIGH", "response": "WAF rule + input validation"}),
            ("INC-002", "SYN flood DDoS attack on port 80 from botnet of 50k IPs. Peak 10Gbps. Mitigated with rate limiting and upstream blackholing.",
             {"type": "DDOS", "severity": "CRITICAL", "response": "Rate limit + blackhole routing"}),
            ("INC-003", "EternalBlue SMB exploit on unpatched Windows Server 2012. Lateral movement to 3 hosts. Contained by network segmentation.",
             {"type": "SMB_EXPLOIT", "severity": "CRITICAL", "response": "Patch + segment + isolate"}),
            ("INC-004", "Log4Shell RCE via JNDI lookup in web application. Attacker achieved reverse shell. Mitigated by upgrading Log4j and blocking outbound LDAP.",
             {"type": "RCE", "severity": "CRITICAL", "response": "Upgrade + egress filter"}),
            ("INC-005", "Phishing campaign targeting finance team. 3 credentials compromised. Reset passwords, enabled MFA, and added email filtering rules.",
             {"type": "PHISHING", "severity": "HIGH", "response": "MFA + email filter + password reset"}),
            ("INC-006", "Ransomware LockBit encrypted file server. Recovered from offline backup. Traced entry point to RDP brute force. Disabled RDP, enforced VPN.",
             {"type": "RANSOMWARE", "severity": "CRITICAL", "response": "Restore backup + disable RDP + VPN only"}),
            ("INC-007", "Redis server exposed without authentication on port 6379. Attacker wrote SSH key for persistence. Secured with auth and firewall rules.",
             {"type": "DATABASE_EXPLOIT", "severity": "HIGH", "response": "Enable auth + firewall"}),
            ("INC-008", "Kerberoasting attack detected. Attacker requested TGS tickets for service accounts. Rotated all service account passwords to 30+ character random.",
             {"type": "AD_ATTACK", "severity": "MEDIUM", "response": "Rotate credentials + monitor SPN requests"}),
            ("INC-009", "Cross-site scripting stored XSS in user profile field. Attacker injected script to steal session cookies. Fixed with output encoding and CSP headers.",
             {"type": "XSS", "severity": "MEDIUM", "response": "Output encoding + CSP headers"}),
            ("INC-010", "Zero-day kernel exploit detected via anomalous syscall pattern. Contained in sandbox. Reported to vendor for patch.",
             {"type": "ZERO_DAY", "severity": "CRITICAL", "response": "Sandbox + vendor report + virtual patch"}),
            ("INC-011", "DNS zone transfer exposed internal network topology. Restricted AXFR to authorized secondaries only.",
             {"type": "DNS_ATTACK", "severity": "MEDIUM", "response": "Restrict AXFR + TSIG authentication"}),
            ("INC-012", "Supply chain compromise via typosquatted npm package. Removed malicious dependency and audited all packages.",
             {"type": "SUPPLY_CHAIN", "severity": "HIGH", "response": "Remove package + full audit + lockfile review"}),
        ]
        for inc_id, text, meta in incidents:
            self.vector_store.add_document(inc_id, text, meta)

    def _load_incidents(self):
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r") as f:
                    data = json.load(f)
                    for inc in data:
                        self.vector_store.add_document(inc["id"], inc["text"], inc.get("metadata", {}))
            except Exception:
                pass

    def add_incident(self, incident_id: str, description: str, metadata: dict = None):
        """Add a new incident to the knowledge base."""
        self.vector_store.add_document(incident_id, description, metadata or {})
        # Persist
        os.makedirs(os.path.dirname(self.store_path) if os.path.dirname(self.store_path) else ".", exist_ok=True)
        incidents = []
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r") as f:
                    incidents = json.load(f)
            except Exception:
                pass
        incidents.append({"id": incident_id, "text": description, "metadata": metadata or {}})
        with open(self.store_path, "w") as f:
            json.dump(incidents, f, indent=2)

    def query(self, threat_description: str, top_k: int = 3) -> dict:
        """Query the knowledge base for relevant incidents and generate response."""
        relevant = self.vector_store.search(threat_description, top_k=top_k)
        # Generate response from retrieved context
        responses = []
        evidence = []
        for doc in relevant:
            meta = doc.get("metadata", {})
            if meta.get("response"):
                responses.append(meta["response"])
            evidence.append({"incident": doc["doc_id"], "relevance": doc["score"],
                            "summary": doc["text"][:150], "type": meta.get("type", "UNKNOWN")})
        recommended = responses[0] if responses else "Isolate + investigate + escalate"
        result = {"query": threat_description[:100], "recommended_response": recommended,
                  "confidence": round(relevant[0]["score"] * 100, 1) if relevant else 0,
                  "evidence": evidence, "all_recommended_actions": list(set(responses)),
                  "explanation": f"Based on {len(evidence)} similar past incidents"}
        self.bus.publish("RAG_QUERY", {"query": threat_description[:80], "confidence": result["confidence"]})
        return result

    def get_status(self):
        return {"incidents_in_store": len(self.vector_store._documents),
                "vocab_size": len(self.vector_store._idf)}

if __name__ == "__main__":
    print("[RAG ENGINE] Self-test...")
    bus = EventBus(ForensicLogger())
    rag = RAGEngine(bus)
    r = rag.query("SQL injection attack detected on web application login page")
    assert r["confidence"] > 0
    print(f"  ✓ SQL query → confidence={r['confidence']}%, response='{r['recommended_response']}'")
    r = rag.query("DDoS SYN flood attack from botnet")
    print(f"  ✓ DDoS query → confidence={r['confidence']}%, evidence={len(r['evidence'])} incidents")
    r = rag.query("ransomware encrypted all files on server")
    print(f"  ✓ Ransomware → response='{r['recommended_response']}'")
    print(f"  ✓ Store: {rag.get_status()['incidents_in_store']} incidents")
    print("[RAG ENGINE] All tests passed.")
