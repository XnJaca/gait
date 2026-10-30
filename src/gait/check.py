import re
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from gait.adapters import generic
from gait.i18n import t
from gait.repo import current_branch, is_protected
from gait.work import WORK_DIR, plans

AGENTS_LIMIT = 100
CONTEXT_LIMIT = 60
CODE_SPAN = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)[^)]*\)")
PATH_LIKE = re.compile(r"[\w.\-/]+")


def without_gait_block(text: str) -> str:
    """The Gait block points to files on the installing machine, not in the repo."""
    if generic.START not in text:
        return text
    before, _, rest = text.partition(generic.START)
    return before + rest.partition(generic.END)[2]


def mentioned_paths(text: str, repo: Path) -> list[str]:
    """Code spans that look like repo paths: they contain `/` and start at an existing top-level entry."""
    paths = []
    for span in CODE_SPAN.findall(text):
        candidate = re.split(r"[#:]", span, maxsplit=1)[0].rstrip("/")
        if "/" not in candidate or not PATH_LIKE.fullmatch(candidate) or candidate.startswith((".", "/")):
            continue
        if (repo / candidate.split("/", 1)[0]).exists():
            paths.append(candidate)
    return paths


def linked_paths(text: str) -> list[str]:
    """Relative markdown links and images; external links and anchors are skipped."""
    links = []
    visible = re.sub(r"<!--.*?-->", "", re.sub(r"`[^`\n]*`", "", text), flags=re.S)
    for target in MARKDOWN_LINK.findall(visible):
        target = target.split("#", 1)[0]
        if target and "://" not in target and not target.startswith(("mailto:", "/")):
            links.append(target)
    return links


def svg_problem(path: Path) -> str | None:
    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError:
        return "invalid"
    if not root.tag.endswith("svg"):
        return "invalid"
    if "viewBox" not in root.attrib:
        return "viewBox"
    return None


def problems(repo: Path) -> list[str]:
    found = []
    agents = repo / "AGENTS.md"
    if not agents.exists():
        return [t("check.no_agents")]
    readme = repo / "docs" / "README.md"
    documents = [
        (agents, AGENTS_LIMIT),
        *([(readme, CONTEXT_LIMIT)] if readme.exists() else []),
        *((path, CONTEXT_LIMIT) for path in sorted((repo / "docs" / "context").glob("*.md"))),
    ]
    for path, limit in documents:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(repo)
        lines = len(text.splitlines())
        if lines > limit:
            found.append(t("check.too_long", path=relative, lines=lines, limit=limit))
        for target in mentioned_paths(without_gait_block(text), repo):
            if not (repo / target).exists():
                found.append(t("check.broken_path", path=relative, target=target))
        for target in linked_paths(without_gait_block(text)):
            if not (path.parent / target).exists():
                found.append(t("check.broken_link", path=relative, target=target))

    for svg in sorted((repo / "docs" / "diagrams").glob("*.svg")):
        if problem := svg_problem(svg):
            found.append(t(f"check.svg_{problem}", path=svg.relative_to(repo)))

    branch = current_branch(repo)
    if branch and is_protected(repo, branch):
        found += [t("check.work_on_main", path=f"{WORK_DIR}/{path.name}", branch=branch) for path in plans(repo)]
    return found


def run(repo: Path) -> int:
    found = problems(repo)
    for problem in found:
        print(f"  {problem}")
    if not found:
        print(t("check.ok"))
    return 1 if found else 0
