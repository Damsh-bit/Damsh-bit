"""Actualiza la cantidad de commits de cada proyecto destacado del README.

Cada número vive entre marcadores invisibles: <!--c:REPO-->140<!--/c-->
El script consulta la API de GitHub y reemplaza solo esos números.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

OWNER = os.environ.get("GITHUB_OWNER", "Damsh-bit")
TOKEN = os.environ.get("GITHUB_TOKEN")
README = Path(__file__).resolve().parent.parent / "README.md"
MARKER = re.compile(r"<!--c:([\w.-]+)-->\d+<!--/c-->")


def commit_count(repo: str) -> int:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{repo}/commits?per_page=1",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"},
    )
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as res:
        # Con per_page=1, el número de la última página es el total de commits.
        last = re.search(r'[?&]page=(\d+)>; rel="last"', res.headers.get("Link", ""))
        return int(last.group(1)) if last else len(json.load(res))


def main() -> int:
    text = README.read_text(encoding="utf-8")
    counts = {}
    for repo in dict.fromkeys(MARKER.findall(text)):
        try:
            counts[repo] = commit_count(repo)
        except Exception as e:  # si un repo falla, se deja el número anterior
            print(f"{repo}: no se pudo consultar ({e})", file=sys.stderr)
    for repo, n in counts.items():
        print(f"{repo}: {n}")

    def replace(m: re.Match) -> str:
        repo = m.group(1)
        return f"<!--c:{repo}-->{counts[repo]}<!--/c-->" if repo in counts else m.group(0)

    updated = MARKER.sub(replace, text)
    if updated != text:
        README.write_text(updated, encoding="utf-8", newline="\n")
        print("README actualizado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
