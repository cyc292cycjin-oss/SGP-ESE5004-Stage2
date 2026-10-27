"""HPR checklist H-P8: leak scan. Targets: the package v9 folder, the operator guide, the Windows work folder, the deliverable folder, the WSL helper
folder and every commit of the branch since the base (git log -p). Patterns: (1) the VALUES of the local licence file (read in memory, never printed,
only compared; values shorter than 8 characters ignored), (2) key-name / address / port / host patterns supplied AT RUN TIME through LEAK_PATTERNS
(regex; nothing of them is written in this file). Output: per target the number of hits and the file names (never the matched text). Exclusions
(LEAK_EXCLUDE, regex on path): the instruction file (it lists the key names as scan targets).
    LEAK_PATTERNS="<regex>" [LEAK_EXCLUDE="<regex>"] python leak_scan.py <out json> <target dir>... """
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

WT = Path(os.environ.get("LEAK_WT", "/home/jin/wt_hpr_20261027")); BASE = os.environ.get("LEAK_BASE", "82c32c53")
LIC = Path(os.environ.get("GRB_LICENSE_FILE", "/home/jin/gurobi.lic"))
out = Path(sys.argv[1]); targets = [Path(t) for t in sys.argv[2:]]
pat = os.environ.get("LEAK_PATTERNS", ""); excl = re.compile(os.environ.get("LEAK_EXCLUDE", "(?!x)x"))
rx = re.compile(pat, re.I) if pat else None
values = []
if LIC.exists():
    for line in LIC.read_text(errors="ignore").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            v = line.split("=", 1)[1].strip()
            if len(v) >= 8:
                values.append(v)
res = dict(licence_file=str(LIC), licence_file_exists=LIC.exists(), licence_mode=(oct(LIC.stat().st_mode & 0o777) if LIC.exists() else None), n_secret_values=len(values),
           patterns_supplied=bool(pat), exclude_supplied=bool(os.environ.get("LEAK_EXCLUDE")), targets={}, written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def scan_text(text):
    hv = sum(text.count(v) for v in values); hp = len(rx.findall(text)) if rx else 0
    return hv, hp


for t in targets:
    files = [p for p in t.rglob("*") if p.is_file() and not any(part in (".git", "__pycache__") for part in p.parts)]
    hits = []; skipped = []; n_bin = 0
    for p in files:
        if excl.search(str(p)):
            skipped.append(str(p.relative_to(t))); continue
        try:
            b = p.read_bytes()
        except OSError:
            continue
        if b"\x00" in b[:4096] and p.suffix not in (".py", ".sh", ".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".pbs"):
            n_bin += 1
            hv = sum(b.count(v.encode()) for v in values); hp = 0   # binary: licence values only
        else:
            hv, hp = scan_text(b.decode("utf-8", errors="ignore"))
        if hv or hp:
            hits.append(dict(file=str(p.relative_to(t)), value_hits=hv, pattern_hits=hp))
    res["targets"][str(t)] = dict(files=len(files), binary=n_bin, hits=hits, n_hit_files=len(hits), excluded=skipped)
log = subprocess.run(["git", "-C", str(WT), "log", "--format=%H", f"{BASE}..HEAD"], capture_output=True, text=True, check=True).stdout.split()
commits = {}
for c in log:
    show = subprocess.run(["git", "-C", str(WT), "show", "--format=%H%n%an%n%s", c], capture_output=True, text=True, errors="ignore").stdout
    hv, hp = 0, 0; files_hit = set(); cur = None
    for line in show.splitlines():
        if line.startswith("diff --git"):
            cur = line.split(" b/")[-1]
        if cur and excl.search(cur):
            continue
        a, b = scan_text(line); hv += a; hp += b
        if a or b:
            files_hit.add(cur or "<header>")
    commits[c[:8]] = dict(value_hits=hv, pattern_hits=hp, files=sorted(files_hit))
res["commits"] = commits; res["n_commits"] = len(log)
res["clean"] = all(v["n_hit_files"] == 0 for v in res["targets"].values()) and all(v["value_hits"] == 0 and v["pattern_hits"] == 0 for v in commits.values())
out.write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(dict(clean=res["clean"], n_secret_values=len(values), targets={k: dict(files=v["files"], hits=[(h["file"], h["value_hits"], h["pattern_hits"]) for h in v["hits"]], excluded=v["excluded"]) for k, v in res["targets"].items()},
                      commits={k: v for k, v in commits.items() if v["value_hits"] or v["pattern_hits"]}, n_commits=len(log)), indent=1))
