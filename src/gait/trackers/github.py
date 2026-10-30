import json
from pathlib import Path

from gait.repo import run
from gait.trackers import Ticket, without_people


class GitHubTracker:
    def __init__(self, repo: Path):
        self.repo = repo

    def gh(self, *args: str) -> str:
        return run(["gh", *args], self.repo)

    def my_tickets(self) -> list[Ticket]:
        issues = json.loads(self.gh("issue", "list", "--assignee", "@me", "--state", "open", "--json", "number,title,url"))
        return [Ticket(f"#{issue['number']}", issue["title"], issue["url"]) for issue in issues]

    def read(self, key: str) -> Ticket:
        issue = json.loads(self.gh("issue", "view", key.lstrip("#"), "--json", "number,title,body,url"))
        return Ticket(f"#{issue['number']}", issue["title"], issue["url"], without_people(issue["body"]))

    def comment(self, key: str, text: str) -> None:
        self.gh("issue", "comment", key.lstrip("#"), "--body", text)
