# Base rules

Apply in every repo that uses Gait. A repo's `AGENTS.md` can add rules, never relax these.

1. **Code in English**: identifiers, comments, test names, commits, PR titles and descriptions. Project docs follow the language the repo chooses.
2. **Conventional Commits**: `type(scope): summary`, imperative, lowercase summary.
3. **No tool attribution** in commits or PRs: no `Co-Authored-By` for agents, no "Generated with".
4. **Humans merge.** Agents never merge PRs and never push to `main`.
5. **Minimal comments**: only what the code cannot say.
6. **No secrets** in files, logs or prompts. Never read `.env` files or keys unless the user asks.
7. **Truth is what is implemented.** Do not keep decision logs or history in docs; git has it. `docs/context/` describes the system as it is now.
8. **Context budgets**: `AGENTS.md` under 100 lines, each `docs/context/*.md` under 60.
