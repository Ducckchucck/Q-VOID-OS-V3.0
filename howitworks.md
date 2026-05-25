# How Q-Void OS Works

Complete technical breakdown of every module, how they connect, and what happens when you run the system.

---

## 1. System Boot — What Happens When You Launch

When you run `python terminal_ui/qvoid_shell.py`, the boot sequence:

1. **ForensicLogger** initializes — creates `logs/forensic_audit.jsonl`. Every event from this point forward is appended here as a JSON line, chained with SHA-256 hashes (blockchain-style). If anyone tampers with the log, the `audit` command will detect the broken chain.

2. **EventBus** initializes — this is the backbone. Every module publishes events (e.g., `THREAT_DETECTED`, `CRYPTO_ENCRYPT`, `POLYMORPH_MUTATION`) and subscribes to events it cares about. Modules never call each other directly. This is the Publish/Subscribe pattern used in enterprise systems like Kafka.

3. **All 11 subsystems** are imported and initialized:
   - Each module gets a reference to the EventBus
   - Each module subscribes to events it needs
   - The Polymorphic Engine starts its background mutation timer

4. **Boot animation** plays in the terminal using the Rich library — shows each module loading with a spinner.

5. **Shell prompt** appears: `Q-VOID >` — ready for commands.

---

## 2. Core Framework — `core/qvoid_core.py`

### EventBus
- Dictionary mapping event types to callback functions
- `publish(event_type, data)` — notifies all subscribers. Each callback runs in its own thread so one slow handler doesn't block others.
- Dead letters: if a callback throws an exception, the event goes to a dead-letter queue for debugging.

### ForensicLogger
- Each log entry contains: UUID, sequence number, timestamp, event type, severity, data, previous hash, and current hash.
- The hash is computed as `SHA-256(previous_hash + JSON(entry))`. This creates a chain — if any entry is modified or deleted, the chain breaks.
- The `verify_chain()` method reads the entire log and recomputes every hash to check integrity.

### ModuleRegistry
- Simple dictionary of registered modules with status tracking (REGISTERED, RUNNING, ERROR, etc.)

---

## 3. Polymorphic Shell — `polymorphic/polymorph_engine.py`

**Problem it solves:** Malware and exploits target specific system call numbers, memory addresses, and file paths. If these change constantly, cached exploits become useless.

**How it works:**
- Maintains three internal tables: syscall dispatch, memory layout, filesystem aliases
- Every N seconds (configurable), runs a mutation cycle:
  1. Shuffles the syscall dispatch table — `SYS_READ` gets a random alias like `QV_a3f7b2c1_READ`
  2. Randomizes memory segment base addresses (simulated ASLR)
  3. Generates random filesystem path aliases — `/etc` becomes `/.qv/7c4a2b9e1f03`
  4. Computes a SHA-256 "DNA signature" of the entire state
