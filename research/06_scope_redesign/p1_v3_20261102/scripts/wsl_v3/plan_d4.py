"""Supplement 04: progress, mirror list; a check of the report's numbers against the archived results."""
import json
from pathlib import Path
import pandas as pd
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "| 补充 04 冒烟 | 完成：两次 optimal，验收通过，B6 12.53 bn | 求解 `f4a8b5e1` |\n"
b = a + "| 补充 04 新包 | 完成：27 文件 254,656,373 B，干跑与预检通过，未上传；全量测试 745 通过、58 跳过、3 失败（与 v3 无关） | 代码 `04c1eabf` |\n| 补充 04 报告 | 完成：`V3_REPORT_SUPPLEMENT04.md` | 本次提交 |\n"
assert s.count(a) == 1; s = s.replace(a, b)
i = s.index("补充 04：冒烟完成"); j = s.index("## 计数")
s = s[:i] + "补充 04 完成，等审阅。筛查上云另有指令和用户授权（包 `work/p1_v3_20261102/screen_package_v3_bound/`）。HPC 打包和 v3 版 `RUN_PLAN_HPC.md` 在筛查之后。\n\n" + s[j:]
a = "补充 04 为 2 / 2，上限本机计算 2 小时、磁盘 20 GB。"; b = "补充 04 为 2 / 2，本机计算约 1.5 小时 / 2 小时，磁盘约 9.2 GB / 20 GB。"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s)
p = "/home/jin/v3/mirror_s1.sh"; s = open(p, encoding="utf-8").read()
a = 'F="V3_HANDOFF_SUPP04.md'; b = 'F="V3_REPORT_SUPPLEMENT04.md V3_HANDOFF_SUPP04.md'
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, b))
t = open(D + "V3_REPORT_SUPPLEMENT04.md", encoding="utf-8").read(); e = json.loads(Path(D + "evidence/smoke_s4/V3_SMOKE_RESULT.json").read_text()); bad = []


def has(x):
    if x not in t:
        bad.append(x)


for r in ("integrated", "no_new_xb"):
    x = e[r]; has(f"{x['objective_eur'] / 1e9:.4f}"); has(f"{x['peak_rss_gib']:.2f}"); has(f"{x['ledger_relative_error']:.1e}"); has(f"{x['ship_capacity_duals']['max_utilisation'] * 100:.1f} %")
has(f"{(e['no_new_xb']['objective_eur'] - e['integrated']['objective_eur']) / 1e9:.4f}")
c = pd.read_csv(D + "evidence/SOURCE_CAPACITY_V3.csv")
for k in ("moved_mw", "non_thermal_mw", "avail_dry_week_mw", "avail_year_mw", "avail_sep_mw"):
    has(f"{c[k].sum():,.0f}")
    for v in c[k]:
        has(f"{v:,.0f}")
b = pd.read_csv(D + "evidence/smoke_s4/BENEFIT.csv").set_index("player").owen_benefit_eur / 1e9
for k, v in b.items():
    has(f"{abs(v):.3f}")
print("missing", bad); print("ok")
