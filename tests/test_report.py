import json

import pytest

from gait import report
from gait.cli import main
from gait.work import Plan


def pr(number, kind, size, rounds, escalations, branch, plan_at="2026-10-01T10:00:00Z", merged_at="2026-10-01T14:00:00Z"):
    body = f"# Goal\n\nType: {kind} · Size: {size}\n\n## Delivery notes\n\n- Verifier rounds: {rounds}\n- Escalations: {escalations}\n"
    return {
        "number": number,
        "body": body,
        "createdAt": "2026-10-01T12:00:00Z",
        "mergedAt": merged_at,
        "headRefName": branch,
        "commits": [{"messageHeadline": "chore: plan x", "committedDate": plan_at}, {"messageHeadline": "feat: x", "committedDate": "2026-10-01T11:00:00Z"}],
    }


PRS = [
    pr(1, "visual", "small", 0, 0, "feat/a"),
    pr(2, "rule", "large", 2, 1, "feat/b", merged_at="2026-10-02T10:00:00Z"),
    pr(3, "rule", "small", 1, 0, "feat/c"),
    {"number": 4, "body": "Plain PR", "createdAt": "2026-10-01T10:00:00Z", "mergedAt": "2026-10-01T11:00:00Z", "headRefName": "x", "commits": []},
]


@pytest.fixture
def repo(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    path = tmp_path / "shop"
    path.mkdir()
    monkeypatch.chdir(path)
    monkeypatch.setattr(report, "merged_prs", lambda repo, limit: PRS)
    return path


def test_change_from_pr_uses_the_plan_commit():
    change = report.to_change(PRS[1])
    assert (change.type, change.size, change.verifier_rounds, change.escalations) == ("rule", "large", 2, 1)
    assert change.hours == 24.0


def test_pr_without_plan_is_skipped():
    assert report.to_change(PRS[3]) is None


def test_summary_by_type(repo):
    changes = [report.to_change(item) for item in PRS[:3]]
    rows = {row["type"]: row for row in report.summarize(changes)}
    assert rows["rule"]["changes"] == 2
    assert rows["rule"]["escalations"] == 1
    assert rows["rule"]["verifier_rounds"] == 1.5
    assert rows["all"]["changes"] == 3
    assert "behavior" not in rows
    assert rows["all"]["output_tokens"] is None


def test_report_table(repo, capsys):
    assert main(["report"]) == 0
    out = capsys.readouterr().out
    assert "verifier rounds" in out
    assert "PRs without a Gait plan: 1" in out


def write_transcript(repo, entries, name="s.jsonl"):
    directory = report.transcripts_dir(repo)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).parent.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text("\n".join(json.dumps(entry) for entry in entries) + "\nnot json\n")


def assistant(branch, request, inp, out):
    usage = {"input_tokens": inp, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": out}
    return {"type": "assistant", "gitBranch": branch, "requestId": request, "message": {"usage": usage}}


def test_tokens_per_branch_dedupe_requests(repo):
    write_transcript(repo, [assistant("feat/b", "r1", 100, 10), assistant("feat/b", "r1", 100, 10), assistant("feat/b", "r2", 50, 5)])
    write_transcript(repo, [assistant("feat/b", "r3", 1, 1), {"type": "user", "gitBranch": "feat/b"}], name="sub/agent.jsonl")
    assert report.tokens_by_branch(repo) == {"feat/b": (151, 16)}


def test_report_json_includes_tokens(repo, capsys):
    write_transcript(repo, [assistant("feat/b", "r1", 2000, 300)])
    assert main(["report", "--json"]) == 0
    rows = {row["number"]: row for row in json.loads(capsys.readouterr().out)}
    assert rows[2]["input_tokens"] == 2000
    assert rows[1]["input_tokens"] is None


def test_plan_description_carries_the_metadata(tmp_path):
    plan = Plan(tmp_path / "x.md", "x", "rule", "large", "WCPMH-1", "Goal", "# Goal\n\n## Steps\n")
    assert plan.description().startswith("# Goal\n\nType: rule · Size: large · Ticket: WCPMH-1\n")
    assert report.META.search(plan.description())


def test_compact_numbers():
    assert report.compact(None) == "—"
    assert report.compact(950) == "950"
    assert report.compact(12_400) == "12k"
    assert report.compact(3_200_000) == "3.2M"


def test_merged_prs_fetches_commits_only_for_gait_prs(monkeypatch, tmp_path):
    calls = []

    def fake_run(command, cwd, check=True):
        calls.append(command)
        if command[2] == "list":
            return json.dumps([{**PRS[0], "commits": None}, PRS[3]])
        return json.dumps({"commits": PRS[0]["commits"]})

    monkeypatch.setattr(report, "run", fake_run)
    prs = report.merged_prs(tmp_path, 10)
    assert [call[2] for call in calls] == ["list", "view"]
    assert prs[0]["commits"] == PRS[0]["commits"]
    assert "commits" not in calls[0][-1]
