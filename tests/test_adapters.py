import subprocess

import pytest

from gait import doctor
import json

from gait.adapters import MARKER, claude_code, code_puppy, generic
from gait.cli import main
from gait.install import parse_models
from gait.roles import load_roles


@pytest.fixture
def home(tmp_path, monkeypatch):
    path = tmp_path / "home"
    path.mkdir()
    monkeypatch.setenv("HOME", str(path))
    monkeypatch.setattr(claude_code.shutil, "which", lambda name: None)
    return path


@pytest.fixture
def repo(tmp_path, monkeypatch):
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    monkeypatch.chdir(path)
    return path


def front_matter(text):
    return dict(line.split(": ", 1) for line in text.split("---\n")[1].splitlines())


def test_claude_code_writes_one_agent_per_role_and_the_skill(home, repo):
    assert main(["install", "--agent", "claude-code"]) == 0
    agents = sorted(path.name for path in (home / ".claude" / "agents").iterdir())
    expected = sorted(f"gait-{name}.md" for name in load_roles() if name != "orchestrator")
    assert agents == expected
    assert (home / ".claude" / "skills" / "gait" / "SKILL.md").exists()


def test_agents_map_tiers_to_models_and_tools(home, repo):
    main(["install", "--agent", "claude-code"])
    agents = home / ".claude" / "agents"
    planner = front_matter((agents / "gait-planner.md").read_text())
    verifier = front_matter((agents / "gait-verifier.md").read_text())
    builder = front_matter((agents / "gait-builder.md").read_text())
    tester = front_matter((agents / "gait-tester.md").read_text())
    assert planner["model"] == "opus"
    assert verifier["model"] == "haiku"
    assert builder["model"] == "sonnet"
    assert "Edit" not in verifier["tools"]
    assert "tools" not in builder
    assert tester["background"] == "true"


def test_custom_models_override_defaults(home, repo):
    main(["install", "--agent", "claude-code", "--models", "strong=fable"])
    planner = front_matter((home / ".claude" / "agents" / "gait-planner.md").read_text())
    assert planner["model"] == "fable"


def test_invalid_models_are_rejected():
    with pytest.raises(ValueError):
        parse_models("huge=opus")


def test_writing_roles_carry_the_base_rules(home, repo):
    main(["install", "--agent", "claude-code"])
    agents = home / ".claude" / "agents"
    assert "# Base rules" in (agents / "gait-builder.md").read_text()
    assert "# Base rules" not in (agents / "gait-scout.md").read_text()


def test_skill_is_manual_and_delegates_to_subagents(home, repo):
    main(["install", "--agent", "claude-code"])
    skill = (home / ".claude" / "skills" / "gait" / "SKILL.md").read_text()
    assert front_matter(skill)["disable-model-invocation"] == "true"
    assert "`gait-planner`" in skill
    assert MARKER in skill


def test_foreign_files_are_not_overwritten(home, repo, capsys):
    foreign = home / ".claude" / "agents" / "gait-scout.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("my own agent")
    assert main(["install", "--agent", "claude-code"]) == 1
    assert foreign.read_text() == "my own agent"
    assert main(["install", "--agent", "claude-code", "--force"]) == 0
    assert MARKER in foreign.read_text()


def test_reinstall_reports_up_to_date(home, repo, capsys):
    main(["install", "--agent", "claude-code"])
    capsys.readouterr()
    main(["install", "--agent", "claude-code"])
    assert "up to date" in capsys.readouterr().out


def test_generic_appends_block_and_keeps_content(repo):
    (repo / "AGENTS.md").write_text("# Project\n\nOwn rules.\n")
    assert main(["install", "--agent", "generic"]) == 0
    text = (repo / "AGENTS.md").read_text()
    assert text.startswith("# Project\n\nOwn rules.\n")
    assert text.count(generic.START) == 1
    assert "orchestrator.md" in text


