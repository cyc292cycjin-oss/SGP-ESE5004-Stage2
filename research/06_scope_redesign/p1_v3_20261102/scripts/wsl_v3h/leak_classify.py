"""Classify the pattern hits of scan_h.sh without printing the matched text: for every hit file (and the hit commits), the index of the pattern line of the pattern
file outside the repository, the line number and a masked form of the match (first 3 characters, length, character classes). Read only.
usage: python leak_classify.py <LEAK_SCAN json> <pattern file> <worktree>"""
import json, re, subprocess, sys
from pathlib import Path

r = json.load(open(sys.argv[1])); pats = [l.split("=", 1)[1] for l in Path(sys.argv[2]).read_text().splitlines() if l and not l.startswith("#") and "=" in l]
kinds = [l.split("=", 1)[0] for l in Path(sys.argv[2]).read_text().splitlines() if l and not l.startswith("#") and "=" in l]
rx = [re.compile(p, re.I) for p in pats]; wt = Path(sys.argv[3])
DIG = re.compile(r"[0-9.:]+")
mask = lambda s: s[:3] + "…(len " + str(len(s)) + ", " + ("digits" if DIG.fullmatch(s) else "text") + ")"
for t, v in r["targets"].items():
    for h in v["hits"]:
        p = Path(t) / h["file"]; text = p.read_text(errors="ignore").splitlines()
        for i, line in enumerate(text, 1):
            for k, x in enumerate(rx):
                for m in x.finditer(line):
                    print(f"{Path(t).name}/{h['file']}:{i}: kind={kinds[k]} match={mask(m.group(0))} context={line[max(0, m.start() - 25):m.start()].strip()[-25:]!r}")
for c, v in r["commits"].items():
    if v["value_hits"] or v["pattern_hits"]:
        show = subprocess.run(["git", "-C", str(wt), "show", "--format=", c], capture_output=True, text=True, errors="ignore").stdout.splitlines()
        for line in show:
            for k, x in enumerate(rx):
                for m in x.finditer(line):
                    print(f"commit {c}: kind={kinds[k]} match={mask(m.group(0))} line_start={line[:60]!r}")
