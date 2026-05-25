"""
╔══════════════════════════════════════════════════════════════════╗
║  GHOST FILE SYSTEM (GFS) v3.0 — Dual-Layer Steganographic FS    ║
║  Sensitive data rendered invisible. Unlocks via passphrase.      ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, sys, json, time, hashlib, struct, threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from core.qvoid_core import EventBus, ForensicLogger
from rust_core import engine as rust_core

class GhostFile:
    """A file that exists in the hidden layer of GFS."""
    def __init__(self, name: str, data: bytes, tags: List[str] = None):
        self.name = name
        self.data = data
        self.tags = tags or []
        self.created = datetime.now(timezone.utc)
        self.modified = self.created
        self.size = len(data)
        self.checksum = rust_core.fast_sha256(data)
    def to_dict(self):
        return {"name": self.name, "size": self.size, "checksum": self.checksum[:16],
                "created": self.created.isoformat(), "tags": self.tags}

class GhostFSError(RuntimeError):
    """Base error for GhostFS operational failures."""

class InvalidPassphraseError(GhostFSError):
    """Raised when a passphrase cannot unlock the GhostFS volume."""

class GhostFSIntegrityError(GhostFSError):
    """Raised when encrypted GhostFS data cannot be authenticated or parsed."""

class GhostFileSystem:
    """
    Dual-layer filesystem:
      - Visible layer: decoy files (always accessible)
      - Hidden layer: real sensitive data (locked behind passphrase)
    Steganography: can hide data inside cover files via LSB insertion.
    """
    def __init__(self, event_bus: EventBus, base_dir: str = "ghostfs_data"):
        self.bus = event_bus
        self.base_dir = base_dir
        self._visible_dir = os.path.join(base_dir, "visible")
        self._hidden_dir = os.path.join(base_dir, ".hidden")
        self._marker_path = os.path.join(self._hidden_dir, ".volume")
        os.makedirs(self._visible_dir, exist_ok=True)
        os.makedirs(self._hidden_dir, exist_ok=True)
        self._lock = threading.Lock()
        self._unlocked = False
        self._derived_key: Optional[bytes] = None
        salt_path = os.path.join(self._hidden_dir, ".salt")
        if os.path.exists(salt_path):
            with open(salt_path, "rb") as f:
                self._salt = f.read()
        else:
            self._salt = rust_core.secure_random(32)  # Secure random per-volume
            with open(salt_path, "wb") as f:
                f.write(self._salt)
        self._auto_lock_timer: Optional[threading.Timer] = None
        self._auto_lock_sec = 300  # 5 minutes
        self._hidden_files: Dict[str, GhostFile] = {}
        self._load_errors: List[dict] = []

    # ── Key Derivation ──────────────────────────────────────────
    def _derive_key(self, passphrase: str) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                         salt=self._salt, iterations=480000)
        return kdf.derive(passphrase.encode())

    # ── Unlock / Lock ───────────────────────────────────────────
    def unlock(self, passphrase: str) -> bool:
        """Unlock the hidden layer with a passphrase."""
        with self._lock:
            self._derived_key = self._derive_key(passphrase)
            self._validate_or_create_marker()
            self._unlocked = True
            self._load_hidden_files()
            self._reset_auto_lock()
            self.bus.publish("GFS_UNLOCKED", {
                "files": len(self._hidden_files),
                "load_errors": len(self._load_errors),
            })
            return True

    def _validate_or_create_marker(self):
        """Authenticate the volume marker, creating it on first unlock."""
        assert self._derived_key is not None
        aesgcm = AESGCM(self._derived_key)
        if not os.path.exists(self._marker_path):
            nonce = os.urandom(12)
            marker = json.dumps({
                "type": "qvoid-ghostfs-volume",
                "created": datetime.now(timezone.utc).isoformat(),
            }).encode()
            with open(self._marker_path, "wb") as f:
                f.write(nonce + aesgcm.encrypt(nonce, marker, b"ghostfs-volume-marker"))
            return
        try:
            with open(self._marker_path, "rb") as f:
                blob = f.read()
            nonce, ct = blob[:12], blob[12:]
            marker = json.loads(aesgcm.decrypt(nonce, ct, b"ghostfs-volume-marker"))
            if marker.get("type") != "qvoid-ghostfs-volume":
                raise ValueError("invalid volume marker")
        except Exception as exc:
            self._derived_key = None
            self._unlocked = False
            self.bus.publish("GFS_UNLOCK_FAILED", {"reason": "invalid_passphrase"}, severity="WARNING")
            raise InvalidPassphraseError("Invalid GhostFS passphrase or corrupted volume marker") from exc

    def lock(self):
        """Lock the hidden layer, wiping the key from memory."""
        with self._lock:
            self._unlocked = False
            self._derived_key = None
            self._hidden_files.clear()
            if self._auto_lock_timer:
                self._auto_lock_timer.cancel()
            self.bus.publish("GFS_LOCKED", {})

    def _reset_auto_lock(self):
        if self._auto_lock_timer:
            self._auto_lock_timer.cancel()
        self._auto_lock_timer = threading.Timer(self._auto_lock_sec, self.lock)
        self._auto_lock_timer.daemon = True
        self._auto_lock_timer.start()

    # ── Hidden File Operations ──────────────────────────────────
    def _load_hidden_files(self):
        """Load and decrypt hidden files from disk."""
        self._hidden_files.clear()
        self._load_errors.clear()
        if not self._derived_key:
            return
        for fname in os.listdir(self._hidden_dir):
            if fname == ".volume":
                continue
            fpath = os.path.join(self._hidden_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, "rb") as f:
                    blob = f.read()
                nonce, ct = blob[:12], blob[12:]
                aesgcm = AESGCM(self._derived_key)
                plaintext = aesgcm.decrypt(nonce, ct, None)
                meta_len = struct.unpack(">I", plaintext[:4])[0]
                meta = json.loads(plaintext[4:4+meta_len])
                data = plaintext[4+meta_len:]
                gf = GhostFile(meta["name"], data, meta.get("tags", []))
                self._hidden_files[meta["name"]] = gf
            except Exception as exc:
                error = {"file": fname, "error": type(exc).__name__}
                self._load_errors.append(error)
                self.bus.publish("GFS_LOAD_ERROR", error, severity="ERROR")

    def store_hidden(self, name: str, data: bytes, tags: List[str] = None) -> bool:
        """Store a file in the hidden encrypted layer."""
        if not self._unlocked or not self._derived_key:
            return False
        with self._lock:
            meta = json.dumps({"name": name, "tags": tags or []}).encode()
            meta_len = struct.pack(">I", len(meta))
            plaintext = meta_len + meta + data
            aesgcm = AESGCM(self._derived_key)
            nonce = os.urandom(12)
            ct = aesgcm.encrypt(nonce, plaintext, None)
            safe_name = rust_core.fast_sha256(name.encode())[:24] + ".ghost"
            with open(os.path.join(self._hidden_dir, safe_name), "wb") as f:
                f.write(nonce + ct)
            self._hidden_files[name] = GhostFile(name, data, tags)
            self._reset_auto_lock()
            self.bus.publish("GFS_FILE_STORED", {"name": name, "size": len(data)})
            return True

    def read_hidden(self, name: str) -> Optional[bytes]:
        """Read a file from the hidden layer."""
        if not self._unlocked:
            raise GhostFSError("GhostFS hidden layer is locked")
        with self._lock:
            gf = self._hidden_files.get(name)
            self._reset_auto_lock()
            return gf.data if gf else None

    def delete_hidden(self, name: str) -> bool:
        if not self._unlocked:
            return False
        with self._lock:
            if name not in self._hidden_files:
                return False
            del self._hidden_files[name]
            safe_name = rust_core.fast_sha256(name.encode())[:24] + ".ghost"
            fpath = os.path.join(self._hidden_dir, safe_name)
            if os.path.exists(fpath):
                os.remove(fpath)
            self.bus.publish("GFS_FILE_DELETED", {"name": name})
            return True

    def list_hidden(self) -> List[dict]:
        if not self._unlocked:
            return []
        with self._lock:
            return [gf.to_dict() for gf in self._hidden_files.values()]

    # ── Visible Layer ───────────────────────────────────────────
    def store_visible(self, name: str, data: bytes) -> str:
        path = os.path.join(self._visible_dir, name)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def list_visible(self) -> List[dict]:
        result = []
        for fname in os.listdir(self._visible_dir):
            fpath = os.path.join(self._visible_dir, fname)
            if os.path.isfile(fpath):
                result.append({"name": fname, "size": os.path.getsize(fpath)})
        return result

    # ── Steganography (LSB) ─────────────────────────────────────
    def steg_hide(self, cover_data: bytearray, secret: bytes) -> bytearray:
        """Hide secret data inside cover data using LSB insertion."""
        length_bits = format(len(secret), '032b')
        secret_bits = ''.join(format(b, '08b') for b in secret)
        all_bits = length_bits + secret_bits
        if len(all_bits) > len(cover_data):
            raise ValueError("Cover data too small for secret")
        result = bytearray(cover_data)
        for i, bit in enumerate(all_bits):
            result[i] = (result[i] & 0xFE) | int(bit)
        return result

    def steg_extract(self, steg_data: bytearray) -> bytes:
        """Extract hidden data from steganographic cover."""
        length_bits = ''.join(str(steg_data[i] & 1) for i in range(32))
        secret_len = int(length_bits, 2)
        secret_bits = ''.join(str(steg_data[32+i] & 1) for i in range(secret_len * 8))
        return bytes(int(secret_bits[i:i+8], 2) for i in range(0, len(secret_bits), 8))

    # ── Status ──────────────────────────────────────────────────
    def get_status(self):
        return {"unlocked": self._unlocked, "visible_files": len(self.list_visible()),
                "hidden_files": len(self._hidden_files) if self._unlocked else "LOCKED",
                "auto_lock_sec": self._auto_lock_sec, "base_dir": self.base_dir,
                "load_errors": list(self._load_errors)}

if __name__ == "__main__":
    print("[GHOST FS] Self-test...")
    bus = EventBus(ForensicLogger())
    gfs = GhostFileSystem(bus, base_dir="ghostfs_test")
    # Test visible layer
    gfs.store_visible("readme.txt", b"This is a decoy file.")
    assert len(gfs.list_visible()) >= 1
    print("  ✓ Visible layer works")
    # Test hidden layer
    gfs.unlock("s3cr3t_passphrase!")
    gfs.store_hidden("classified.doc", b"TOP SECRET DATA HERE", tags=["classified"])
    hidden = gfs.list_hidden()
    assert len(hidden) == 1 and hidden[0]["name"] == "classified.doc"
    data = gfs.read_hidden("classified.doc")
    assert data == b"TOP SECRET DATA HERE"
    print("  ✓ Hidden layer: store/read/list works")
    # Test steganography
    cover = bytearray(os.urandom(1024))
    secret = b"hidden message"
    steg = gfs.steg_hide(cover, secret)
    extracted = gfs.steg_extract(steg)
    assert extracted == secret
    print("  ✓ Steganography: hide/extract works")
    # Test lock
    gfs.lock()
    assert gfs.list_hidden() == []
    print("  ✓ Lock: hidden files inaccessible")
    # Cleanup
    import shutil
    shutil.rmtree("ghostfs_test", ignore_errors=True)
    print("[GHOST FS] All tests passed.")
