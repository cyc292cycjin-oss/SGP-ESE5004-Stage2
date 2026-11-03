"""replace sections 7-11 of V3_REPORT_HPC_PACKAGE.md with report_tail.md (the text before '## 7. ' is kept as it is)"""
import sys
from pathlib import Path
rep = Path("/home/jin/wt_v3_hpc/research/06_scope_redesign/p1_v3_20261102/V3_REPORT_HPC_PACKAGE.md")
tail = Path("/home/jin/v3h/report_tail.md").read_text(encoding="utf-8")
t = rep.read_text(encoding="utf-8")
i = t.index("\n## 7. ")
rep.write_text(t[: i + 1] + tail, encoding="utf-8")
print("kept", i + 1, "chars; new length", len(t[: i + 1] + tail))
