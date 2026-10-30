from pathlib import Path

from gait.adapters import MARKER
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
        f"Rules every change follows: `{roles.parent / 'rules' / 'base.md'}`; diagrams: `{roles.parent / 'rules' / 'diagrams.md'}`.\n"
        f"{END}\n"
    )


def command_file(repo: Path) -> Path:
    """`/gait` for agents that read prompt files from `.agents/commands/`, such as Code Puppy."""
    return repo / ".agents" / "commands" / "gait.md"


def render_command() -> str:
    roles = ROLES_DIR.resolve()
    return (
        f"{MARKER}\n\n"
        f"Start a Gait session. Read `{roles / 'orchestrator.md'}` and follow it, beginning with its opening menu. "
        "Show every decision as a numbered list the user answers with a number. "
        "You have no subagents: follow its \"Without subagents\" section and run each role yourself, "
        f"reading `{roles}/<role>.md` only when you reach its step. "
        f"Rules every change follows: `{roles.parent / 'rules' / 'base.md'}`.\n"
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
