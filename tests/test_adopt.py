import json

import pytest

from gait.adapters import claude_code
from gait.cli import main
from gait.inventory import take
from gait.repo import current_branch, git
from gait.work import current


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    for variable, value in {"NAME": "Dev", "EMAIL": "dev@example.com"}.items():
        monkeypatch.setenv(f"GIT_AUTHOR_{variable}", value)
        monkeypatch.setenv(f"GIT_COMMITTER_{variable}", value)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def legacy(tmp_path, monkeypatch):
    repo = tmp_path / "shop"
    write(repo / "package.json", json.dumps({
        "name": "shop",
        "scripts": {"test": "vitest", "lint": "eslint .", "typecheck": "tsc", "dev": "astro dev"},
        "dependencies": {"astro": "5"},
    }))
    write(repo / "pnpm-lock.yaml", "")
    write(repo / "docs" / "specs" / "orders" / "README.md", "R1\nR2\n")
    write(repo / "docs" / "DECISIONES.md", "- one\n")
    write(repo / ".claude" / "hooks" / "spec-gate.py", "print()\n")
    write(repo / "src" / "index.ts", "export {}\n")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: start")
    monkeypatch.chdir(repo)
    return repo


def test_inventory_detects_stack_commands_and_legacy(legacy):
    found = take(legacy)
    assert found.name == "shop"
    assert found.stack == ["Node.js", "Astro"]
    assert found.commands == {"test": "pnpm test", "lint": "pnpm run lint", "typecheck": "pnpm run typecheck", "dev": "pnpm run dev"}
    assert found.ui
    assert found.agents_lines is None
    assert ("docs/specs", "2 lines") in found.legacy
    assert (".claude/hooks", "1 files") in found.legacy


def test_inventory_only_changes_nothing(legacy, capsys):
    assert main(["adopt", "--inventory"]) == 0
    assert "Stack: Node.js, Astro" in capsys.readouterr().out
    assert current_branch(legacy) == "main"
    assert not (legacy / "AGENTS.md").exists()


def test_adopt_writes_the_base_on_its_branch(legacy):
    assert main(["adopt"]) == 0
    assert current_branch(legacy) == "chore/adopt-gait"
    assert git(legacy, "status", "--porcelain") == ""
    agents = (legacy / "AGENTS.md").read_text()
    assert agents.startswith("# shop")
    assert "| Test | `pnpm test` |" in agents
    assert (legacy / "docs" / "context" / "design.md").exists()
    assert git(legacy, "config", "core.hooksPath") == ".githooks"
    permissions = json.loads((legacy / ".claude" / "settings.json").read_text())["permissions"]
    assert "Bash(pnpm test:*)" in permissions["allow"]
    plan = current(legacy)
    assert plan.slug == "adopt-gait"
    assert "`docs/specs` (2 lines)" in plan.body
    assert (legacy / "docs" / "DECISIONES.md").exists()


def test_adopt_keeps_existing_agents_and_hooks(legacy):
    write(legacy / "AGENTS.md", "# Mine\n")
    git(legacy, "add", "-A")
    git(legacy, "commit", "-q", "-m", "docs: agents")
    git(legacy, "config", "core.hooksPath", ".husky")
    assert main(["adopt"]) == 0
    assert (legacy / "AGENTS.md").read_text().startswith("# Mine\n")
    assert git(legacy, "config", "core.hooksPath") == ".husky"
    assert ".husky" in current(legacy).body


def test_adopt_adds_the_generic_block_without_claude_code(legacy, monkeypatch):
    monkeypatch.setattr(claude_code, "detected", lambda: False)
    main(["adopt"])
    assert "gait:start" in (legacy / "AGENTS.md").read_text()


def test_adopt_refuses_a_dirty_tree(legacy):
    write(legacy / "src" / "new.ts", "x\n")
    assert main(["adopt"]) == 1
    assert current_branch(legacy) == "main"


def test_adopt_refuses_a_second_run(legacy):
    main(["adopt"])
    git(legacy, "switch", "-q", "main")
    assert main(["adopt"]) == 1


def test_adopt_needs_a_commit(tmp_path, monkeypatch):
    repo = tmp_path / "empty"
    repo.mkdir()
    git(repo, "init", "-q")
    monkeypatch.chdir(repo)
    assert main(["adopt"]) == 1


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        ({"pubspec.yaml": "name: app\n"}, {"test": "flutter test", "lint": "flutter analyze", "dev": "flutter run"}),
        ({"pyproject.toml": "[project]\nname = 'x'\n[tool.ruff]\n", "uv.lock": ""}, {"test": "uv run pytest", "lint": "uv run ruff check ."}),
        ({"go.mod": "module x\n"}, {"test": "go test ./...", "lint": "go vet ./..."}),
    ],
)
def test_commands_for_other_stacks(tmp_path, files, expected):
    for name, text in files.items():
        write(tmp_path / name, text)
    assert take(tmp_path).commands == expected


def test_adopt_keeps_existing_docs_and_adds_the_vault(legacy):
    write(legacy / "docs" / "README.md", "# Old docs\n")
    git(legacy, "add", "-A")
    git(legacy, "commit", "-q", "-m", "docs: readme")
    main(["adopt"])
    assert (legacy / "docs" / "README.md").read_text() == "# Old docs\n"
    assert (legacy / "docs" / "diagrams" / "overview.svg").exists()
    assert (legacy / "docs" / ".obsidian" / "app.json").exists()
