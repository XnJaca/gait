import re
from dataclasses import dataclass
from pathlib import Path

from gait.roles import ROLES_DIR, parse_front_matter

WORK_DIR = ".work"
TEMPLATES_DIR = ROLES_DIR.parent / "templates"
TYPES = ("visual", "behavior", "rule")
SIZES = ("small", "large")
KINDS = ("feat", "fix", "refactor", "chore")
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
STEP = re.compile(r"^- \[( |x)\] (.+)$")


@dataclass(frozen=True)
class Plan:
    path: Path
    slug: str
    type: str
    size: str
    ticket: str
    goal: str
    body: str

    def steps(self) -> list[tuple[bool, str]]:
        _, _, section = self.body.partition("## Steps")
        section = section.split("\n## ", 1)[0]
        return [
            (match.group(1) == "x", match.group(2).strip())
            for match in map(STEP.match, section.splitlines())
            if match
        ]

    def description(self) -> str:
        """The plan as a PR description: no template comments, with a metadata line `gait report` reads."""
        body = re.sub(r"\n?<!--.*?-->\n?", "\n", self.body, flags=re.S).strip()
        heading, _, rest = body.partition("\n")
        meta = f"Type: {self.type} · Size: {self.size}" + (f" · Ticket: {self.ticket}" if self.ticket else "")
        return f"{heading}\n\n{meta}\n{rest}".rstrip() + "\n"


def render(slug: str, type: str, size: str, goal: str, ticket: str = "") -> str:
    template = (TEMPLATES_DIR / "work.md").read_text(encoding="utf-8")
    values = {"slug": slug, "type": type, "size": size, "goal": goal, "ticket": ticket}
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def plan_path(repo: Path, slug: str) -> Path:
    return repo / WORK_DIR / f"{slug}.md"


def load(path: Path) -> Plan:
    data, body = parse_front_matter(path.read_text(encoding="utf-8"))
    heading = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), "")
    return Plan(
        path=path,
        slug=str(data.get("slug", path.stem)),
        type=str(data.get("type", "")),
        size=str(data.get("size", "")),
        ticket=str(data.get("ticket", "")),
        goal=heading,
        body=body,
    )


def plans(repo: Path) -> list[Path]:
    return sorted((repo / WORK_DIR).glob("*.md"))


def current(repo: Path) -> Plan | None:
    found = plans(repo)
    return load(found[0]) if found else None
