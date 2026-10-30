import json
import shutil
from pathlib import Path

from gait.repo import git
from gait.roles import ROLES_DIR

ASSETS_DIR = ROLES_DIR.parent
HOOKS = ("commit-msg", "pre-push")
HOOKS_DIR = ".githooks"
WORKFLOW = Path(".github") / "workflows" / "gait.yml"
ALLOW = (
    "Bash(gait:*)",
    "Bash(git status:*)",
    "Bash(git diff:*)",
    "Bash(git log:*)",
    "Bash(git show:*)",
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Bash(git switch:*)",
    "Bash(git push:*)",
    "Bash(gh pr view:*)",
    "Bash(gh pr diff:*)",
)
DENY = ("Bash(gh pr merge:*)",)


def install_hooks(repo: Path) -> list[Path]:
    target = repo / HOOKS_DIR
    target.mkdir(exist_ok=True)
    written = []
    for name in HOOKS:
        path = target / name
        shutil.copyfile(ASSETS_DIR / "hooks" / name, path)
        path.chmod(0o755)
        written.append(path)
    git(repo, "config", "core.hooksPath", HOOKS_DIR)
    return written


def install_workflow(repo: Path) -> Path | None:
    path = repo / WORKFLOW
    if path.exists():
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ASSETS_DIR / "ci" / "gait.yml", path)
    return path


def command_rule(command: str) -> str:
    return f"Bash({command}:*)"


def install_permissions(repo: Path, commands: list[str]) -> Path:
    """Adds Gait's allow and deny rules to the project's Claude Code settings, keeping existing ones."""
    path = repo / ".claude" / "settings.json"
    settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    permissions = settings.setdefault("permissions", {})
    for key, rules in (("allow", [*ALLOW, *map(command_rule, filter(None, commands))]), ("deny", DENY)):
        current = permissions.setdefault(key, [])
        current += [rule for rule in rules if rule not in current]
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return path


def install(repo: Path, commands: list[str]) -> list[Path]:
    written = install_hooks(repo)
    workflow = install_workflow(repo)
    if workflow:
        written.append(workflow)
    written.append(install_permissions(repo, commands))
    return written
