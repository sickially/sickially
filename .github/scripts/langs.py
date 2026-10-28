import json
import os
import urllib.request
from xml.sax.saxutils import escape

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "sickially")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("OUT_FILE", "assets/langs.svg")
TOP = 6

BAR_COLORS = ["#b388ff", "#9575cd", "#7c4dff", "#6a3fd6", "#5e35b1", "#4a148c"]


def get(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "langs-card",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def collect():
    totals = {}
    page = 1
    while True:
        repos = get(
            f"https://api.github.com/users/{OWNER}/repos?per_page=100&type=owner&page={page}"
        )
        if not repos:
            break
        for repo in repos:
            if repo.get("fork"):
                continue
            for lang, size in get(repo["languages_url"]).items():
                totals[lang] = totals.get(lang, 0) + size
        if len(repos) < 100:
            break
        page += 1
    return totals


def render(totals):
    width = 420
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:TOP]
    total = sum(totals.values()) or 1
    row_h = 30
    height = 62 + max(len(top), 1) * row_h + 10

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Most used languages">',
        f'<rect width="{width}" height="{height}" rx="14" fill="#0d0b1a" stroke="#2a1f45"/>',
        '<text x="24" y="38" font-family="\'Noto Sans JP\', \'Segoe UI\', sans-serif" '
        'font-size="17" font-weight="600" fill="#b388ff">よく使う言語 · Most used languages</text>',
    ]

    if not top:
        parts.append(
            '<text x="24" y="86" font-family="\'Segoe UI\', sans-serif" font-size="13" '
            'fill="#d1c4e9">No public language data yet.</text>'
        )
    else:
        biggest = top[0][1]
        for i, (lang, size) in enumerate(top):
            y = 62 + i * row_h
            pct = size / total * 100
            bar_w = max(6, int(size / biggest * 190))
            color = BAR_COLORS[i % len(BAR_COLORS)]
            parts.append(
                f'<text x="24" y="{y + 14}" font-family="\'Segoe UI\', sans-serif" '
                f'font-size="13" fill="#d1c4e9">{escape(lang)}</text>'
            )
            parts.append(
                f'<rect x="136" y="{y + 4}" width="190" height="12" rx="6" fill="#1a1330"/>'
            )
            parts.append(
                f'<rect x="136" y="{y + 4}" width="{bar_w}" height="12" rx="6" fill="{color}"/>'
            )
            parts.append(
                f'<text x="{width - 24}" y="{y + 14}" text-anchor="end" '
                f'font-family="\'Segoe UI\', sans-serif" font-size="12" fill="#b39ddb">'
                f'{pct:.1f}%</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    svg = render(collect())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT}")
