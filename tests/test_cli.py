import pytest

from gait import __version__
from gait.cli import COMMANDS, main
from gait.i18n import language, t

PENDING = ("report",)


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    for name in COMMANDS:
        assert name in out


def test_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


@pytest.mark.parametrize("name", COMMANDS)
def test_command_help(name, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main([name, "--help"])
    assert exit_info.value.code == 0
    assert t(f"cmd.{name}") in capsys.readouterr().out


@pytest.mark.parametrize("name", PENDING)
def test_pending_command_fails(name):
    assert main([name]) == 2


def test_unknown_command_fails():
    with pytest.raises(SystemExit) as exit_info:
        main(["nope"])
    assert exit_info.value.code == 2


@pytest.mark.parametrize(
    ("value", "expected"),
    [("es_CR.UTF-8", "es"), ("en_US.UTF-8", "en"), ("fr_FR.UTF-8", "en"), ("C", "en")],
)
def test_language_follows_the_system(monkeypatch, value, expected):
    monkeypatch.delenv("GAIT_LANG")
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.setenv("LANG", value)
    assert language() == expected


def test_help_is_translated(monkeypatch, capsys):
    monkeypatch.setenv("GAIT_LANG", "es")
    main([])
    assert "comandos" in capsys.readouterr().out


def test_locales_have_the_same_keys():
    import json
    from gait.i18n import LOCALES_DIR

    keys = [set(json.loads(path.read_text())) for path in LOCALES_DIR.glob("*.json")]
    assert all(group == keys[0] for group in keys)
