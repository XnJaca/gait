import argparse
import sys
from pathlib import Path

from gait import __version__, check, doctor, finish, init, install, start, ui
from gait.i18n import t
from gait.work import KINDS, SIZES, TYPES

COMMANDS = ("init", "adopt", "install", "start", "continue", "check", "finish", "report", "doctor")
MENU = ("start", "continue", "review", "free")


def new_parser(**kwargs) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, **kwargs)
    parser._optionals.title = t("cli.options")
    parser.add_argument("-h", "--help", action="help", help=t("cli.help"))
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = new_parser(prog="gait", description=t("cli.description"))
    parser.add_argument("--version", action="version", version=f"gait {__version__}", help=t("cli.version"))
    subparsers = parser.add_subparsers(dest="command", title=t("cli.commands"), metavar=t("cli.command"))
    commands = {}
    for name in COMMANDS:
        help_text = t(f"cmd.{name}")
        commands[name] = subparsers.add_parser(name, help=help_text, description=help_text, add_help=False)
        commands[name]._optionals.title = t("cli.options")
        commands[name]._positionals.title = t("cli.arguments")
        commands[name].add_argument("-h", "--help", action="help", help=t("cli.help"))

    commands["install"].add_argument("--agent", choices=install.AGENTS, help=t("arg.agent"))
    commands["install"].add_argument("--models", help=t("arg.models"))
    commands["install"].add_argument("--force", action="store_true", help=t("arg.force"))

    for field in ("name", "about", "stack", *init.COMMANDS):
        commands["init"].add_argument(f"--{field}", default="", help=t(f"arg.{field}"))
    commands["init"].add_argument("--ui", action=argparse.BooleanOptionalAction, default=None, help=t("arg.ui"))

    commands["start"].add_argument("slug", nargs="?", default="", help=t("arg.slug"))
    commands["start"].add_argument("--type", choices=TYPES, default="", help=t("arg.type"))
    commands["start"].add_argument("--size", choices=SIZES, default="", help=t("arg.size"))
    commands["start"].add_argument("--goal", default="", help=t("arg.goal"))
    commands["start"].add_argument("--ticket", default="", help=t("arg.ticket"))
    commands["start"].add_argument("--kind", choices=KINDS, default="feat", help=t("arg.kind"))

    commands["finish"].add_argument("--title", help=t("arg.title"))
    commands["finish"].add_argument("--draft", action="store_true", help=t("arg.draft"))
    return parser


def menu(repo: Path) -> int:
    ui.heading(t("menu.title"))
    labels = [t(f"menu.{option}") for option in MENU]
    option = MENU[labels.index(ui.choose([(label, "") for label in labels], labels[0]))]
    if option == "start":
        return start.run(start.Request(), repo)
    if option == "continue":
        return start.resume(repo)
    print(t("menu.in_agent"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path.cwd()
    if args.command is None:
        if ui.is_interactive():
            return menu(repo)
        parser.print_help()
        return 0
    if args.command == "install":
        return install.run(args.agent, args.models, args.force, repo)
    if args.command == "doctor":
        return doctor.run(repo)
    if args.command == "init":
        fields = {field: getattr(args, field) for field in ("name", "about", "stack", *init.COMMANDS)}
        return init.run(init.Answers(**fields, ui=args.ui), repo)
    if args.command == "start":
        return start.run(start.Request(args.slug, args.type, args.size, args.goal, args.ticket, args.kind), repo)
    if args.command == "continue":
        return start.resume(repo)
    if args.command == "check":
        return check.run(repo)
    if args.command == "finish":
        return finish.run(repo, args.title, args.draft)
    print(t("cmd.pending", command=args.command), file=sys.stderr)
    return 2
