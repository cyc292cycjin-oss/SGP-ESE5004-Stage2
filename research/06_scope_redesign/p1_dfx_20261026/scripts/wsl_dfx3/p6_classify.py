"""DFX v3 P6: classify the pattern hits of the leak scan by sub-pattern (key name / ssh port / IPv4-like / host) for the files or commits given on the
command line. The sub-patterns come from the pattern file outside the repository (lines name=regex); nothing of them is written here. For non-licence
files (public environment locks, registry rows, reports) the matched substrings are printed to show what matched; for the key-name class only the count.
    python p6_classify.py <file> | <commit>:<path> ..."""
import os
import re
import subprocess
import sys
from pathlib import Path

WT = "/home/jin/wt_dfx_v3_20261026"
PF = Path(os.environ.get("LEAK_PATTERN_FILE", "/home/jin/.dfx_leak_patterns"))
pats = dict(line.split("=", 1) for line in PF.read_text().splitlines() if line and not line.startswith("#"))
for arg in sys.argv[1:]:
    if ":" in arg and not arg.startswith("/"):
        commit, path = arg.split(":", 1); name = f"commit {commit} {Path(path).name} (diff)"
        t = subprocess.run(["git", "-C", WT, "show", commit, "--", path], capture_output=True, text=True, errors="ignore").stdout
    else:
        name = arg; t = Path(arg).read_text(errors="ignore")
    for k, p in pats.items():
        ms = [m.group(0) for m in re.finditer(p, t, re.I | re.M)]
        if ms:
            show = sorted(set(x.strip() for x in ms))[:12] if k != "key" else [f"{len(ms)} key-name literal(s) (no value)"]
            print(f"{name}: {k}: {len(ms)} -> {show}")
