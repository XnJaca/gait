import json
import os
from functools import cache
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
DEFAULT = "en"


def language() -> str:
    for variable in ("GAIT_LANG", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable, "")
        if value:
            code = value.split("_")[0].split(".")[0].lower()
            return code if (LOCALES_DIR / f"{code}.json").exists() else DEFAULT
    return DEFAULT


@cache
def _strings(code: str) -> dict[str, str]:
    return json.loads((LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8"))


def t(key: str, **values: object) -> str:
    strings = _strings(language())
    text = strings.get(key) or _strings(DEFAULT)[key]
    return text.format(**values)
