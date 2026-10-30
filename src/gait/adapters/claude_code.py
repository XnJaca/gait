import shutil
from pathlib import Path

from gait.adapters import MARKER
from gait.roles import ROLES_DIR, Role, load_roles

DEFAULT_MODELS = {"cheap": "haiku", "mid": "sonnet", "strong": "opus"}
EFFORT = {"cheap": "low", "mid": "medium", "strong": "high"}
# Roles that only read get a restricted tool list; the rest inherit every tool.
TOOLS = {
    "triage": "Read",
    "scout": "Read, Grep, Glob, Bash",
    "planner": "Read, Grep, Glob, Write, Edit, Bash",
    "verifier": "Read, Grep, Glob, Bash",
    "reviewer": "Read, Grep, Glob, Bash",
}
BACKGROUND = {"tester"}
WITH_RULES = {"planner", "builder", "tester", "deliver"}
WITH_DIAGRAM_RULES = {"deliver"}


def detected() -> bool:
    return shutil.which("claude") is not None or (Path.home() / ".claude").is_dir()


def claude_dir() -> Path:
    return Path.home() / ".claude"


def rules(name: str = "base") -> str:
    return (ROLES_DIR.parent / "rules" / f"{name}.md").read_text(encoding="utf-8")


def render_agent(role: Role, models: dict[str, str]) -> str:
    header = [
        "---",
        f"name: gait-{role.name}",
        f"description: {role.description}",
        f"model: {models[role.tier]}",
        f"effort: {EFFORT[role.tier]}",
    ]
    if role.name in TOOLS:
        header.append(f"tools: {TOOLS[role.name]}")
    if role.name in BACKGROUND:
        header.append("background: true")
    header.append("---")
    body = role.body
    if role.name in WITH_RULES:
        body = f"{body}\n{rules()}"
    if role.name in WITH_DIAGRAM_RULES:
        body = f"{body}\n{rules('diagrams')}"
    return "\n".join(header) + f"\n\n{MARKER}\n\n{body}"


def render_skill(orchestrator: Role, roles: dict[str, Role]) -> str:
    delegation = "\n".join(
        f"- **{name}** → subagent `gait-{name}`" for name in roles if name != "orchestrator"
    )
    return (
        "---\n"
        "name: gait\n"
        f"description: {orchestrator.description}\n"
        "disable-model-invocation: true\n"
        "---\n\n"
        f"{MARKER}\n\n"
        f"{orchestrator.body}\n"
        "## Roles in Claude Code\n\n"
        "Run each role as its subagent and pass only the inputs it lists. "
        "Start builder and tester in the same turn so they run in parallel.\n\n"
        f"{delegation}\n\n"
        f"{rules()}"
    )


def files(models: dict[str, str] | None = None) -> dict[Path, str]:
    models = {**DEFAULT_MODELS, **(models or {})}
    roles = load_roles()
    target = claude_dir()
    result = {
        target / "agents" / f"gait-{role.name}.md": render_agent(role, models)
        for role in roles.values()
        if role.name != "orchestrator"
    }
    result[target / "skills" / "gait" / "SKILL.md"] = render_skill(roles["orchestrator"], roles)
    return result
