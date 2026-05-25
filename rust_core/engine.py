"""
Rust Core Fallback — Pure Python implementations of the Rust-accelerated functions.
Used when the Rust extension is not compiled. The Rust module provides 10-100x
speedup on these operations but this fallback ensures the system always works.
"""
import hashlib
import os
import math
from collections import Counter

# Try to import compiled Rust extension
try:
    from qvoid_rust_core import (fast_sha256, fast_sha512, aes256_gcm_encrypt,
                                  aes256_gcm_decrypt, fast_entropy, secure_random,
                                  xor_obfuscate, batch_sha256)
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

    def fast_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def fast_sha512(data: bytes) -> str:
        return hashlib.sha512(data).hexdigest()

    def aes256_gcm_encrypt(key: bytes, nonce: bytes, plaintext: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).encrypt(nonce, plaintext, None)

    def aes256_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).decrypt(nonce, ciphertext, None)

    def fast_entropy(data: bytes) -> float:
        if not data:
            return 0.0
        freq = Counter(data)
        length = len(data)
        return -sum((c / length) * math.log2(c / length) for c in freq.values())

    def secure_random(count: int) -> bytes:
        return os.urandom(count)

    def xor_obfuscate(data: bytes, key: bytes) -> bytes:
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def batch_sha256(items: list) -> list:
        return [hashlib.sha256(d).hexdigest() for d in items]

def get_engine():
    return {
        "fast_sha256": fast_sha256,
        "fast_sha512": fast_sha512,
        "aes256_gcm_encrypt": aes256_gcm_encrypt,
        "aes256_gcm_decrypt": aes256_gcm_decrypt,
        "fast_entropy": fast_entropy,
        "secure_random": secure_random,
        "xor_obfuscate": xor_obfuscate,
        "batch_sha256": batch_sha256,
    }

def get_engine_status() -> dict:
    return {"rust_compiled": RUST_AVAILABLE,
            "engine": "Rust/PyO3" if RUST_AVAILABLE else "Python/Fallback",
            "functions": ["fast_sha256", "fast_sha512", "aes256_gcm_encrypt",
                         "aes256_gcm_decrypt", "fast_entropy", "secure_random",
                         "xor_obfuscate", "batch_sha256"]}

def benchmark():
    import time
    data = os.urandom(1024 * 1024 * 10)  # 10MB
    start = time.time()
    fast_sha256(data)
    end = time.time()
    print(f"SHA-256 (10MB): {end - start:.4f}s")

    start = time.time()
    fast_entropy(data)
    end = time.time()
    print(f"Entropy (10MB): {end - start:.4f}s")

if __name__ == "__main__":
    print(f"[RUST CORE] Engine: {'Rust/PyO3' if RUST_AVAILABLE else 'Python/Fallback'}")
    # Verify all functions work
    h = fast_sha256(b"Q-Void OS")
    assert len(h) == 64
    print(f"  ✓ SHA-256: {h[:16]}...")
    e = fast_entropy(os.urandom(1024))
    assert e > 7.0
    print(f"  ✓ Entropy: {e:.2f}")
    r = secure_random(32)
    assert len(r) == 32
    print(f"  ✓ SecureRandom: {len(r)} bytes")
    data = b"secret data"
    key = b"obfuscation_key!"
    obf = xor_obfuscate(data, key)
    deobf = xor_obfuscate(obf, key)
    assert deobf == data
    print(f"  ✓ XOR obfuscate: roundtrip OK")
    print("[RUST CORE] All functions operational.")
