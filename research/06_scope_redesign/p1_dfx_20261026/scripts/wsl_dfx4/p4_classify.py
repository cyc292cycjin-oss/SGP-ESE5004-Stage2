"""DFX phase 4: classify leak-scan hits by sub-pattern. Pattern-file classes (key / ssh / ip / host; file outside the repository) as in p6_classify.py,
plus the connection values supplied only through the environment at run time (DFX_HOST, DFX_PORT, DFX_INST). For the connection classes the matched
value is never printed: only the count and up to three contexts with the match replaced by a placeholder. Key names: count only.
    DFX_HOST=.. DFX_PORT=.. DFX_INST=.. python p4_classify.py <file> | commit:<sha> ..."""
import os
import re
import subprocess
import sys
from pathlib import Path

WT = "/home/jin/wt_dfx_v3_20261026"
pats = dict(l.split("=", 1) for l in Path("/home/jin/.dfx_leak_patterns").read_text().splitlines() if l and not l.startswith("#"))
conn = {"conn_host": re.escape(os.environ["DFX_HOST"]), "conn_port": r"\b" + re.escape(os.environ["DFX_PORT"]) + r"\b",
        "conn_inst": r"\b" + re.escape(os.environ["DFX_INST"]) + r"\b"}
for arg in sys.argv[1:]:
    if arg.startswith("commit:"):
        c = arg.split(":", 1)[1]; name = f"commit {c[:8]}"
        t = subprocess.run(["git", "-C", WT, "show", "--format=", c], capture_output=True, text=True, errors="ignore").stdout
    else:
        name = arg.split("/")[-2] + "/" + arg.split("/")[-1]; t = Path(arg).read_text(errors="ignore")
    for k, p in list(pats.items()) + list(conn.items()):
        ms = list(re.finditer(p, t, re.I | re.M))
        if not ms:
            continue
        if k == "key":
            show = f"{len(ms)} key-name literal(s) (no value)"
        elif k.startswith("conn_"):
            ctx = []
            for m in ms[:3]:
                a, b = max(0, m.start() - 24), min(len(t), m.end() + 24)
                ctx.append((t[a:m.start()] + "<" + k.upper() + ">" + t[m.end():b]).replace("\n", " "))
            show = ctx
        else:
            show = sorted(set(m.group(0).strip() for m in ms))[:8]
        print(f"{name}: {k}: {len(ms)} -> {show}")
