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


def get_all_raw_files() -> list[str]:
    result = [
        str(p) for p in Path("raw").iterdir()
        if p.is_file() and p.suffix in RAW_EXTENSIONS
        and not p.name.startswith(".")
    ]
    print(f"  All raw files: {result}")
    return result


def get_raw_files(diff_filter: str) -> list[str]:
    output = run([
        "git", "-c", "core.quotePath=false",
        "diff", "--name-only", f"--diff-filter={diff_filter}", "HEAD~1", "HEAD",
    ])
    all_files = [f for f in output.split("\n") if f]
    result = [
        f for f in all_files
        if Path(f).parent.name == "raw" and Path(f).suffix in RAW_EXTENSIONS
    ]
    print(f"  All changed: {all_files}")
    print(f"  Raw files ({diff_filter}): {result}")
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


def add_frontmatter_field(content: str, key: str, value: str) -> str:
    if content.startswith("---"):
        end = content.index("---", 3)
        return content[:end] + f"{key}: {value}\n" + content[end:]
    return f"---\n{key}: {value}\n---\n{content}"


def post_path_from_branch(branch: str) -> Path:
    return Path(f"_posts/{branch.removeprefix('post/')}.md")


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
- "category": choose the best fit from these existing categories: "poem", "seeds", "half-baked", "blog", "review", "books"
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


def build_post_content(metadata: dict) -> str:
    tags_yaml = "[" + ", ".join(metadata.get("tags", [])) + "]"
    return (
        f"---\n"
        f"layout: post\n"
        f"title: \"{metadata['title']}\"\n"
        f"category: {metadata['category']}\n"
        f"tags: {tags_yaml}\n"
        f"author: {AUTHOR}\n"
        f"direction: {metadata.get('direction', 'ltr')}\n"
        f"published: true\n"
        f"---\n"
        f"{metadata['body']}\n"
    )


def setup_git() -> None:
    run(["git", "config", "user.name", "github-actions[bot]"])
    run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])


def branch_exists_on_remote(branch: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch],
        capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def process_new_file(raw_file: str, base_branch: str, today: str) -> None:
    print(f"\nNew file: {raw_file}")
    path = Path(raw_file)

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        print("  Skipping — empty file")
        return

    is_markdown = path.suffix in {".md", ".markdown"}
    _, body = parse_frontmatter(content)
    raw_body = body if is_markdown else content

    print("  Calling Claude...")
    metadata = convert_with_claude(raw_body, is_markdown)
    print(f"  Metadata: {json.dumps({k: v for k, v in metadata.items() if k != 'body'})}")

    branch = f"post/{today}-{metadata['slug']}"
    post_path = post_path_from_branch(branch)

    # Step 1: Write branch reference into raw file on base branch FIRST,
    # so the PR branch's delete has no conflict on merge.
    if path.suffix == ".txt":
        md_path = path.with_suffix(".md")
        md_path.write_text(add_frontmatter_field(content, "branch", branch), encoding="utf-8")
        path.unlink()
        run(["git", "add", str(md_path), raw_file])
        raw_file = str(md_path)
        path = md_path
    else:
        path.write_text(add_frontmatter_field(content, "branch", branch), encoding="utf-8")
        run(["git", "add", raw_file])

    run(["git", "commit", "-m", f"Store branch reference in raw file [skip ci]"])
    run(["git", "push"])

    # Step 2: Create PR branch from updated HEAD — raw file already has branch: field
    run(["git", "checkout", "-b", branch])
    post_path.write_text(build_post_content(metadata), encoding="utf-8")
    path.unlink()
    run(["git", "add", str(post_path), raw_file])
    run(["git", "commit", "-m", f"Add post: {metadata['title']}"])
    run(["git", "push", "origin", branch])

    # Step 3: Open PR
    pr_body = (
        f"Auto-converted from `{raw_file}` using Claude.\n\n"
        f"**Title:** {metadata['title']}\n"
        f"**Category:** {metadata['category']}\n"
        f"**Tags:** {', '.join(metadata.get('tags', []))}\n\n"
        f"Review `{post_path}` and merge when ready."
    )
    run(["gh", "pr", "create",
         "--title", f"New post: {metadata['title']}",
         "--body", pr_body,
         "--base", base_branch,
         "--head", branch])

    run(["git", "checkout", base_branch])
    print(f"  Done — branch: {branch}")


def process_modified_file(raw_file: str, base_branch: str) -> None:
    print(f"\nModified file: {raw_file}")
    path = Path(raw_file)

    content = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    branch = meta.get("branch")

    if not branch:
        print("  No branch in frontmatter — not yet converted, skipping")
        return

    if not branch_exists_on_remote(branch):
        print(f"  Branch {branch} not found — PR may already be merged")
        return

    is_markdown = path.suffix in {".md", ".markdown"}
    print("  Calling Claude...")
    metadata = convert_with_claude(body, is_markdown)
    print(f"  Metadata: {json.dumps({k: v for k, v in metadata.items() if k != 'body'})}")

    post_path = post_path_from_branch(branch)

    run(["git", "fetch", "origin", branch])
    run(["git", "checkout", branch])
    post_path.write_text(build_post_content(metadata), encoding="utf-8")
    run(["git", "add", str(post_path)])
    run(["git", "commit", "-m", f"Update post: {metadata['title']}"])
    run(["git", "push", "origin", branch])

    run(["git", "checkout", base_branch])
    print(f"  Updated branch: {branch}")


def main() -> None:
    process_all = os.environ.get("PROCESS_ALL", "false").lower() == "true"

    if process_all:
        print("Manual trigger — processing all files in raw/")
        new_files = get_all_raw_files()
        modified_files = []
    else:
        new_files = get_raw_files("A")
        modified_files = get_raw_files("M")

    if not new_files and not modified_files:
        print("No new or modified raw files — nothing to do.")
        return

    base_branch = os.environ.get("BASE_BRANCH", "gh-pages")
    today = date.today().strftime("%Y-%m-%d")
    setup_git()

    failed = []

    for f in new_files:
        try:
            process_new_file(f, base_branch, today)
        except Exception as e:
            print(f"  FAILED ({f}): {e}", file=sys.stderr)
            failed.append(f)
            subprocess.run(["git", "checkout", base_branch], capture_output=True)

    for f in modified_files:
        try:
            process_modified_file(f, base_branch)
        except Exception as e:
            print(f"  FAILED ({f}): {e}", file=sys.stderr)
            failed.append(f)
            subprocess.run(["git", "checkout", base_branch], capture_output=True)

    if failed:
        print(f"\nFailed: {failed}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
