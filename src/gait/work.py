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

    def section(self, name: str) -> str:
        _, found, section = self.body.partition(f"\n## {name}\n")
        return re.sub(r"<!--.*?-->", "", section.split("\n## ", 1)[0], flags=re.S).strip() if found else ""

    def steps(self) -> list[tuple[bool, str]]:
        section = self.section("Steps")
        return [
            (match.group(1) == "x", match.group(2).strip())
            for match in map(STEP.match, section.splitlines())
            if match
        ]

    def description(self) -> str:
        """A short PR description: goal, the metadata line `gait report` reads, summary and delivery notes.

        The full plan stays in the branch history, in its `chore: plan` commit."""
        meta = f"Type: {self.type} · Size: {self.size}" + (f" · Ticket: {self.ticket}" if self.ticket else "")
        summary = self.section("Summary")
        if not summary.strip("- \n"):
            summary = "\n".join(f"- {text.split(chr(10))[0].rstrip('.')}" for _, text in self.steps())
        parts = [f"# {self.goal}", meta, f"## Summary\n\n{summary}"]
        notes = self.section("Delivery notes")
        if notes:
            parts.append(f"## Delivery notes\n\n{notes}")
        parts.append(f"Full plan: the `chore: plan {self.slug}` commit.")
        return "\n\n".join(parts) + "\n"


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
