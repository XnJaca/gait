from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
# Installed wheels bundle roles inside the package; a source checkout keeps them at the repo root.
ROLES_DIR = next(path for path in (PACKAGE_DIR / "roles", PACKAGE_DIR.parents[1] / "roles") if path.is_dir())
TIERS = ("cheap", "mid", "strong", "session")


@dataclass(frozen=True)
class Role:
    name: str
    tier: str
    inputs: list[str]
    output_budget: int
    description: str
    body: str


def parse_front_matter(text: str) -> tuple[dict[str, str | list[str]], str]:
    """Parses flat `key: value` front matter; `[a, b]` values become lists."""
    if not text.startswith("---\n"):
        raise ValueError("missing front matter")
    header, _, body = text[4:].partition("\n---\n")
    data: dict[str, str | list[str]] = {}
    for line in header.splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            data[key.strip()] = [item.strip() for item in value[1:-1].split(",") if item.strip()]
        else:
            data[key.strip()] = value
    return data, body.lstrip("\n")


def load_role(path: Path) -> Role:
    data, body = parse_front_matter(path.read_text(encoding="utf-8"))
    tier = str(data["tier"])
    if tier not in TIERS:
        raise ValueError(f"{path.name}: unknown tier {tier!r}")
    return Role(
        name=str(data["role"]),
        tier=tier,
        inputs=list(data["inputs"]),
        output_budget=int(str(data["output_budget"])),
        description=str(data["description"]),
        body=body,
    )


def load_roles(directory: Path = ROLES_DIR) -> dict[str, Role]:
    roles = (load_role(path) for path in sorted(directory.glob("*.md")))
    return {role.name: role for role in roles}
