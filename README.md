<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/gait-on-dark.svg">
    <img src="docs/assets/gait-on-light.svg" alt="Gait" width="260">
  </picture>
</p>

<p align="center">Estilo de trabajo con agentes de IA, para cualquier proyecto y cualquier agente.</p>

Gait lleva un cambio de la idea o el ticket al PR con el menor contexto posible. Tú apruebas el plan y mergeas; lo demás lo conducen los agentes, cada uno con el modelo que su tarea necesita. Funciona con Claude Code, Code Puppy, Cursor y Codex.

![Un cambio con Gait](docs/diagrams/cycle.svg)

Diseño completo: [docs/plans/2026-10-29-gait-design.md](docs/plans/2026-10-29-gait-design.md).

## Instalar

```bash
uv tool install git+https://github.com/XnJaca/gait
gait install          # adaptador del agente detectado (Claude Code u otro)
gait doctor
```

En Claude Code, `gait install` crea un subagente por rol con su modelo (Haiku para lo mecánico, Sonnet para construir y revisar, Opus solo para planear) y el comando `/gait`. Los modelos se cambian con `--models cheap=haiku,mid=sonnet,strong=opus`.

## Empezar

```bash
gait init             # proyecto nuevo: 3 preguntas y AGENTS.md
gait adopt            # repo existente: rama chore/adopt-gait con la base y el plan de adopción
```

![Dónde vive cada cosa](docs/diagrams/install.svg)

Ambos instalan los git hooks (Conventional Commits, sin firma de herramientas, sin push a `main`), el workflow de CI y los permisos del proyecto para Claude Code.

## Trabajar

Abre el agente y usa `/gait`:

```
¿Qué quieres hacer hoy?
1. Empezar un cambio
2. Continuar lo que dejé
3. Atender revisión de un PR
4. Sesión libre
```

Cada decisión se elige de una lista, no se escribe. En un cambio grande ves un resumen del plan (objetivo, decisiones inferidas, lo difícil de revertir) y abres el archivo solo para ajustarlo.

El proceso pesa según el cambio: un botón no carga lo mismo que una regla de negocio.

![Lo que corre según el tipo de cambio](docs/diagrams/by-type.svg)

## Qué queda en cada repo

![Qué queda en cada repo](docs/diagrams/context.svg)

```
AGENTS.md            qué es, stack, comandos y reglas (< 100 líneas)
docs/README.md       índice para personas (< 60 líneas)
docs/context/        reglas no obvias por área (< 60 líneas cada una), se sobrescriben
docs/diagrams/       diagramas SVG que mantienen los agentes: overview.svg y flujos o áreas complejas
design-tokens.json   valores visuales, si hay interfaz
.work/<slug>.md      plan del cambio en curso; se borra al abrir el PR
.gait.toml           tracker, si hay
```

Sin specs vivos, ADRs ni historial de decisiones: la verdad es lo implementado y git guarda la historia.

`docs/` se lee mejor en Obsidian (*Open folder as vault* → `docs`), pero todo es markdown y SVG: también se ve en GitHub o en cualquier editor.

## Comandos

| Comando | Qué hace |
|---|---|
| `gait init` / `gait adopt` | Base de un proyecto nuevo / existente |
| `gait install` / `gait doctor` | Adaptador del agente / estado de la instalación |
| `gait start` / `gait continue` | Rama y plan de un cambio / dónde quedó |
| `gait check` | Presupuestos de contexto, rutas rotas, planes en `main` |
| `gait finish` | Quita el plan, hace push y abre el PR con el objetivo, un resumen y las notas de entrega; exige un título Conventional Commit de 72 caracteres o menos |
| `gait tracker` / `gait ticket` | Configura el tracker / lista, muestra y comenta tickets |
| `gait report` | Métricas por tipo de cambio: tiempo, vueltas, escalamientos y tokens (entrada, caché y salida) |

Los comandos los corre el agente. El CLI habla español o inglés según el idioma del sistema (`GAIT_LANG` lo fuerza).

## Tracker

Opcional. `gait tracker set github`, `gait tracker set jira --url https://jira.empresa.com --project KEY` (el token va al llavero con `gait tracker login`), `manual` o `jira-agent` (los tickets los da el agente de la empresa). Correos y menciones nunca llegan al repo.

## CI

`gait init` y `gait adopt` agregan `.github/workflows/gait.yml`. Mientras Gait sea privado, el repo necesita el secret `GAIT_TOKEN` con lectura sobre `XnJaca/gait`.

## Desarrollo

```bash
uv run pytest
```
