import json

import pytest

from gait import tracker as tracker_cli
from gait.cli import main
from gait.repo import CommandError
from gait.trackers import Config, Ticket, load_config, save_config, without_people
from gait.trackers import github as github_module
from gait.trackers import jira as jira_module
from gait.trackers.jira import JiraTracker


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_config_round_trip(repo):
    save_config(repo, Config("jira", "SHOP", "https://jira.example.com"))
    assert load_config(repo) == Config("jira", "SHOP", "https://jira.example.com")


def test_missing_config_means_no_tracker(repo):
    assert load_config(repo) == Config()


def test_tracker_set_and_show(repo, capsys):
    assert main(["tracker", "set", "github"]) == 0
    capsys.readouterr()
    assert main(["tracker"]) == 0
    assert "Tracker: github" in capsys.readouterr().out


def test_jira_needs_a_url(repo):
    assert main(["tracker", "set", "jira"]) == 1


@pytest.mark.parametrize(("kind", "text"), [("none", "no tracker"), ("manual", "paste"), ("jira-agent", "Jira agent")])
def test_kinds_without_api_point_elsewhere(repo, capsys, kind, text):
    save_config(repo, Config(kind))
    assert main(["ticket", "list"]) == tracker_cli.UNAVAILABLE
    assert text in capsys.readouterr().out


def test_login_only_for_jira(repo):
    save_config(repo, Config("github"))
    assert main(["tracker", "login"]) == 1


def test_people_are_removed():
    text = "Ask ana.mora@acme.com or @ana-m, cc [~jdoe]. Use @angular/core and https://x.com/@y."
    cleaned = without_people(text)
    assert "ana.mora@acme.com" not in cleaned
    assert "@ana-m" not in cleaned
    assert "[~jdoe]" not in cleaned
    assert "@angular/core" in cleaned


def test_ticket_markdown():
    ticket = Ticket("SHOP-1", "Login", "https://jira/browse/SHOP-1", "Given a user\n")
    assert ticket.markdown() == "# SHOP-1 — Login\n\nhttps://jira/browse/SHOP-1\n\nGiven a user\n"


def test_github_tickets(repo, monkeypatch, capsys):
    calls = []

    def fake_run(command, cwd, check=True):
        calls.append(command)
        if command[2] == "list":
            return json.dumps([{"number": 3, "title": "Bread list", "url": "u3"}])
        if command[2] == "view":
            return json.dumps({"number": 3, "title": "Bread list", "url": "u3", "body": "Reported by @ana"})
        return ""

    monkeypatch.setattr(github_module, "run", fake_run)
    save_config(repo, Config("github"))
    assert main(["ticket", "list"]) == 0
    assert "#3  Bread list" in capsys.readouterr().out
    assert main(["ticket", "show", "#3"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# #3 — Bread list")
    assert "@ana" not in out
    assert main(["ticket", "comment", "#3", "--body", "PR: u"]) == 0
    assert calls[-1] == ["gh", "issue", "comment", "3", "--body", "PR: u"]


def test_tracker_failures_are_reported(repo, monkeypatch, capsys):
    def failing(command, cwd, check=True):
        raise CommandError(command, "boom")

    monkeypatch.setattr(github_module, "run", failing)
    save_config(repo, Config("github"))
    assert main(["ticket", "list"]) == 1
    assert "failed" in capsys.readouterr().err


class FakeJira:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, method, url, token, payload=None):
        self.calls.append((method, url, token, payload))
        return self.responses.pop(0) if self.responses else {}


def jira(responses, monkeypatch, token="secret"):
    monkeypatch.setattr(jira_module, "get_secret", lambda service: token)
    fake = FakeJira(responses)
    return JiraTracker("https://jira.example.com/", "SHOP", request=fake), fake


def test_jira_prefers_the_open_sprint(monkeypatch):
    tracker, fake = jira([{"issues": [{"key": "SHOP-9", "fields": {"summary": "Menu"}}]}], monkeypatch)
    tickets = tracker.my_tickets()
    assert tickets == [Ticket("SHOP-9", "Menu", "https://jira.example.com/browse/SHOP-9")]
    method, url, token, _ = fake.calls[0]
    assert (method, token) == ("GET", "secret")
    assert "openSprints" in url and "project+%3D+SHOP" in url


def test_jira_falls_back_to_unresolved(monkeypatch):
    tracker, fake = jira([{"issues": []}, {"issues": [{"key": "SHOP-2", "fields": {"summary": "Old"}}]}], monkeypatch)
    assert [ticket.key for ticket in tracker.my_tickets()] == ["SHOP-2"]
    assert "openSprints" not in fake.calls[1][1]


def test_jira_read_and_comment(monkeypatch):
    issue = {"key": "SHOP-9", "fields": {"summary": "Menu", "description": "Given [~jdoe] logs in"}}
    tracker, fake = jira([issue], monkeypatch)
    ticket = tracker.read("SHOP-9")
    assert ticket.description == "Given [person] logs in"
    tracker.comment("SHOP-9", "PR: u")
    assert fake.calls[-1][0] == "POST"
    assert fake.calls[-1][1].endswith("/rest/api/2/issue/SHOP-9/comment")
    assert fake.calls[-1][3] == {"body": "PR: u"}


def test_jira_without_token(monkeypatch):
    tracker, _ = jira([], monkeypatch, token=None)
    with pytest.raises(PermissionError):
        tracker.my_tickets()
