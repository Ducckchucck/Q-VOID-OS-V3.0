"""Q-Void OS — Rust Core Acceleration Module"""
from .engine import (
    fast_sha256, fast_sha512, aes256_gcm_encrypt, aes256_gcm_decrypt,
    fast_entropy, secure_random, xor_obfuscate, batch_sha256,
    get_engine_status, get_engine, benchmark
)

__all__ = [
    "fast_sha256", "fast_sha512", "aes256_gcm_encrypt", "aes256_gcm_decrypt",
    "fast_entropy", "secure_random", "xor_obfuscate", "batch_sha256",
    "get_engine_status", "get_engine", "benchmark"
]
