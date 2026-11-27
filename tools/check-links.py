#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check every relative link and #anchor in the docs' Markdown files.

Usage: tools/check-links.py [ROOT]   (default: the repo root). Exit 1 on a broken link.
Stdlib only. Anchors follow GitHub's heading slugs (duplicates get -1, -2, ...) and
explicit <a id=...>/<a name=...> tags. Fenced code and inline code are ignored.
"""

import os
import re
import sys
from urllib.parse import unquote

LINK = re.compile(
    r"!?\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)"
)
REFDEF = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+.*)?$")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
HTML_ANCHOR = re.compile(r"<a\s+(?:id|name)=\"([^\"]+)\"", re.IGNORECASE)
FENCE = re.compile(r"^\s{0,3}(```|~~~)")
INLINE_CODE = re.compile(r"`+[^`]*`+")


def slug(text):
    """GitHub's heading anchor: plain text, lower case, punctuation dropped, spaces to '-'."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> their text
    text = re.sub(r"<[^>]+>", "", text)  # inline HTML
    text = text.replace("`", "").lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def prose_lines(path):
    """Yield (line number, line) outside fenced code blocks."""
    fence = None
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            m = FENCE.match(line)
            if m:
                if fence is None:
                    fence = m.group(1)
                elif line.strip().startswith(fence):
                    fence = None
                continue
            if fence is None:
                yield n, line


_ANCHORS = {}


def anchors(path):
    cache = _ANCHORS
    if path not in cache:
        seen, found = {}, set()
        for _, line in prose_lines(path):
            found.update(HTML_ANCHOR.findall(line))
            m = HEADING.match(line)
            if m:
                s = slug(m.group(2))
                k = seen.get(s, 0)
                seen[s] = k + 1
                found.add(s if k == 0 else f"{s}-{k}")
        cache[path] = found
    return cache[path]


def links(path):
    for n, line in prose_lines(path):
        m = REFDEF.match(line)
        if m:
            yield n, m.group(1)
            continue
        for m in LINK.finditer(INLINE_CODE.sub("", line)):
            yield n, m.group(1)


def check_file(path, root):
    errors = []
    for n, target in links(path):
        if re.match(
            r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE
        ):  # http:, mailto:, ...
            continue
        file_part, _, frag = target.partition("#")
        file_part = unquote(file_part)
        if file_part.startswith("/"):
            dest = os.path.join(root, file_part.lstrip("/"))
        elif file_part:
            dest = os.path.normpath(os.path.join(os.path.dirname(path), file_part))
        else:
            dest = path
        where = f"{os.path.relpath(path, root)}:{n}"
        if not os.path.exists(dest):
            errors.append(f"{where}: missing {target}")
        elif (
            frag
            and dest.endswith(".md")
            and os.path.isfile(dest)
            and unquote(frag).lower() not in anchors(dest)
        ):
            errors.append(
                f"{where}: no anchor #{frag} in {os.path.relpath(dest, root)}"
            )
    return errors


def md_files(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x != "node_modules"]
        for f in sorted(files):
            if f.endswith(".md"):
                yield os.path.join(d, f)


def main(argv):
    root = os.path.abspath(
        argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(__file__), "..")
    )
    errors = [e for p in md_files(root) for e in check_file(p, root)]
    for e in errors:
        print(e)
    print(f"{len(errors)} broken link(s)" if errors else "links ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
