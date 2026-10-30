# Diagram rules

Diagrams live in `docs/diagrams/<name>.svg` and are embedded from the docs that explain them: `![Orders flow](../diagrams/orders-flow.svg)`. They describe the system as it is now and are overwritten, never versioned.

## When

- `docs/diagrams/overview.svg`: the system's parts and how they connect (apps, services, data, external systems). Every repo has one.
- One diagram per flow with several actors or branches, or per area with three or more related entities.
- Not for a single screen, a style change or anything a list says as well.

## How

- Hand-written SVG, no external fonts, images or scripts. `viewBox` set, no fixed `width`/`height`.
- A filled background `rect`, so the diagram reads on light and dark themes alike.
- At most 12 boxes. Text at least 12 px, system sans-serif. Labels in the docs' language.
- Boxes for parts or entities, arrows labeled with what moves or happens. One accent color for the main path; everything else neutral.
- Names match the code: tables, services, screens.
