import json
import os
import subprocess

import pytest

from gait.cli import main
from gait.repo import git
from gait.validations import ASSETS_DIR, install_permissions

COMMIT_MSG = ASSETS_DIR / "hooks" / "commit-msg"
PRE_PUSH = ASSETS_DIR / "hooks" / "pre-push"


def commit_msg(tmp_path, message):
    path = tmp_path / "MSG"
    path.write_text(message)
    return subprocess.run(["sh", str(COMMIT_MSG), str(path)], capture_output=True, text=True).returncode


@pytest.mark.parametrize(
    "message",
    [
        "feat(api): add invitations\n",
        "fix: keep the session after refresh\n\nBody line.\n",
        "chore: plan bread-list\n",
        "refactor(web,mobile)!: rename crews\n",
        "Merge pull request #4 from acme/feat/x\n",
        "# comment first\nfeat: add x\n",
        "fixup! feat: add x\n",
    ],
)
def test_commit_msg_accepts(tmp_path, message):
    assert commit_msg(tmp_path, message) == 0


@pytest.mark.parametrize(
    "message",
    [
        "Add invitations\n",
        "feat add invitations\n",
        "feature(api): add invitations\n",
        "feat(API): add invitations\n",
        "feat: add x\n\nCo-Authored-By: Claude Opus <noreply@anthropic.com>\n",
        "feat: add x\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n",
        "feat: add x\n\nCo-authored-by: Copilot <copilot@github.com>\n",
    ],
)
def test_commit_msg_rejects(tmp_path, message):
    assert commit_msg(tmp_path, message) == 1


def test_commit_msg_allows_human_coauthors(tmp_path):
    assert commit_msg(tmp_path, "feat: add x\n\nCo-Authored-By: Ana Mora <ana@example.com>\n") == 0


def pre_push(remote_ref, env=None):
    line = f"refs/heads/x 1111 {remote_ref} 0000\n"
    return subprocess.run(
        ["sh", str(PRE_PUSH), "origin", "url"], input=line, capture_output=True, text=True, env={**os.environ, **(env or {})}
    ).returncode


@pytest.mark.parametrize("ref", ["refs/heads/main", "refs/heads/master"])
def test_pre_push_blocks_default_branches(ref):
    assert pre_push(ref) == 1


def test_pre_push_allows_feature_branches():
    assert pre_push("refs/heads/feat/bread-list") == 0


def test_pre_push_escape_for_the_first_push():
    assert pre_push("refs/heads/main", {"GAIT_ALLOW_MAIN": "1"}) == 0


@pytest.fixture
def initialized(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    assert main(["init", "--name", "Shop", "--about", "Sells bread.", "--test", "npm test", "--no-ui"]) == 0
    return repo


def test_init_installs_hooks_workflow_and_permissions(initialized):
    hooks = initialized / ".githooks"
    assert os.access(hooks / "commit-msg", os.X_OK)
    assert os.access(hooks / "pre-push", os.X_OK)
    assert git(initialized, "config", "core.hooksPath") == ".githooks"
    assert (initialized / ".github" / "workflows" / "gait.yml").exists()
    permissions = json.loads((initialized / ".claude" / "settings.json").read_text())["permissions"]
    assert "Bash(gait:*)" in permissions["allow"]
    assert "Bash(npm test:*)" in permissions["allow"]
    assert permissions["deny"] == ["Bash(gh pr merge:*)"]


def test_hooks_reject_an_attributed_commit_in_the_repo(initialized, monkeypatch):
    for variable, value in {"NAME": "Dev", "EMAIL": "dev@example.com"}.items():
        monkeypatch.setenv(f"GIT_AUTHOR_{variable}", value)
        monkeypatch.setenv(f"GIT_COMMITTER_{variable}", value)
    git(initialized, "add", "-A")
    result = subprocess.run(
        ["git", "commit", "-q", "-m", "chore: init", "-m", "Co-Authored-By: Claude <noreply@anthropic.com>"],
        cwd=initialized,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert git(initialized, "commit", "-q", "-m", "chore: init") == ""


def test_doctor_passes_after_init(initialized):
    main(["install", "--agent", "claude-code"])
    assert main(["doctor"]) == 0


def test_permissions_keep_existing_settings(tmp_path):
    path = tmp_path / ".claude" / "settings.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"model": "opus", "permissions": {"allow": ["Bash(make:*)", "Bash(gait:*)"]}}))
    install_permissions(tmp_path, ["pnpm test"])
    settings = json.loads(path.read_text())
    assert settings["model"] == "opus"
    assert settings["permissions"]["allow"].count("Bash(gait:*)") == 1
    assert "Bash(make:*)" in settings["permissions"]["allow"]
    assert "Bash(pnpm test:*)" in settings["permissions"]["allow"]


def test_existing_workflow_is_kept(tmp_path, monkeypatch):
    workflow = tmp_path / "repo" / ".github" / "workflows" / "gait.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("mine")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path / "repo")
    main(["init", "--name", "Shop", "--about", "Sells bread.", "--no-ui"])
    assert workflow.read_text() == "mine"
