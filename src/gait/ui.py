"""Terminal styles and interactive questions. Agents pass flags instead."""
import sys
from collections.abc import Callable

from gait.i18n import t

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _style(text: str, code: str) -> str:
    return f"{code}{text}{RESET}" if sys.stdout.isatty() else text


def heading(text: str) -> None:
    print(f"\n{_style(text, BOLD)}")


def explain(text: str) -> None:
    for line in text.strip("\n").split("\n"):
        print(_style(f"  {line}", DIM))


def ask(question: str, default: str = "", validate: Callable[[str], str | None] | None = None) -> str:
    """Asks until the answer is valid. `validate` returns an error message or None."""
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"{question}{suffix}: ").strip() or default
        error = t("ui.required") if not answer else (validate(answer) if validate else None)
        if not error:
            return answer
        print(f"  {error}")


def choose(options: list[tuple[str, str]], default: str) -> str:
    """Numbered menu of (value, description) pairs; returns the chosen value."""
    for number, (value, description) in enumerate(options, 1):
        print(f"  {number}. {_style(value, BOLD)}  {description}")
    values = [value for value, _ in options]
    default_number = str(values.index(default) + 1)

    def valid(answer: str) -> str | None:
        if answer in values or (answer.isdigit() and 1 <= int(answer) <= len(values)):
            return None
        return t("ui.choose_range", count=len(values))

    answer = ask(t("ui.option"), default_number, valid)
    return values[int(answer) - 1] if answer.isdigit() else answer


def confirm(question: str, default: bool = True) -> bool:
    hint = t("ui.yes_no_default_yes") if default else t("ui.yes_no_default_no")
    while True:
        answer = input(f"{question} [{hint}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("s", "si", "sí", "y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print(f"  {t('ui.yes_no')}")
