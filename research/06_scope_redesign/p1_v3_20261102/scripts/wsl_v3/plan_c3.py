"""Supplement 03: progress, deployment list, mirror list; a check of the report's numbers."""
import json
from pathlib import Path
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "| 补充 03 冒烟 | 完成：两次 optimal，验收通过，B6 12.47 bn | 求解 `7e5baa3f` |\n"
b = a + "| 补充 03 新包 | 完成：27 文件 253,971,700 B，干跑与预检通过，未上传；全量测试 738 通过、58 跳过、3 失败（与 v3 无关） | 代码 `92aa82ba` |\n| 补充 03 报告 | 完成：`V3_REPORT_SUPPLEMENT03.md` | 本次提交 |\n"
assert s.count(a) == 1; s = s.replace(a, b)
i = s.index("补充 03：冒烟完成"); j = s.index("## 计数")
s = s[:i] + "补充 03 完成，等审阅。筛查上云另有指令和用户授权（包 `work/p1_v3_20261102/screen_package_v3_oneway/`）。HPC 打包和 v3 版 `RUN_PLAN_HPC.md` 在筛查之后。\n\n" + s[j:]
a = "补充 03 为 2 / 2，上限本机计算 2 小时、磁盘 20 GB。"; b = "补充 03 为 2 / 2，本机计算约 1.6 小时 / 2 小时，磁盘约 9.5 GB / 20 GB。"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_DEPLOY_FILES.md"; s = open(p, encoding="utf-8", newline="").read()
a = "## 1. 两边共用\n"; b = "**补充 03 更新（2026-11-03）：** 专线改单向后网络全部重建，现行登记见 `RUN_PLAN_V3.md` 第 17 节，现行筛查包是 `work/p1_v3_20261102/screen_package_v3_oneway/`，`screen_package_v3/` 已作废。\n\n## 1. 两边共用\n"
assert s.count(a) == 1; open(p, "w", encoding="utf-8", newline="").write(s.replace(a, b))
p = "/home/jin/v3/mirror_s1.sh"; s = open(p, encoding="utf-8").read()
a = 'F="V3_REPORT_SUPPLEMENT02.md'; b = 'F="V3_REPORT_SUPPLEMENT03.md V3_REPORT_SUPPLEMENT02.md'
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, b))
t = open(D + "V3_REPORT_SUPPLEMENT03.md", encoding="utf-8").read(); e = json.loads(Path(D + "evidence/smoke_s3/V3_SMOKE_RESULT.json").read_text()); bad = []
def has(x):
    if x not in t: bad.append(x)
for r in ("integrated", "no_new_xb"):
    x = e[r]; has(f"{x['objective_eur'] / 1e9:.4f}"); has(f"{x['peak_rss_gib']:.2f}"); has(f"{x['ledger_relative_error']:.1e}"); has(f"{x['ship_capacity_duals']['max_utilisation'] * 100:.1f} %")
print("missing", bad); print("ok")
