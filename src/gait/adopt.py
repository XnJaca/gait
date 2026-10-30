import sys
from pathlib import Path

from gait import docs, inventory, ui, validations
from gait.adapters import claude_code, generic
from gait.doctor import hooks_path
from gait.i18n import t
from gait.init import Answers, render_agents
from gait.repo import branch_exists, git, is_repo
from gait.work import TEMPLATES_DIR, WORK_DIR, plan_path

BRANCH = "chore/adopt-gait"
SLUG = "adopt-gait"
ABOUT = "<!-- What it is and what problem it solves, in one sentence. -->"


def blocker(repo: Path) -> str | None:
    if not is_repo(repo):
        return t("start.no_repo")
    if not git(repo, "rev-parse", "--verify", "-q", "HEAD", check=False):
        return t("adopt.no_commits")
    if git(repo, "status", "--porcelain"):
        return t("adopt.dirty")
    if branch_exists(repo, BRANCH):
        return t("start.branch_exists", branch=BRANCH)
    return None


def write_base(repo: Path, found: inventory.Inventory) -> list[str]:
    """Writes the Gait base without touching what the project already has; returns warnings."""
    warnings = []
    agents = repo / "AGENTS.md"
    if not agents.exists():
        answers = Answers(name=found.name, about=ABOUT, stack=", ".join(found.stack), ui=found.ui, **found.commands)
        agents.write_text(render_agents(answers), encoding="utf-8")
    context = repo / "docs" / "context"
    context.mkdir(parents=True, exist_ok=True)
    if found.ui:
        for source, target in (("context/design.md", context / "design.md"), ("design-tokens.json", repo / "design-tokens.json")):
            if not target.exists():
                target.write_text((TEMPLATES_DIR / source).read_text(encoding="utf-8"), encoding="utf-8")
    if not any(context.iterdir()):
        (context / ".gitkeep").touch()
    docs.write_base(repo, found.name, ABOUT)
    if not claude_code.detected():
        generic.install(repo)

    current_hooks = hooks_path(repo)
    if current_hooks and current_hooks != validations.HOOKS_DIR:
        warnings.append(t("adopt.hooks_kept", path=current_hooks))
    else:
        validations.install_hooks(repo)
    if not validations.install_workflow(repo):
        warnings.append(t("adopt.workflow_kept", path=validations.WORKFLOW))
    validations.install_permissions(repo, list(found.commands.values()))
    return warnings


def write_plan(repo: Path, found: inventory.Inventory, warnings: list[str]) -> Path:
    notes = "\n".join(f"- {warning}" for warning in warnings)
    text = (TEMPLATES_DIR / "adopt.md").read_text(encoding="utf-8")
    text = text.replace("{{inventory}}", found.markdown() + (f"\n{notes}" if notes else ""))
    path = plan_path(repo, SLUG)
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run(repo: Path, only_inventory: bool = False) -> int:
    found = inventory.take(repo)
    if only_inventory:
        print(found.markdown())
        return 0
    if problem := blocker(repo):
        print(problem, file=sys.stderr)
        return 1

    git(repo, "switch", "-q", "-c", BRANCH)
    warnings = write_base(repo, found)
    path = write_plan(repo, found, warnings)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: add the gait base and the adoption plan")

    print(t("adopt.done", branch=BRANCH, path=f"{WORK_DIR}/{path.name}"))
    for warning in warnings:
        ui.explain(warning)
    ui.explain(t("adopt.next"))
    return 0
