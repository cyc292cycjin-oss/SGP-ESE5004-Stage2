"""I2: mirror the delivery folder work/p1_v4_w07_20261106/I2/ into the I2 worktree (research/06_scope_redesign/p1_v4_w07_20261106/I2/).

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_sync.py [--check]

Text files are written with LF line endings (the repository stores LF; files written on Windows can be CRLF). Review zips, __pycache__ and
the figure cache are not mirrored. --check only lists the differences (work folder vs worktree file) and exits 1 when any exists.
The instruction file and its SHA256 file (one level up) are mirrored too.
"""
from __future__ import annotations

import sys
from pathlib import Path

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106")
SRC = WORK / "I2"
DST = Path("/home/jin/wt_v4_i2/research/06_scope_redesign/p1_v4_w07_20261106/I2")
TEXT = {".md", ".csv", ".py", ".json", ".txt", ".sh", ".yaml", ".svg"}
SKIP_DIRS = {"__pycache__"}


def files():
    for p in sorted(SRC.rglob("*")):
        if p.is_dir() or any(x in SKIP_DIRS for x in p.parts) or p.suffix == ".zip":
            continue
        yield p, DST / p.relative_to(SRC)
    for n in ("V4_I2_INSTRUCTION.md", "V4_I2_SHA256.txt"):
        yield WORK / n, DST.parent / n


def payload(p: Path) -> bytes:
    b = p.read_bytes()
    return b.replace(b"\r\n", b"\n") if p.suffix in TEXT else b


def main():
    check = "--check" in sys.argv
    diff = []
    for s, d in files():
        b = payload(s)
        if not d.exists() or d.read_bytes() != b:
            diff.append(str(d))
            if not check:
                d.parent.mkdir(parents=True, exist_ok=True)
                d.write_bytes(b)
    print(("differences: " if check else "written: ") + str(len(diff)))
    for x in diff[:40]:
        print("  ", x)
    if check and diff:
        sys.exit(1)


if __name__ == "__main__":
    main()
