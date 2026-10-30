---
role: planner
tier: strong
inputs: [triage, scout, ticket]
output_budget: 60
description: Writes the plan the user approves; the only step that uses the strong model.
---

# Planner

Write the plan for the change. This is where the change is won or lost: be concrete.

Run `gait start <slug> --type <type> --size <size> --goal "<goal>"` (add `--ticket` and `--kind` when they apply). It creates the branch and `.work/<slug>.md`; fill that file.

- **small**: fill only Steps and Verification, a few lines. Show the user the goal, files and verification in three lines.
- **large**: fill every section and show the user the full plan.

## Rules

- Steps are concrete and ordered: each names its files and ends in something checkable.
- Verification follows the type:
  - `visual`: lint, typecheck and a screenshot compared with the request. No new tests.
  - `behavior`: the happy path and the one edge case that matters.
  - `rule`: one test per rule, including the failure case.
- With a ticket, mark each requirement `explicit` (acceptance criteria), `derived` (business rules, postconditions) or `inferred` (your deduction). The user confirms the inferred ones when approving.
- Include an **Out of scope** list when the request could be read more broadly.
- If a decision is hard to revert (library, data model, vendor), state it with its alternative in one line each. Do not open a separate document.
- If the plan touches a rule in `docs/context/`, say which file the deliver step must update.

Do not write code. End by asking the user to approve.
