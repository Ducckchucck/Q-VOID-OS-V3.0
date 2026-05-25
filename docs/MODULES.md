# Module Truth Table

| Module | Status | Confidence | Notes |
|---|---:|---:|---|
| Core Event Bus | real | high | Functional event delivery and chained logging. |
| Polymorphic Shell | simulated | medium | Mutates internal maps, not OS/kernel structures. |
| Solipsism Trap | experimental | medium | Docker-backed honeypot path; needs hardening. |
| Hive Mind | experimental | low | P2P concept without trust/security model. |
| Ghost FS | real | medium | AES-GCM storage with passphrase validation. |
| QCrypt | experimental | medium | Real RSA/AES hybrid; PQC is simulated unless liboqs is present. |
| Precog Engine | experimental | medium | ML classifier prototype without formal evaluation yet. |
| QPM | simulated | medium | Local package registry simulator. |
| Digital Forge | simulated | high | In-memory VM lifecycle simulator. |
| Heuristic Oracle | simulated | medium | Educational Advanced-Search inspired and entropy analysis. |
| MCP Router | real | medium | Rule-based model routing and detection heuristics. |
| RAG Engine | simulated | medium | TF-IDF incident retrieval; no LLM generation. |
| DNA Encoder | real | high | Deterministic codec with checksum; not encryption. |
| Rust Core | experimental | medium | Python fallback with optional PyO3 acceleration. |
| LLM Adapter | real | medium | Integration with OpenRouter and Claude models for inference. |
| Threat Pipeline | real | high | Security incident lifecycle management and queuing. |
| OS Controller | real | high | Centralized command and module coordination logic. |

The source of truth lives in `modules/registry.py`.
