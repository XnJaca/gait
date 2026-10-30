from html import escape
from pathlib import Path

from gait.work import TEMPLATES_DIR

IGNORE = "docs/.obsidian/workspace*.json"


def overview_svg(name: str) -> str:
    """A starting overview the agent replaces once it knows the system's parts."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 160" font-family="system-ui, sans-serif">\n'
        '  <rect width="480" height="160" fill="#ffffff"/>\n'
        '  <rect x="140" y="50" width="200" height="60" rx="8" fill="#f6f6f4" stroke="#1a1a1a"/>\n'
        f'  <text x="240" y="86" text-anchor="middle" font-size="16" fill="#1a1a1a">{escape(name)}</text>\n'
        "</svg>\n"
    )


def write_base(repo: Path, name: str, about: str) -> list[Path]:
    """docs/ as a human-readable vault: index, overview diagram and Obsidian settings. Keeps what exists."""
    docs = repo / "docs"
    files = {
        docs / "README.md": (TEMPLATES_DIR / "docs" / "README.md").read_text(encoding="utf-8").replace("{{name}}", name).replace("{{about}}", about),
        docs / "diagrams" / "overview.svg": overview_svg(name),
        docs / ".obsidian" / "app.json": (TEMPLATES_DIR / "docs" / ".obsidian" / "app.json").read_text(encoding="utf-8"),
    }
    written = []
    for path, content in files.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            written.append(path)

    gitignore = repo / ".gitignore"
    current = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if IGNORE not in current.splitlines():
        separator = "" if not current or current.endswith("\n") else "\n"
        gitignore.write_text(f"{current}{separator}{IGNORE}\n", encoding="utf-8")
    return written
