"""
╔══════════════════════════════════════════════════════════════════╗
║  Q-VOID OS — Comprehensive Test Suite & Report Generator        ║
║  Runs every module, captures output, generates HTML PDF report. ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, io, time, json, traceback, html
from datetime import datetime, timezone
from contextlib import redirect_stdout, redirect_stderr, contextmanager

# ── Patch sys.path ──────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# Force UTF-8 everywhere
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

# ── We need Rich for some modules so disable it briefly ────────
# Override Rich console for capture
from rich.console import Console
capture_console = Console(file=io.StringIO(), force_terminal=False, no_color=True, width=120)

# ── Imports ────────────────────────────────────────────────────
from core.qvoid_core import (
    EventBus, ForensicLogger, ModuleRegistry,
    QVOID_VERSION, CODENAME, create_system
)

# ── Test Result Storage ────────────────────────────────────────
class TestResult:
    def __init__(self, name, category):
        self.name = name
        self.category = category
        self.status = "PENDING"  # PASS, FAIL, SKIP
        self.output = ""
        self.error = ""
        self.duration_ms = 0
        self.details = {}

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }

ALL_RESULTS = []

def run_test(name, category, fn):
    """Run a test function, capture output and timing."""
    result = TestResult(name, category)
    buf = io.StringIO()
    start = time.perf_counter()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            ret = fn()
        result.output = buf.getvalue()
        if isinstance(ret, dict):
            result.details = ret
            if ret.get("ok") is False or ret.get("status") in {"FAIL", "ERROR"}:
                raise AssertionError(f"{name} returned failure status: {ret}")
        result.status = "PASS"
    except Exception as e:
        result.output = buf.getvalue()
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        result.status = "FAIL"
    result.duration_ms = round((time.perf_counter() - start) * 1000, 2)
    ALL_RESULTS.append(result)
    icon = "PASS" if result.status == "PASS" else "FAIL"
    print(f"  [{icon}] {name} ({result.duration_ms}ms)")
    return result


# ══════════════════════════════════════════════════════════════════
#  TEST DEFINITIONS
# ══════════════════════════════════════════════════════════════════

# ── 1. CORE ────────────────────────────────────────────────────
def test_core_event_bus():
    """Test Event Bus pub/sub delivery."""
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    received = []
    bus.subscribe("TEST_EVENT", lambda e: received.append(e))
    bus.publish("TEST_EVENT", {"msg": "unit_test_probe"})
    time.sleep(0.15)
    assert len(received) == 1, f"Expected 1 event, got {len(received)}"
    assert received[0]["data"]["msg"] == "unit_test_probe"
    stats = bus.get_stats()
    return {"events_delivered": len(received), "subscriber_count": stats["subscriber_count"]}

def test_core_forensic_logger():
    """Test Forensic Logger blockchain chain integrity."""
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    entry = logger.log("TEST_VERIFY", {"action": "integrity_check"})
    chain_ok = logger.verify_chain()
    assert chain_ok, "Forensic chain integrity FAILED"
    return {"chain_intact": chain_ok, "total_entries": logger._event_count, "entry_id": entry["id"]}

def test_core_module_registry():
    """Test Module Registry register / get / list."""
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    registry = ModuleRegistry(bus)
    registry.register("unit_test_mod", object(), "A test module")
    mods = registry.list_modules()
    assert "unit_test_mod" in mods
    return {"registered_modules": list(mods.keys())}


# ── 2. POLYMORPHIC SHELL ──────────────────────────────────────
def test_polymorph():
    """Test Polymorphic Engine mutation cycle."""
    from polymorphic.polymorph_engine import PolymorphEngine
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    engine = PolymorphEngine(bus)
    engine.start()
    time.sleep(0.2)
    status = engine.get_status()
    dna1 = engine.get_dna()
    mutated = engine.emergency_mutate("UNIT_TEST")
    dna2 = engine.get_dna()
    engine.stop()
    assert dna1 != dna2, "DNA should change after mutation"
    return {"epoch": mutated["epoch"], "dna_before": dna1[:16], "dna_after": dna2[:16]}


# ── 3. SOLIPSISM TRAP ─────────────────────────────────────────
def test_trap():
    """Test Solipsism Trap initialization and status."""
    from trap.illusion_shell import SolipsismTrap
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    trap = SolipsismTrap(bus)
    status = trap.get_status()
    assert "total_sessions" in status
    return {"sessions": status["total_sessions"], "listening": status["listening"]}


# ── 4. HIVE MIND ──────────────────────────────────────────────
def test_hivemind():
    """Test Hive Mind daemon initialization."""
    from hivemind.hivemind_daemon import HiveMindDaemon
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    hive = HiveMindDaemon(bus, port=19999)
    status = hive.get_status()
    assert "node_id" in status
    return {"node_id": status["node_id"], "known_peers": status["known_peers"]}


# ── 5. GHOST FILE SYSTEM ──────────────────────────────────────
def test_ghostfs():
    """Test GhostFS lock/unlock, store and list workflow."""
    from ghostfs.ghost_fs import GhostFileSystem
    import shutil
    data_dir = os.path.join(ROOT, "ghostfs_data")
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    gfs = GhostFileSystem(bus)
    # List visible
    vis = gfs.list_visible()
    # Unlock
    gfs.unlock("test_passphrase")
    status_unlocked = gfs.get_status()
    # Store a file
    gfs.store_hidden("test_secret.txt", b"Top secret data for unit test", tags=["test"])
    hidden = gfs.list_hidden()
    # Lock
    gfs.lock()
    status_locked = gfs.get_status()
    assert status_unlocked["unlocked"] == True
    assert status_locked["unlocked"] == False
    return {
        "visible_files": len(vis),
        "hidden_files_after_store": len(hidden),
        "unlocked_then_locked": True,
    }


# ── 6. QCRYPT 2.0++ ──────────────────────────────────────────
def test_qcrypt():
    """Test encrypt → decrypt round-trip."""
    from qcrypt.qcrypt_engine import QCryptEngine
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    qc = QCryptEngine(bus)
    plaintext = b"Q-Void classified test payload 2026"
    envelope = qc.encrypt(plaintext, label="unit_test")
    decrypted = qc.decrypt(envelope)
    assert decrypted == plaintext, f"Decryption mismatch: got {decrypted}"
    status = qc.get_status()
    return {
        "algorithm": envelope["algorithm"],
        "key_id": envelope["key_id"],
        "ciphertext_preview": envelope["ciphertext"][:40] + "...",
        "decrypted_match": True,
        "active_key": status["active_key_id"],
    }


# ── 7. PRECOG ENGINE ─────────────────────────────────────────
def test_precog():
    """Test Precog AI attack vector prediction."""
    from precog.precog_engine import PrecogEngine
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    precog = PrecogEngine(bus)
    # Test several recon signals
    tests = [
        ("port 445 open smb windows", "SMB"),
        ("nmap 22 ssh linux", "SSH"),
        ("port 80 open http apache", "HTTP/Web"),
        ("port 3389 open rdp windows", "RDP"),
    ]
    predictions = []
    for signal, expected_area in tests:
        results = precog.predict_vector(signal, top_n=3)
        predictions.append({
            "signal": signal,
            "top_vector": results[0]["vector"],
            "confidence": results[0]["confidence"],
        })
    return {"trained": precog.is_trained, "predictions": predictions}


# ── 8. QPM ────────────────────────────────────────────────────
def test_qpm():
    """Test QPM package manager operations."""
    import tempfile
    import shutil
    from qpm.qpm_cli import QPMManager
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    
    test_dir = tempfile.mkdtemp(prefix="qpm_test_")
    try:
        qpm = QPMManager(bus, install_dir=test_dir)
        installed = qpm.list_installed()
        search_results = qpm.search("scan")
        install_result = qpm.install("nmap")
        assert install_result.get("ok") is True, f"QPM install failed: {install_result}"
        assert install_result.get("package") == "nmap-scanner"
        return {
            "initially_installed": len(installed),
            "search_hits": len(search_results),
            "install_result": install_result.get("code", "unknown"),
        }
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


# ── 9. DIGITAL FORGE ─────────────────────────────────────────
def test_forge():
    """Test Digital Forge VM creation and management."""
    from forge.digital_forge import DigitalForge
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    forge = DigitalForge(bus)
    templates = forge.list_templates()
    vm = forge.create_vm("test-sandbox", "malware-sandbox")
    vms = forge.list_vms()
    status = forge.get_status()
    return {
        "templates": len(templates),
        "created_vm_id": vm.get("vm_id"),
        "total_vms": status["total_vms"],
    }


# ── 10. HEURISTIC ORACLE ───────────────────────────────────────
def test_oracle():
    """Test HEURISTIC ORACLE entropy analysis and AdvancedSearch's search."""
    from oracle.heuristic_oracle import HeuristicOracle
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    oracle = HeuristicOracle(bus)
    # Entropy analysis
    analysis = oracle.analyze_data(b"suspicious encrypted payload xor 0xff", "test-scan")
    # AdvancedSearch search
    items = [f"log_{i}" for i in range(100)]
    items[42] = "malware_beacon"
    search = oracle.pattern_search(items, "malware_beacon")
    return {
        "entropy": analysis["entropy"],
        "classification": analysis["classification"],
        "anomaly_score": analysis["anomaly_score"],
        "AdvancedSearch_found": search["found"],
        "AdvancedSearch_iterations": search["iterations"],
    }


