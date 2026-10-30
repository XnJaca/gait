from pathlib import Path

from gait import ui
from gait.adapters import claude_code, file_status, generic
from gait.i18n import t
from gait.repo import git


def hooks_path(repo: Path) -> str | None:
    return git(repo, "config", "--get", "core.hooksPath", check=False) or None


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
        print(f"  {t('doctor.claude', state=t(f'doctor.state.{state}'))}")
        if state != "current":
            hints.append(t("doctor.hint_install"))
    else:
        print(f"  {t('doctor.claude_missing')}")

    if (repo / "AGENTS.md").exists():
        state = generic.status(repo)
        print(f"  {t('doctor.block', state=t(f'doctor.state.{state}'))}")
        if state != "current" and not claude_code.detected():
            hints.append(t("doctor.hint_generic"))

    hooks = hooks_path(repo)
    print(f"  {t('doctor.hooks', state=hooks or t('doctor.hooks_off'))}")
    if hooks is None:
        hints.append(t("doctor.hint_hooks"))

    for hint in hints:
        ui.explain(hint)
    return 1 if hints else 0
