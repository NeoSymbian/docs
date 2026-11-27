#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build roadmap.md's full stage board from the stage blocks in the area docs.

Each stage doc owns its status in one block:

    <!-- stages -->
    | Stage | What | State | Updated | Next / evidence |
    |---|---|---|---|---|
    | FS7 | Install a big Z: | active | 2026-11-26 | step 0 done (kernel#45); steps 1-4 open |
    <!-- /stages -->

State is one of: done, active, open, parked, dropped.
Usage: tools/roadmap.py          rewrite the board in roadmap.md
       tools/roadmap.py --check  exit 1 if roadmap.md's board is out of date or a block is malformed
"""

import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AREAS = [  # folder, track title (board order)
    ("kernel", "Kernel"),
    ("user-side", "User side"),
    ("storage", "Storage"),
    ("hardware", "Hardware"),
    ("neoui-shell", "Shell (neoui)"),
    ("apps", "Apps"),
    ("developer-tools", "Developer tools"),
]
STATES = {
    "done": "✅ done",
    "active": "🔵 active",
    "open": "⬜ open",
    "parked": "⏸ parked",
    "dropped": "✖ dropped",
}
BLOCK = re.compile(r"<!-- stages -->\n(.*?)<!-- /stages -->", re.DOTALL)
BOARD = re.compile(r"(<!-- board -->\n)(.*?)(<!-- /board -->)", re.DOTALL)
HEADER = ["Stage", "What", "State", "Updated", "Next / evidence"]


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def title(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line[2:].strip()
    return os.path.basename(path)


def area_docs(folder):
    docs = []
    for d, dirs, files in os.walk(os.path.join(ROOT, folder)):
        dirs[:] = sorted(x for x in dirs if x != "history")
        for f in files:
            if f.endswith(".md"):
                docs.append(os.path.join(d, f))
    # the area's README first, then by path
    return sorted(
        docs, key=lambda p: (os.path.relpath(p, ROOT) != f"{folder}/README.md", p)
    )


def blocks(path, errors):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    rel = os.path.relpath(path, ROOT)
    rows = []
    for m in BLOCK.finditer(text):
        lines = [x for x in m.group(1).splitlines() if x.strip()]
        if len(lines) < 2 or cells(lines[0]) != HEADER:
            errors.append(
                f"{rel}: a stages block must start with | {' | '.join(HEADER)} |"
            )
            continue
        for line in lines[2:]:
            row = cells(line)
            if len(row) != len(HEADER):
                errors.append(
                    f"{rel}: {len(row)} cells, want {len(HEADER)}: {line.strip()}"
                )
            elif row[2] not in STATES:
                errors.append(
                    f"{rel}: state '{row[2]}' not one of {', '.join(STATES)}: {row[0]}"
                )
            elif row[3] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}|—", row[3]):
                errors.append(
                    f"{rel}: date '{row[3]}' is not YYYY-MM-DD or —: {row[0]}"
                )
            else:
                rows.append(row)
    return rows


def board(errors):
    out = []
    for folder, track in AREAS:
        section = []
        for path in area_docs(folder):
            rel = os.path.relpath(path, ROOT)
            for stage, what, state, updated, nxt in blocks(path, errors):
                section.append(
                    f"| {stage} | {what} | {STATES[state]} | {updated} | {nxt} | [{title(path)}]({rel}) |"
                )
        if section:
            out += [
                f"### {track}",
                "",
                "| Stage | What | State | Updated | Next / evidence | Doc |",
            ]
            out += ["|---|---|---|---|---|---|", *section, ""]
    return "\n".join(out)


def main(argv):
    errors = []
    new = board(errors)
    path = os.path.join(ROOT, "roadmap.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = BOARD.search(text)
    if not m:
        errors.append("roadmap.md: no <!-- board --> ... <!-- /board --> markers")
    for e in errors:
        print(e)
    if errors or not m:
        return 1
    updated = text[: m.start(2)] + new + "\n" + text[m.end(2) :]
    if "--check" in argv:
        if updated != text:
            print("roadmap.md's board is out of date: run tools/roadmap.py")
            return 1
        print("board ok")
        return 0
    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)
    print(
        f"board written: {sum(line.startswith('| ') for line in new.splitlines()) - new.count('### ')} stages"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
