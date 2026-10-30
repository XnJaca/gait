import subprocess

import pytest

from gait import finish
from gait.adapters import claude_code, generic
from gait.cli import main
from gait.repo import current_branch, git
from gait.work import current, load

INIT = ["init", "--name", "Shop", "--about", "Sells bread online.", "--stack", "Astro", "--test", "npm test"]


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    for variable, value in {"NAME": "Dev", "EMAIL": "dev@example.com"}.items():
        monkeypatch.setenv(f"GIT_AUTHOR_{variable}", value)
        monkeypatch.setenv(f"GIT_COMMITTER_{variable}", value)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    path = tmp_path / "repo"
    path.mkdir()
    monkeypatch.chdir(path)
    return path


@pytest.fixture
def project(repo):
    assert main([*INIT, "--ui"]) == 0
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: init")
    return repo


@pytest.fixture
def started(project):
    assert main(["start", "bread-list", "--type", "behavior", "--size", "small", "--goal", "Buyers see today's bread"]) == 0
    return project


def test_init_writes_agents_with_commands(repo):
    assert main([*INIT, "--no-ui"]) == 0
    agents = (repo / "AGENTS.md").read_text()
    assert agents.startswith("# Shop\n\nSells bread online.")
    assert "| Test | `npm test` |" in agents
    assert "Screenshot" not in agents
    assert (repo / "docs" / "context" / ".gitkeep").exists()
    assert not (repo / "design-tokens.json").exists()
    assert current_branch(repo) == "main"


def test_init_with_ui_adds_design_base(repo):
    assert main([*INIT, "--ui"]) == 0
    assert (repo / "docs" / "context" / "design.md").exists()
    assert (repo / "design-tokens.json").exists()
    assert "Screenshot" in (repo / "AGENTS.md").read_text()


def test_init_adds_the_generic_block_without_claude_code(repo, tmp_path, monkeypatch):
    monkeypatch.setattr(claude_code, "detected", lambda: False)
    main([*INIT, "--no-ui"])
    assert generic.START in (repo / "AGENTS.md").read_text()


def test_init_refuses_an_existing_agents_file(repo):
    (repo / "AGENTS.md").write_text("# Mine\n")
    assert main([*INIT, "--no-ui"]) == 1
    assert (repo / "AGENTS.md").read_text() == "# Mine\n"


def test_init_requires_name_and_about(repo):
    assert main(["init", "--no-ui"]) == 1
    assert not (repo / "AGENTS.md").exists()


def test_new_project_passes_check(project):
    assert main(["check"]) == 0


def test_start_creates_branch_and_committed_plan(started):
    assert current_branch(started) == "feat/bread-list"
    plan = current(started)
    assert (plan.slug, plan.type, plan.size, plan.goal) == ("bread-list", "behavior", "small", "Buyers see today's bread")
    assert git(started, "status", "--porcelain") == ""
    assert git(started, "log", "-1", "--format=%s") == "chore: plan bread-list"


def test_start_rejects_bad_slug_and_missing_fields(project):
    assert main(["start", "Bread List", "--type", "visual", "--size", "small", "--goal", "x"]) == 1
    assert main(["start", "bread"]) == 1
    assert current_branch(project) == "main"


def test_start_refuses_an_existing_branch(started):
    git(started, "switch", "-q", "main")
    assert main(["start", "bread-list", "--type", "visual", "--size", "small", "--goal", "x"]) == 1


def test_continue_reports_the_next_step(started, capsys):
    plan = started / ".work" / "bread-list.md"
    plan.write_text(plan.read_text().replace("## Steps\n\n- [ ] \n", "## Steps\n\n- [x] Add the list\n- [ ] Add the filter\n"))
    capsys.readouterr()
    assert main(["continue"]) == 0
    out = capsys.readouterr().out
    assert "1 of 2" in out
    assert "Next: Add the filter" in out


def test_continue_without_a_plan(project):
    assert main(["continue"]) == 1


def test_check_flags_long_files(project, capsys):
    (project / "docs" / "context" / "orders.md").write_text("line\n" * 61)
    assert main(["check"]) == 1
    assert "docs/context/orders.md has 61 lines" in capsys.readouterr().out


def test_check_flags_broken_paths_but_ignores_other_code_spans(project, capsys):
    agents = project / "AGENTS.md"
    agents.write_text(
        agents.read_text()
        + "\nSee `docs/context/gone.md`, `docs/context/design.md`, `feature/NNNN-slug`, `@scope/pkg` and `npm run x`.\n"
    )
    assert main(["check"]) == 1
    out = capsys.readouterr().out
    assert "`docs/context/gone.md`" in out
    assert out.count("does not exist") == 1


