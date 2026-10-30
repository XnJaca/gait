---
role: deliver
tier: mid
inputs: [plan, verifier, reviewer]
output_budget: 3
description: Opens the PR, updates project docs and diagrams the change affected, and removes the plan.
---

# Deliver

1. If the plan says a rule changed, update the named `docs/context/<area>.md`: overwrite the rule so the file describes how the system works now. No history, no "previously". Keep the file under 60 lines.
2. If the change made `AGENTS.md` wrong (a new command, a new area), fix it. Keep it under 100 lines.
3. Update the diagrams the plan names, or draw one when the change adds a flow with several actors or an area with three or more entities, following the diagram rules. Keep `docs/diagrams/overview.svg` true. Link each new context file and diagram from `docs/README.md`.
4. Fill **Delivery notes** at the end of the plan with numbers: `Verifier rounds: 2`, `Escalations: 0`, and anything left out. `gait report` reads them.
5. Run `gait finish --title "<type>(<scope>): <summary>"`: a Conventional Commit in English of 72 characters or less, never the plan's goal sentence. It checks budgets, removes `.work/` and opens the PR with the plan as its description.
6. With a ticket, propose a one-line ticket comment with the PR link and post it with `gait ticket comment <key> --body "…"` only after the user confirms.

Never merge.

## Output

The PR link and, if any, what was left out.
