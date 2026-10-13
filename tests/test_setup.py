"""Smoke tests: the package imports and the configuration is sane."""

import qanoun
from qanoun.config import PROJECT_ROOT, Settings


def test_package_has_version():
    assert qanoun.__version__ == "0.1.0"


def test_data_folders_live_under_data_dir():
    s = Settings()
    assert s.raw_dir.parent == s.data_dir
    assert s.processed_dir.name == "processed"


def test_project_root_contains_pyproject():
    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_api_key_is_never_printed(monkeypatch):
    monkeypatch.setenv("QANOUN_LLM_API_KEY", "sk-very-secret")
    s = Settings()
    assert "sk-very-secret" not in repr(s)
    assert s.llm_api_key.get_secret_value() == "sk-very-secret"


def test_default_language_can_be_changed(monkeypatch):
    monkeypatch.setenv("QANOUN_DEFAULT_LANGUAGE", "ar")
    s = Settings()
    assert s.default_language == "ar"
