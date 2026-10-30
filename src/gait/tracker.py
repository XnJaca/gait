import getpass
import sys
import urllib.error
from pathlib import Path

from gait import ui
from gait.i18n import t
from gait.repo import CommandError
from gait.trackers import AGENT_KINDS, Config, connect, load_config, save_config
from gait.trackers.jira import service
from gait.trackers.keychain import set_secret

UNAVAILABLE = 3


def show_config(repo: Path) -> int:
    config = load_config(repo)
    print(t("tracker.kind", kind=config.kind))
    if config.project:
        print(t("tracker.project", project=config.project))
    if config.url:
        print(t("tracker.url", url=config.url))
    return 0


def set_config(repo: Path, kind: str, project: str, url: str) -> int:
    if kind == "jira" and not url:
        print(t("tracker.needs_url"), file=sys.stderr)
        return 1
    path = save_config(repo, Config(kind, project, url))
    print(t("tracker.saved", path=path.name))
    if kind == "jira":
        ui.explain(t("tracker.login_hint"))
    return 0


def login(repo: Path) -> int:
    config = load_config(repo)
    if config.kind != "jira":
        print(t("tracker.login_jira_only"), file=sys.stderr)
        return 1
    token = getpass.getpass(t("tracker.token"))
    if not token or not set_secret(service(config.url), token):
        print(t("tracker.login_failed"), file=sys.stderr)
        return 1
    print(t("tracker.login_done"))
    return 0


def ticket(repo: Path, action: str, key: str = "", body: str = "") -> int:
    config = load_config(repo)
    tracker = connect(repo, config)
    if tracker is None:
        message = t(f"ticket.{config.kind}") if config.kind in AGENT_KINDS else t("ticket.none")
        print(message)
        return UNAVAILABLE
    try:
        if action == "list":
            tickets = tracker.my_tickets()
            for item in tickets:
                print(f"{item.key}  {item.title}")
            if not tickets:
                print(t("ticket.empty"))
        elif action == "show":
            print(tracker.read(key).markdown(), end="")
        elif action == "comment":
            if ui.is_interactive() and not ui.confirm(t("ticket.confirm_comment", key=key), default=False):
                return 1
            tracker.comment(key, body)
            print(t("ticket.commented", key=key))
    except PermissionError:
        print(t("ticket.login"), file=sys.stderr)
        return 1
    except (CommandError, urllib.error.URLError, KeyError) as error:
        print(t("ticket.failed", error=error), file=sys.stderr)
        return 1
    return 0
