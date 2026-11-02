"""Supplement 05 stop note: evidence, progress, mirror list. No code change."""
import shutil
from pathlib import Path
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/s5_status"); D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
for f in ("MOVED_STOCK_STATUS_V3.csv", "MOVED_STOCK_STATUS_BY_NODE_V3.csv"):
    shutil.copy2(R / f, D + "evidence/" + f)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "\n## 恢复点"
b = "| 审阅决定 `V3_REVIEW_DECISIONS_SUPP04.md` | 已收，补充 05：源母线只放运营中机组（第 180 项） | — |\n| 补充 05 第 1 条 | **停止**：43 台 11,028 MW 候选机组的 `gem_status` 空白，见 `V3_S5_STOP_NOTE.md`；未改代码、未构建、未求解 | 本次提交 |\n\n## 恢复点"
assert s.count(a) == 1; s = s.replace(a, b).replace("|\n\n| 审阅决定 `V3_REVIEW_DECISIONS_SUPP04.md`", "|\n| 审阅决定 `V3_REVIEW_DECISIONS_SUPP04.md`")
i = s.index("补充 04 完成，等审阅。"); j = s.index("## 计数")
s = s[:i] + "补充 05 停在第 1 条之前，等用户对 `V3_S5_STOP_NOTE.md` 第 4 节的决定。额度：本机 Gurobi 2 次，计算 1.5 小时，磁盘 15 GB。上一版包 `screen_package_v3_bound/` 保留不用。\n\n" + s[j:]
a = "磁盘约 9.2 GB / 20 GB。"; b = a + "补充 05 为 0 / 2。"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s)
p = "/home/jin/v3/mirror_s1.sh"; s = open(p, encoding="utf-8").read()
a = 'F="V3_REPORT_SUPPLEMENT04.md'; b = 'F="V3_S5_STOP_NOTE.md V3_REPORT_SUPPLEMENT04.md'
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, b)); print("ok")
