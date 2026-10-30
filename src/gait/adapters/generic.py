from pathlib import Path

from gait.roles import ROLES_DIR

START = "<!-- gait:start -->"
END = "<!-- gait:end -->"


def render_block() -> str:
    roles = ROLES_DIR.resolve()
    return (
        f"{START}\n"
        "## Gait\n\n"
        "This repo works with Gait. When the user starts a session or asks for a change, "
        f"read `{roles / 'orchestrator.md'}` and follow it. "
        f"Each step's instructions are in `{roles}/<role>.md`; read a role only when you reach its step. "
        f"Rules every change follows: `{roles.parent / 'rules' / 'base.md'}`.\n"
        f"{END}\n"
    )


def apply_block(text: str, block: str) -> str:
    """Replaces the Gait block in AGENTS.md, or appends it if missing."""
    if START in text and END in text:
        before, _, rest = text.partition(START)
        _, _, after = rest.partition(END)
        return before + block.rstrip("\n") + after
    separator = "" if not text or text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    return text + separator + block


def agents_file(repo: Path) -> Path:
    return repo / "AGENTS.md"


def status(repo: Path) -> str:
    path = agents_file(repo)
    if not path.exists():
        return "missing"
    text = path.read_text(encoding="utf-8")
    if START not in text:
        return "missing"
    return "current" if apply_block(text, render_block()) == text else "outdated"


def install(repo: Path) -> Path:
    path = agents_file(repo)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(apply_block(text, render_block()), encoding="utf-8")
    return path
