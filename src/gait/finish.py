import re
import sys
from pathlib import Path

from gait import check
from gait.i18n import t
from gait.repo import CommandError, current_branch, default_branch, git, is_protected, run as run_command
from gait.work import current

TITLE = re.compile(r"^[a-z]+(\([a-z0-9-]+\))?!?: \S")
TITLE_MAX = 72


def run(repo: Path, title: str | None = None, draft: bool = False) -> int:
    plan = current(repo)
    if plan is None:
        print(t("finish.no_plan"), file=sys.stderr)
        return 1
    branch = current_branch(repo)
    if is_protected(repo, branch):
        print(t("finish.on_main", branch=branch), file=sys.stderr)
        return 1
    found = check.problems(repo)
    if found:
        for problem in found:
            print(f"  {problem}", file=sys.stderr)
        print(t("finish.check_failed"), file=sys.stderr)
        return 1

    kind = branch.split("/", 1)[0] if "/" in branch else "feat"
    pr_title = title or f"{kind}: {plan.goal}"
    if len(pr_title) > TITLE_MAX or not TITLE.match(pr_title):
        print(t("finish.bad_title", title=pr_title, max=TITLE_MAX), file=sys.stderr)
        return 1
    body = plan.description()
    command = ["gh", "pr", "create", "--base", default_branch(repo), "--title", pr_title, "--body", body]
    if draft:
        command.append("--draft")
    try:
        git(repo, "rm", "-q", str(plan.path.relative_to(repo)))
        git(repo, "commit", "-q", "-m", f"chore: remove the plan for {plan.slug}")
        git(repo, "push", "-q", "-u", "origin", branch)
        url = run_command(command, repo)
    except CommandError as error:
        print(t("finish.failed", command=" ".join(error.command[:3])), file=sys.stderr)
        print(error.output, file=sys.stderr)
        return 1
    print(t("finish.done", url=url.splitlines()[-1] if url else ""))
    return 0
