import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", ".venv", "dist", "build", ".dart_tool", "target", ".next", ".astro"}
FRAMEWORKS = {
    "astro": "Astro",
    "next": "Next.js",
    "@angular/core": "Angular",
    "@nestjs/core": "NestJS",
    "react": "React",
    "vue": "Vue",
    "svelte": "Svelte",
    "express": "Express",
}
UI_FRAMEWORKS = {"Astro", "Next.js", "Angular", "React", "Vue", "Svelte", "Flutter"}
LEGACY = (
    "PRODUCT.md",
    "DESIGN.md",
    "CLAUDE.md",
    "docs/specs",
    "docs/changes",
    "docs/adr",
    "docs/domain",
    "docs/tech-debt",
    "docs/DECISIONES.md",
    "docs/PENDIENTES.md",
    "docs/BOARD-changes.md",
    "docs/BOARD-tech-debt.md",
    "docs/DASHBOARD.md",
    "docs/.obsidian",
    ".claude/commands",
    ".claude/agents",
    ".claude/hooks",
    ".claude/rules",
)
TYPECHECK_SCRIPTS = ("typecheck", "type-check", "check-types", "tsc")


@dataclass
class Inventory:
    name: str
    stack: list[str] = field(default_factory=list)
    commands: dict[str, str] = field(default_factory=dict)
    ui: bool = False
    agents_lines: int | None = None
    legacy: list[tuple[str, str]] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)

    def markdown(self) -> str:
        lines = [f"- Stack: {', '.join(self.stack) or 'not detected'}"]
        lines += [f"- {task.capitalize()}: `{command}`" for task, command in self.commands.items()]
        lines.append(f"- UI: {'yes' if self.ui else 'no'}")
        lines.append(f"- AGENTS.md: {f'{self.agents_lines} lines' if self.agents_lines is not None else 'missing'}")
        if self.workflows:
            lines.append(f"- CI: {', '.join(self.workflows)}")
        if self.legacy:
            lines.append("- Legacy to condense:")
            lines += [f"  - `{path}` ({size})" for path, size in self.legacy]
        return "\n".join(lines)


def files_named(repo: Path, name: str, depth: int = 3) -> list[Path]:
    found = []

    def walk(directory: Path, level: int) -> None:
        candidate = directory / name
        if candidate.is_file():
            found.append(candidate)
        if level < depth:
            for child in sorted(directory.iterdir()):
                if child.is_dir() and child.name not in SKIP_DIRS and not child.name.startswith("."):
                    walk(child, level + 1)

    walk(repo, 0)
    return found


def package_manager(repo: Path) -> str:
    for lockfile, manager in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun")):
        if (repo / lockfile).exists():
            return manager
    return "npm"


def node_commands(repo: Path) -> dict[str, str]:
    path = repo / "package.json"
    if not path.exists():
        return {}
    scripts = json.loads(path.read_text(encoding="utf-8")).get("scripts", {})
    manager = package_manager(repo)
    found = {}
    for task, names in (("test", ("test",)), ("lint", ("lint",)), ("typecheck", TYPECHECK_SCRIPTS), ("dev", ("dev", "start"))):
        name = next((name for name in names if name in scripts), None)
        if name:
            found[task] = f"{manager} test" if name == "test" else f"{manager} run {name}"
    return found


def python_commands(repo: Path) -> dict[str, str]:
    path = repo / "pyproject.toml"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    prefix = "uv run " if (repo / "uv.lock").exists() else ""
    found = {"test": f"{prefix}pytest"}
    if "ruff" in text:
        found["lint"] = f"{prefix}ruff check ."
    if "mypy" in text:
        found["typecheck"] = f"{prefix}mypy ."
    return found


def other_commands(repo: Path) -> dict[str, str]:
    if (repo / "pubspec.yaml").exists():
        return {"test": "flutter test", "lint": "flutter analyze", "dev": "flutter run"}
    if (repo / "go.mod").exists():
        return {"test": "go test ./...", "lint": "go vet ./..."}
    if (repo / "Cargo.toml").exists():
        return {"test": "cargo test", "lint": "cargo clippy"}
    makefile = repo / "Makefile"
    if makefile.exists() and "\ntest:" in "\n" + makefile.read_text(encoding="utf-8"):
        return {"test": "make test"}
    return {}


def detect_stack(repo: Path) -> list[str]:
    stack: list[str] = []
    packages = files_named(repo, "package.json")
    if packages:
        stack.append("Node.js")
        for path in packages:
            data = json.loads(path.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            stack += [label for dependency, label in FRAMEWORKS.items() if dependency in deps and label not in stack]
    if files_named(repo, "pubspec.yaml"):
        stack.append("Flutter")
    if (repo / "pyproject.toml").exists():
        stack.append("Python")
    if (repo / "go.mod").exists():
        stack.append("Go")
    if (repo / "Cargo.toml").exists():
        stack.append("Rust")
    if (repo / "pnpm-workspace.yaml").exists() or (repo / "turbo.json").exists():
        stack.append("monorepo")
    return stack


def line_count(path: Path) -> int:
    if path.is_file():
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    return sum(line_count(child) for child in path.rglob("*.md") if child.is_file())


def size(path: Path) -> str:
    """Markdown lines for docs; a file count for tooling folders without markdown."""
    lines = line_count(path)
    if lines or path.is_file():
        return f"{lines} lines"
    return f"{sum(1 for child in path.rglob('*') if child.is_file())} files"


def project_name(repo: Path) -> str:
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        name = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {}).get("name")
        if name:
            return name
    package = repo / "package.json"
    if package.exists():
        name = json.loads(package.read_text(encoding="utf-8")).get("name")
        if name:
            return name
    return repo.name


def take(repo: Path) -> Inventory:
    stack = detect_stack(repo)
    commands = {**other_commands(repo), **python_commands(repo), **node_commands(repo)}
    agents = repo / "AGENTS.md"
    workflows = repo / ".github" / "workflows"
    return Inventory(
        name=project_name(repo),
        stack=stack,
        commands={task: commands[task] for task in ("test", "lint", "typecheck", "dev") if task in commands},
        ui=bool(UI_FRAMEWORKS & set(stack)),
        agents_lines=line_count(agents) if agents.exists() else None,
        legacy=[(path, size(repo / path)) for path in LEGACY if (repo / path).exists()],
        workflows=sorted(path.name for path in workflows.glob("*.y*ml")) if workflows.is_dir() else [],
    )
