"""Truth registry for Q-VOID OS modules.

This registry deliberately separates implemented capability from simulated or
experimental capability. Reviewers should be able to tell what is production-
leaning, what is a lab simulation, and what is still exploratory.
"""

from dataclasses import asdict, dataclass
from typing import Literal

CapabilityStatus = Literal["real", "simulated", "experimental"]
Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class ModuleMetadata:
    name: str
    import_path: str
    status: CapabilityStatus
    confidence: Confidence
    summary: str
    production_notes: str

    def to_dict(self) -> dict:
        return asdict(self)


MODULE_REGISTRY: dict[str, ModuleMetadata] = {
    "core": ModuleMetadata(
        name="Core Event Bus",
        import_path="core.qvoid_core",
        status="real",
        confidence="high",
        summary="Threaded publish/subscribe event bus, chained forensic logger, and module registry.",
        production_notes="Needs bounded worker pools and stronger log storage before hostile production use.",
    ),
    "polymorphic": ModuleMetadata(
        name="Polymorphic Shell",
        import_path="polymorphic.polymorph_engine",
        status="simulated",
        confidence="medium",
        summary="Moving-target defense simulator that mutates dispatch tables, memory maps, and path aliases.",
        production_notes="It does not mutate OS syscalls or kernel memory; keep claims scoped to simulation.",
    ),
    "trap": ModuleMetadata(
        name="Solipsism Trap",
        import_path="trap.illusion_shell",
        status="experimental",
        confidence="medium",
        summary="Docker-backed honeypot shell that records attacker commands and emits threat events.",
        production_notes="Requires Docker hardening, image pinning, resource limits, and command escaping review.",
    ),
    "hivemind": ModuleMetadata(
        name="Hive Mind",
        import_path="hivemind.hivemind_daemon",
        status="experimental",
        confidence="low",
        summary="Minimal P2P threat-sharing daemon with Kademlia-style routing concepts.",
        production_notes="No peer authentication, encryption, replay protection, or trust model yet.",
    ),
    "ghostfs": ModuleMetadata(
        name="Ghost File System",
        import_path="ghostfs.ghost_fs",
        status="real",
        confidence="medium",
        summary="AES-GCM encrypted hidden file layer with passphrase-derived keys and LSB steganography helpers.",
        production_notes="Now validates volume passphrases; still needs per-volume random salt migration and secure deletion.",
    ),
    "qcrypt": ModuleMetadata(
        name="QCrypt",
        import_path="qcrypt.qcrypt_engine",
        status="experimental",
        confidence="medium",
        summary="Real RSA-OAEP plus AES-GCM hybrid encryption with simulated post-quantum fallback.",
        production_notes="Production deployments must set QVOID_KEYSTORE_PASSWORD and use real liboqs for PQC claims.",
    ),
    "precog": ModuleMetadata(
        name="Precog Engine",
        import_path="precog.precog_engine",
        status="experimental",
        confidence="medium",
        summary="TF-IDF plus ComplementNB classifier for mapping recon text to likely attack vectors.",
        production_notes="Needs held-out evaluation, precision/recall, model card, and deterministic offline mode.",
    ),
    "qpm": ModuleMetadata(
        name="QPM",
        import_path="qpm.qpm_cli",
        status="simulated",
        confidence="medium",
        summary="Local package registry simulator with install/search/remove/audit flows.",
        production_notes="Does not install real external tools; integrity values are placeholders.",
    ),
    "forge": ModuleMetadata(
        name="Digital Forge",
        import_path="forge.digital_forge",
        status="simulated",
        confidence="high",
        summary="In-memory VM lifecycle simulation for cyber range storytelling.",
        production_notes="Not a hypervisor. Integrate libvirt, Docker, or a cloud provider for real sandbox provisioning.",
    ),
    "oracle": ModuleMetadata(
        name="Quantum Oracle",
        import_path="oracle.quantum_oracle",
        status="simulated",
        confidence="medium",
        summary="Entropy analysis and quantum-search-inspired simulation.",
        production_notes="Grover behavior is educational simulation, not quantum acceleration.",
    ),
    "mcp": ModuleMetadata(
        name="MCP Router",
        import_path="mcp.mcp_router",
        status="real",
        confidence="medium",
        summary="Rule-based routing to specialized detection heuristics.",
        production_notes="Rules are useful for demos; production use needs evaluation data and model governance.",
    ),
    "rag": ModuleMetadata(
        name="RAG Engine",
        import_path="rag.rag_engine",
        status="simulated",
        confidence="medium",
        summary="Local TF-IDF incident retrieval over seeded incident records.",
        production_notes="No LLM generation; position as retrieval-assisted response recommendations.",
    ),
    "dna": ModuleMetadata(
        name="DNA Encoder",
        import_path="dna.dna_encryptor",
        status="real",
        confidence="high",
        summary="Deterministic byte-to-ACGT codec with checksum validation.",
        production_notes="Encoding is not encryption; treat it as educational steganographic representation.",
    ),
    "rust_core": ModuleMetadata(
        name="Rust Core",
        import_path="rust_core.engine",
        status="experimental",
        confidence="medium",
        summary="Python fallback with optional PyO3 acceleration.",
        production_notes="Build and benchmark the extension in CI before claiming acceleration.",
    ),
    "llm": ModuleMetadata(
        name="LLM Adapter",
        import_path="llm.llm_adapter",
        status="real",
        confidence="high",
        summary="LLM communication layer with unified OpenRouter API support.",
        production_notes="Requires OPENROUTER_API_KEY environment variable.",
    ),
}


def get_module_metadata(module_id: str) -> dict:
    return MODULE_REGISTRY[module_id].to_dict()


def list_module_metadata() -> list[dict]:
    return [module.to_dict() for module in MODULE_REGISTRY.values()]
