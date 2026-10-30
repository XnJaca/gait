import sys
from dataclasses import dataclass
from pathlib import Path

from gait import ui
from gait.adapters import claude_code, generic
from gait.i18n import t
from gait.repo import git, is_repo
from gait.work import TEMPLATES_DIR

COMMANDS = ("test", "lint", "typecheck", "dev")


@dataclass
class Answers:
    name: str = ""
    about: str = ""
    stack: str = ""
    test: str = ""
    lint: str = ""
    typecheck: str = ""
    dev: str = ""
    ui: bool | None = None


def interview(answers: Answers) -> Answers:
    print(t("init.intro"))
    if not answers.name:
        ui.heading(t("init.name"))
        answers.name = ui.ask(t("init.name"))
    if not answers.about:
        ui.heading(t("init.about.title"))
        ui.explain(t("init.about.help"))
        answers.about = ui.ask(t("init.about"))
    ui.heading(t("init.stack.title"))
    ui.explain(t("init.stack.help"))
    for field in ("stack", *COMMANDS):
        if not getattr(answers, field):
            setattr(answers, field, input(f"{t(f'init.{field}')}: ").strip())
    if answers.ui is None:
        answers.ui = ui.confirm(t("init.ui"), default=True)
    return answers


def render_commands(answers: Answers) -> str:
    rows = [f"| {field.capitalize()} | `{getattr(answers, field)}` |" for field in COMMANDS if getattr(answers, field)]
    if answers.ui:
        rows.append("| Screenshot | The affected screen at 1440 and 390 px wide, with the dev server running |")
    if not rows:
        return "<!-- Add the commands to test, lint, typecheck and run the project. -->"
    return "\n".join(["| Task | Command |", "|---|---|", *rows])


def render_agents(answers: Answers) -> str:
    template = (TEMPLATES_DIR / "AGENTS.md").read_text(encoding="utf-8")
    values = {
        "name": answers.name,
        "about": answers.about,
        "stack": answers.stack or "<!-- Languages, frameworks and where each part lives. -->",
        "commands": render_commands(answers),
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def run(answers: Answers, repo: Path) -> int:
    agents = repo / "AGENTS.md"
    if agents.exists():
        print(t("init.exists", path=agents), file=sys.stderr)
        return 1
    if ui.is_interactive():
        answers = interview(answers)
    missing = [field for field in ("name", "about") if not getattr(answers, field)]
    if missing:
        print(t("init.missing", fields=", ".join(missing)), file=sys.stderr)
        return 1
    if not is_repo(repo):
        git(repo, "init", "-q", "-b", "main")

    written = [agents]
    agents.write_text(render_agents(answers), encoding="utf-8")
    context = repo / "docs" / "context"
    context.mkdir(parents=True, exist_ok=True)
    if answers.ui:
        for source, target in (("context/design.md", context / "design.md"), ("design-tokens.json", repo / "design-tokens.json")):
            if not target.exists():
                target.write_text((TEMPLATES_DIR / source).read_text(encoding="utf-8"), encoding="utf-8")
                written.append(target)
    else:
        (context / ".gitkeep").touch()
    if not claude_code.detected():
        generic.install(repo)

    print(t("init.done", files=", ".join(str(path.relative_to(repo)) for path in written)))
    return 0
