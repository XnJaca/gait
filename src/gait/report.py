import json
import re
import statistics
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from gait.i18n import t
from gait.repo import CommandError, run
from gait.work import TYPES

META = re.compile(r"^Type: (\w+) · Size: (\w+)", re.M)
ROUNDS = re.compile(r"Verifier rounds: *(\d+)")
ESCALATIONS = re.compile(r"Escalations: *(\d+)")


@dataclass
class Change:
    number: int
    branch: str
    type: str
    size: str
    hours: float
    verifier_rounds: int
    escalations: int
    input_tokens: int | None = None
    output_tokens: int | None = None


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def number(pattern: re.Pattern, text: str) -> int:
    match = pattern.search(text)
    return int(match.group(1)) if match else 0


def to_change(pr: dict) -> Change | None:
    meta = META.search(pr.get("body") or "")
    if not meta:
        return None
    plan_commit = next(
        (commit for commit in pr.get("commits", []) if commit.get("messageHeadline", "").startswith("chore: plan ")),
        None,
    )
    started = parse_time(plan_commit["committedDate"] if plan_commit else pr["createdAt"])
    hours = (parse_time(pr["mergedAt"]) - started).total_seconds() / 3600
    body = pr["body"]
    return Change(pr["number"], pr["headRefName"], meta.group(1), meta.group(2), round(hours, 1), number(ROUNDS, body), number(ESCALATIONS, body))


def merged_prs(repo: Path, limit: int) -> list[dict]:
    """Merged PRs; commits are fetched only for Gait PRs, since listing them all exceeds GitHub's query limits."""
    fields = "number,body,createdAt,mergedAt,headRefName"
    prs = json.loads(run(["gh", "pr", "list", "--state", "merged", "--limit", str(limit), "--json", fields], repo))
    for pr in prs:
        if META.search(pr.get("body") or ""):
            pr["commits"] = json.loads(run(["gh", "pr", "view", str(pr["number"]), "--json", "commits"], repo))["commits"]
    return prs


def transcripts_dir(repo: Path) -> Path:
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(repo.resolve()))


def tokens_by_branch(repo: Path) -> dict[str, tuple[int, int]]:
    """Input (with cache) and output tokens per git branch, from Claude Code transcripts and their subagents."""
    totals: dict[str, list[int]] = {}
    seen: set[str] = set()
    directory = transcripts_dir(repo)
    if not directory.is_dir():
        return {}
    for path in directory.rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            usage = (entry.get("message") or {}).get("usage") if entry.get("type") == "assistant" else None
            request = entry.get("requestId") or (entry.get("message") or {}).get("id")
            if not usage or not entry.get("gitBranch") or request in seen:
                continue
            seen.add(request)
            spent = sum(usage.get(key) or 0 for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
            branch = totals.setdefault(entry["gitBranch"], [0, 0])
            branch[0] += spent
            branch[1] += usage.get("output_tokens") or 0
    return {branch: (values[0], values[1]) for branch, values in totals.items()}


def summarize(changes: list[Change]) -> list[dict]:
    rows = []
    for kind in (*TYPES, "all"):
        group = [change for change in changes if kind in ("all", change.type)]
        if not group:
            continue
        measured = [change for change in group if change.output_tokens is not None]
        rows.append({
            "type": kind,
            "changes": len(group),
            "median_hours": round(statistics.median(change.hours for change in group), 1),
            "verifier_rounds": round(statistics.mean(change.verifier_rounds for change in group), 1),
            "escalations": sum(change.escalations for change in group),
            "input_tokens": round(statistics.mean(change.input_tokens for change in measured)) if measured else None,
            "output_tokens": round(statistics.mean(change.output_tokens for change in measured)) if measured else None,
        })
    return rows


def compact(value: int | None) -> str:
    if value is None:
        return "—"
    return f"{value / 1_000_000:.1f}M" if value >= 1_000_000 else f"{value / 1000:.0f}k" if value >= 1000 else str(value)


def print_table(rows: list[dict], without_gait: int) -> None:
    headers = [t(f"report.{key}") for key in ("type", "changes", "median_hours", "verifier_rounds", "escalations", "input_tokens", "output_tokens")]
    lines = [headers]
    for row in rows:
        lines.append([
            row["type"],
            str(row["changes"]),
            f"{row['median_hours']}",
            f"{row['verifier_rounds']}",
            str(row["escalations"]),
            compact(row["input_tokens"]),
            compact(row["output_tokens"]),
        ])
    widths = [max(len(line[index]) for line in lines) for index in range(len(headers))]
    for line in lines:
        print("  ".join(cell.ljust(width) for cell, width in zip(line, widths)).rstrip())
    if without_gait:
        print(t("report.without_gait", count=without_gait))


def run_report(repo: Path, limit: int = 100, as_json: bool = False) -> int:
    try:
        prs = merged_prs(repo, limit)
    except CommandError as error:
        print(t("finish.failed", command=" ".join(error.command[:3])), file=sys.stderr)
        print(error.output, file=sys.stderr)
        return 1
    tokens = tokens_by_branch(repo)
    changes = []
    for pr in prs:
        change = to_change(pr)
        if change:
            change.input_tokens, change.output_tokens = tokens.get(change.branch, (None, None))
            changes.append(change)
    if as_json:
        print(json.dumps([asdict(change) for change in changes], indent=2))
        return 0
    if not changes:
        print(t("report.empty"))
        return 0
    print_table(summarize(changes), len(prs) - len(changes))
    return 0
