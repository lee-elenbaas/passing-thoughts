#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import anthropic

AUTHOR = "Lee Elenbaas"
MODEL = "claude-sonnet-4-6"
RAW_EXTENSIONS = {".txt", ".md", ".markdown"}


def run(cmd: list[str]) -> str:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}", file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
    return result.stdout.strip()


def get_changed_raw_files() -> list[str]:
    output = run(["git", "-c", "core.quotePath=false", "diff", "--name-only", "--diff-filter=AM", "HEAD~1", "HEAD"])
    all_files = [f for f in output.split("\n") if f]
    raw_files = [
        f for f in all_files
        if Path(f).parent.name == "raw" and Path(f).suffix in RAW_EXTENSIONS
    ]
    print(f"Changed files: {all_files}")
    print(f"Raw files to process: {raw_files}")
    return raw_files


def convert_with_claude(content: str, is_markdown: bool) -> dict:
    if is_markdown:
        format_instruction = (
            "The input is already markdown-formatted. Preserve the existing formatting and structure exactly. "
            "Only reformat the body if it has obvious issues. Do not use <br> tags — use blank lines between lines instead."
        )
    else:
        format_instruction = (
            "The input is plain text. Format the body as clean markdown. "
            "For poems, separate every line with a blank line — do not use <br> tags."
        )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""You are helping convert raw text into a Jekyll blog post for a personal blog called "Passing Thoughts" by Lee Elenbaas. The blog contains poems, personal reflections, and tech thoughts. Posts can be in Hebrew or English.

{format_instruction}

Return a JSON object with these fields:
- "title": a suitable title for the post (use existing title if one is present in the content)
- "slug": URL-safe, lowercase, English-only, hyphenated (max 50 chars — transliterate Hebrew if needed)
- "category": one word, choose the best fit: "poem", "thought", "story", or "tech"
- "tags": array of 2-4 lowercase hyphenated tags
- "direction": "rtl" if the post body is primarily in Hebrew or another right-to-left language, otherwise "ltr"
- "body": the post body as markdown, WITHOUT any Jekyll frontmatter block

Return ONLY valid JSON. No markdown code fences, no explanation, no other text.

Input:
{content}""",
        }],
    )
    text = response.content[0].text.strip()
    text = re.sub(r"^```(?:json)?\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


def setup_git() -> None:
    run(["git", "config", "user.name", "github-actions[bot]"])
    run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])


def process_file(txt_file: str, base_branch: str, today: str) -> None:
    print(f"\nProcessing: {txt_file}")
    path = Path(txt_file)

    if not path.exists():
        print("  Skipping — file not found")
        return

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        print("  Skipping — empty file")
        return

    is_markdown = path.suffix in {".md", ".markdown"}
    print("  Calling Claude...")
    metadata = convert_with_claude(content, is_markdown)
    print(f"  Claude response: {json.dumps({k: v for k, v in metadata.items() if k != 'body'})}")

    slug = metadata["slug"]
    title = metadata["title"]
    category = metadata["category"]
    tags = metadata.get("tags", [])
    direction = metadata.get("direction", "ltr")
    body = metadata["body"]

    branch = f"post/{today}-{slug}"
    post_path = Path(f"_posts/{today}-{slug}.md")

    run(["git", "checkout", "-b", branch])

    tags_yaml = "[" + ", ".join(tags) + "]" if tags else "[]"
    post_content = f"""---
layout: post
title: "{title}"
category: {category}
tags: {tags_yaml}
author: {AUTHOR}
direction: {direction}
published: true
---
{body}
"""
    post_path.write_text(post_content, encoding="utf-8")
    path.unlink()

    run(["git", "add", str(post_path), txt_file])
    run(["git", "commit", "-m", f"Add post: {title}"])
    run(["git", "push", "origin", branch])

    pr_body = (
        f"Auto-converted from `{txt_file}` using Claude.\n\n"
        f"**Title:** {title}\n"
        f"**Category:** {category}\n"
        f"**Tags:** {', '.join(tags)}\n\n"
        f"Review `{post_path}` and merge when ready."
    )

    run([
        "gh", "pr", "create",
        "--title", f"New post: {title}",
        "--body", pr_body,
        "--base", base_branch,
        "--head", branch,
    ])

    print(f"  PR created for: {title}")
    run(["git", "checkout", base_branch])


def main() -> None:
    raw_files = get_changed_raw_files()
    if not raw_files:
        print("No new raw files found — nothing to do.")
        return

    base_branch = os.environ.get("BASE_BRANCH", "gh-pages")
    today = date.today().strftime("%Y-%m-%d")
    setup_git()

    failed = []
    for f in raw_files:
        try:
            process_file(f, base_branch, today)
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            failed.append(f)
            run(["git", "checkout", base_branch])

    if failed:
        print(f"\nFailed to process: {failed}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