def test_generic_replaces_its_block_instead_of_duplicating(repo):
    (repo / "AGENTS.md").write_text(f"# Project\n\n{generic.START}\nold\n{generic.END}\n\nAfter.\n")
    main(["install", "--agent", "generic"])
    text = (repo / "AGENTS.md").read_text()
    assert "old" not in text
    assert text.count(generic.START) == 1
    assert text.endswith("\n\nAfter.\n")
    assert generic.status(repo) == "current"


def test_generic_writes_the_gait_command(repo, capsys):
    assert main(["install", "--agent", "generic"]) == 0
    command = (repo / ".agents" / "commands" / "gait.md").read_text()
    assert MARKER in command
    assert "orchestrator.md" in command and "numbered list" in command
    assert ".agents/commands/gait.md" in capsys.readouterr().out


def test_generic_keeps_a_foreign_command(repo):
    path = repo / ".agents" / "commands" / "gait.md"
    path.parent.mkdir(parents=True)
    path.write_text("my own gait command\n")
    assert main(["install", "--agent", "generic"]) == 1
    assert path.read_text() == "my own gait command\n"
    assert main(["install", "--agent", "generic", "--force"]) == 0
    assert MARKER in path.read_text()


def test_code_puppy_writes_one_agent_per_role_and_the_command(home, repo, capsys):
    assert main(["install", "--agent", "code-puppy"]) == 0
    agents = {path.name: json.loads(path.read_text()) for path in (home / ".code_puppy" / "agents").iterdir()}
    assert sorted(agents) == sorted(f"gait-{name}.json" for name in load_roles() if name != "orchestrator")
    for config in agents.values():
        assert {"name", "description", "system_prompt", "tools"} <= config.keys()
        assert config["generated_by"] == MARKER
        assert "model" not in config
    assert agents["gait-triage.json"]["tools"] == ["read_file"]
    assert "edit_file" in agents["gait-builder.json"]["tools"]
    command = (repo / ".agents" / "commands" / "gait.md").read_text()
    assert "ask_user_question" in command and "`gait-planner`" in command and "invoke_agent" in command
    assert ".agents/commands/gait.md" in capsys.readouterr().out


def test_code_puppy_models_per_tier(home, repo):
    main(["install", "--agent", "code-puppy", "--models", "strong=big,cheap=small"])
    agents = home / ".code_puppy" / "agents"
    assert json.loads((agents / "gait-planner.json").read_text())["model"] == "big"
    assert json.loads((agents / "gait-triage.json").read_text())["model"] == "small"
    assert "model" not in json.loads((agents / "gait-builder.json").read_text())


def test_code_puppy_is_detected_without_claude(home, repo):
    (home / ".code_puppy").mkdir()
    assert code_puppy.detected()
    assert main(["install"]) == 0
    assert (home / ".code_puppy" / "agents" / "gait-scout.json").exists()


def test_generic_block_stays_short():
    assert len(generic.render_block().splitlines()) <= 10


def test_doctor_reports_missing_adapter_and_hooks(home, repo, capsys):
    (home / ".claude").mkdir()
    assert main(["doctor"]) == 1
    out = capsys.readouterr().out
    assert "not installed" in out
    assert "not active" in out


def test_doctor_passes_when_everything_is_in_place(home, repo, capsys):
    main(["install", "--agent", "claude-code"])
    subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath", ".githooks"], check=True)
    assert main(["doctor"]) == 0
    assert doctor.claude_code_state() == "current"


def test_deliver_carries_the_diagram_rules(home, repo):
    main(["install", "--agent", "claude-code"])
    agents = home / ".claude" / "agents"
    assert "# Diagram rules" in (agents / "gait-deliver.md").read_text()
    assert "# Diagram rules" not in (agents / "gait-builder.md").read_text()


def test_skill_asks_decisions_as_choices(home, repo):
    main(["install", "--agent", "claude-code"])
    skill = (home / ".claude" / "skills" / "gait" / "SKILL.md").read_text()
    assert "AskUserQuestion" in skill
    assert "Every decision is a choice" in skill
