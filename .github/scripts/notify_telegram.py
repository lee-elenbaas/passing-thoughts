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
POST_EXTENSIONS = {".md", ".markdown"}


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def get_posts(diff_filter: str) -> list[str]:
    output = run(["git", "diff", "--name-only", f"--diff-filter={diff_filter}", "HEAD~1", "HEAD"])
    return [
        f for f in output.split("\n")
        if f and Path(f).parent.name == "_posts" and Path(f).suffix in POST_EXTENSIONS
    ]


def get_recent_posts(hours: int = 48) -> list[str]:
    output = run([
        "git", "-c", "core.quotePath=false",
        "log", "--name-only", "--format=", "--diff-filter=AM", "--no-merges",
        f"--since={hours} hours ago", "--", "_posts/",
    ])
    seen = set()
    result = []
    for f in output.split("\n"):
        if f and f not in seen and Path(f).parent.name == "_posts" and Path(f).suffix in POST_EXTENSIONS:
            seen.add(f)
            result.append(f)
    return result


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


def insert_frontmatter_field(file_path: str, key: str, value) -> None:
    content = Path(file_path).read_text(encoding="utf-8")
    end = content.index("---", 3)
    updated = content[:end] + f"{key}: {value}\n" + content[end:]
    Path(file_path).write_text(updated, encoding="utf-8")


def clean_markdown(text: str) -> str:
    text = re.sub(r"[*_`#]", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def get_body_text(body: str, max_chars: int = 1500) -> tuple[str, bool]:
    """Returns (cleaned_text, truncated). Preserves paragraph breaks."""
    cleaned = clean_markdown(body)
    if len(cleaned) <= max_chars:
        return cleaned, False
    # Truncate at the last paragraph break before max_chars
    cut = cleaned[:max_chars]
    last_break = cut.rfind("\n\n")
    if last_break > max_chars // 2:
        cut = cut[:last_break]
    else:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip() + "…", True


def build_url(filename: str) -> str:
    stem = Path(filename).stem
    parts = stem.split("-", 3)
    if len(parts) < 4:
        return SITE_URL
    year, month, day, slug = parts
    return f"{SITE_URL}/{year}/{month}/{day}/{slug}/"


def build_message(title: str, url: str, body: str, truncated: bool) -> dict:
    text = f"<b>{title}</b>"
    if body:
        text += f"\n\n{body}"
    link_label = "Continue reading ➜" if truncated else "Read on blog ➜"
    return {
        "text": text,
        "reply_markup": {"inline_keyboard": [[{"text": link_label, "url": url}]]},
    }


def telegram(method: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")
    return result


def setup_git() -> None:
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)


def commit_message_id(post_file: str, message_id: int) -> None:
    subprocess.run(["git", "add", post_file], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"Store Telegram message ID [skip ci]"],
        check=True,
    )
    subprocess.run(["git", "push"], check=True)


def handle_new_post(post_file: str) -> None:
    print(f"New post: {post_file}")
    path = Path(post_file)
    if not path.exists():
        print("  File not found, skipping")
        return

    content = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    title = meta.get("title", path.stem.replace("-", " ").title())
    url = build_url(post_file)
    body_text, truncated = get_body_text(body)
    msg = build_message(title, url, body_text, truncated)

    result = telegram("sendMessage", {
        "chat_id": CHANNEL_ID,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        **msg,
    })

    message_id = result["result"]["message_id"]
    insert_frontmatter_field(post_file, "telegram_message_id", message_id)
    commit_message_id(post_file, message_id)
    print(f"  Sent — message ID {message_id} stored in frontmatter")


def handle_modified_post(post_file: str) -> None:
    print(f"Modified post: {post_file}")
    path = Path(post_file)
    if not path.exists():
        print("  File not found, skipping")
        return

    content = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    message_id = meta.get("telegram_message_id")

    if not message_id:
        print("  No telegram_message_id in frontmatter, skipping edit")
        return

    title = meta.get("title", path.stem.replace("-", " ").title())
    url = build_url(post_file)
    body_text, truncated = get_body_text(body)
    msg = build_message(title, url, body_text, truncated)

    telegram("editMessageText", {
        "chat_id": CHANNEL_ID,
        "message_id": int(message_id),
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        **msg,
    })

    print(f"  Edited message {message_id}")


def main() -> None:
    manual = os.environ.get("EVENT_NAME") == "workflow_dispatch"
    failed = []

    if manual:
        print("Manual trigger — processing posts from the last 48 hours")
        posts = get_recent_posts(48)
        if not posts:
            print("No posts found in the last 48 hours")
            return
        setup_git()
        for post_file in posts:
            try:
                content = Path(post_file).read_text(encoding="utf-8")
                meta, _ = parse_frontmatter(content)
                if meta.get("telegram_message_id"):
                    handle_modified_post(post_file)
                else:
                    handle_new_post(post_file)
            except Exception as e:
                print(f"  FAILED ({post_file}): {e}", file=sys.stderr)
                failed.append(post_file)
    else:
        new_posts = get_posts("A")
        modified_posts = get_posts("M")
        if not new_posts and not modified_posts:
            print("No new or modified posts found")
            return
        setup_git()
        for post_file in new_posts:
            try:
                handle_new_post(post_file)
            except Exception as e:
                print(f"  FAILED: {e}", file=sys.stderr)
                failed.append(post_file)
        for post_file in modified_posts:
            try:
                handle_modified_post(post_file)
            except Exception as e:
                print(f"  FAILED: {e}", file=sys.stderr)
                failed.append(post_file)

    if failed:
        print(f"\nFailed: {failed}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
