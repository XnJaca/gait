import pytest


@pytest.fixture(autouse=True)
def english(monkeypatch):
    monkeypatch.setenv("GAIT_LANG", "en")
