import sys
from dataclasses import dataclass
from pathlib import Path

from gait import ui
from gait.i18n import t
from gait.repo import branch_exists, git, is_repo
from gait.work import SIZES, SLUG, TYPES, WORK_DIR, current, plan_path, render


@dataclass
class Request:
    slug: str = ""
    type: str = ""
    size: str = ""
    goal: str = ""
    ticket: str = ""
    kind: str = "feat"


def slug_error(value: str) -> str | None:
    return None if SLUG.fullmatch(value) else t("start.bad_slug")


def interview(request: Request) -> Request:
    print(t("start.intro"))
    if not request.goal:
        request.goal = ui.ask(t("start.goal"))
    if not request.slug:
        request.slug = ui.ask(t("start.slug"), validate=slug_error)
    if not request.type:
        ui.heading(t("start.type"))
        request.type = ui.choose([(value, "") for value in TYPES], TYPES[1])
    if not request.size:
        ui.heading(t("start.size"))
        request.size = ui.choose([(value, "") for value in SIZES], SIZES[0])
    return request


def run(request: Request, repo: Path) -> int:
    if not is_repo(repo):
        print(t("start.no_repo"), file=sys.stderr)
        return 1
    if ui.is_interactive():
        request = interview(request)
    missing = [field for field in ("slug", "type", "size", "goal") if not getattr(request, field)]
    if missing:
        print(t("start.missing", fields=", ".join(missing)), file=sys.stderr)
        return 1
    if error := slug_error(request.slug):
        print(error, file=sys.stderr)
        return 1

    branch = f"{request.kind}/{request.slug}"
    if branch_exists(repo, branch):
        print(t("start.branch_exists", branch=branch), file=sys.stderr)
        return 1
    git(repo, "switch", "-q", "-c", branch)
    path = plan_path(repo, request.slug)
    path.parent.mkdir(exist_ok=True)
    path.write_text(render(request.slug, request.type, request.size, request.goal, request.ticket), encoding="utf-8")
    git(repo, "add", str(path))
    git(repo, "commit", "-q", "-m", f"chore: plan {request.slug}")
    print(t("start.done", branch=branch, path=f"{WORK_DIR}/{path.name}"))
    return 0


def resume(repo: Path) -> int:
    plan = current(repo)
    if plan is None:
        print(t("continue.none"))
        return 1
    steps = plan.steps()
    done = sum(1 for checked, _ in steps if checked)
    print(t("continue.plan", path=plan.path.relative_to(repo)))
    print(t("continue.goal", goal=plan.goal))
    print(t("continue.progress", done=done, total=len(steps)))
    pending = next((text for checked, text in steps if not checked), None)
    print(t("continue.next", step=pending) if pending else t("continue.all_done"))
    return 0

