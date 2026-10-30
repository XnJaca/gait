import json
import shutil
from pathlib import Path

from gait.adapters import MARKER, generic
from gait.adapters.claude_code import WITH_DIAGRAM_RULES, WITH_RULES, rules
from gait.roles import Role, load_roles

READ = ["list_files", "read_file", "grep"]
EDIT = [*READ, "edit_file", "delete_file", "shell"]
TOOLS = {
    "triage": ["read_file"],
    "scout": [*READ, "shell"],
    "planner": [*READ, "edit_file", "shell"],
    "verifier": [*READ, "shell"],
    "reviewer": [*READ, "shell"],
}
ORCHESTRATOR_TOOLS = ["invoke_agent", "list_agents", "ask_user_question", *READ, "shell"]


def detected() -> bool:
    return shutil.which("code-puppy") is not None or (Path.home() / ".code_puppy").is_dir()


def agents_dir() -> Path:
    return Path.home() / ".code_puppy" / "agents"


def render_agent(role: Role, models: dict[str, str]) -> str:
    prompt = role.body
    if role.name in WITH_RULES:
        prompt = f"{prompt}\n{rules()}"
    if role.name in WITH_DIAGRAM_RULES:
        prompt = f"{prompt}\n{rules('diagrams')}"
    config = {
        "name": f"gait-{role.name}",
        "description": role.description,
        "system_prompt": prompt,
        "tools": TOOLS.get(role.name, EDIT),
        "generated_by": MARKER,
    }
    if role.tier in models:
        config["model"] = models[role.tier]
    return json.dumps(config, indent=2, ensure_ascii=False) + "\n"


def render_command(orchestrator: Role, roles: dict[str, Role]) -> str:
    delegation = "\n".join(f"- **{name}** → `gait-{name}`" for name in roles if name != "orchestrator")
    return (
        f"{MARKER}\n\n"
        f"{orchestrator.body}\n"
        "## In Code Puppy\n\n"
        "Ask every decision with `ask_user_question`: the opening menu, the ticket, the plan approval, "
        "escalations, and deletions with several choices. Put the recommended option first.\n\n"
        "Run each role with `invoke_agent` and its agent name, passing only the inputs it lists:\n\n"
        f"{delegation}\n\n"
        f"{rules()}"
    )


def files(repo: Path, models: dict[str, str] | None = None) -> dict[Path, str]:
    """Global role agents, plus the repo's `/gait` command."""
    roles = load_roles()
    result = {
        agents_dir() / f"gait-{role.name}.json": render_agent(role, models or {})
        for role in roles.values()
        if role.name != "orchestrator"
    }
    result[generic.command_file(repo)] = render_command(roles["orchestrator"], roles)
    return result
