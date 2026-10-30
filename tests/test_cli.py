import pytest

from gait import __version__
from gait.cli import COMMANDS, main


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
    assert COMMANDS[name] in capsys.readouterr().out


@pytest.mark.parametrize("name", COMMANDS)
def test_pending_command_fails(name):
    assert main([name]) == 2


def test_unknown_command_fails():
    with pytest.raises(SystemExit) as exit_info:
        main(["nope"])
    assert exit_info.value.code == 2
