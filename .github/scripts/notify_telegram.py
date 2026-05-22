#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

SITE_URL = "https://passing-thoughts.lee-elenbaas.github.io"
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def get_new_posts() -> list[str]:
    output = run([
        "git", "diff", "--name-only", "--diff-filter=A",
        "HEAD~1", "HEAD", "--", "_posts/*.md", "_posts/*.markdown",
    ])
    return [f for f in output.split("\n") if f]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    end = content.index("---", 3)
    meta = {}
    for line in content[3:end].strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"')
    return meta, content[end + 3:].strip()


def get_excerpt(body: str, max_chars: int = 280) -> str:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not paragraphs:
        return ""
    excerpt = paragraphs[0]
    excerpt = re.sub(r"[*_`#]", "", excerpt)
    excerpt = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", excerpt)
    excerpt = re.sub(r"<[^>]+>", "", excerpt)
    excerpt = " ".join(excerpt.split())
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars].rsplit(" ", 1)[0] + "…"
    return excerpt


def build_url(filename: str) -> str:
    stem = Path(filename).stem
    parts = stem.split("-", 3)
    if len(parts) < 4:
        return SITE_URL
    year, month, day, slug = parts
    return f"{SITE_URL}/{year}/{month}/{day}/{slug}/"


def send_message(title: str, url: str, excerpt: str) -> None:
    text = f"<b>{title}</b>"
    if excerpt:
        text += f"\n\n{excerpt}"
    text += f'\n\n<a href="{url}">Read more</a>'

    payload = json.dumps({
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }).encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    if not result.get("ok"):
        print(f"Telegram error: {result}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    new_posts = get_new_posts()
    if not new_posts:
        print("No new posts found")
        return

    for post_file in new_posts:
        print(f"Processing: {post_file}")
        path = Path(post_file)
        if not path.exists():
            print(f"  Skipping — file not found")
            continue

        content = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)

        title = meta.get("title", Path(post_file).stem.replace("-", " ").title())
        url = build_url(post_file)
        excerpt = get_excerpt(body)

        send_message(title, url, excerpt)
        print(f"  Sent: {title}")


if __name__ == "__main__":
    main()
