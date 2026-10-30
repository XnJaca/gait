import sys
from pathlib import Path

from gait.adapters import ForeignFileError, write_files
from gait.adapters import claude_code, generic

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
        print(f"Bloque de Gait escrito en {path}")
        return 0
    try:
        chosen = parse_models(models)
    except ValueError as error:
        print(f"Modelo inválido: {error}. Formato: cheap=haiku,mid=sonnet,strong=opus", file=sys.stderr)
        return 1
    try:
        written = write_files(claude_code.files(chosen), force=force)
    except ForeignFileError as error:
        print(f"{error.path} existe y no lo creó Gait. Usa --force para reemplazarlo.", file=sys.stderr)
        return 1
    if not written:
        print("El adaptador de Claude Code ya está al día.")
    else:
        print(f"Adaptador de Claude Code instalado ({len(written)} archivos). Abre una sesión nueva y usa /gait.")
    return 0
