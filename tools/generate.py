#!/usr/bin/env python3
"""Regenerate the stats section of my profile README from the GitHub API.

Why I wrote this: the github-readme-stats cards are nice but they go down or
get rate limited and then my profile has a broken image on it. This pulls the
same numbers from the API directly and bakes them into a markdown file I can
paste or commit. Slower to update, never broken.

Usage:
    export GITHUB_TOKEN=your-token-here
    python tools/generate.py --user 22178384 --out stats/generated.md

The token is read from the environment. It is NOT hardcoded, please don't
paste one in. A classic PAT with `public_repo` (read-only, no scopes needed
for public data) is fine. Without a token you get 60 requests/hour from one
IP, which is usually enough for a single run but not for a loop.

Tested with requests 2.31. Python 3.9+.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

API = "https://api.github.com"
TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "widget.md"


def session() -> "requests.Session":
    if requests is None:
        print("error: requests is not installed. run: pip install requests",
              file=sys.stderr)
        raise SystemExit(2)
    s = requests.Session()
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    else:
        print("warning: GITHUB_TOKEN not set, using anonymous rate limits",
              file=sys.stderr)
    s.headers["Accept"] = "application/vnd.github+json"
    s.headers["X-GitHub-Api-Version"] = "2022-11-28"
    return s


def get(s: "requests.Session", path: str, **params):
    resp = s.get(f"{API}{path}", params=params, timeout=20)
    if resp.status_code == 404:
        raise SystemExit(f"error: {path} returned 404 (bad username?)")
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        reset = resp.headers.get("X-RateLimit-Reset")
        when = (datetime.fromtimestamp(int(reset), tz=timezone.utc)
                .strftime("%H:%M UTC") if reset else "later")
        raise SystemExit(f"error: rate limited. resets at {when}. set GITHUB_TOKEN")
    resp.raise_for_status()
    return resp.json()


def fetch_profile(s, user: str) -> dict:
    return get(s, f"/users/{user}")


def fetch_repos(s, user: str, include_forks: bool = False) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        chunk = get(s, f"/users/{user}/repos",
                    per_page=100, page=page, sort="updated")
        if not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    if not include_forks:
        repos = [r for r in repos if not r.get("fork")]
    return repos


def language_breakdown(repos: list[dict]) -> list[tuple[str, int]]:
    counts: Counter = Counter()
    for r in repos:
        lang = r.get("language")
        if lang:
            counts[lang] += 1
    return counts.most_common(8)


def render_table(rows: list[list[str]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def build_context(s, user: str) -> dict:
    profile = fetch_profile(s, user)
    repos = fetch_repos(s, user)

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    langs = language_breakdown(repos)

    top = sorted(repos, key=lambda r: (r.get("stargazers_count", 0),
                                       r.get("forks_count", 0)),
                 reverse=True)[:6]

    repo_rows = [
        [f"[{r['name']}]({r['html_url']})",
         (r.get("description") or "").replace("|", "\\|")[:70] or "—",
         r.get("language") or "—",
         str(r.get("stargazers_count", 0))]
        for r in top
    ]
    lang_rows = [[name, str(n)] for name, n in langs]

    return {
        "login": profile.get("login", user),
        "name": profile.get("name") or profile.get("login", user),
        "bio": profile.get("bio") or "",
        "location": profile.get("location") or "",
        "public_repos": str(profile.get("public_repos", len(repos))),
        "followers": str(profile.get("followers", 0)),
        "following": str(profile.get("following", 0)),
        "total_stars": str(total_stars),
        "repo_count": str(len(repos)),
        "top_repos_table": render_table(repo_rows,
                                        ["repo", "what it does", "lang", "★"]),
        "langs_table": render_table(lang_rows, ["language", "repos"]),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def render(template_text: str, context: dict) -> str:
    text = template_text
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", value)
    # Catch typos in the template instead of silently leaving {{braces}} in.
    leftover = [tok for tok in text.split("{{")[1:] if "}}" in tok]
    if leftover:
        names = sorted({t.split("}}")[0] for t in leftover})
        print(f"warning: unresolved placeholders: {', '.join(names)}",
              file=sys.stderr)
    return text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Render a stats README section.")
    p.add_argument("--user", default="22178384", help="GitHub username")
    p.add_argument("--out", type=Path, default=None,
                   help="write here (default: stdout)")
    p.add_argument("--template", type=Path, default=TEMPLATE)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.template.exists():
        print(f"error: template not found: {args.template}", file=sys.stderr)
        return 2
    s = session()
    ctx = build_context(s, args.user)
    text = render(args.template.read_text(encoding="utf-8"), ctx)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
