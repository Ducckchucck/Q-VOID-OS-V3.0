import time
import threading
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.console import Group
from rich import box

class CyberDefenseDashboard:
    """
    Interactive Cyber Defense Platform Prototype Dashboard.
    Provides a real-time view into the trap, precog, encryption, and mutations.
    """
    def __init__(self, shell):
        self.shell = shell
        self.bus = shell.bus
        self.running = False
        
        self.recent_events = []
        self.attack_timeline = []
        self.heatmap = {"WEB": 0, "SSH": 0, "DB": 0, "SMB": 0, "MALWARE": 0, "ZERO_DAY": 0}
        
        # Subscribe to bus
        self.bus.subscribe("THREAT_DETECTED", self._on_threat)
        self.bus.subscribe("CRYPTO_ENCRYPT", self._on_crypto)
        self.bus.subscribe("CRYPTO_KEYS_GENERATED", self._on_crypto)
        self.bus.subscribe("PRECOG_PREDICTION", self._on_precog)
        self.bus.subscribe("PRECOG_LIVE_INTEL_UPDATED", self._on_precog)
        self.bus.subscribe("POLYMORPH_MUTATION", self._on_mutation)
        self.bus.subscribe("TRAP_ENGAGED", self._on_trap)
        self.bus.subscribe("COUNTERMEASURE_DEPLOYED", self._on_countermeasure)

    def _log(self, msg, style="white"):
        timestamp = time.strftime('%H:%M:%S')
        self.recent_events.insert(0, f"[dim]{timestamp}[/dim] [{style}]{msg}[/{style}]")
        if len(self.recent_events) > 20:
            self.recent_events.pop()

    def _add_timeline(self, step, desc, color):
        self.attack_timeline.append({"time": time.time(), "step": step, "desc": desc, "color": color})
        if len(self.attack_timeline) > 5:
            self.attack_timeline.pop(0)

    # ── Event Handlers ──
    def _on_threat(self, p):
        self._log(f"THREAT DETECTED: {p.get('type')} | IP: {p.get('attacker_ip')}", "bold red")
        self._add_timeline("DETECT", f"Intrusion attempt: {p.get('type')}", "red")

    def _on_trap(self, p):
        self._log(f"TRAP ENGAGED: Isolated Docker sandbox created for {p.get('attacker_ip')}", "bold yellow")
        self._add_timeline("ISOLATE", "Attacker routed to Deception Sandbox", "yellow")

    def _on_crypto(self, p):
        self._log(f"QCRYPT: Operations secured via Kyber/Dilithium.", "cyan")

    def _on_mutation(self, p):
        self._log(f"POLYMORPH: Shifted topology (Epoch {p.get('epoch')})", "magenta")
        self._add_timeline("MUTATE", "Moving-Target topology shifted", "magenta")

    def _on_precog(self, p):
        if "new_threats" in p:
            self._log(f"PRECOG: Ingested {p['new_threats']} live CVEs.", "blue")
        if "top_vector" in p:
            vec = p['top_vector']
            self._log(f"PRECOG PREDICT: {vec}", "bold blue")
            if "WEB" in vec: self.heatmap["WEB"] += 1
            elif "SSH" in vec: self.heatmap["SSH"] += 1
            elif "SQL" in vec or "DB" in vec: self.heatmap["DB"] += 1
            elif "SMB" in vec: self.heatmap["SMB"] += 1
            elif "ZERO_DAY" in vec: self.heatmap["ZERO_DAY"] += 1
            else: self.heatmap["MALWARE"] += 1
            self._add_timeline("PRECOG", f"AI Predicted: {vec}", "blue")

    def _on_countermeasure(self, p):
        self._log(f"COUNTERMEASURE: Sandbox {p.get('session_id')} destroyed.", "bold red on white")
        self._add_timeline("NEUTRALIZE", "Destructive threat terminated.", "red on white")

    # ── Layout Generators ──
    def make_layout(self):
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="left_col", ratio=2),
            Layout(name="right_col", ratio=3)
        )
        layout["left_col"].split(
            Layout(name="heatmap", size=10),
            Layout(name="trap_sessions", ratio=1)
        )
        layout["right_col"].split(
            Layout(name="timeline", size=12),
            Layout(name="logs", ratio=1)
        )
        return layout

    def generate_heatmap(self):
        t = Table(box=box.MINIMAL, expand=True, show_header=False)
        t.add_column("Vector", justify="left")
        t.add_column("Heat", justify="right")
        
        for k, v in self.heatmap.items():
            color = "red" if v > 5 else "yellow" if v > 2 else "green"
            bar = "█" * min(v, 20)
            t.add_row(f"[bold {color}]{k}[/]", f"[{color}]{bar} {v}[/]")
        return Panel(t, title="[bold blue]🧠 Adaptive Threat Heatmap[/]", border_style="blue")

    def generate_trap_sessions(self):
        t = Table(box=box.SIMPLE, expand=True)
        t.add_column("Session ID", style="cyan")
        t.add_column("Attacker IP", style="red")
        t.add_column("OS Image", style="yellow")
        t.add_column("Suspicion", style="magenta")
        
        if self.shell.trap:
            status = self.shell.trap.get_status()
            for s in status.get("sessions", []):
                if not s["terminated"]:
                    t.add_row(s["id"], s["ip"], s.get("os", "unknown"), str(s["suspicion"]))
        
        return Panel(t, title="[bold yellow]🐳 Active Deception Sandboxes[/]", border_style="yellow")

    def generate_timeline(self):
        t = Table(box=None, expand=True, show_header=False)
        t.add_column("Time", width=10, style="dim")
        t.add_column("Step", width=15)
        t.add_column("Description")
        
        if not self.attack_timeline:
            t.add_row("", "[dim]Waiting for attack sequence...[/]", "")
        
        for item in self.attack_timeline:
            ts = time.strftime('%H:%M:%S', time.localtime(item["time"]))
            step = f"[bold {item['color']}]{item['step']}[/]"
            t.add_row(ts, step, item["desc"])
            
        return Panel(t, title="[bold red]🔥 Attack Timeline Replay[/]", border_style="red")

    def generate_logs(self):
        content = "\n".join(self.recent_events)
        if not content:
            content = "[dim]Forensic event stream idle...[/dim]"
        return Panel(Text.from_markup(content), title="[bold green]📜 Forensic Chained Logs[/]", border_style="green")

    def generate_header(self):
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        left = "[bold cyan]Q-VOID OS Cyber Defense Platform[/]"
        center = "[bold yellow]ADAPTIVE DECEPTION ENGINE: ONLINE[/]"
        
        pq = "[green]PQC: Active[/green]" if self.shell.qcrypt and self.shell.qcrypt.get_status().get('pqc_real') else "[yellow]PQC: Sim[/yellow]"
        right_status = f"{pq} | [magenta]Press Ctrl+C to exit[/magenta]"
        
        grid.add_row(left, center, right_status)
        return Panel(grid, style="on grey15")

    def run(self):
        self.running = True
        layout = self.make_layout()
        
        try:
            with Live(layout, refresh_per_second=2, screen=True):
                while self.running:
                    layout["header"].update(self.generate_header())
                    layout["heatmap"].update(self.generate_heatmap())
                    layout["trap_sessions"].update(self.generate_trap_sessions())
                    layout["timeline"].update(self.generate_timeline())
                    layout["logs"].update(self.generate_logs())
                    time.sleep(0.5)
        except KeyboardInterrupt:
            self.running = False
