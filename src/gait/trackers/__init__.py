import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

CONFIG = ".gait.toml"
KINDS = ("none", "manual", "jira-agent", "github", "jira")
# Kinds whose tickets come through the agent or the user, not through the CLI.
AGENT_KINDS = ("manual", "jira-agent")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
MENTION = re.compile(r"\[~[^\]]+\]|(?<![\w/])@[\w-]+(?![\w./-])")


@dataclass(frozen=True)
class Ticket:
    key: str
    title: str
    url: str
    description: str = ""

    def markdown(self) -> str:
        lines = [f"# {self.key} — {self.title}", "", self.url]
        if self.description:
            lines += ["", self.description.strip()]
        return "\n".join(lines) + "\n"


class Tracker(Protocol):
    def my_tickets(self) -> list[Ticket]: ...

    def read(self, key: str) -> Ticket: ...

    def comment(self, key: str, text: str) -> None: ...


@dataclass(frozen=True)
class Config:
    kind: str = "none"
    project: str = ""
    url: str = ""


def without_people(text: str) -> str:
    """Tickets reach the repo without emails or user mentions."""
    return MENTION.sub("[person]", EMAIL.sub("[email]", text or ""))


def load_config(repo: Path) -> Config:
    path = repo / CONFIG
    if not path.exists():
        return Config()
    data = tomllib.loads(path.read_text(encoding="utf-8")).get("tracker", {})
    return Config(kind=data.get("kind", "none"), project=data.get("project", ""), url=data.get("url", ""))


def save_config(repo: Path, config: Config) -> Path:
    path = repo / CONFIG
    lines = ["[tracker]", f'kind = "{config.kind}"']
    if config.project:
        lines.append(f'project = "{config.project}"')
    if config.url:
        lines.append(f'url = "{config.url}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def connect(repo: Path, config: Config) -> Tracker | None:
    if config.kind == "github":
        from gait.trackers.github import GitHubTracker

        return GitHubTracker(repo)
    if config.kind == "jira":
        from gait.trackers.jira import JiraTracker

        return JiraTracker(config.url, config.project)
    return None
