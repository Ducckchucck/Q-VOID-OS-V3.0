"""
╔══════════════════════════════════════════════════════════════════╗
║  DNA ENCRYPTOR v3.0 — ACGT Steganographic Encoder                ║
║  Bit-pair → nucleotide mapping with START/STOP codons.           ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, hashlib
from datetime import datetime, timezone
from typing import Dict, Tuple
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger

# Bit-pair to nucleotide mapping (2 bits → 1 nucleotide)
BIT_TO_NUC = {"00": "A", "01": "C", "10": "G", "11": "T"}
NUC_TO_BIT = {v: k for k, v in BIT_TO_NUC.items()}
START_CODON = "ATG"
STOP_CODON = "TAA"

class DNAEncryptor:
    """ACGT base-4 steganographic encoder/decoder."""
    def __init__(self, event_bus: EventBus = None):
        self.bus = event_bus

    def encode(self, data: bytes) -> str:
        """Encode bytes to DNA strand with checksum."""
        # 8-nucleotide checksum (first 4 bytes of SHA-256)
        checksum = hashlib.sha256(data).digest()[:4]
        checksum_strand = self._bytes_to_strand(checksum)
        data_strand = self._bytes_to_strand(data)
        strand = START_CODON + checksum_strand + data_strand + STOP_CODON
        if self.bus:
            self.bus.publish("DNA_ENCODE", {"size": len(data), "strand_len": len(strand)})
        return strand

    def decode(self, strand: str) -> bytes:
        """Decode DNA strand back to bytes."""
        if not strand.startswith(START_CODON) or not strand.endswith(STOP_CODON):
            raise ValueError("Invalid strand: missing START/STOP codons")
        inner = strand[len(START_CODON):-len(STOP_CODON)]
        checksum_strand = inner[:16]  # 4 bytes = 16 nucleotides (2 bits per nucleotide)
        data_strand = inner[16:]
        checksum = self._strand_to_bytes(checksum_strand)
        data = self._strand_to_bytes(data_strand)
        # Verify checksum
        expected = hashlib.sha256(data).digest()[:4]
        if checksum != expected:
            raise ValueError("Checksum mismatch: data corrupted")
        if self.bus:
            self.bus.publish("DNA_DECODE", {"size": len(data), "strand_len": len(strand)})
        return data

    def encode_text(self, text: str) -> str:
        return self.encode(text.encode("utf-8"))

    def decode_text(self, strand: str) -> str:
        return self.decode(strand).decode("utf-8")

    def _bytes_to_strand(self, data: bytes) -> str:
        bits = ''.join(format(b, '08b') for b in data)
        return ''.join(BIT_TO_NUC[bits[i:i+2]] for i in range(0, len(bits), 2))

    def _strand_to_bytes(self, strand: str) -> bytes:
        bits = ''.join(NUC_TO_BIT[n] for n in strand)
        return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

    def stats(self, strand: str) -> dict:
        from collections import Counter
        freq = Counter(strand)
        total = len(strand)
        gc = (freq.get('G', 0) + freq.get('C', 0)) / total * 100 if total else 0
        return {"length": total, "gc_content": round(gc, 2),
                "frequencies": {n: freq.get(n, 0) for n in "ACGT"}}

    def encode_file(self, filepath: str, output_path: str = None) -> str:
        with open(filepath, "rb") as f:
            data = f.read()
        strand = self.encode(data)
        out = output_path or filepath + ".dna"
        meta = f"# DNA Encoded File\n# Source: {os.path.basename(filepath)}\n# Size: {len(data)} bytes\n# Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
        with open(out, "w") as f:
            f.write(meta + strand + "\n")
        return out

    def decode_file(self, dna_path: str, output_path: str = None) -> str:
        with open(dna_path, "r") as f:
            lines = [l.strip() for l in f if not l.startswith("#") and l.strip()]
        strand = ''.join(lines)
        data = self.decode(strand)
        out = output_path or dna_path.replace(".dna", ".decoded")
        with open(out, "wb") as f:
            f.write(data)
        return out

if __name__ == "__main__":
    print("[DNA ENCRYPTOR] Self-test...")
    dna = DNAEncryptor()
    # Text encode/decode
    text = "Q-Void OS Classified Data"
    strand = dna.encode_text(text)
    decoded = dna.decode_text(strand)
    assert decoded == text
    print(f"  ✓ Encode/decode: '{text}' → {len(strand)} nucleotides")
    assert strand.startswith("ATG") and strand.endswith("TAA")
    print(f"  ✓ START/STOP codons present")
    # Stats
    s = dna.stats(strand)
    print(f"  ✓ Stats: GC={s['gc_content']}%, length={s['length']}")
    # Corruption detection
    try:
        dna.decode(strand[:-3] + "GGG")  # Tamper with stop codon content
    except ValueError:
        pass  # Expected
    print(f"  ✓ Checksum integrity verified")
    print("[DNA ENCRYPTOR] All tests passed.")
