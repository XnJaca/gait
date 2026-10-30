import sys
from pathlib import Path

from gait.adapters import ForeignFileError, write_files
from gait.adapters import claude_code, generic
from gait.i18n import t

AGENTS = ("claude-code", "generic")


def detect_agent() -> str:
    return "claude-code" if claude_code.detected() else "generic"


def parse_models(value: str | None) -> dict[str, str]:
    """`cheap=haiku,strong=opus` → {"cheap": "haiku", "strong": "opus"}."""
    models: dict[str, str] = {}
    for pair in filter(None, (value or "").split(",")):
        tier, _, model = pair.partition("=")
        if tier.strip() not in claude_code.DEFAULT_MODELS or not model.strip():
            raise ValueError(pair)
        models[tier.strip()] = model.strip()
    return models


def run(agent: str | None, models: str | None, force: bool, repo: Path) -> int:
    agent = agent or detect_agent()
    if agent == "generic":
        path = generic.install(repo)
        print(t("install.generic", path=path))
        return 0
    try:
        chosen = parse_models(models)
    except ValueError as error:
        print(t("install.bad_model", pair=error), file=sys.stderr)
        return 1
    try:
        written = write_files(claude_code.files(chosen), force=force)
    except ForeignFileError as error:
        print(t("install.foreign", path=error.path), file=sys.stderr)
        return 1
    if not written:
        print(t("install.current"))
    else:
        print(t("install.done", count=len(written)))
    return 0