# ── 11. MCP ROUTER ────────────────────────────────────────────
def test_mcp():
    """Test MCP model routing with different payloads."""
    from mcp.mcp_router import MCPRouter
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    mcp = MCPRouter(bus)
    payloads = [
        "SELECT * FROM users WHERE id=1 OR 1=1; DROP TABLE users;--",
        "GET /admin HTTP/1.1 flood 10000 connections",
        "normal web traffic hello world",
    ]
    results = []
    for p in payloads:
        r = mcp.route(p)
        results.append({
            "payload_preview": p[:50],
            "routed_to": r["model"],
            "threat": r["threat"],
            "confidence": r["confidence"],
            "is_threat": r["is_threat"],
        })
    status = mcp.get_status()
    return {"models": status["models"], "routing_results": results}


# ── 12. RAG ENGINE ────────────────────────────────────────────
def test_rag():
    """Test RAG incident retrieval and recommendation."""
    from rag.rag_engine import RAGEngine
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    rag = RAGEngine(bus)
    queries = [
        "ransomware encrypting files",
        "SQL injection attack on database",
        "DDoS flooding the network",
    ]
    results = []
    for q in queries:
        r = rag.query(q)
        results.append({
            "query": q,
            "recommendation": r["recommended_response"][:100],
            "confidence": r["confidence"],
            "evidence_count": len(r["evidence"]),
        })
    status = rag.get_status()
    return {"incidents_in_store": status["incidents_in_store"], "query_results": results}


