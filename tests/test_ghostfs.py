import os

import pytest

from core.qvoid_core import EventBus, ForensicLogger
from ghostfs.ghost_fs import GhostFileSystem, GhostFSError, InvalidPassphraseError


def make_gfs(tmp_path):
    bus = EventBus(ForensicLogger(log_dir=str(tmp_path / "logs")))
    return GhostFileSystem(bus, base_dir=str(tmp_path / "ghostfs_data"))


def test_ghostfs_rejects_wrong_passphrase(tmp_path):
    gfs = make_gfs(tmp_path)
    assert gfs.unlock("correct horse battery staple") is True
    gfs.store_hidden("secret.txt", b"classified", tags=["test"])
    gfs.lock()

    with pytest.raises(InvalidPassphraseError):
        gfs.unlock("wrong password")


def test_ghostfs_reports_corrupted_hidden_file(tmp_path):
    gfs = make_gfs(tmp_path)
    gfs.unlock("passphrase")
    gfs.store_hidden("secret.txt", b"classified", tags=["test"])
    gfs.lock()

    hidden_dir = tmp_path / "ghostfs_data" / ".hidden"
    hidden_files = [p for p in hidden_dir.iterdir() if p.name != ".volume"]
    assert hidden_files
    hidden_files[0].write_bytes(os.urandom(64))

    assert gfs.unlock("passphrase") is True
    status = gfs.get_status()
    assert status["load_errors"]
    assert status["hidden_files"] == 0


def test_ghostfs_read_locked_fails_loudly(tmp_path):
    gfs = make_gfs(tmp_path)

    with pytest.raises(GhostFSError):
        gfs.read_hidden("secret.txt")
