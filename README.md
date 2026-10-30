# Gait

Estilo de trabajo con agentes de IA para cualquier proyecto y cualquier agente (Claude Code, Code Puppy, Cursor, Codex). Lleva un cambio de la idea o el ticket al PR con el menor contexto posible: el humano aprueba el plan y mergea; lo demás lo conducen los agentes.

Diseño: [docs/plans/2026-10-29-gait-design.md](docs/plans/2026-10-29-gait-design.md).

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

| Paso | Rol | Modelo |
|---|---|---|
| Clasifica el cambio | triage | barato |
| Encuentra archivos y reglas | scout | barato |
| Escribe el plan | planner | fuerte |
| **Apruebas el plan** | tú | — |
| Implementa y escribe tests en paralelo | builder + tester | medio |
| Corre checks, devuelve solo fallos | verifier | barato |
| Revisa diff contra plan | reviewer | medio |
| Abre el PR | deliver | medio |
| **Mergeas** | tú | — |

El agente solo te interrumpe si el verifier falla 3 veces, si el cambio choca con una regla del proyecto o si un cambio chico resulta grande.

Tests según el tipo de cambio: ninguno para lo visual, pocos para comportamiento, completos para reglas de negocio.

## Qué queda en cada repo

```
AGENTS.md            qué es, stack, comandos y reglas (< 100 líneas)
docs/context/        reglas no obvias por área (< 60 líneas cada una), se sobrescriben
design-tokens.json   valores visuales, si hay interfaz
.work/<slug>.md      plan del cambio en curso; se borra al abrir el PR
.gait.toml           tracker, si hay
```

Sin specs vivos, ADRs ni historial de decisiones: la verdad es lo implementado y git guarda la historia.

## Comandos

| Comando | Qué hace |
|---|---|
| `gait init` / `gait adopt` | Base de un proyecto nuevo / existente |
| `gait install` / `gait doctor` | Adaptador del agente / estado de la instalación |
| `gait start` / `gait continue` | Rama y plan de un cambio / dónde quedó |
| `gait check` | Presupuestos de contexto, rutas rotas, planes en `main` |
| `gait finish` | Quita el plan, hace push y abre el PR con el plan como descripción |
| `gait tracker` / `gait ticket` | Configura el tracker / lista, muestra y comenta tickets |
| `gait report` | Métricas por tipo de cambio: tiempo, vueltas, escalamientos, tokens |

Los comandos los corre el agente. El CLI habla español o inglés según el idioma del sistema (`GAIT_LANG` lo fuerza).

## Tracker

Opcional. `gait tracker set github`, `gait tracker set jira --url https://jira.empresa.com --project KEY` (el token va al llavero con `gait tracker login`), `manual` o `jira-agent` (los tickets los da el agente de la empresa). Correos y menciones nunca llegan al repo.

## CI

`gait init` y `gait adopt` agregan `.github/workflows/gait.yml`. Mientras Gait sea privado, el repo necesita el secret `GAIT_TOKEN` con lectura sobre `XnJaca/gait`.

## Desarrollo

```bash
uv run pytest
```
