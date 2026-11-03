"""Supplement 05: progress, mirror list; a check of the report's numbers against the archived results."""
import json
from pathlib import Path
import pandas as pd
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "| 补充 05 冒烟 | 完成：两次 optimal，验收通过，B6 12.57 bn | 求解 `6c202ec5` |\n"
b = a + "| 补充 05 新包 | 完成：27 文件 254,701,656 B，干跑与预检通过，未上传；相关测试 152 通过、6 跳过、0 失败，全量未跑（额度） | 代码 `55253dd7` |\n| 补充 05 报告 | 完成：`V3_REPORT_SUPPLEMENT05.md` | 本次提交 |\n"
assert s.count(a) == 1; s = s.replace(a, b)
i = s.index("补充 05：冒烟完成"); j = s.index("## 计数")
s = s[:i] + "补充 05 完成，等审阅。筛查上云另有指令和用户授权（包 `work/p1_v3_20261102/screen_package_v3_op/`）。HPC 打包和 v3 版 `RUN_PLAN_HPC.md` 在筛查之后。全量测试最后一次在 `04c1eabf`。\n\n" + s[j:]
a = "补充 05 为 2 / 2。"; b = "补充 05 为 2 / 2，本机计算约 1.15 小时 / 1.5 小时，磁盘约 9.2 GB / 15 GB。"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s)
p = "/home/jin/v3/mirror_s1.sh"; s = open(p, encoding="utf-8").read()
a = 'F="V3_S5_STOP_NOTE.md'; b = 'F="V3_REPORT_SUPPLEMENT05.md V3_S5_STOP_NOTE.md'
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, b))
t = open(D + "V3_REPORT_SUPPLEMENT05.md", encoding="utf-8").read(); e = json.loads(Path(D + "evidence/smoke_s5/V3_SMOKE_RESULT.json").read_text()); bad = []


def has(x):
    if x not in t:
        bad.append(x)


assert "{{" not in t
for r in ("integrated", "no_new_xb"):
    x = e[r]; has(f"{x['objective_eur'] / 1e9:.4f}"); has(f"{x['peak_rss_gib']:.2f}"); has(f"{x['ledger_relative_error']:.1e}"); has(f"{x['ship_capacity_duals']['max_utilisation'] * 100:.1f} %")
has(f"{(e['no_new_xb']['objective_eur'] - e['integrated']['objective_eur']) / 1e9:.4f}")
c = pd.read_csv(D + "evidence/SOURCE_CAPACITY_OP_V3.csv")
for k in ("moved_mw", "non_thermal_mw", "avail_dry_week_mw", "avail_year_mw", "avail_sep_mw", "mw_hydro", "mw_ror"):
    has(f"{c[k].sum():,.0f}")
    for v in c[k]:
        has(f"{v:,.0f}")
b = pd.read_csv(D + "evidence/smoke_s5/BENEFIT.csv").set_index("player").owen_benefit_eur / 1e9
for k, v in b.items():
    has(f"{abs(v):.3f}")
m = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/screen_package_v3_op/PACKAGE_MANIFEST.json")); has(m["sha256sums_sha256"]); has(f"{m['upload_total_bytes_excluding_this_manifest']:,}"); has(m["commit"][:8])
for r in m["files"]:
    if r["path"].endswith(".nc"):
        has(f"{r['bytes']:,}"); has(r["sha256"][:8])
print("missing", bad); print("ok")
