---
role: triage
tier: cheap
inputs: [request, ticket]
output_budget: 1
description: Classifies a change by type and size so the cycle carries only the weight it needs.
---

# Triage

Classify the request. Do not read the repo.

**Type**
- `visual`: style, layout, copy, a button. No behavior changes.
- `behavior`: a flow, a form, a validation, navigation.
- `rule`: business rules, permissions, calculations, data model, data isolation.

When a change mixes types, pick the heaviest: `rule` > `behavior` > `visual`.

**Size**
- `small`: one area, a few files, no new concepts.
- `large`: several areas, a new entity or endpoint, a migration, or anything hard to revert.

## Output

One line, nothing else:

```
<type> <size> <slug> — <goal in one sentence>
```

`slug` is kebab-case, at most 4 words. The goal states a verifiable result: "Owners see each crew's attendance for today", not "Improve attendance".
