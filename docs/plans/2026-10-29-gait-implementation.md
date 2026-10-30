# Gait — plan de implementación

Fecha: 2026-10-29 · Diseño: [2026-10-29-gait-design.md](2026-10-29-gait-design.md)

Python ≥ 3.11 solo con la librería estándar (sin dependencias). Tests con `pytest`. El CLI nunca llama a un modelo.

## Estructura objetivo

```
gait/
├── pyproject.toml
├── roles/                 un .md por rol: frontmatter (tier, entradas, presupuesto de salida) + prompt
├── rules/base.md          reglas base de todo repo
├── templates/             AGENTS.md, context/design.md, design-tokens.json, .gitignore
├── hooks/                 commit-msg, pre-push
├── ci/gait.yml            workflow de GitHub Actions
├── src/gait/
│   ├── cli.py             argparse + menú de inicio
│   ├── ui.py              estilos de terminal (de legacy-cli-styles.py)
│   ├── repo.py            git y gh
│   ├── work.py            .work/<slug>.md
│   ├── init.py · adopt.py · check.py · finish.py · report.py · doctor.py
│   ├── adapters/          claude_code.py · generic.py
│   └── trackers/          none.py · manual.py · github.py · jira_api.py
└── tests/
```

## Fase 0 — Esqueleto

1. `pyproject.toml` (`gait-flow`, comando `gait`), `src/gait/__init__.py`, `__main__.py`.
2. `ui.py` desde `docs/plans/legacy-cli-styles.py`; borrar el legacy.
3. `cli.py` con subcomandos vacíos y `gait --version`.
4. `tests/test_cli.py`: cada subcomando existe y `--help` responde.

**Listo cuando:** `uv run gait --help` lista todos los comandos y `pytest` pasa.

## Fase 1 — Roles y reglas (el método)

Es la fase que más importa: son los prompts que ejecutan los agentes.

1. `roles/<rol>.md` para triage, scout, planner, builder, tester, verifier, reviewer, deliver y `orchestrator` (el que conduce el ciclo y abre con el menú).
2. Frontmatter común:
   ```yaml
   role: verifier
   tier: cheap            # cheap | mid | strong
   inputs: [plan, commands]
   output_budget: 30      # líneas máximas de respuesta
   ```
3. Cada prompt dice qué lee, qué devuelve y cuándo escala. El reviewer incluye su checklist fija y las reglas de activación (datos, contrato).
4. `templates/work.md`: formato del plan (objetivo, tipo, tamaño, archivos, pasos, verificación, requisitos con origen si hay ticket).
5. `rules/base.md`: commits, código en inglés, sin firma de la herramienta, merge humano.
6. `tests/test_roles.py`: todo rol tiene frontmatter válido y `tier` conocido.

**Listo cuando:** un agente cualquiera, con solo leer `orchestrator.md`, puede conducir un cambio de punta a punta.

## Fase 2 — Adaptadores e instalación

1. `adapters/claude_code.py`: genera `~/.claude/agents/gait-<rol>.md` con `model` según el tier (cheap→haiku, mid→sonnet, strong→opus, configurable) y el comando `/gait` desde `orchestrator.md`.
2. `adapters/generic.py`: escribe un bloque entre marcadores `<!-- gait:start -->` / `<!-- gait:end -->` en `AGENTS.md` con el ciclo secuencial (sin subagentes; la verificación pesada va al CI).
3. `gait install [--agent claude-code|generic]`: detecta el agente si no se indica.
4. `gait doctor`: agente detectado, adaptador al día, hooks activos.
5. Tests con `HOME` temporal.

**Listo cuando:** `gait install` en una máquina limpia deja `/gait` disponible en Claude Code.

## Fase 3 — Ciclo en el repo

1. `gait init`: 3 preguntas (qué es, stack y comandos, ¿tiene UI?) y escribe `AGENTS.md`, más `docs/context/design.md` y `design-tokens.json` si hay UI. Con flags para que el agente lo corra sin entrevista.
2. `gait start <slug>`: rama `<tipo>/<slug>` y `.work/<slug>.md` desde la plantilla.
3. `gait continue`: imprime el plan de la rama actual y su último paso hecho.
4. `gait check`: presupuestos (AGENTS.md < 100, fichas < 60), rutas mencionadas existen, `.work/` ausente en `main`. Código de salida ≠ 0 si falla.
5. `gait finish`: corre `check`, borra `.work/`, abre el PR con `gh` usando el plan como descripción. Nunca mergea.
6. Tests sobre repos git temporales.

**Listo cuando:** en un repo de prueba, `init → start → check → finish` deja un PR abierto sin `.work/`.

## Fase 4 — Validaciones

1. `hooks/commit-msg`: Conventional Commits y rechazo de firmas de herramientas.
2. `hooks/pre-push`: bloquea push a `main`.
3. `ci/gait.yml`: comandos del repo (desde `AGENTS.md`), `gait check` y, si se activa, el reviewer asíncrono que comenta el PR.
4. `gait init` y `gait adopt` los instalan y activan `core.hooksPath`.

**Listo cuando:** un commit con `Co-Authored-By: Claude` se rechaza y el CI falla con un `.work/` en `main`.

## Fase 5 — Tracker

1. Interfaz `Tracker`: `my_tickets()`, `read(key)`, `comment(key, text)`.
2. `none` (por defecto), `manual` (el dev pega el ticket) y `github` (vía `gh`).
3. `jira_api` con token en el keychain del sistema (vía `security` en macOS y `secret-tool` en Linux, sin dependencias).
4. `jira-via-agent` no es código: es una instrucción en `orchestrator.md` para pedírselo al agente del tracker.
5. Filtro de personas: solo llave, título, criterios y enlace llegan a `.work/`.

## Fase 6 — Adopt

1. Inventario: README, docs, stack, scripts, tests, CI.
2. El agente (no el CLI) condensa specs, ADRs y decisiones vigentes en `AGENTS.md` y `docs/context/`, respetando los presupuestos.
3. Propone qué borrar de la estructura vieja; el humano aprueba.
4. Todo en una rama `chore/adopt-gait` y un solo PR.

## Fase 7 — Report

1. Lee los PRs mergeados (`gh`) y sus descripciones (que traen el plan): tipo, tamaño, tiempo plan→merge.
2. Vueltas del verifier y escalamientos: el deliver los anota al final del plan.
3. Tokens por cambio si el adaptador los expone (Claude Code: transcripts locales).

## Fase 8 — Piloto

1. Adoptar Latinos Delicious (nuevo y chico) y hacer 3 cambios: uno visual, uno de comportamiento y uno de regla.
2. Comparar tiempo y tokens contra un cambio parecido hecho con el flujo anterior.
3. Ajustar roles y presupuestos; después, Snapline.

## Orden y entregas

Una rama y un PR por fase: `feat/phase-0-skeleton`, `feat/phase-1-roles`, etc. Las fases 0 a 4 dan un Gait usable; 5 a 7 lo hacen escalar a equipos; la 8 lo valida.
