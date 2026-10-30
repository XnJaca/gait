import subprocess
from pathlib import Path

from gait import ui
from gait.adapters import claude_code, file_status, generic

LABELS = {"current": "al día", "outdated": "desactualizado", "missing": "no instalado", "foreign": "archivo ajeno"}


def hooks_path(repo: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--get", "core.hooksPath"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or None


def claude_code_state() -> str:
    states = {file_status(path, content).state for path, content in claude_code.files().items()}
    for state in ("foreign", "missing", "outdated"):
        if state in states:
            return state
    return "current"


def run(repo: Path) -> int:
    hints = []
    ui.heading("Gait doctor")

    if claude_code.detected():
        state = claude_code_state()
        print(f"  Claude Code: {LABELS[state]}")
        if state != "current":
            hints.append("Corre `gait install` para instalar o actualizar el adaptador.")
    else:
        print("  Claude Code: no detectado")

    if (repo / "AGENTS.md").exists():
        state = generic.status(repo)
        print(f"  Bloque en AGENTS.md: {LABELS[state]}")
        if state != "current" and not claude_code.detected():
            hints.append("Corre `gait install --agent generic` para actualizar el bloque.")

    hooks = hooks_path(repo)
    print(f"  Git hooks: {hooks or 'sin activar'}")
    if hooks is None:
        hints.append("Los hooks se activan con `gait init` o `gait adopt`.")

    for hint in hints:
        ui.explain(hint)
    return 1 if hints else 0
