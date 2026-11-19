"""Refresh the live parts of the profile README.

Runs daily in GitHub Actions (stdlib only). It:
  * rewrites assets/stats.svg — repos, stars, top languages, last push
  * rewrites the block between <!--RECENT:start--> and <!--RECENT:end--> in README.md
"""

import json
import os
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape

USER = os.environ.get("GH_USER", "yadavayush834")
TOKEN = os.environ.get("GITHUB_TOKEN")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {USER, "Larp", "Avarta1", "scikit-learn"}  # profile repo + forks/mirrors
LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5", "C++": "#f34b7d",
    "C": "#8b8b8b", "Rust": "#dea584", "HTML": "#e34c26", "CSS": "#663399", "QML": "#44a51c",
    "Shell": "#89e051", "Jupyter Notebook": "#DA5B0B", "PHP": "#4F5D95", "PowerShell": "#2b6cb0",
}


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
    stars = sum(r["stargazers_count"] for r in repos)
    langs = Counter(r["language"] for r in repos if r["language"])
    top = langs.most_common(6)
    total = sum(n for _, n in top) or 1
    last = repos[0] if repos else None

    # ---------- stats.svg ----------
    W = 860
    bar, x = [], 30
    for lang, n in top:
        w = (W - 60) * n / total
        bar.append(f'<rect x="{x:.1f}" y="118" width="{max(w - 3, 1):.1f}" height="10" rx="3" fill="{LANG_COLORS.get(lang, "#9ca3af")}"/>')
        x += w
    legend, lx = [], 30
    for lang, n in top:
        label = f"{lang} {round(100 * n / total)}%"
        legend.append(
            f'<circle cx="{lx + 5}" cy="152" r="5" fill="{LANG_COLORS.get(lang, "#9ca3af")}"/>'
            f'<text x="{lx + 15}" y="157" class="s">{escape(label)}</text>'
        )
        lx += 30 + len(label) * 7.6
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y")
    last_line = f'last push: <tspan class="b">{escape(last["name"])}</tspan> · {ago(last["pushed_at"])}' if last else ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 190" width="{W}" height="190" role="img" aria-label="GitHub stats for {USER}">
  <style>
    text {{ font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; fill: #9ca3af; }}
    .n {{ font-size: 30px; font-weight: 700; fill: #f8fafc; }}
    .l {{ font-size: 12px; letter-spacing: 1.5px; }}
    .s {{ font-size: 13px; }}
    .b {{ fill: #93c5fd; font-weight: 700; }}
    .live {{ fill: #ef4444; }}
  </style>
  <rect x="1" y="1" width="{W - 2}" height="188" rx="14" fill="#0b0f17" stroke="#1f2937" stroke-width="2"/>
  <text x="30" y="40" class="n">{len(repos)}</text><text x="30" y="62" class="l">REPOS</text>
  <text x="160" y="40" class="n">{stars}</text><text x="160" y="62" class="l">STARS</text>
  <text x="280" y="40" class="n">{len(langs)}</text><text x="280" y="62" class="l">LANGUAGES</text>
  <text x="{W - 30}" y="38" text-anchor="end" class="s"><tspan class="live">●</tspan> live · updated {stamp}</text>
  <text x="{W - 30}" y="62" text-anchor="end" class="s">{last_line}</text>
  <text x="30" y="104" class="l">WHAT I BUILD IN</text>
  {"".join(bar)}
  {"".join(legend)}
</svg>
'''
    with open(os.path.join(ROOT, "assets", "stats.svg"), "w") as f:
        f.write(svg)

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