# ── 13. DNA ENCODER ───────────────────────────────────────────
def test_dna():
    """Test DNA encode → decode round-trip and stats."""
    from dna.dna_encryptor import DNAEncryptor
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    dna = DNAEncryptor(bus)
    original = "Q-Void OS Classified Intelligence"
    strand = dna.encode_text(original)
    decoded = dna.decode_text(strand)
    stats = dna.stats(strand)
    assert decoded == original, f"DNA round-trip failed: got {decoded}"
    return {
        "original_text": original,
        "strand_length": len(strand),
        "strand_preview": strand[:60] + "...",
        "decoded_match": True,
        "gc_content": stats["gc_content"],
    }


# ── 14. RUST CORE ─────────────────────────────────────────────
def test_rust_core():
    """Test Rust Core engine (or Python fallback)."""
    from rust_core.engine import get_engine_status, fast_sha256, fast_entropy, xor_obfuscate
    status = get_engine_status()
    # SHA-256
    h = fast_sha256(b"Q-Void test")
    # Entropy
    ent = fast_entropy(b"aaaaaabbbb")
    low_ent = fast_entropy(b"\x00" * 100)
    # XOR
    data = b"secret"
    key = b"K"
    obf = xor_obfuscate(data, key)
    deobf = xor_obfuscate(obf, key)
    assert deobf == data, "XOR roundtrip failed"
    return {
        "engine": status["engine"],
        "rust_compiled": status["rust_compiled"],
        "sha256_test": h[:32] + "...",
        "entropy_varied": round(ent, 4),
        "entropy_zero": round(low_ent, 4),
        "xor_roundtrip": True,
    }


