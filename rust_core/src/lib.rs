// ╔══════════════════════════════════════════════════════════════════╗
// ║  Q-VOID OS — Rust Core Acceleration Module                      ║
// ║  High-performance hashing, encryption primitives, and entropy   ║
// ║  analysis compiled as PyO3 Python extension.                    ║
// ╚══════════════════════════════════════════════════════════════════╝

use pyo3::prelude::*;
use sha2::{Sha256, Sha512, Digest};
use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit};
use rand::Rng;

/// Fast SHA-256 hash of input bytes, returns hex string
#[pyfunction]
fn fast_sha256(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

/// Fast SHA-512 hash of input bytes, returns hex string
#[pyfunction]
fn fast_sha512(data: &[u8]) -> String {
    let mut hasher = Sha512::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

/// AES-256-GCM encrypt: takes key (32 bytes), nonce (12 bytes), plaintext
/// Returns ciphertext bytes
#[pyfunction]
fn aes256_gcm_encrypt(key: &[u8], nonce_bytes: &[u8], plaintext: &[u8]) -> PyResult<Vec<u8>> {
    if key.len() != 32 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Key must be 32 bytes"));
    }
    if nonce_bytes.len() != 12 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Nonce must be 12 bytes"));
    }
    let cipher_key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(cipher_key);
    let nonce = Nonce::from_slice(nonce_bytes);
    cipher.encrypt(nonce, plaintext)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Encryption failed: {}", e)))
}

/// AES-256-GCM decrypt: takes key (32 bytes), nonce (12 bytes), ciphertext
/// Returns plaintext bytes
#[pyfunction]
fn aes256_gcm_decrypt(key: &[u8], nonce_bytes: &[u8], ciphertext: &[u8]) -> PyResult<Vec<u8>> {
    if key.len() != 32 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Key must be 32 bytes"));
    }
    if nonce_bytes.len() != 12 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Nonce must be 12 bytes"));
    }
    let cipher_key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(cipher_key);
    let nonce = Nonce::from_slice(nonce_bytes);
    cipher.decrypt(nonce, ciphertext)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Decryption failed: {}", e)))
}

/// Fast Shannon entropy calculation on raw bytes
/// Returns entropy value (0.0 to 8.0)
#[pyfunction]
fn fast_entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let mut freq = [0u64; 256];
    for &byte in data {
        freq[byte as usize] += 1;
    }
    let len = data.len() as f64;
    let mut entropy = 0.0;
    for &count in &freq {
        if count > 0 {
            let p = count as f64 / len;
            entropy -= p * p.log2();
        }
    }
    entropy
}

/// Generate cryptographically secure random bytes
#[pyfunction]
fn secure_random(count: usize) -> Vec<u8> {
    let mut rng = rand::thread_rng();
    let mut buf = vec![0u8; count];
    rng.fill(&mut buf[..]);
    buf
}

/// XOR-based fast data obfuscation (for polymorphic engine)
#[pyfunction]
fn xor_obfuscate(data: &[u8], key: &[u8]) -> Vec<u8> {
    data.iter()
        .enumerate()
        .map(|(i, &b)| b ^ key[i % key.len()])
        .collect()
}

/// Batch hash: compute SHA-256 hashes for multiple inputs
#[pyfunction]
fn batch_sha256(items: Vec<&[u8]>) -> Vec<String> {
    items.iter().map(|data| {
        let mut hasher = Sha256::new();
        hasher.update(data);
        format!("{:x}", hasher.finalize())
    }).collect()
}

/// Python module definition
#[pymodule]
fn qvoid_rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_sha256, m)?)?;
    m.add_function(wrap_pyfunction!(fast_sha512, m)?)?;
    m.add_function(wrap_pyfunction!(aes256_gcm_encrypt, m)?)?;
    m.add_function(wrap_pyfunction!(aes256_gcm_decrypt, m)?)?;
    m.add_function(wrap_pyfunction!(fast_entropy, m)?)?;
    m.add_function(wrap_pyfunction!(secure_random, m)?)?;
    m.add_function(wrap_pyfunction!(xor_obfuscate, m)?)?;
    m.add_function(wrap_pyfunction!(batch_sha256, m)?)?;
    Ok(())
}