def test_check_ignores_paths_inside_the_gait_block(project):
    generic.install(project)
    assert main(["check"]) == 0


def test_check_flags_plans_on_main(started, capsys):
    git(started, "switch", "-q", "main")
    git(started, "merge", "-q", "feat/bread-list")
    assert main(["check"]) == 1
    assert ".work/bread-list.md cannot stay on main" in capsys.readouterr().out


def test_plan_description_has_no_front_matter_or_comments(started):
    description = current(started).description()
    assert description.startswith("# Buyers see today's bread")
    assert "<!--" not in description
    assert "slug:" not in description


@pytest.fixture
def remote(started, tmp_path):
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    git(started, "remote", "add", "origin", str(origin))
    return origin


def test_finish_removes_the_plan_pushes_and_opens_the_pr(started, remote, monkeypatch, capsys):
    calls = []

    def fake_run(command, cwd, check=True):
        calls.append(command)
        return "https://github.com/acme/shop/pull/7"

    monkeypatch.setattr(finish, "run_command", fake_run)
    assert main(["finish"]) == 0
    assert not (started / ".work").exists()
    assert git(started, "ls-remote", "--heads", "origin", "feat/bread-list")
    command = calls[0]
    assert command[command.index("--title") + 1] == "feat: Buyers see today's bread"
    assert command[command.index("--base") + 1] == "main"
    assert command[command.index("--body") + 1].startswith("# Buyers see today's bread")
    assert "pull/7" in capsys.readouterr().out


def test_finish_uses_the_given_title_and_draft(started, remote, monkeypatch):
    calls = []
    monkeypatch.setattr(finish, "run_command", lambda command, cwd, check=True: calls.append(command) or "url")
    assert main(["finish", "--title", "feat(shop): list today's bread", "--draft"]) == 0
    assert "feat(shop): list today's bread" in calls[0]
    assert "--draft" in calls[0]


def test_finish_refuses_on_main(started):
    git(started, "switch", "-q", "main")
    git(started, "merge", "-q", "feat/bread-list")
    assert main(["finish"]) == 1


def test_finish_refuses_when_check_fails(started, monkeypatch):
    (started / "docs" / "context" / "long.md").write_text("x\n" * 70)
    monkeypatch.setattr(finish, "run_command", lambda *args, **kwargs: pytest.fail("must not open a PR"))
    assert main(["finish"]) == 1
    assert (started / ".work" / "bread-list.md").exists()


def test_steps_ignore_other_sections(tmp_path):
    path = tmp_path / "plan.md"
    path.write_text("---\nslug: a\n---\n# Goal\n\n## Steps\n\n- [x] One\n- [ ] Two\n\n## Verification\n\n- [ ] Not a step\n")
    assert load(path).steps() == [(True, "One"), (False, "Two")]


def test_init_sets_up_docs_as_a_vault(project):
    docs = project / "docs"
    assert (docs / "README.md").read_text().startswith("# Shop\n\nSells bread online.")
    assert (docs / "diagrams" / "overview.svg").read_text().startswith("<svg")
    assert '"useMarkdownLinks": true' in (docs / ".obsidian" / "app.json").read_text()
    assert "docs/.obsidian/workspace*.json" in (project / ".gitignore").read_text()


def test_check_flags_broken_links_and_ignores_external_ones(project, capsys):
    readme = project / "docs" / "README.md"
    readme.write_text(
        readme.read_text()
        + "\n[Orders](context/orders.md) · [Site](https://x.com) · [Top](#areas) · `[x](nope.md)`\n![Flow](diagrams/flow.svg)\n"
    )
    assert main(["check"]) == 1
    out = capsys.readouterr().out
    assert "links to context/orders.md" in out
    assert "links to diagrams/flow.svg" in out
    assert out.count("links to") == 2


@pytest.mark.parametrize(
    ("svg", "message"),
    [("<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>", "needs a viewBox"), ("<svg", "not a valid SVG"), ("<div/>", "not a valid SVG")],
)
def test_check_validates_diagrams(project, capsys, svg, message):
    (project / "docs" / "diagrams" / "flow.svg").write_text(svg)
    assert main(["check"]) == 1
    assert message in capsys.readouterr().out
