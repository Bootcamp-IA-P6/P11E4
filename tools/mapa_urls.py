#!/usr/bin/env python3
"""
mapa_urls.py
Genera MAPA_URLS.md a partir de issues.json (salida de `gh issue list --json ...`).
Enlaza SOLO a URLs vivas de GitHub (Opcion 1): repo, issues, PRs, Kanban (Project),
README, milestones, y la lista de issues con su URL.

El owner/repo se deriva de las urls de issues.json. El numero del Project es la unica
constante manual (no viene en issues.json).

Uso:
  python mapa_urls.py issues.json > MAPA_URLS.md
  python mapa_urls.py issues.json MAPA_URLS.md
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Unica constante manual: numero del Project (Kanban) en la organizacion ---
PROJECT_NUMBER = 69  # https://github.com/orgs/<owner>/projects/<N>


def repo_owner_name(issues):
    for it in issues:
        url = it.get("url", "")
        parts = url.split("/")
        if "github.com" in url and len(parts) >= 5:
            return parts[3], parts[4]
    sys.exit("No pude derivar owner/repo de issues.json (urls vacias).")


def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python mapa_urls.py <issues.json> [salida.md]")

    src = Path(sys.argv[1])
    issues = json.loads(src.read_text(encoding="utf-8"))
    if not issues:
        sys.exit("issues.json esta vacio.")
    issues.sort(key=lambda it: it["number"])

    owner, repo = repo_owner_name(issues)
    base = f"https://github.com/{owner}/{repo}"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# \U0001F5FA\uFE0F Mapa de URLs \u2014 {owner}/{repo}",
        "",
        f"Generado: {ts} (UTC) \u00b7 fuente: {src.name}",
        "",
        "## Enlaces principales",
        "",
        f"- **Repositorio:** {base}",
        f"- **Issues:** {base}/issues",
        f"- **Pull requests:** {base}/pulls",
        f"- **Kanban (Project #{PROJECT_NUMBER}):** "
        f"https://github.com/orgs/{owner}/projects/{PROJECT_NUMBER}",
        f"- **README:** {base}#readme",
        f"- **Milestones:** {base}/milestones",
        "",
        f"## Issues ({len(issues)})",
        "",
        "| # | Titulo | Estado | URL |",
        "|---|--------|--------|-----|",
    ]
    for it in issues:
        title = it["title"].replace("|", "\\|")
        lines.append(
            f'| {it["number"]} | {title} | {it["state"]} | {it.get("url", "")} |'
        )
    lines += [
        "",
        "## Demo / App desplegada",
        "",
        "- _(pendiente \u2014 nivel experto)_",
        "",
    ]

    out = "\n".join(lines) + "\n"
    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(out, encoding="utf-8")
        print(f"OK: MAPA escrito en {sys.argv[2]}")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
