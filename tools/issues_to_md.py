#!/usr/bin/env python3
"""
issues_to_md.py
Convierte issues.json (salida de `gh issue list --json ...`) en:
  - un archivo Markdown por issue:  issues_md/issue-XXXX.md
  - un indice:                      issues_md/index.md

Prerrequisito (genera el JSON una sola vez):
  gh issue list -R Bootcamp-IA-P6/P11E4 --state all --limit 200 \
    --json number,title,state,labels,body,createdAt,updatedAt,url,assignees,milestone \
    > issues.json

Uso:
  python issues_to_md.py issues.json
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def repo_slug(issues):
    """Deriva 'owner/repo' a partir de la url de la primera issue."""
    for it in issues:
        url = it.get("url", "")
        parts = url.split("/")
        if "github.com" in url and len(parts) >= 5:
            return f"{parts[3]}/{parts[4]}"
    return "(desconocido)"


def names(labels):
    return [l["name"] for l in (labels or [])]


def logins(assignees):
    return [a["login"] for a in (assignees or [])]


def milestone_title(ms):
    return ms["title"] if ms else ""


def yaml_str(value):
    return '"' + str(value).replace('"', "'") + '"'


def yaml_list(items):
    return "[" + ", ".join(yaml_str(x) for x in items) + "]"


def render_issue(it):
    lbls = names(it.get("labels"))
    asgn = logins(it.get("assignees"))
    ms = milestone_title(it.get("milestone"))
    body = (it.get("body") or "").strip() or "_(sin descripcion)_"

    front = [
        "---",
        f'number: {it["number"]}',
        f'title: {yaml_str(it["title"])}',
        f'state: {yaml_str(it["state"])}',
        f"labels: {yaml_list(lbls)}",
        f"assignees: {yaml_list(asgn)}",
        f"milestone: {yaml_str(ms)}",
        f'created: {yaml_str(it.get("createdAt", ""))}',
        f'updated: {yaml_str(it.get("updatedAt", ""))}',
        f'url: {yaml_str(it.get("url", ""))}',
        "---",
    ]
    md = [
        f'# #{it["number"]} \u2014 {it["title"]}',
        "",
        f'- **Estado:** {it["state"]}',
        f'- **Labels:** {", ".join(lbls) or "\u2014"}',
        f'- **Asignados:** {", ".join("@" + a for a in asgn) or "\u2014"}',
        f'- **Milestone:** {ms or "\u2014"}',
        f'- **Creado:** {it.get("createdAt", "")}',
        f'- **Actualizado:** {it.get("updatedAt", "")}',
        f'- **URL:** {it.get("url", "")}',
        "",
        body,
        "",
    ]
    return "\n".join(front) + "\n\n" + "\n".join(md)


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python issues_to_md.py <issues.json>")

    src = Path(sys.argv[1])
    issues = json.loads(src.read_text(encoding="utf-8"))
    issues.sort(key=lambda it: it["number"])

    out = Path("issues_md")
    out.mkdir(exist_ok=True)

    # Mejora 3: limpiar ficheros generados previos (elimina huerfanos)
    for f in list(out.glob("issue-*.md")) + [out / "index.md"]:
        if f.exists():
            f.unlink()

    # Mejora 1: cabecera con sello de generacion, fuente y repo derivado
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = repo_slug(issues)
    index = [
        f"# Indice de issues \u2014 {slug}",
        "",
        f"Generado: {ts} (UTC) \u00b7 fuente: {src.name}",
        "",
        f"Total: {len(issues)} issues",
        "",
    ]
    for it in issues:
        fname = f"issue-{it['number']:04d}.md"
        (out / fname).write_text(render_issue(it), encoding="utf-8")
        lbls = ", ".join(names(it.get("labels"))) or "\u2014"
        index.append(
            f"- [#{it['number']} \u2014 {it['title']}]({fname}) "
            f"\u00b7 `{it['state']}` \u00b7 {lbls}"
        )
    (out / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"OK: {len(issues)} issues -> {out}/ (index.md + issue-XXXX.md)")


if __name__ == "__main__":
    main()
