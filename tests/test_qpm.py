import os

from core.qvoid_core import EventBus, ForensicLogger
from qpm.qpm_cli import QPMManager


def make_qpm(tmp_path):
    bus = EventBus(ForensicLogger(log_dir=str(tmp_path / "logs")))
    return QPMManager(bus, install_dir=str(tmp_path / "qpm_modules"))


def test_qpm_installs_canonical_alias(tmp_path):
    qpm = make_qpm(tmp_path)

    result = qpm.install("nmap")

    assert result["ok"] is True
    assert result["status"] == "SUCCESS"
    assert result["code"] == "INSTALLED"
    assert result["package"] == "nmap-scanner"
    assert os.path.exists(tmp_path / "qpm_modules" / "nmap-scanner" / "manifest.json")


def test_qpm_failed_install_is_explicit(tmp_path):
    qpm = make_qpm(tmp_path)

    result = qpm.install("not-a-real-package")

    assert result["ok"] is False
    assert result["status"] == "FAIL"
    assert result["code"] == "PACKAGE_NOT_FOUND"
