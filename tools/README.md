# Tooling del repositorio — uso

Scripts de apoyo a la gestión del proyecto (no forman parte del modelo de visión).

**Requisitos:** [GitHub CLI](https://cli.github.com/) (`gh`) autenticado y Python 3.

> Ejecuta los comandos **desde la raíz del repo**.

## Flujo

```bash
# 1) JSON (fuente única para ambos scripts)
gh issue list -R Bootcamp-IA-P6/P11E4 --state all --limit 200 \
  --json number,title,state,labels,body,createdAt,updatedAt,url,assignees,milestone \
  > issues.json

# 2) Issues -> Markdown  (genera issues_md/index.md + issue-XXXX.md)
python tools/issues_to_md.py issues.json

# 3) MAPA_URLS.md  (URLs vivas de GitHub)
python tools/mapa_urls.py issues.json docs/MAPA_URLS.md
```

## Qué hace cada script

- **`tools/issues_to_md.py`** — convierte `issues.json` en un `.md` por issue más un
  `index.md`. Añade cabecera con sello de generación (UTC) y fuente, y limpia ficheros
  huérfanos en cada ejecución.
- **`tools/mapa_urls.py`** — genera `docs/MAPA_URLS.md` con los enlaces vivos del repo
  (repositorio, issues, PRs, Kanban, README, milestones) y la tabla de issues con su URL.

## Notas

- `issues.json` e `issues_md/` son **artefactos generados**: están en `.gitignore`
  (decisión: el MAPA enlaza a URLs vivas, no se versiona el volcado local).
- `docs/MAPA_URLS.md` **sí** se versiona; regéneralo cuando cambien las issues.
- `mapa_urls.py` tiene una constante `PROJECT_NUMBER = 69` (el nº del Kanban no viene en
  el JSON). Edítala arriba del script si cambia el Project.
