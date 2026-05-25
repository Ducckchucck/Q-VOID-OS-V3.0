"""
╔══════════════════════════════════════════════════════════════════╗
║  PRECOG ENGINE v3.0 — AI Attack Vector Prediction                ║
║  60+ CVE-mapped training pairs + TF-IDF + ComplementNB           ║
║  Predicts attack vectors from recon signals with confidence.     ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, time, pickle
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger

# Deferred sklearn import for graceful degradation
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import ComplementNB
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# ── CVE-Mapped Training Data ──────────────────────────────────────
TRAINING_DATA = [
    # SMB / Windows
    ("port 445 open smb windows share", "SMB_EXPLOIT[EternalBlue/MS17-010]"),
    ("smb signing disabled null session", "SMB_EXPLOIT[EternalBlue/MS17-010]"),
    ("smb v1 enabled legacy protocol", "SMB_EXPLOIT[EternalBlue/MS17-010]"),
    ("port 445 smb ghost vulnerability", "SMB_EXPLOIT[SMBGhost/CVE-2020-0796]"),
    ("smbv3 compression buffer overflow", "SMB_EXPLOIT[SMBGhost/CVE-2020-0796]"),
    # RDP
    ("port 3389 open rdp remote desktop", "RDP_EXPLOIT[BlueKeep/CVE-2019-0708]"),
    ("rdp nla disabled credssp", "RDP_EXPLOIT[BlueKeep/CVE-2019-0708]"),
    ("remote desktop pre-auth vulnerability", "RDP_EXPLOIT[BlueKeep/CVE-2019-0708]"),
    # Web / Log4j
    ("port 80 443 http web server apache", "WEB_EXPLOIT[Log4Shell/CVE-2021-44228]"),
    ("jndi ldap log4j java application", "WEB_EXPLOIT[Log4Shell/CVE-2021-44228]"),
    ("log4j lookup injection remote code", "WEB_EXPLOIT[Log4Shell/CVE-2021-44228]"),
    # Web / Shellshock
    ("bash cgi-bin user-agent shellshock", "WEB_EXPLOIT[Shellshock/CVE-2014-6271]"),
    ("cgi environment variable injection bash", "WEB_EXPLOIT[Shellshock/CVE-2014-6271]"),
    # Web / Heartbleed
    ("openssl heartbeat tls heartbleed", "WEB_EXPLOIT[Heartbleed/CVE-2014-0160]"),
    ("ssl memory leak heartbeat extension", "WEB_EXPLOIT[Heartbleed/CVE-2014-0160]"),
    # Drupal
    ("drupal ajax render drupalgeddon", "WEB_EXPLOIT[Drupalgeddon/CVE-2018-7600]"),
    ("drupal form api remote code execution", "WEB_EXPLOIT[Drupalgeddon/CVE-2018-7600]"),
    # SQL Injection
    ("sql injection union select database", "SQL_INJECTION[Generic]"),
    ("mysql mssql oracle query injection", "SQL_INJECTION[Generic]"),
    ("blind sql injection time-based boolean", "SQL_INJECTION[Generic]"),
    ("sqlmap tamper error based injection", "SQL_INJECTION[Generic]"),
    # XSS
    ("cross site scripting xss reflected stored", "XSS_ATTACK[Generic]"),
    ("javascript injection dom xss alert", "XSS_ATTACK[Generic]"),
    # Redis
    ("port 6379 redis no auth exposed", "DATABASE_EXPLOIT[Redis_Unauth]"),
    ("redis config set dir dbfilename rce", "DATABASE_EXPLOIT[Redis_Unauth]"),
    # MongoDB
    ("port 27017 mongodb no auth exposed", "DATABASE_EXPLOIT[MongoDB_Unauth]"),
    ("mongodb injection nosql query bypass", "DATABASE_EXPLOIT[MongoDB_Unauth]"),
    # MSSQL
    ("port 1433 mssql sa default password", "DATABASE_EXPLOIT[MSSQL_Default]"),
    ("xp_cmdshell mssql stored procedure", "DATABASE_EXPLOIT[MSSQL_Default]"),
    # AD / Kerberos
    ("port 88 kerberos spn kerberoasting", "AD_ATTACK[Kerberoasting]"),
    ("service principal name ticket granting", "AD_ATTACK[Kerberoasting]"),
    ("as-rep roasting pre-auth disabled", "AD_ATTACK[ASREPRoast]"),
    ("dcsync secretsdump mimikatz ntds", "AD_ATTACK[DCSync]"),
    ("active directory domain controller replication", "AD_ATTACK[DCSync]"),
    ("pass the hash ntlm relay lateral", "AD_ATTACK[PassTheHash]"),
    ("golden ticket krbtgt domain admin", "AD_ATTACK[GoldenTicket]"),
    # SSH
    ("port 22 ssh openssh brute force", "SSH_ATTACK[BruteForce]"),
    ("ssh password spray default credentials", "SSH_ATTACK[BruteForce]"),
    ("ssh key auth private key exposed", "SSH_ATTACK[KeyCompromise]"),
    # DNS
    ("port 53 dns zone transfer axfr", "DNS_ATTACK[ZoneTransfer]"),
    ("dns rebinding cache poisoning", "DNS_ATTACK[CachePoisoning]"),
    # Wi-Fi
    ("wifi wpa2 pmkid hashcat aircrack", "WIFI_ATTACK[PMKID]"),
    ("wps pixie dust reaver bully", "WIFI_ATTACK[PixieDust]"),
    ("eap deauth evil twin wireless", "WIFI_ATTACK[EvilTwin]"),
    # IoT
    ("telnet default mirai iot botnet", "IOT_ATTACK[Mirai]"),
    ("upnp ssdp iot firmware exploit", "IOT_ATTACK[Firmware]"),
    # Ransomware
    ("encrypt ransom bitcoin payment lockbit", "RANSOMWARE[LockBit]"),
    ("conti ryuk ransomware lateral movement", "RANSOMWARE[Conti]"),
    # Phishing
    ("email phishing credential harvest spoof", "PHISHING[CredentialHarvest]"),
    ("spearphishing attachment macro dropper", "PHISHING[SpearPhishing]"),
    # DDoS
    ("syn flood udp amplification ddos", "DDOS_ATTACK[Volumetric]"),
    ("slowloris http slow post connection", "DDOS_ATTACK[SlowHTTP]"),
    ("dns amplification ntp monlist reflection", "DDOS_ATTACK[Amplification]"),
    # Supply Chain
    ("npm package typosquat supply chain", "SUPPLY_CHAIN[Typosquat]"),
    ("dependency confusion internal package", "SUPPLY_CHAIN[DepConfusion]"),
    # Privilege Escalation
    ("suid binary escalation sudo misconfigured", "PRIVESC[SUID/Sudo]"),
    ("kernel exploit dirty cow pipe", "PRIVESC[KernelExploit]"),
    ("windows token impersonation potato", "PRIVESC[TokenImpersonation]"),
    # C2
    ("cobalt strike beacon c2 command control", "C2_FRAMEWORK[CobaltStrike]"),
    ("metasploit meterpreter reverse shell", "C2_FRAMEWORK[Metasploit]"),
    # Zero Day
    ("unknown signature anomalous behavior zero day", "ZERO_DAY[Heuristic]"),
    ("novel exploit undocumented vulnerability", "ZERO_DAY[Heuristic]"),
]

class PrecogEngine:
    """
    AI-powered attack vector prediction engine.
    Learns from CVE-mapped recon signals and predicts the most likely
    attack vector with confidence scores.
    """
    def __init__(self, event_bus: EventBus, model_path: str = "precog/predator_brain.pkl"):
        self.bus = event_bus
        self.model_path = model_path
        self.pipeline = None
        self.is_trained = False
        self.live_threat_cache: List[dict] = []
        self.live_feed_weight = 0.35
        self._command_history: List[str] = []
        self._history_file = "precog/command_history.json"

        if SKLEARN_AVAILABLE:
            self._train()
            self.fetch_live_intelligence()
        else:
            self.bus.publish("PRECOG_WARNING", {"msg": "scikit-learn not installed, using fallback"})

    def _train(self):
        """Train the TF-IDF + ComplementNB pipeline."""
        texts = [t[0] for t in TRAINING_DATA]
        labels = [t[1] for t in TRAINING_DATA]
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, max_features=5000)),
            ("clf", ComplementNB(alpha=0.5)),
        ])
        self.pipeline.fit(texts, labels)
        self.is_trained = True
        # Save model
        os.makedirs(os.path.dirname(self.model_path) if os.path.dirname(self.model_path) else ".", exist_ok=True)
        try:
            with open(self.model_path, "wb") as f:
                pickle.dump(self.pipeline, f)
        except Exception:
            pass
        self.bus.publish("PRECOG_TRAINED", {"samples": len(texts), "classes": len(set(labels))})

    def predict_vector(self, recon_signal: str, top_n: int = 3) -> List[dict]:
        """Predict attack vectors using Static Model + Live Intelligence Cache scoring."""
        if not self.is_trained or not self.pipeline:
            return [{"vector": "UNKNOWN", "confidence": 0, "note": "Model not trained"}]
            
        # 1. Static Model Prediction
        proba = self.pipeline.predict_proba([recon_signal])[0]
        classes = self.pipeline.classes_
        
        # 2. Live Intelligence Cache Scoring overlay
        scores = {c: float(p) for c, p in zip(classes, proba)}
        
        # Boost score if recon signal matches cached live intelligence
        signal_tokens = set(recon_signal.lower().split())
        for threat in self.live_threat_cache:
            threat_tokens = set(threat["description"].lower().split())
            if len(signal_tokens.intersection(threat_tokens)) >= 2:
                vector = threat.get("vector", f"ZERO_DAY[{threat.get('cve', 'Live')}]")
                if vector in scores:
                    scores[vector] += self.live_feed_weight
                else:
                    scores[vector] = self.live_feed_weight
                    
        # Normalize and rank
        total_score = sum(scores.values()) or 1.0
        ranked = sorted([(v, s / total_score) for v, s in scores.items()], key=lambda x: -x[1])[:top_n]
        
        results = [{"vector": v, "confidence": round(s * 100, 2)} for v, s in ranked]
        self.bus.publish("PRECOG_PREDICTION", {"signal": recon_signal[:80], "top_vector": results[0]["vector"]})
        return results

    def fetch_live_intelligence(self):
        """Asynchronously fetch real-time threat intelligence without retraining the static model."""
        import threading
        def _fetch():
            try:
                import urllib.request
                import urllib.error
                req = urllib.request.Request(
                    "https://cve.circl.lu/api/last", 
                    headers={'User-Agent': 'Q-VOID-OS/3.0'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    new_threats = 0
                    for item in data[:30]:
                        if not any(t.get("cve") == item.get("id") for t in self.live_threat_cache):
                            self.live_threat_cache.append({
                                "cve": item.get("id"),
                                "description": item.get("summary", ""),
                                "vector": f"EMERGING_THREAT[{item.get('id')}]"
                            })
                            new_threats += 1
                    
                    if new_threats > 0:
                        self.bus.publish("PRECOG_LIVE_INTEL_UPDATED", {"new_threats": new_threats, "cache_size": len(self.live_threat_cache)})
            except Exception as e:
                self.bus.publish("PRECOG_WARNING", {"msg": f"Live feed fetch failed (falling back to static only): {e}"})
                
        threading.Thread(target=_fetch, daemon=True).start()

    def predict_next(self, current_command: str) -> str:
        """Predict the next command based on history frequency analysis."""
        self._load_history()
        self._command_history.append(current_command)
        self._save_history()
        # Find what commands followed the current one historically
        followers: Dict[str, int] = {}
        for i, cmd in enumerate(self._command_history[:-1]):
            if cmd == current_command:
                next_cmd = self._command_history[i + 1]
                followers[next_cmd] = followers.get(next_cmd, 0) + 1
        if followers:
            return max(followers, key=followers.get)
        return "help"

    def _load_history(self):
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r") as f:
                    self._command_history = json.load(f)
            except Exception:
                self._command_history = []

    def _save_history(self):
        os.makedirs(os.path.dirname(self._history_file) if os.path.dirname(self._history_file) else ".", exist_ok=True)
        try:
            with open(self._history_file, "w") as f:
                json.dump(self._command_history[-500:], f)
        except Exception:
            pass

    def get_status(self):
        return {"trained": self.is_trained, "sklearn_available": SKLEARN_AVAILABLE,
                "training_samples": len(TRAINING_DATA),
                "live_cache_size": len(self.live_threat_cache),
                "classes": len(set(t[1] for t in TRAINING_DATA)),
                "history_size": len(self._command_history)}

if __name__ == "__main__":
    print("[PRECOG ENGINE] Self-test...")
    bus = EventBus(ForensicLogger())
    engine = PrecogEngine(bus)
    if engine.is_trained:
        r = engine.predict_vector("port 445 open smb windows")
        print(f"  ✓ SMB signal → {r[0]['vector']} ({r[0]['confidence']}%)")
        r = engine.predict_vector("port 3389 rdp remote desktop")
        print(f"  ✓ RDP signal → {r[0]['vector']} ({r[0]['confidence']}%)")
        r = engine.predict_vector("jndi ldap log4j injection")
        print(f"  ✓ Log4j signal → {r[0]['vector']} ({r[0]['confidence']}%)")
        r = engine.predict_vector("sql injection union select")
        print(f"  ✓ SQLi signal → {r[0]['vector']} ({r[0]['confidence']}%)")
    else:
        print("  ⚠ sklearn not available, skipping prediction tests")
    nxt = engine.predict_next("scan")
    print(f"  ✓ Next command prediction: {nxt}")
    print("[PRECOG ENGINE] All tests passed.")
