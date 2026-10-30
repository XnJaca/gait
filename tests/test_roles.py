import pytest

from gait.roles import ROLES_DIR, TIERS, load_role, load_roles, parse_front_matter

CYCLE = ("orchestrator", "triage", "scout", "planner", "builder", "tester", "verifier", "reviewer", "deliver")


def test_every_cycle_role_exists():
    assert set(load_roles()) == set(CYCLE)


@pytest.mark.parametrize("path", sorted(ROLES_DIR.glob("*.md")), ids=lambda path: path.stem)
def test_role_is_well_formed(path):
    role = load_role(path)
    assert role.name == path.stem
    assert role.tier in TIERS
    assert role.inputs
    assert role.output_budget > 0
    assert role.description
    assert role.body.startswith("# ")


@pytest.mark.parametrize("path", sorted(ROLES_DIR.glob("*.md")), ids=lambda path: path.stem)
def test_role_stays_short(path):
    assert len(path.read_text(encoding="utf-8").splitlines()) <= 70


def test_only_the_planner_uses_the_strong_model():
    strong = [role.name for role in load_roles().values() if role.tier == "strong"]
    assert strong == ["planner"]


def test_front_matter_lists_and_scalars():
    data, body = parse_front_matter("---\na: one\nb: [x, y]\n---\n\n# Body\n")
    assert data == {"a": "one", "b": ["x", "y"]}
    assert body == "# Body\n"


def test_missing_front_matter_is_rejected():
    with pytest.raises(ValueError):
        parse_front_matter("# No header\n")


def test_unknown_tier_is_rejected(tmp_path):
    path = tmp_path / "x.md"
    path.write_text("---\nrole: x\ntier: huge\ninputs: [a]\noutput_budget: 1\ndescription: d\n---\n# X\n")
    with pytest.raises(ValueError):
        load_role(path)
