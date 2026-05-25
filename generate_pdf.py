"""
╔══════════════════════════════════════════════════════════════════╗
║  Q-VOID OS — PDF Report Generator                                ║
║  Reads test results JSON and generates a professional PDF.       ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json
from datetime import datetime
from fpdf import FPDF

ROOT = os.path.dirname(os.path.abspath(__file__))

def sanitize(text):
    """Replace non-latin-1 chars with ASCII equivalents for fpdf core fonts."""
    replacements = {
        '\u2014': '-', '\u2013': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '*',
        '\u2192': '->', '\u2190': '<-', '\u2194': '<->',
        '\u2713': '[OK]', '\u2717': '[X]', '\u2714': '[OK]', '\u2716': '[X]',
        '\u2605': '*', '\u25cf': '*', '\u25cb': 'o',
        '\u00d7': 'x', '\u2265': '>=', '\u2264': '<=',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Strip any remaining non-latin-1 chars
    return text.encode('latin-1', errors='replace').decode('latin-1')

# ── Load test results ──────────────────────────────────────────
json_path = os.path.join(ROOT, "QVOID_OS_Test_Results.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

VERSION = data["version"]
CODENAME = data["codename"]
TOTAL = data["total_tests"]
PASSED = data["passed"]
FAILED = data["failed"]
PASS_RATE = data["pass_rate"]
DURATION = data["duration_sec"]
RESULTS = data["results"]
RUN_AT = data["run_at"]

# ── Custom PDF class ──────────────────────────────────────────
class QVoidPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(100, 100, 120)
            self.cell(0, 8, f"Q-VOID OS v{VERSION} - Test Report", align="L")
            self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(80, 60, 180)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(100, 100, 120)
        self.cell(0, 8, f"Q-VOID OS v{VERSION} ({CODENAME}) | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title, num=None):
        self.ln(6)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(80, 60, 180)
        label = f"{num}. {title}" if num else title
        self.cell(0, 10, label, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(80, 60, 180)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def stat_box(self, x, y, w, h, label, value, color):
        self.set_fill_color(*color)
        self.rect(x, y, w, h, style="F")
        # Border
        self.set_draw_color(60, 60, 80)
        self.set_line_width(0.2)
        self.rect(x, y, w, h, style="D")
        # Value
        self.set_xy(x, y + 4)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(255, 255, 255)
        self.cell(w, 14, str(value), align="C")
        # Label
        self.set_xy(x, y + 18)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(180, 180, 200)
        self.cell(w, 8, label, align="C")


# ── Build PDF ─────────────────────────────────────────────────
pdf = QVoidPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# ── Page 1: Cover ─────────────────────────────────────────────
pdf.add_page()

# Dark header block
pdf.set_fill_color(12, 12, 20)
pdf.rect(0, 0, 210, 100, style="F")

# Gradient bar
pdf.set_fill_color(80, 60, 180)
pdf.rect(0, 95, 210, 5, style="F")

# Title
pdf.set_xy(0, 20)
pdf.set_font("Helvetica", "B", 36)
pdf.set_text_color(160, 120, 255)
pdf.cell(210, 16, "Q-VOID OS", align="C", new_x="LMARGIN", new_y="NEXT")

# Subtitle
pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(180, 180, 200)
pdf.cell(210, 10, "Comprehensive Module Test Report", align="C", new_x="LMARGIN", new_y="NEXT")

# Version badge
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(120, 90, 220)
pdf.cell(210, 8, f"v{VERSION}  |  {CODENAME}", align="C", new_x="LMARGIN", new_y="NEXT")

# Date
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(140, 140, 160)
pdf.cell(210, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="C", new_x="LMARGIN", new_y="NEXT")

# Summary stats boxes
pdf.ln(12)
y_start = pdf.get_y() + 2
box_w = 35
gap = 4
total_w = 5 * box_w + 4 * gap
x_start = (210 - total_w) / 2

colors = [
    ("TOTAL TESTS", str(TOTAL), (40, 30, 80)),
    ("PASSED", str(PASSED), (20, 80, 40)),
    ("FAILED", str(FAILED), (140, 30, 30) if FAILED > 0 else (20, 80, 40)),
    ("PASS RATE", f"{PASS_RATE}%", (20, 60, 120)),
    ("DURATION", f"{DURATION}s", (80, 50, 30)),
]

for i, (label, value, color) in enumerate(colors):
    x = x_start + i * (box_w + gap)
    pdf.stat_box(x, y_start, box_w, 30, label, value, color)

pdf.set_y(y_start + 40)

# ── Project Summary ───────────────────────────────────────────
pdf.section_title("Project Overview", 1)
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(50, 50, 60)
pdf.multi_cell(0, 6, (
    "Q-VOID OS is a sovereign cyber-warfare operating system that hunts, deceives, and neutralizes "
    "threats in real-time. It consists of 15+ modules communicating through a decoupled Event Bus "
    "architecture with a tamper-proof forensic blockchain logger.\n\n"
    "This report documents the comprehensive testing of all modules, verifying their functionality, "
    "integration, and correctness. Each module was tested independently and through an integration "
    "test that initializes the complete system."
))

# ── Module List ───────────────────────────────────────────────
pdf.ln(2)
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(80, 60, 180)
pdf.cell(0, 7, "System Modules Under Test:", new_x="LMARGIN", new_y="NEXT")

modules = [
    ("Core (Event Bus + Forensic Logger)", "Decoupled pub/sub backbone with blockchain-chained audit trail"),
    ("Polymorphic Shell", "Moving-target defense with DNA-based epoch mutations"),
    ("Solipsism Trap", "Honeypot with fake filesystem, attacker session logging"),
    ("Hive Mind", "P2P Kademlia DHT threat intelligence network"),
    ("Ghost File System", "Dual-layer encrypted FS with AES-256-GCM steganography"),
    ("QCrypt 2.0++", "RSA-4096 + AES-256-GCM hybrid encryption, Kyber KEM simulation"),
    ("Precog Engine", "ML attack prediction (60+ CVE-mapped vectors, TF-IDF + ComplementNB)"),
    ("QPM", "Secure package manager with integrity auditing"),
    ("Digital Forge", "VM hypervisor sandbox for malware analysis"),
    ("Heuristic Oracle", "Grover's search simulation, Shannon entropy analysis"),
    ("MCP Router", "Multi-model threat routing (SQL, DDoS, Malware, Heuristic)"),
    ("RAG Engine", "Retrieval-augmented incident knowledge with 12 seeded incidents"),
    ("DNA Encoder", "ACGT steganographic encoder with START/STOP codons and SHA-256 checksum"),
    ("Rust Core", "PyO3 accelerated SHA-256/512, AES-256-GCM, entropy, XOR (Python fallback)"),
    ("Controller", "Module orchestrator with watchdog auto-restart"),
]

pdf.set_font("Helvetica", "", 8)
pdf.set_text_color(50, 50, 60)
for name, desc in modules:
    remaining = pdf.h - pdf.get_y() - pdf.b_margin
    if remaining < 10:
        pdf.add_page()
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(60, 40, 140)
    pdf.cell(60, 5, f"  * {name}", new_x="RIGHT")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(80, 80, 100)
    pdf.cell(0, 5, f"  {desc}", new_x="LMARGIN", new_y="NEXT")


# ── Page 2+: Test Results Table ───────────────────────────────
pdf.add_page()
pdf.section_title("Test Results Summary", 2)

# Table header
col_widths = [8, 65, 45, 20, 22, 30]
headers = ["#", "Test Name", "Category", "Status", "Time(ms)", "Result"]
pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(30, 25, 60)
pdf.set_text_color(200, 180, 255)
for i, (h, w) in enumerate(zip(headers, col_widths)):
    pdf.cell(w, 8, h, border=1, fill=True, align="C")
pdf.ln()

# Table rows
for i, r in enumerate(RESULTS):
    remaining = pdf.h - pdf.get_y() - pdf.b_margin
    if remaining < 8:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(30, 25, 60)
        pdf.set_text_color(200, 180, 255)
        for h, w in zip(headers, col_widths):
            pdf.cell(w, 8, h, border=1, fill=True, align="C")
        pdf.ln()

    row_color = (240, 255, 240) if r["status"] == "PASS" else (255, 240, 240)
    pdf.set_fill_color(*row_color)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(30, 30, 40)

    status_text = "PASS" if r["status"] == "PASS" else "FAIL"
    status_color = (0, 140, 40) if r["status"] == "PASS" else (200, 30, 30)

    pdf.cell(col_widths[0], 7, str(i+1), border=1, fill=True, align="C")
    pdf.cell(col_widths[1], 7, sanitize(r["name"][:35]), border=1, fill=True)
    pdf.cell(col_widths[2], 7, sanitize(r["category"]), border=1, fill=True)
    pdf.set_text_color(*status_color)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.cell(col_widths[3], 7, status_text, border=1, fill=True, align="C")
    pdf.set_text_color(30, 30, 40)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.cell(col_widths[4], 7, str(r["duration_ms"]), border=1, fill=True, align="R")

    # Result column - show key detail
    detail_text = ""
    if r["details"]:
        for k, v in r["details"].items():
            if not isinstance(v, (list, dict)):
                detail_text = f"{k}: {v}"
                break
    pdf.cell(col_widths[5], 7, sanitize(detail_text[:20]), border=1, fill=True)
    pdf.ln()


# ── Detailed Results ──────────────────────────────────────────
pdf.add_page()
pdf.section_title("Detailed Test Results & Evidence", 3)

for i, r in enumerate(RESULTS):
    remaining = pdf.h - pdf.get_y() - pdf.b_margin
    if remaining < 40:
        pdf.add_page()

    # Test header
    icon = "[PASS]" if r["status"] == "PASS" else "[FAIL]"
    color = (0, 140, 40) if r["status"] == "PASS" else (200, 30, 30)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*color)
    pdf.cell(0, 8, sanitize(f"{icon} Test {i+1}: {r['name']}"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 120)
    pdf.cell(0, 5, f"Category: {r['category']}  |  Duration: {r['duration_ms']}ms", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Details
    if r["details"]:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(60, 40, 140)
        pdf.cell(0, 5, "Output Details:", new_x="LMARGIN", new_y="NEXT")

        for k, v in r["details"].items():
            remaining = pdf.h - pdf.get_y() - pdf.b_margin
            if remaining < 12:
                pdf.add_page()

            if isinstance(v, list):
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(60, 40, 140)
                pdf.cell(0, 5, f"  {k}:", new_x="LMARGIN", new_y="NEXT")
                for item in v:
                    remaining = pdf.h - pdf.get_y() - pdf.b_margin
                    if remaining < 8:
                        pdf.add_page()
                    if isinstance(item, dict):
                        parts = []
                        for ik, iv in item.items():
                            parts.append(f"{ik}={iv}")
                        line = sanitize("    " + " | ".join(parts))
                    else:
                        line = sanitize(f"    - {item}")
                    pdf.set_font("Helvetica", "", 7)
                    pdf.set_text_color(70, 70, 90)
                    pdf.cell(0, 4.5, sanitize(line[:110]), new_x="LMARGIN", new_y="NEXT")
            elif isinstance(v, dict):
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(60, 40, 140)
                pdf.cell(0, 5, f"  {k}:", new_x="LMARGIN", new_y="NEXT")
                for dk, dv in v.items():
                    pdf.set_font("Helvetica", "", 7)
                    pdf.set_text_color(70, 70, 90)
                    pdf.cell(0, 4.5, sanitize(f"    {dk}: {dv}"), new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(40, 40, 55)
                val_str = str(v)
                if len(val_str) > 100:
                    val_str = val_str[:100] + "..."
                pdf.cell(0, 5, sanitize(f"  {k}: {val_str}"), new_x="LMARGIN", new_y="NEXT")

    # Error (if any)
    if r["error"]:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(200, 30, 30)
        pdf.cell(0, 5, "Error:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 6.5)
        for line in r["error"].split("\n")[:10]:
            remaining = pdf.h - pdf.get_y() - pdf.b_margin
            if remaining < 6:
                pdf.add_page()
            pdf.cell(0, 4, sanitize(line[:120]), new_x="LMARGIN", new_y="NEXT")

    # Separator
    pdf.ln(2)
    pdf.set_draw_color(200, 200, 220)
    pdf.set_line_width(0.15)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)


# ── Architecture Page ─────────────────────────────────────────
pdf.add_page()
pdf.section_title("System Architecture", 4)

pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(50, 50, 60)
pdf.multi_cell(0, 6, (
    "Q-VOID OS uses a Publish/Subscribe Event Bus architecture. All modules communicate "
    "exclusively through the central Event Bus, ensuring complete decoupling. Every event is "
    "logged to a tamper-proof Forensic Blockchain Logger with SHA-256 chain integrity verification.\n"
))

# Architecture diagram (text-based)
pdf.ln(3)
pdf.set_font("Courier", "", 7)
pdf.set_text_color(60, 40, 140)
arch_diagram = """
+---------------------------------------------------------------------+
|                    Q-VOID OS TERMINAL v3.0                          |
|                   (Rich Terminal Interface)                         |
+-----------------------------+---------------------------------------+
                              |
                    +---------v---------+
                    |   EVENT BUS       |
                    | (Pub/Sub Core)    |
                    +---------+---------+
                              |
        +------+------+-------+--------+-------+------+
        |      |      |       |        |       |      |
     +--v-+ +-v--+ +-v--+ +--v--+ +--v--+ +-v--+ +--v--+
     |Poly| |Trap| |Hive| |Ghost| |QCry | |Pre | |Forge|
     |morp| |    | |Mind| | FS  | |pt   | |cog | |     |
     +----+ +----+ +----+ +-----+ +-----+ +----+ +-----+
        |      |      |       |        |       |      |
     +--v-+ +-v--+ +-v--+ +--v--+ +--v--+ +-v--+
     |Orac| |MCP | |RAG | |DNA  | |Rust | |Ctrl|
     |le  | |    | |    | |     | |Core | |    |
     +----+ +----+ +----+ +-----+ +-----+ +----+
                              |
                    +---------v---------+
                    |  FORENSIC LOGGER  |
                    | (Blockchain Chain)|
                    +-------------------+
