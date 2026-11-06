#!/usr/bin/env python3
"""V4 W10-5: REPORT.md = scripts/REPORT_TEMPLATE.md with {{T1}}..{{T7}} replaced by the generated tables of evidence/REPORT_TABLES.md."""
import re
import sys
from pathlib import Path

d = Path(sys.argv[1])
tpl = (d / "scripts" / "REPORT_TEMPLATE.md").read_text(encoding="utf-8")
tab = (d / "evidence" / "REPORT_TABLES.md").read_text(encoding="utf-8")
parts = {}
for blk in re.split(r"(?m)^(?=### T\d )", tab):
    m = re.match(r"### (T\d) (.*)\n", blk)
    if m:
        parts[m.group(1)] = f"**{m.group(1)}　{m.group(2).strip()}**\n" + blk[m.end():].rstrip() + "\n"
missing = [k for k in re.findall(r"\{\{(T\d)\}\}", tpl) if k not in parts]
if missing:
    raise SystemExit(f"missing tables {missing}")
out = re.sub(r"\{\{(T\d)\}\}", lambda m: parts[m.group(1)], tpl)
(d / "REPORT.md").write_text(out, encoding="utf-8", newline="\n")
print("REPORT.md", len(out.splitlines()), "lines")
