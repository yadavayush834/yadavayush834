"""Refresh the live parts of the profile README.

Runs daily in GitHub Actions (stdlib only). It:
  * rewrites the block between <!--RECENT:start--> and <!--RECENT:end--> in README.md
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from html import escape

USER = os.environ.get("GH_USER", "yadavayush834")
TOKEN = os.environ.get("GITHUB_TOKEN")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {USER, "Larp", "Avarta1", "scikit-learn"}  # profile repo + forks/mirrors


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ago(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - dt).days
    return "today" if days == 0 else "yesterday" if days == 1 else f"{days} days ago"


def main():
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&sort=pushed") if not r["fork"] and r["name"] not in SKIP]
    # ---------- README recent block ----------
    rows = []
    for r in repos[:5]:
        desc = (r["description"] or "").strip()
        desc = f" — {desc}" if desc else ""
        rows.append(f'- **[{r["name"]}]({r["html_url"]})**{escape(desc, quote=False)} <sub>· {ago(r["pushed_at"])}</sub>')
    block = "<!--RECENT:start-->\n" + "\n".join(rows) + "\n<!--RECENT:end-->"
    path = os.path.join(ROOT, "README.md")
    readme = open(path).read()
    readme = re.sub(r"<!--RECENT:start-->.*?<!--RECENT:end-->", lambda _: block, readme, flags=re.S)
    open(path, "w").write(readme)


if __name__ == "__main__":
    main()
