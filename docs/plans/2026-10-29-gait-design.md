# Gait — diseño

Fecha: 2026-10-29 · Estado: validado en sesión de diseño

## Qué es

Gait es un estilo de trabajo con agentes de IA para cualquier proyecto y cualquier equipo, sin importar el agente (Claude Code, Code Puppy, Cursor, Codex). Lleva un cambio de la idea o el ticket al PR con el menor contexto posible y con decisiones humanas solo donde importan.

Reemplaza a la versión anterior de Gait, a `spec-kickoff` y al sistema `SPEC-NNNN` de Acdemic.

## Principios

- **La verdad es lo implementado.** Código y tests. No se guarda historia de decisiones: para eso está git.
- **Solo se documenta lo que el código no dice**, y se sobrescribe, no se acumula.
- **Contexto mínimo.** El agente principal recibe resúmenes, nunca el repo entero ni logs.
- **Modelo según la tarea.** El modelo fuerte solo planea; lo mecánico va a modelos baratos.
- **Proporcional.** Un botón no carga el proceso de una regla de negocio.
- **Agnóstico de agente.** El método vive en archivos y en un CLI; cada agente se conecta con un adaptador.
- **Se cumple con validaciones**, no con buena voluntad: git hooks y CI.

## Base

- Böckeler (martinfowler.com): casi todo SDD es *spec-first*; mantener specs vivos (*spec-anchored*) genera revisión pesada, documentos repetitivos y sobrecarga en cambios pequeños.
- El *drift* entre spec y código es el fallo más reportado (Spec Growth Engine, SpecMine, TrueFoundry).
- Un `AGENTS.md` corto reduce tiempo (~28 %) y tokens de salida (~16 %); los largos o generados empeoran el resultado (arXiv 2601.20404).
- Memoria en capas: *hot* corta siempre cargada, *cold* por área bajo demanda (Codified Context, arXiv 2602.20478).
- Patrones agénticos: ruteo, contexto aislado, planner-executor, paralelización, evaluador-optimizador.

## Lo que desaparece

Specs vivos, changes con deltas, EARS, escenarios con ID, ADRs, `DECISIONES.md`, boards, dashboard, vault de Obsidian, comandos y agentes copiados en cada repo, perfiles por capas y el hook `spec-gate`.

## Dónde vive cada cosa

El método vive en un solo lugar; los repos guardan solo lo propio.

```
gait/                      el repo de la herramienta, se instala una vez
├── roles/                 triage, scout, planner, builder, tester, verifier, reviewer, deliver
├── rules/                 reglas base (commits, código en inglés, sin firma de la herramienta)
├── adapters/
│   ├── claude-code/       genera subagentes con su modelo por rol
│   └── generic/           bloque para AGENTS.md (Code Puppy, Cursor, Codex)
├── hooks/                 git hooks y workflow de CI reutilizables
└── src/gait/              CLI en Python
```

```
<repo>/
├── AGENTS.md              hot: qué es, stack, comandos, reglas propias (< 100 líneas)
├── docs/context/          cold: una ficha por área con reglas no obvias (< 60 líneas c/u, opcional)
│   └── design.md          solo en proyectos con UI
├── design-tokens.json     solo en proyectos con UI; es la verdad visual
└── .work/<slug>.md        plan del cambio en curso; viaja en la rama, se borra al mergear
```

La sección *Comandos* de `AGENTS.md` dice cómo se verifica el repo (`test`, `lint`, `dev`, captura). El verifier la lee y no necesita saber el stack.

### Diseño

`design-tokens.json` es la verdad, porque es código y genera CSS y Dart. `docs/context/design.md` guarda solo lo que los tokens no dicen: personalidad, anti-referencias y reglas de UI (tablas CRUD, botones de diálogo, encabezados). Se carga solo en cambios visuales.

## Al abrir una sesión

```
¿Qué quieres hacer hoy?
1. Empezar un cambio
2. Continuar lo que dejé
3. Atender revisión de un PR
4. Sesión libre
```

Si el repo no usa Gait, la primera opción es adoptarlo. "Continuar" lee `.work/` de la rama: no depende de la memoria del agente.

## El ciclo de un cambio