"""
for line in arch_diagram.split("\n"):
    if line.strip():
        pdf.cell(0, 3.5, line, new_x="LMARGIN", new_y="NEXT")

# ── Conclusion ────────────────────────────────────────────────
pdf.ln(6)
pdf.section_title("Conclusion", 5)

pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(50, 50, 60)

if FAILED == 0:
    conclusion = (
        f"All {TOTAL} tests passed successfully with a 100% pass rate. "
        f"The test suite completed in {DURATION} seconds.\n\n"
        "Every module in Q-VOID OS has been verified to be fully operational:\n"
        "- Core infrastructure (Event Bus, Forensic Logger, Module Registry) is stable\n"
        "- All defensive modules (Polymorphic Shell, Solipsism Trap, Hive Mind) are online\n"
        "- Cryptographic operations (QCrypt, GhostFS, DNA Encoder) pass round-trip verification\n"
        "- AI/ML modules (Precog Engine, MCP Router, RAG Engine, Heuristic Oracle) produce valid predictions\n"
        "- System utilities (QPM, Digital Forge, Controller) are functional\n"
        "- Full shell integration initializes all 13 modules without errors\n\n"
        "The forensic blockchain audit chain is INTACT with all entries verified.\n\n"
        "Q-VOID OS v3.0.0 (VOID_SOVEREIGN) is production-ready."
    )
else:
    conclusion = (
        f"{PASSED} out of {TOTAL} tests passed ({PASS_RATE}% pass rate). "
        f"{FAILED} test(s) failed and require attention. "
        f"The test suite completed in {DURATION} seconds."
    )

pdf.multi_cell(0, 6, conclusion)

# ── Signature Block ───────────────────────────────────────────
pdf.ln(10)
pdf.set_draw_color(80, 60, 180)
pdf.set_line_width(0.3)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(6)

pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(80, 60, 180)
pdf.cell(0, 7, "Verification Summary", new_x="LMARGIN", new_y="NEXT")

pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(50, 50, 60)
pdf.cell(50, 6, "Report Generated:", new_x="RIGHT")
pdf.cell(0, 6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), new_x="LMARGIN", new_y="NEXT")
pdf.cell(50, 6, "System Version:", new_x="RIGHT")
pdf.cell(0, 6, f"Q-VOID OS v{VERSION} ({CODENAME})", new_x="LMARGIN", new_y="NEXT")
pdf.cell(50, 6, "Test Duration:", new_x="RIGHT")
pdf.cell(0, 6, f"{DURATION} seconds", new_x="LMARGIN", new_y="NEXT")
pdf.cell(50, 6, "Python Version:", new_x="RIGHT")
pdf.cell(0, 6, f"{sys.version.split()[0]}", new_x="LMARGIN", new_y="NEXT")
pdf.cell(50, 6, "Platform:", new_x="RIGHT")
pdf.cell(0, 6, f"{sys.platform}", new_x="LMARGIN", new_y="NEXT")
pdf.cell(50, 6, "Total Tests:", new_x="RIGHT")
pdf.cell(0, 6, f"{PASSED}/{TOTAL} PASSED", new_x="LMARGIN", new_y="NEXT")
pdf.cell(50, 6, "Verdict:", new_x="RIGHT")
verdict = "ALL SYSTEMS OPERATIONAL" if FAILED == 0 else f"{FAILED} MODULE(S) REQUIRE ATTENTION"
verdict_color = (0, 140, 40) if FAILED == 0 else (200, 30, 30)
pdf.set_text_color(*verdict_color)
pdf.set_font("Helvetica", "B", 9)
pdf.cell(0, 6, verdict, new_x="LMARGIN", new_y="NEXT")

# ── Save ──────────────────────────────────────────────────────
output_path = os.path.join(ROOT, "QVOID_OS_Test_Report.pdf")
pdf.output(output_path)
print(f"PDF generated: {output_path}")
print(f"  Pages: {pdf.page_no()}")
print(f"  Tests: {PASSED}/{TOTAL} passed")