- When a `THREAT_DETECTED` event is published anywhere in the system, the engine triggers an emergency mutation immediately (doesn't wait for the timer).
- All mutations are logged forensically.

---

## 4. Solipsism Trap — `trap/illusion_shell.py`

**Problem it solves:** Instead of just blocking an attacker, trap them in a fake environment. Waste their time while studying their techniques.

**How it works:**
- Maintains a complete fake filesystem tree in memory (Python dictionaries)
- Fake files contain planted credentials, SSH keys, API keys — all fake but realistic-looking
- When an attacker connects (via TCP listener on port 2222 or interactive mode):
  1. They see a realistic Linux login banner
  2. They get a root shell prompt: `[root@prod-web-01 ~]#`
  3. Commands like `ls`, `cat`, `cd`, `whoami`, `ifconfig`, `ps`, `netstat` all return fake but realistic output
  4. Suspicious commands (e.g., `cat /etc/shadow`, `wget`, `curl`) increase a suspicion score and fire `THREAT_DETECTED` events
  5. Destructive commands (e.g., `rm -rf`) trigger countermeasures — session terminated, full forensic report saved
- Every command is logged with timestamp, working directory, and suspicion flag
- Session reports saved as JSON to `logs/trap_session_<id>.json`

---

## 5. Hive Mind — `hivemind/hivemind_daemon.py`

**Problem it solves:** One node sees an attack, all nodes should know about it instantly.

**How it works:**
- Each node has a unique 16-character node ID derived from `SHA-256(host:port:timestamp)`
- Uses Kademlia-style routing table organized by XOR distance between node IDs
- Peer discovery via TCP PING/PONG:
  1. Node A sends JSON `{"type": "PING", "node_id": ..., "host": ..., "port": ...}` to Node B
  2. Node B responds with `{"type": "PONG", "node_id": ...}`
  3. Both nodes add each other to their routing tables
- When a `THREAT_DETECTED` event fires locally, the daemon broadcasts `THREAT_BROADCAST` to all known peers via TCP
- Receiving peers publish `THREAT_SHARED` to their local EventBus — so all local modules react

---

## 6. Ghost File System — `ghostfs/ghost_fs.py`

**Problem it solves:** Sensitive data should be invisible to anyone without the passphrase.

**How it works:**
- Two layers:
  - **Visible layer:** Normal files in `ghostfs_data/visible/` — decoys
  - **Hidden layer:** Encrypted files in `ghostfs_data/.hidden/`
- Unlocking: passphrase → PBKDF2 (480,000 iterations, SHA-256) → 32-byte AES key
- Each hidden file is stored as: `12-byte nonce + AES-256-GCM(4-byte metadata_length + JSON metadata + file data)`
- File names on disk are `SHA-256(original_name)[:24].ghost` — no original name leaks
- Auto-lock after 5 minutes of inactivity (configurable timer)
- **Steganography:** `steg_hide()` embeds secret data into cover data using Least Significant Bit insertion. Each bit of the secret replaces the LSB of a cover byte. `steg_extract()` reverses it.

---

## 7. QCrypt 2.0++ — `qcrypt/qcrypt_engine.py`

**Problem it solves:** Need encryption that works today and survives post-classical computers.

**How it works:**
- **Hybrid encryption (the main workhorse):**
  1. Generate random 32-byte AES key
  2. Generate random 12-byte nonce
  3. Encrypt data with AES-256-GCM (authenticated encryption — detects tampering)
  4. Wrap the AES key with RSA-4096 OAEP (only the private key holder can unwrap)
  5. Output: `{wrapped_key, nonce, ciphertext, key_id, algorithm}`

- **Post-classical (simulated):**
  - Kyber KEM simulation: generates shared secret, computes encapsulation ciphertext
  - XMSS signature simulation: hash-based signature using Merkle tree concept
  - In production, these would use liboqs — the simulation demonstrates the protocol

- **Key lifecycle:**
  - Keys stored in PEM format in `keystore/`
  - `rotate_keys()` — revokes old key, generates new RSA-4096 keypair, updates Kyber
  - KeyStore tracks all keys with creation time, status (ACTIVE/REVOKED), and rotation count

---

## 8. Precog Engine — `precog/precog_engine.py`

**Problem it solves:** Given a recon signal (e.g., "port 445 open smb windows"), predict the most likely attack vector.

**How it works:**
- 60+ CVE-mapped training pairs covering: SMB (EternalBlue, SMBGhost), RDP (BlueKeep), Web (Log4Shell, Shellshock, Heartbleed), SQL injection, XSS, databases (Redis, MongoDB, MSSQL), Active Directory (Kerberoasting, DCSync), WiFi, IoT, Ransomware, Phishing, DDoS, Supply Chain, Privilege Escalation, C2 frameworks, Zero-day
- Pipeline: TF-IDF vectorizer (unigrams + bigrams, sublinear TF) → ComplementNB classifier
  - TF-IDF: converts text to numerical vectors weighted by term importance
  - ComplementNB: Naive Bayes variant that handles imbalanced classes better than standard MultinomialNB
- `predict_vector(signal)` returns ranked attack types with confidence percentages
- `predict_next(command)` uses frequency analysis of command history to suggest the next command
- Model saved to `precog/predator_brain.pkl` via pickle serialization

---

## 9. QPM — `qpm/qpm_cli.py`

**Problem it solves:** Need a managed way to install, track, and audit security tools.

**How it works:**
- Built-in registry of 10 tools (nmap, hydra, sqlmap, wireshark, volatility, burpsuite, metasploit, john, gobuster, nikto) with metadata
- `install <name>` — checks registry, resolves dependencies (installs deps first), creates module directory with manifest.json
- `remove <name>` — deletes module directory
- `search <query>` — fuzzy search across names and descriptions
- `audit` — verifies all installed packages have valid manifests (integrity check)
- State persisted in `qpm_modules/installed.json`

---

## 10. Digital Forge — `forge/digital_forge.py`

**Problem it solves:** Need instant sandboxes for malware analysis and red team testing.

**How it works:**
- 5 VM templates: malware-sandbox, red-team-kali, forensics-lab, honeypot-node, windows-target
- Each template specifies: OS, RAM, CPU, disk, network mode (isolated/nat/bridged/dmz)
- `create_vm(name, template)` — creates VirtualMachine object with unique 8-char UUID
- `start_vm()`, `stop_vm()`, `destroy_vm()` — lifecycle management
- `snapshot(vm_id, label)` — saves VM state snapshots
- Host resource monitoring via psutil (CPU, RAM usage)
- All lifecycle events published to EventBus

---

## 11. Heuristic Oracle — `oracle/heuristic_oracle.py`

**Problem it solves:** Find patterns faster than classical search, detect anomalies in encrypted data.

**How it works:**
- **Grover's Search Simulator:**
  - Classical search: O(N) — check every item
  - Grover's: O(√N) — advanced heuristic amplification
  - The simulator runs `π/4 * √N` iterations, amplifying the probability of the target item, then "measures" when probability exceeds 0.5
  - Demonstrates the advanced speedup concept

- **Entropy Analyzer:**
  - Shannon entropy: `-Σ p(x) * log2(p(x))` over byte frequency distribution
  - Ranges: 0-1 (structured), 1-3.5 (text), 3.5-5 (mixed), 5-7 (compressed), 7-8 (encrypted/random)
  - Also checks for suspicious byte patterns (PE headers, ELF magic, script tags)

- **Correlation Engine:**
  - Collects observations across categories (network, auth, file, etc.)
  - Finds categories that share common keys or values
  - Example: if "network" and "auth" both reference the same `src_ip`, they're correlated

---

## 12. MCP Router — `mcp/mcp_router.py`

**Problem it solves:** Different attack types need different detection models.

**How it works:**
- 4 specialized models:
  1. **SQLDetector:** 11 regex patterns for SQL injection signatures (UNION SELECT, OR 1=1, DROP TABLE, etc.)
  2. **DDoSClassifier:** checks for keywords: syn_flood, udp_amp, slowloris, http_flood, dns_amp
  3. **MalwareAnalyzer:** looks for behavioral indicators: file_encrypt, registry_modify, process_inject, persistence, keylog, data_exfil, etc.
  4. **HeuristicEngine:** entropy analysis + anomaly keyword matching for zero-day detection
- Routing rules: keyword lists map to models. Payload with "sql" or "select" goes to SQLDetector, "ddos" or "flood" goes to DDoSClassifier, etc.
- `route(payload)` picks the best-matching model, runs its `analyze()`, logs the routing decision
- `route_all(payload)` runs ALL models and returns aggregated results sorted by confidence

---

## 13. RAG Engine — `rag/rag_engine.py`

**Problem it solves:** Use past incident history to inform current threat response.

**How it works:**
- TF-IDF vector store: each incident is a document with text + metadata
- 12 seeded incidents covering SQL injection, DDoS, EternalBlue, Log4Shell, phishing, ransomware, Redis exploit, Kerberoasting, XSS, zero-day, DNS zone transfer, supply chain
- `query(threat_description)`:
  1. Tokenize query → compute TF-IDF vector
  2. Cosine similarity against all indexed incidents
  3. Return top-K matches with relevance scores
  4. Extract recommended responses from matched incident metadata
  5. Provide evidence trail: which past incidents informed the recommendation
- New incidents can be added and are persisted to `rag/incident_store.json`

---

## 14. DNA Encoder — `dna/dna_encryptor.py`

**Problem it solves:** Hide data using biological encoding (steganography).

**How it works:**
- Bit-pair mapping: `00→A`, `01→C`, `10→G`, `11→T`. Each byte becomes 4 nucleotides.
- Encoding: `ATG` (START codon) + 8-nucleotide SHA-256 checksum + data nucleotides + `TAA` (STOP codon)
- Decoding: strip codons, extract checksum, decode data, verify checksum. Raises ValueError on corruption.
- File I/O: `encode_file()` reads binary, outputs `.dna` file with metadata header. `decode_file()` reverses.

---

## 15. Rust Core — `rust_core/`

**Problem it solves:** Python is slow for crypto and hashing. Rust is 10-100x faster.

**How it works:**
- `rust_core/src/lib.rs`: PyO3 extension module with functions:
  - `fast_sha256()`, `fast_sha512()` — Rust SHA-2 implementation
  - `aes256_gcm_encrypt()`, `aes256_gcm_decrypt()` — Rust AES-GCM
  - `fast_entropy()` — Shannon entropy in Rust (much faster on large data)
  - `secure_random()` — Rust CSPRNG
  - `xor_obfuscate()` — fast XOR for polymorphic engine
  - `batch_sha256()` — hash multiple inputs in one call
- `rust_core/engine.py`: Python fallback. If the Rust `.pyd`/`.so` is not compiled, identical Python implementations are used. The system auto-detects which is available.
- To compile: `cd rust_core && maturin develop`

---

## 16. Terminal Shell — `terminal_ui/qvoid_shell.py`

**How it works:**
- Imports all 11 subsystems + DNA + Rust with graceful degradation (try/except on each import)
- Boot sequence renders animated ASCII banner and progress bars via Rich library
- Main loop: read command → dispatch to handler → print result
- 20+ commands, each calling the appropriate subsystem's API
- `scan <host>` does real multi-threaded TCP port scanning (24 common ports), then feeds results to Precog for attack prediction
- `status` renders a Rich table showing all modules with online/offline indicators and details

---

## 17. Controller — `controller/qvoid_controller.py`

**How it works:**
- Registry of all 12 modules with their Python scripts
- `start(module)` — spawns subprocess, captures stdout to log file
- `stop(module)` — terminate with fallback kill
- `restart(module)` — stop + start, increments restart counter
- `status()` — table of all modules with icon, PID, uptime (HH:MM:SS), restart count
- Watchdog thread: polls running processes every 5 seconds, auto-restarts crashed modules if configured

---

## 18. Data Flow Example — What Happens During an Attack

1. Attacker connects to port 2222 (Solipsism Trap)
2. Trap publishes `TRAP_ENGAGED` event
3. Attacker runs `cat /etc/shadow` — trap publishes `THREAT_DETECTED`
4. **Polymorphic Shell** receives `THREAT_DETECTED` → emergency mutation
5. **Hive Mind** receives `THREAT_DETECTED` → broadcasts to all peers
6. **ForensicLogger** logs every event with chained hashes
7. Trap saves session report to `logs/trap_session_<id>.json`

This all happens automatically because of the EventBus pub/sub pattern. No module needs to know about any other module.

---

## 19. Security Guarantees

- **Tamper-proof logs:** blockchain-style hash chain in forensic logger. `audit` command verifies.
- **Zero-trust:** all modules communicate through events, no direct access to internal state.
- **Air-gap capable:** no external network dependencies required to run.
- **Auto-lock:** Ghost FS locks after inactivity timeout.
- **Key rotation:** QCrypt supports full key lifecycle with revocation.