| # | Rol | Patrón | Qué hace | Modelo | Devuelve |
|---|---|---|---|---|---|
| 1 | Triage | Ruteo | Tipo (visual, comportamiento, regla) y tamaño (chico, grande) | Barato | 1 línea |
| 2 | Scout | Contexto aislado | Archivos que toca y restricciones aplicables | Barato | ≤ 30 líneas |
| 3 | Planner | Planner-executor | `.work/<slug>.md`: objetivo, archivos, pasos, verificación | Fuerte | El plan |
| — | Humano | — | Aprueba el plan. Si es chico, son 3 líneas en el chat, sin archivo | — | — |
| 4 | Builder + Tester | Paralelización | Implementa; en paralelo, tests desde el plan sin ver el código | Medio | Diff y tests |
| 5 | Verifier | Evaluador-optimizador | Tests, lint, captura. Solo fallos; el builder corrige. Máx. 3 vueltas | Barato | Solo fallos |
| 6 | Reviewer | Evaluador | Ver "Revisión" | Medio | ≤ 10 hallazgos |
| 7 | Deliver | — | PR con el plan como descripción; actualiza `docs/context/` si tocó una regla; borra `.work/` | Medio | Link del PR |

El humano siempre mergea. Revisión del PR según el cambio: visual y chico, un vistazo a la captura; regla o datos, revisión completa.

## Tests

| Tipo de cambio | Verificación | Tests nuevos |
|---|---|---|
| Visual (estilo, botón, copy, layout) | Lint, typecheck, captura comparada con lo pedido | No |
| Comportamiento (flujo, formulario, validación) | Camino feliz y el borde que importa | Pocos |
| Regla de negocio o dato | Tests de la regla | Sí: son el spec que sobrevive |

El tester trabaja en segundo plano. La suite completa corre en el CI del PR, no en la sesión. En agentes sin subagentes, lo del verifier va al CI.

## Revisión

1. **Proporcional.** Lo visual no pasa por un revisor: captura y lint.
2. **Determinista primero.** Lint, typecheck y tests antes que cualquier modelo. El revisor solo mira lo que una herramienta no ve: el diff contra el plan, la lógica y la seguridad.
3. **Entrada congelada.** Recibe el diff y el plan, no explora el repo. Checklist fija, modelo medio, ≤ 10 hallazgos con severidad.
4. **En paralelo, solo si aplican.** Revisor de datos si el diff toca migraciones; de contrato si toca endpoints.
5. **Incremental.** Tras corregir, revisa solo lo nuevo.
6. **Asíncrono.** Puede correr en CI y dejar el resultado como comentario del PR.

## Escalamiento

El agente se detiene y pregunta, en una línea, cuando:

- el verifier falla 3 veces seguidas;
- el scout encuentra que el cambio contradice una regla de `AGENTS.md` o `docs/context/`;
- un cambio chico resulta grande: se replanifica, no se sigue.

## Validaciones

- **Git hooks:** formato de commits (Conventional Commits en inglés) y sin firma de la herramienta.
- **CI:** tests, lint y `gait check`.
- **`gait check`:** `AGENTS.md` < 100 líneas, fichas < 60, rutas mencionadas en los docs existen, `.work/` no llega a `main`.
- Push a `main` bloqueado; merge siempre humano.

## Tracker

Opcional. Sin tracker, el cambio parte de lo que describe el dev. Con tracker (Jira a través del agente de la empresa, Jira API con token en el keychain, GitHub Issues), el triage lee el ticket completo y el planner marca cada requisito como explícito, derivado o inferido; los inferidos los confirma el humano al aprobar el plan. Escritura en el tracker solo al entregar y con confirmación. Nombres, correos y comentarios del tracker no llegan al repo.

## CLI

| Comando | Qué hace |
|---|---|
| `gait init` | Entrevista de 3 preguntas y escribe `AGENTS.md` (y la base de diseño si hay UI) |
| `gait adopt` | Lo mismo en un repo existente; condensa specs y docs viejos en `docs/context/` en un solo PR |
| `gait start` / `gait continue` | Rama y `.work/<slug>.md` / retoma desde `.work/` |
| `gait check` | Presupuestos y validaciones |
| `gait finish` | PR, limpieza de `.work/`, ticket si hay |
| `gait report` | Cambios por tipo, plan→merge, vueltas del verifier, escalamientos y tokens por cambio si el adaptador los expone |
| `gait doctor` | Agente detectado, adaptador instalado, hooks activos |

El CLI hace lo determinista y nunca llama a un modelo; el agente hace lo que requiere criterio. Se mantienen el logo y los estilos de la versión anterior.

## Migración

- Repo `XnJaca/gait` nuevo y privado; la versión anterior se borró el 2026-10-29.
- `gait-demo` (sitio y logo) se actualiza a esta metodología después.
- Snapline, Unitward, GainGang, Latinos Delicious y Acdemic pasan con `gait adopt`, uno a la vez.

## Pendiente

- Licencia (open core o FSL). No publicar como open source sin decidirlo.
- Confirmar si Code Puppy puede abrir con el agente `gait` por defecto.
