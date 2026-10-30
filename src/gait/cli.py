import argparse
import sys

from gait import __version__

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
    for name, help_text in COMMANDS.items():
        subparsers.add_parser(name, help=help_text, description=help_text)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    print(f"gait {args.command}: pendiente de implementar.", file=sys.stderr)
    return 2
