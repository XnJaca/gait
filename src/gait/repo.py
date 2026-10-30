import subprocess
from pathlib import Path

PROTECTED = {"main", "master"}


class CommandError(Exception):
    def __init__(self, command: list[str], output: str):
        super().__init__(" ".join(command))
        self.command = command
        self.output = output


def run(command: list[str], cwd: Path, check: bool = True) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise CommandError(command, (result.stderr or result.stdout).strip())
    return result.stdout.strip()


def git(repo: Path, *args: str, check: bool = True) -> str:
    return run(["git", *args], repo, check=check)


def is_repo(path: Path) -> bool:
    return git(path, "rev-parse", "--is-inside-work-tree", check=False) == "true"


def current_branch(repo: Path) -> str:
    return git(repo, "branch", "--show-current", check=False)


def default_branch(repo: Path) -> str:
    remote_head = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
    if remote_head:
        return remote_head.split("/", 1)[1]
    return "master" if branch_exists(repo, "master") and not branch_exists(repo, "main") else "main"


def branch_exists(repo: Path, name: str) -> bool:
    return bool(git(repo, "branch", "--list", name, check=False))


def is_protected(repo: Path, branch: str) -> bool:
    return branch in PROTECTED or branch == default_branch(repo)
