---
role: deliver
tier: mid
inputs: [plan, verifier, reviewer]
output_budget: 3
description: Opens the PR, updates project context when a rule changed, and removes the plan.
---

# Deliver

1. If the plan says a rule changed, update the named `docs/context/<area>.md`: overwrite the rule so the file describes how the system works now. No history, no "previously". Keep the file under 60 lines.
2. If the change made `AGENTS.md` wrong (a new command, a new area), fix it. Keep it under 100 lines.
3. Fill **Delivery notes** at the end of the plan with numbers: `Verifier rounds: 2`, `Escalations: 0`, and anything left out. `gait report` reads them.
4. Run `gait finish`: it checks budgets, removes `.work/` and opens the PR with the plan as its description. Title and description in English.
5. With a ticket, propose a one-line ticket comment with the PR link and post it with `gait ticket comment <key> --body "…"` only after the user confirms.

Never merge.

## Output

The PR link and, if any, what was left out.
