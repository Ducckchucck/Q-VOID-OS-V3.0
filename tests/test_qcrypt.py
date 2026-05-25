from core.qvoid_core import EventBus, ForensicLogger
from qcrypt.qcrypt_engine import QCryptEngine


def test_qcrypt_encrypts_private_key_at_rest(tmp_path, monkeypatch):
    monkeypatch.setenv("QVOID_KEYSTORE_PASSWORD", "test-password")
    bus = EventBus(ForensicLogger(log_dir=str(tmp_path / "logs")))

    QCryptEngine(bus, key_dir=str(tmp_path / "keystore"))

    private_key = (tmp_path / "keystore" / "qvoid_rsa_priv.pem").read_text()
    assert "ENCRYPTED PRIVATE KEY" in private_key


def test_qcrypt_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("QVOID_KEYSTORE_PASSWORD", "test-password")
    bus = EventBus(ForensicLogger(log_dir=str(tmp_path / "logs")))
    engine = QCryptEngine(bus, key_dir=str(tmp_path / "keystore"))

    envelope = engine.encrypt(b"hello qvoid", label="unit")

    assert engine.decrypt(envelope) == b"hello qvoid"
