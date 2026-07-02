from pathlib import Path

import pytest


def test_windows_native_install_path_docs_match_installer() -> None:
    doc_path = Path("website/docs/user-guide/windows-native.md")
    if not doc_path.exists():
        pytest.skip("website docs are not present in this distribution")
    doc = doc_path.read_text()
    install = Path("scripts/install.ps1").read_text()

    assert "%LOCALAPPDATA%\\hermes\\hermes-agent\\venv\\Scripts" in doc
    assert "Get-Command hermes        # should print C:\\Users\\<you>\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts\\hermes.exe" in doc
    assert '$hermesBin = "$InstallDir\\venv\\Scripts"' in install
