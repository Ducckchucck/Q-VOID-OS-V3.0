"""
╔══════════════════════════════════════════════════════════════════╗
║  QCRYPT 2.0++ — Post-Classical Hybrid Encryption Engine            ║
║  RSA-4096 + AES-256-GCM + Simulated Kyber + XMSS                ║
║  Full key lifecycle: generate → store → rotate → revoke → destroy║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, time, hashlib, secrets, struct
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.qvoid_core import EventBus, ForensicLogger
from qcrypt.pqc_adapter import PQCAdapter
from rust_core import engine as rust_core

class KeyStore:
    """Manages cryptographic key lifecycle."""
    def __init__(self, store_dir: str = "keystore"):
        self.store_dir = store_dir
        os.makedirs(store_dir, exist_ok=True)
        self._keys: Dict[str, dict] = {}
        self._load_index()
    def _index_path(self): return os.path.join(self.store_dir, "key_index.json")
    def _load_index(self):
        if os.path.exists(self._index_path()):
            with open(self._index_path(), "r") as f:
                self._keys = json.load(f)
    def _save_index(self):
        with open(self._index_path(), "w") as f:
            json.dump(self._keys, f, indent=2)
    def register(self, key_id: str, key_type: str, metadata: dict = None):
        self._keys[key_id] = {"type": key_type, "created": datetime.now(timezone.utc).isoformat(),
                              "status": "ACTIVE", "rotations": 0, **(metadata or {})}
        self._save_index()
    def revoke(self, key_id: str):
        if key_id in self._keys:
            self._keys[key_id]["status"] = "REVOKED"
            self._keys[key_id]["revoked_at"] = datetime.now(timezone.utc).isoformat()
            self._save_index()
    def get(self, key_id: str): return self._keys.get(key_id)
    def list_keys(self): return dict(self._keys)

class QCryptEngine:
    """
    Hybrid Post-Classical Encryption Engine.
    Combines classical (RSA-4096 + AES-256-GCM) with simulated
    Post-Classical primitives (Kyber-like lattice, XMSS-like hash).
    """
    def __init__(self, event_bus: EventBus, key_dir: str = "keystore"):
        self.bus = event_bus
        self.key_dir = key_dir
        self.keystore = KeyStore(key_dir)
        self.pqc = PQCAdapter()
        self._rsa_private = None
        self._rsa_public = None
        self._kyber_secret = None
        self._kyber_public = None
        self._dilithium_secret = None
        self._dilithium_public = None
        self._active_key_id = None
        self._keystore_password_source = "env" if os.environ.get("QVOID_KEYSTORE_PASSWORD") else "development-default"
        self._loaded_legacy_unencrypted_key = False
        self._init_keys()

    def _key_password(self) -> bytes:
        # Threat model note: the development default only prevents accidental plaintext
        # key files in demos. Production deployments must set QVOID_KEYSTORE_PASSWORD.
        return os.environ.get("QVOID_KEYSTORE_PASSWORD", "qvoid-dev-change-me").encode("utf-8")

    def _init_keys(self):
        """Generate or load RSA-4096 keypair."""
        priv_path = os.path.join(self.key_dir, "qvoid_rsa_priv.pem")
        pub_path = os.path.join(self.key_dir, "qvoid_rsa_pub.pem")
        if os.path.exists(priv_path) and os.path.exists(pub_path):
            try:
                with open(priv_path, "rb") as f:
                    private_bytes = f.read()
                try:
                    self._rsa_private = serialization.load_pem_private_key(private_bytes, password=self._key_password())
                except TypeError:
                    self._rsa_private = serialization.load_pem_private_key(private_bytes, password=None)
                    self._loaded_legacy_unencrypted_key = True
                except ValueError as exc:
                    self.bus.publish("CRYPTO_KEYSTORE_ERROR", {
                        "message": "Could not decrypt private key. Check QVOID_KEYSTORE_PASSWORD."
                    }, severity="ERROR")
                    raise RuntimeError("Could not decrypt QCrypt private key") from exc
                with open(pub_path, "rb") as f:
                    self._rsa_public = serialization.load_pem_public_key(f.read())
                self._active_key_id = "RSA-PRIMARY"
                if self._loaded_legacy_unencrypted_key:
                    self.bus.publish("CRYPTO_KEYSTORE_WARNING", {
                        "message": "Loaded legacy unencrypted private key. Rotate keys to rewrite encrypted at rest."
                    }, severity="WARNING")
                return
            except RuntimeError:
                raise
            except Exception:
                pass
        # Generate new keypair
        self._rsa_private = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        self._rsa_public = self._rsa_private.public_key()
        with open(priv_path, "wb") as f:
            f.write(self._rsa_private.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                serialization.BestAvailableEncryption(self._key_password())))
        with open(pub_path, "wb") as f:
            f.write(self._rsa_public.public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        self._active_key_id = "RSA-PRIMARY"
        self.keystore.register(self._active_key_id, "RSA-4096")
        self._init_pqc()
        self.bus.publish("CRYPTO_KEYS_GENERATED", {"key_id": self._active_key_id})

    def _init_pqc(self):
        """Post-Classical (Lattice-based) key generation via Adapter."""
        self._kyber_public, self._kyber_secret = self.pqc.kyber_generate_keypair()
        self._dilithium_public, self._dilithium_secret = self.pqc.dilithium_generate_keypair()
        
        algo_suffix = "" if self.pqc.is_real() else "-SIMULATED"
        self.keystore.register("KYBER-PRIMARY", f"KYBER512{algo_suffix}",
                               {"note": "Real liboqs" if self.pqc.is_real() else "Simulated fallback"})
        self.keystore.register("DILITHIUM-PRIMARY", f"DILITHIUM2{algo_suffix}")

    # ── Hybrid Encrypt (RSA + AES-256-GCM) ─────────────────────
    def encrypt(self, plaintext: bytes, label: str = "") -> dict:
        """Hybrid encryption: RSA-OAEP wraps a random AES key, AES-GCM encrypts data."""
        aes_key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        ciphertext = rust_core.aes256_gcm_encrypt(aes_key, nonce, plaintext)
        wrapped_key = self._rsa_public.encrypt(
            aes_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                   algorithm=hashes.SHA256(), label=None))
        result = {"wrapped_key": wrapped_key.hex(), "nonce": nonce.hex(),
                  "ciphertext": ciphertext.hex(), "label": label,
                  "key_id": self._active_key_id, "algorithm": "RSA-4096+AES-256-GCM",
                  "timestamp": datetime.now(timezone.utc).isoformat()}
        self.bus.publish("CRYPTO_ENCRYPT", {"label": label, "size": len(plaintext)})
        return result

    def decrypt(self, envelope: dict) -> bytes:
        """Decrypt a hybrid-encrypted envelope."""
        wrapped_key = bytes.fromhex(envelope["wrapped_key"])
        nonce = bytes.fromhex(envelope["nonce"])
        ciphertext = bytes.fromhex(envelope["ciphertext"])
        label = envelope.get("label", "")
        aes_key = self._rsa_private.decrypt(
            wrapped_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                       algorithm=hashes.SHA256(), label=None))
        plaintext = rust_core.aes256_gcm_decrypt(aes_key, nonce, ciphertext)
        self.bus.publish("CRYPTO_DECRYPT", {"label": label, "size": len(plaintext)})
        return plaintext

    # ── Post-Classical Key Exchange (Kyber) ────────────────────────
    def pq_key_exchange(self) -> dict:
        """Kyber key encapsulation against our public key."""
        ciphertext, shared_secret = self.pqc.kyber_encapsulate(self._kyber_public)
        algo = "KYBER-512" if self.pqc.is_real() else "KYBER-512-SIMULATED"
        note = "Real liboqs" if self.pqc.is_real() else "Simulated fallback"
        return {"ciphertext": ciphertext.hex(), "shared_secret": shared_secret.hex(),
                "algorithm": algo, "note": note}

    # ── Post-Classical Signature (Dilithium) ─────────────────────────
    def pq_sign(self, message: bytes) -> dict:
        """Dilithium digital signature."""
        signature = self.pqc.dilithium_sign(message, self._dilithium_secret)
        algo = "DILITHIUM-2" if self.pqc.is_real() else "DILITHIUM-2-SIMULATED"
        return {"signature": signature.hex(), "algorithm": algo, 
                "message_hash": rust_core.fast_sha256(message)}

    def pq_verify(self, message: bytes, sig_data: dict) -> bool:
        """Verify Dilithium signature."""
        signature = bytes.fromhex(sig_data["signature"])
        return self.pqc.dilithium_verify(message, signature, self._dilithium_public)

    # ── Key Rotation ────────────────────────────────────────────
    def rotate_keys(self) -> dict:
        """Rotate all cryptographic keys."""
        self.keystore.revoke(self._active_key_id)
        self._rsa_private = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        self._rsa_public = self._rsa_private.public_key()
        priv_path = os.path.join(self.key_dir, "qvoid_rsa_priv.pem")
        pub_path = os.path.join(self.key_dir, "qvoid_rsa_pub.pem")
        with open(priv_path, "wb") as f:
            f.write(self._rsa_private.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                serialization.BestAvailableEncryption(self._key_password())))
        with open(pub_path, "wb") as f:
            f.write(self._rsa_public.public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        self._active_key_id = f"RSA-ROTATED-{int(time.time())}"
        self.keystore.register(self._active_key_id, "RSA-4096")
        self._init_pqc()
        self.bus.publish("CRYPTO_KEY_ROTATION", {"new_key_id": self._active_key_id}, severity="WARNING")
        return {"new_key_id": self._active_key_id, "status": "ROTATED"}

    # ── Status ──────────────────────────────────────────────────
    def get_status(self):
        return {"active_key_id": self._active_key_id,
                "rsa_ready": self._rsa_private is not None,
                "pqc_real": self.pqc.is_real(),
                "keystore_password_source": self._keystore_password_source,
                "legacy_unencrypted_key_loaded": self._loaded_legacy_unencrypted_key,
                "algorithms": ["RSA-4096", "AES-256-GCM", "KYBER-512", "DILITHIUM-2"],
                "total_keys": len(self.keystore.list_keys())}

if __name__ == "__main__":
    import shutil
    print("[QCRYPT 2.0++] Self-test...")
    bus = EventBus(ForensicLogger())
    engine = QCryptEngine(bus, key_dir="keystore_test")
    # Hybrid encrypt/decrypt
    msg = b"TOP SECRET: Operation Midnight Sun"
    env = engine.encrypt(msg, label="test")
    dec = engine.decrypt(env)
    assert dec == msg
    print(f"  ✓ Hybrid RSA+AES encrypt/decrypt: {len(msg)} bytes")
    # PQ key exchange
    kem = engine.pq_key_exchange()
    assert len(kem["shared_secret"]) >= 64
    print(f"  ✓ Kyber KEM: {kem['algorithm']}")
    # Dilithium signature
    sig = engine.pq_sign(msg)
    assert engine.pq_verify(msg, sig)
    print(f"  ✓ Dilithium signature: sign + verify")
    # Key rotation
    old_id = engine._active_key_id
    engine.rotate_keys()
    assert engine._active_key_id != old_id
    print(f"  ✓ Key rotation: {old_id} → {engine._active_key_id}")
    shutil.rmtree("keystore_test", ignore_errors=True)
    print("[QCRYPT 2.0++] All tests passed.")
