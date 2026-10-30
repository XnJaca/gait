---
slug: adopt-gait
type: rule
size: large
ticket:
---

# The repo works with Gait

## Inventory

{{inventory}}

## Requirements

- `AGENTS.md` says what the project is, its stack, its commands and its rules, in under 100 lines.
- `docs/context/` holds only rules the code does not make obvious, one file per area, under 60 lines each, describing the system as it is now.
- Nothing from the legacy docs is lost if it is still true and not obvious from the code.

## Out of scope

- Changing application code.
- Writing new tests.

## Steps

- [ ] Read each legacy entry from the inventory, one at a time. Keep only rules still true in the code; mark those you cannot verify as "Unverified".
- [ ] Rewrite `AGENTS.md`: what it is, stack, commands, project rules. Keep the Gait block if present. Under 100 lines.
- [ ] Write one `docs/context/<area>.md` per area with non-obvious rules. No history, no decision logs.
- [ ] With UI: condense the product and design docs into `docs/context/design.md`; keep `design-tokens.json` as the source of visual values.
- [ ] Show the user the list of legacy files and agent tooling (`.claude/commands`, `.claude/agents`, `.claude/hooks`) to delete. Delete only what they approve.
- [ ] Run `gait check` until it passes.

## Verification

- `gait check` passes.
- The user approved the deletion list.

## Context to update

- `AGENTS.md` and `docs/context/`

## Delivery notes

- Verifier rounds: 
- Escalations: 
- Left out: 
