"""Supplement 05: full suite authorised by the user after the first report: progress."""
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
for a, b in (("干跑与预检通过，未上传；相关测试 152 通过、6 跳过、0 失败，全量未跑（额度） | 代码 `55253dd7` |", "干跑与预检通过，未上传；相关测试 152 通过、6 跳过、0 失败 | 代码 `55253dd7` |"),
             ("| 补充 05 报告 | 完成：`V3_REPORT_SUPPLEMENT05.md` | 本次提交 |\n", "| 补充 05 报告 | 完成：`V3_REPORT_SUPPLEMENT05.md` | `93e2e8be` |\n| 全量测试（用户授权补跑） | 提交 `93e2e8be`：752 通过、58 跳过、3 失败（与 v3 无关，同之前） | 本次提交 |\n"),
             ("HPC 打包和 v3 版 `RUN_PLAN_HPC.md` 在筛查之后。全量测试最后一次在 `04c1eabf`。", "HPC 打包和 v3 版 `RUN_PLAN_HPC.md` 在筛查之后。"),
             ("本机计算约 1.15 小时 / 1.5 小时，磁盘约 9.2 GB / 15 GB。", "本机计算约 1.6 小时 / 1.5 小时（超出部分是用户授权补跑的全量测试），磁盘约 9.2 GB / 15 GB。")):
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
