import json
import urllib.parse
import urllib.request
from collections.abc import Callable

from gait.trackers import Ticket, without_people
from gait.trackers.keychain import get_secret

FIELDS = "summary,description"


def service(url: str) -> str:
    return f"gait-jira-{urllib.parse.urlparse(url).hostname}"


def http(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
    return json.loads(body) if body else {}


class JiraTracker:
    """Jira Data Center / Server REST API v2 with a personal access token from the keychain."""

    def __init__(self, url: str, project: str = "", request: Callable[..., dict] = http):
        self.url = url.rstrip("/")
        self.project = project
        self.request = request

    def call(self, method: str, path: str, payload: dict | None = None) -> dict:
        token = get_secret(service(self.url))
        if not token:
            raise PermissionError(service(self.url))
        return self.request(method, f"{self.url}/rest/api/2/{path}", token, payload)

    def search(self, jql: str) -> list[Ticket]:
        query = urllib.parse.urlencode({"jql": jql, "fields": "summary", "maxResults": 50})
        issues = self.call("GET", f"search?{query}").get("issues", [])
        return [Ticket(issue["key"], issue["fields"]["summary"], self.browse(issue["key"])) for issue in issues]

    def browse(self, key: str) -> str:
        return f"{self.url}/browse/{key}"

    def my_tickets(self) -> list[Ticket]:
        scope = f"project = {self.project} AND " if self.project else ""
        mine = f"{scope}assignee = currentUser() AND resolution = Unresolved"
        return self.search(f"{mine} AND sprint in openSprints() ORDER BY rank") or self.search(f"{mine} ORDER BY updated DESC")

    def read(self, key: str) -> Ticket:
        issue = self.call("GET", f"issue/{key}?fields={FIELDS}")
        fields = issue["fields"]
        return Ticket(issue["key"], fields["summary"], self.browse(issue["key"]), without_people(fields.get("description") or ""))

    def comment(self, key: str, text: str) -> None:
        self.call("POST", f"issue/{key}/comment", {"body": text})
