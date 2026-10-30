import argparse
import sys
from pathlib import Path

from gait import __version__, doctor, install

COMMANDS = {
    "init": "Prepara un proyecto nuevo y escribe su AGENTS.md.",
    "adopt": "Lleva un repo existente a Gait.",
    "install": "Instala el adaptador del agente.",
    "start": "Crea la rama y el plan de un cambio.",
    "continue": "Muestra el plan de la rama actual y su avance.",
    "check": "Valida presupuestos de contexto y rutas.",
    "finish": "Abre el PR y limpia el plan.",
    "report": "Métricas de los cambios del repo.",
    "doctor": "Revisa el agente, el adaptador y los hooks.",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gait",
        description="Estilo de trabajo con agentes de IA para cualquier proyecto.",
    )
    parser.add_argument("--version", action="version", version=f"gait {__version__}")
    subparsers = parser.add_subparsers(dest="command", metavar="<comando>")
    commands = {
        name: subparsers.add_parser(name, help=help_text, description=help_text)
        for name, help_text in COMMANDS.items()
    }
    commands["install"].add_argument("--agent", choices=install.AGENTS, help="Por defecto, el agente detectado.")
    commands["install"].add_argument("--models", help="Modelo por nivel, p. ej. cheap=haiku,mid=sonnet,strong=opus.")
    commands["install"].add_argument("--force", action="store_true", help="Reemplaza archivos que no creó Gait.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    repo = Path.cwd()
    if args.command == "install":
        return install.run(args.agent, args.models, args.force, repo)
    if args.command == "doctor":
        return doctor.run(repo)
    print(f"gait {args.command}: pendiente de implementar.", file=sys.stderr)
    return 2