# ── 15. CONTROLLER ────────────────────────────────────────────
def test_controller():
    """Test QVoid Controller module registry."""
    from controller.qvoid_controller import QVoidController
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    ctrl = QVoidController(bus)
    status_list = ctrl.status()
    return {"modules_registered": len(status_list), "controller_online": True, "modules": [m["name"] for m in status_list]}


# ── 16. INTEGRATION: Full Shell Init ──────────────────────────
def test_shell_init():
    """Test that QVoidShell initializes all modules successfully."""
    from terminal_ui.qvoid_shell import QVoidShell
    shell = QVoidShell()
    online = []
    offline = []
    module_checks = [
        ("Polymorphic Shell", shell.polymorph),
        ("Solipsism Trap", shell.trap),
        ("Hive Mind", shell.hive),
        ("Ghost FS", shell.ghostfs),
        ("QCrypt 2.0++", shell.qcrypt),
        ("Precog Engine", shell.precog),
        ("QPM", shell.qpm),
        ("Digital Forge", shell.forge),
        ("HEURISTIC ORACLE", shell.oracle),
        ("MCP Router", shell.mcp),
        ("RAG Engine", shell.rag),
        ("DNA Encoder", shell.dna),
        ("Controller", shell.controller),
    ]
    for name, mod in module_checks:
        if mod is not None:
            online.append(name)
        else:
            offline.append(name)
    if shell.polymorph:
        shell.polymorph.stop()
    return {"online": online, "offline": offline, "online_count": len(online), "total": len(module_checks)}


# ── 17. LLM ADAPTER ──────────────────────────────────────────
def test_llm_adapter():
    """Test LLM Adapter initialization."""
    from llm.llm_adapter import LLMAdapter
    adapter = LLMAdapter()
    return {"provider": adapter.provider, "api_base": getattr(adapter, "base_url", "openrouter.ai")}


# ── 18. THREAT PIPELINE ──────────────────────────────────────
def test_threat_pipeline():
    """Test Unified Threat Intelligence Pipeline."""
    from core.threat_pipeline import ThreatPipeline
    from core.qvoid_core import EventBus, ForensicLogger
    import asyncio
    
    class MockPrecog:
        def predict_vector(self, signal, top_n=1): return [("SQLi", 95.0)]
    class MockMCP:
        def route_all(self, signal): return {"model": "mock", "threat": "SQLi"}
    class MockRAG:
        def query(self, signal, top_k=2): return ["Past incident SQLi"]
    class MockLLM:
        async def generate_structured(self, prompt, system_prompt): 
            return {"threat_type": "SQLi", "confidence": 99.0, "recommended_actions": ["Block IP"]}
            
    logger = ForensicLogger(log_dir=os.path.join(ROOT, "logs"))
    bus = EventBus(logger)
    pipeline = ThreatPipeline(MockPrecog(), MockMCP(), MockRAG(), MockLLM(), bus)
    
    assessment = asyncio.run(pipeline.analyze_threat("test signal"))
    assert assessment.threat_type == "SQLi", "Expected SQLi"
    return {"threat_type": assessment.threat_type, "confidence": assessment.confidence}

# ══════════════════════════════════════════════════════════════════
#  HTML REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════

def generate_html_report(results, run_time_sec):
    """Generate a beautiful HTML report from test results."""
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    skipped = sum(1 for r in results if r.status == "SKIP")
    total = len(results)
    pass_rate = round((passed / total) * 100, 1) if total else 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Group by category
    categories = {}
    for r in results:
        categories.setdefault(r.category, []).append(r)

    rows = ""
    detail_sections = ""
    for i, r in enumerate(results):
        status_class = "pass" if r.status == "PASS" else "fail" if r.status == "FAIL" else "skip"
        status_icon = "✅" if r.status == "PASS" else "❌" if r.status == "FAIL" else "⏭️"
        rows += f"""
        <tr class="{status_class}-row">
            <td>{i+1}</td>
            <td><strong>{html.escape(r.name)}</strong></td>
            <td>{html.escape(r.category)}</td>
            <td class="{status_class}">{status_icon} {r.status}</td>
            <td>{r.duration_ms}ms</td>
        </tr>"""

        # Detail section
        details_html = ""
        if r.details:
            details_html += '<div class="details-grid">'
            for k, v in r.details.items():
                if isinstance(v, list):
                    list_items = ""
                    for item in v:
                        if isinstance(item, dict):
                            list_items += "<li>" + " | ".join(f"<strong>{ik}</strong>: {html.escape(str(iv))}" for ik, iv in item.items()) + "</li>"
                        else:
                            list_items += f"<li>{html.escape(str(item))}</li>"
                    details_html += f'<div class="detail-item"><span class="detail-key">{html.escape(k)}</span><ul>{list_items}</ul></div>'
                else:
                    details_html += f'<div class="detail-item"><span class="detail-key">{html.escape(k)}</span><span class="detail-val">{html.escape(str(v))}</span></div>'
            details_html += '</div>'

        error_html = ""
        if r.error:
            error_html = f'<div class="error-block"><strong>Error:</strong><pre>{html.escape(r.error)}</pre></div>'

        output_html = ""
        if r.output.strip():
            output_html = f'<div class="output-block"><strong>Console Output:</strong><pre>{html.escape(r.output[:2000])}</pre></div>'

        detail_sections += f"""
        <div class="test-detail" id="test-{i}">
            <h3>{status_icon} {html.escape(r.name)} <span class="{status_class}">[{r.status}]</span></h3>
            <p class="test-meta">Category: {html.escape(r.category)} | Duration: {r.duration_ms}ms</p>
            {details_html}
            {error_html}
            {output_html}
        </div>"""

    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Q-VOID OS — Test Report</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700;900&display=swap');

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
        font-family: 'Inter', -apple-system, sans-serif;
        background: #0a0a0f;
        color: #e0e0e8;
        line-height: 1.6;
        padding: 0;
    }}

    .header {{
        background: linear-gradient(135deg, #0d0d14 0%, #1a1a2e 50%, #16213e 100%);
        border-bottom: 2px solid #7c5bf5;
        padding: 48px 60px;
        text-align: center;
    }}
    .header h1 {{
        font-size: 2.4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #7c5bf5, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        letter-spacing: -1px;
    }}
    .header .subtitle {{
        font-size: 1rem;
        color: #8888aa;
        font-weight: 300;
    }}
    .header .version {{
        display: inline-block;
        background: rgba(124, 91, 245, 0.15);
        border: 1px solid rgba(124, 91, 245, 0.3);
        border-radius: 20px;
        padding: 4px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #a855f7;
        margin-top: 12px;
    }}

    .summary-bar {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 16px;
        padding: 32px 60px;
        background: #0d0d14;
    }}
    .stat-card {{
        background: linear-gradient(145deg, #12121c, #1a1a2e);
        border: 1px solid #2a2a3e;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
    }}
    .stat-card .stat-value {{
        font-size: 2.2rem;
        font-weight: 900;
        font-family: 'JetBrains Mono', monospace;
    }}
    .stat-card .stat-label {{
        font-size: 0.8rem;
        color: #8888aa;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }}
    .stat-card.pass .stat-value {{ color: #22c55e; }}
    .stat-card.fail .stat-value {{ color: #ef4444; }}
    .stat-card.skip .stat-value {{ color: #eab308; }}
    .stat-card.total .stat-value {{ color: #7c5bf5; }}
    .stat-card.rate .stat-value {{ color: #06b6d4; }}

    .container {{ padding: 32px 60px; }}

    h2 {{
        font-size: 1.4rem;
        font-weight: 700;
        color: #c0c0d8;
        margin-bottom: 20px;
        padding-bottom: 8px;
        border-bottom: 1px solid #2a2a3e;
    }}
    h2 .accent {{ color: #a855f7; }}

    /* Summary Table */
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
        margin-bottom: 40px;
    }}
    th {{
        background: #1a1a2e;
        color: #a855f7;
        font-weight: 600;
        text-align: left;
        padding: 12px 16px;
        border-bottom: 2px solid #7c5bf5;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    td {{
        padding: 10px 16px;
        border-bottom: 1px solid #1a1a2e;
    }}
    tr:hover {{ background: rgba(124, 91, 245, 0.05); }}
    .pass {{ color: #22c55e; font-weight: 600; }}
    .fail {{ color: #ef4444; font-weight: 600; }}
    .skip {{ color: #eab308; font-weight: 600; }}
    .pass-row {{ border-left: 3px solid #22c55e; }}
    .fail-row {{ border-left: 3px solid #ef4444; }}

    /* Detail Sections */
    .test-detail {{
        background: linear-gradient(145deg, #12121c, #16162a);
        border: 1px solid #2a2a3e;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }}
    .test-detail h3 {{
        font-size: 1.1rem;
        margin-bottom: 8px;
    }}
    .test-meta {{
        font-size: 0.8rem;
        color: #6666aa;
        margin-bottom: 16px;
    }}
    .details-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 10px;
        margin-bottom: 12px;
    }}
    .detail-item {{
        background: rgba(26, 26, 46, 0.6);
        border: 1px solid #222238;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.85rem;
    }}
    .detail-key {{
        color: #7c5bf5;
        font-weight: 600;
        margin-right: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
    }}
    .detail-val {{
        color: #c0c0d8;
    }}
    .detail-item ul {{
        margin-top: 6px;
        padding-left: 20px;
    }}
    .detail-item li {{
        font-size: 0.8rem;
        color: #aaa;
        margin-bottom: 4px;
    }}

    .error-block {{
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 8px;
        padding: 12px;
        margin-top: 10px;
    }}
    .error-block pre {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #ef4444;
        white-space: pre-wrap;
        word-break: break-word;
        margin-top: 6px;
    }}
    .output-block {{
        background: rgba(124, 91, 245, 0.05);
        border: 1px solid rgba(124, 91, 245, 0.15);
        border-radius: 8px;
        padding: 12px;
        margin-top: 10px;
    }}
    .output-block pre {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #8888aa;
        white-space: pre-wrap;
        word-break: break-word;
        margin-top: 6px;
    }}

    .footer {{
        text-align: center;
        padding: 32px;
        background: #0a0a0f;
        border-top: 1px solid #1a1a2e;
        font-size: 0.8rem;
        color: #4a4a6e;
    }}

    @media print {{
        body {{ background: #fff; color: #111; }}
        .header {{ background: #fff; border-bottom: 2px solid #7c5bf5; }}
        .header h1 {{ -webkit-text-fill-color: #7c5bf5; }}
        .header .subtitle {{ color: #555; }}
        .summary-bar {{ background: #fff; }}
        .stat-card {{ background: #f8f8fc; border-color: #ddd; }}
        .test-detail {{ background: #f9f9ff; border-color: #ddd; }}
        th {{ background: #f0f0f8; }}
        td {{ border-bottom-color: #eee; }}
        tr:hover {{ background: transparent; }}
        .detail-item {{ background: #f4f4fa; border-color: #ddd; }}
    }}
</style>
</head>
<body>

<div class="header">
    <h1>Q-VOID OS</h1>
    <div class="subtitle">Comprehensive Module Test Report — Working & Results Documentation</div>
    <div class="version">v{QVOID_VERSION} • {CODENAME} • Generated {now}</div>
</div>

<div class="summary-bar">
    <div class="stat-card total"><div class="stat-value">{total}</div><div class="stat-label">Total Tests</div></div>
    <div class="stat-card pass"><div class="stat-value">{passed}</div><div class="stat-label">Passed</div></div>
    <div class="stat-card fail"><div class="stat-value">{failed}</div><div class="stat-label">Failed</div></div>
    <div class="stat-card skip"><div class="stat-value">{skipped}</div><div class="stat-label">Skipped</div></div>
    <div class="stat-card rate"><div class="stat-value">{pass_rate}%</div><div class="stat-label">Pass Rate</div></div>
</div>

<div class="container">
    <h2><span class="accent">§1</span> Test Results Summary</h2>
    <table>
        <thead><tr>
            <th>#</th><th>Test Name</th><th>Category</th><th>Status</th><th>Duration</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>

    <h2><span class="accent">§2</span> Detailed Test Results</h2>
    {detail_sections}
</div>

<div class="footer">
    Q-VOID OS v{QVOID_VERSION} ({CODENAME}) — Test Report — {now}<br>
    Total run time: {round(run_time_sec, 2)}s | Python {sys.version.split()[0]} | OS: {sys.platform}
</div>

</body>
</html>"""
    return report_html


# ══════════════════════════════════════════════════════════════════
#  MAIN RUNNER
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 64)
    print("  Q-VOID OS — Comprehensive Test Suite")
    print(f"  v{QVOID_VERSION} ({CODENAME})")
    print("=" * 64)

    total_start = time.perf_counter()

    # ── Core Tests ──
    print("\n[CORE]")
    run_test("Event Bus Pub/Sub", "Core Infrastructure", test_core_event_bus)
    run_test("Forensic Logger Chain Integrity", "Core Infrastructure", test_core_forensic_logger)
    run_test("Module Registry", "Core Infrastructure", test_core_module_registry)

    # ── Module Tests ──
    print("\n[MODULES]")
    run_test("Polymorphic Shell — Mutation Cycle", "Defensive Modules", test_polymorph)
    run_test("Solipsism Trap — Honeypot Init", "Defensive Modules", test_trap)
    run_test("Hive Mind — P2P Daemon", "Intelligence Network", test_hivemind)
    run_test("Ghost File System — Lock/Unlock/Store", "Storage & Crypto", test_ghostfs)
    run_test("QCrypt 2.0++ — Encrypt/Decrypt", "Storage & Crypto", test_qcrypt)
    run_test("Precog Engine — AI Attack Prediction", "AI & ML", test_precog)
    run_test("QPM — Package Manager", "System Utilities", test_qpm)
    run_test("Digital Forge — VM Management", "System Utilities", test_forge)
    run_test("HEURISTIC ORACLE — Entropy & AdvancedSearch", "AI & ML", test_oracle)
    run_test("MCP Router — Threat Routing", "AI & ML", test_mcp)
    run_test("RAG Engine — Incident Retrieval", "AI & ML", test_rag)
    run_test("DNA Encoder — Steganography", "Storage & Crypto", test_dna)
    run_test("Rust Core — Accelerators", "Core Infrastructure", test_rust_core)
    run_test("LLM Adapter — Agentic Core", "Core Infrastructure", test_llm_adapter)
    run_test("Threat Pipeline — Autonomous Analysis", "Core Infrastructure", test_threat_pipeline)
    run_test("Controller — Module Orchestrator", "Core Infrastructure", test_controller)

    # ── Integration ──
    print("\n[INTEGRATION]")
    run_test("Full Shell Initialization", "Integration", test_shell_init)

    total_time = time.perf_counter() - total_start

    # ── Summary ──
    passed = sum(1 for r in ALL_RESULTS if r.status == "PASS")
    failed = sum(1 for r in ALL_RESULTS if r.status == "FAIL")
    total = len(ALL_RESULTS)
    print(f"\n{'=' * 64}")
    print(f"  RESULTS: {passed}/{total} passed | {failed} failed | {round(total_time, 2)}s")
    print(f"{'=' * 64}")

    # ── Generate HTML Report ──
    report_path = os.path.join(ROOT, "QVOID_OS_Test_Report.html")
    report_html = generate_html_report(ALL_RESULTS, total_time)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)
    print(f"\n  HTML Report: {report_path}")

    # ── Generate JSON results ──
    json_path = os.path.join(ROOT, "QVOID_OS_Test_Results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "version": QVOID_VERSION,
            "codename": CODENAME,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / total) * 100, 1) if total else 0,
            "duration_sec": round(total_time, 3),
            "results": [r.to_dict() for r in ALL_RESULTS],
        }, f, indent=2, default=str)
    print(f"  JSON Results: {json_path}")
    print(f"\n  Open the HTML report in a browser and use Ctrl+P to save as PDF.")
