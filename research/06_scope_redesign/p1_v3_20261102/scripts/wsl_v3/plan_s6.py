"""Supplement 02: final numbers of the report, progress file, mirror list."""
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "V3_REPORT_SUPPLEMENT02.md"; s = open(p, encoding="utf-8", newline="").read()
for a, b in (("RES_HOURS", "1.8"), ("RES_DISK", "9.6"), ("TEST_LINE", "提交 `f40a14e4` 上 737 通过、58 跳过、3 失败。3 项与之前相同，都与 v3 无关（`RUN_PLAN_V3.md` 第 6 节）。")):
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "| 补充 02 第 2.3 节第 2 项 冒烟 | 完成：两次 optimal，验收通过，B6 12.42 bn；第 176 项全文未到，待补 | 求解 `9dc4c35e` |\n"
b = a + """| 补充 02 第 2.4 节 筛查准备 | 完成：`RUN_PLAN_SCREEN_V3.md`，部署包 27 文件 254,022,757 B，干跑与预检通过，未上传 | 代码 `f40a14e4` |
| 全量测试 | 提交 `f40a14e4`：737 通过、58 跳过、3 失败（与 v3 无关） | 本次提交 |
| 补充 02 第 2.5 节 报告 | 完成：`V3_REPORT_SUPPLEMENT02.md` | 本次提交 |
"""
assert s.count(a) == 1; s = s.replace(a, b)
a = s[s.index("## 恢复点"):]
b = """## 恢复点

补充 02 完成，等审阅。待办：第 176 项全文写入 `V3_RULES.md` 第 10 节，并替换部署包内的 `V3_RULES.md`、重算 `SHA256SUMS`。筛查上云另有指令和用户授权（包 `work/p1_v3_20261102/screen_package_v3/`）。HPC 打包和 v3 版 `RUN_PLAN_HPC.md` 在筛查之后。

## 计数

本机 Gurobi：阶段 3 第二轮 2 / 2；补充 01 为 4 / 4；补充 02 为 2 / 2。补充 02 本机计算约 1.8 小时 / 4 小时，磁盘约 9.6 GB / 30 GB。
"""
s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s)
p = "/home/jin/v3/mirror_s1.sh"; s = open(p, encoding="utf-8").read()
a = 'F="V3_REPORT_SUPPLEMENT01.md RUN_PLAN_V3.md'
b = 'F="V3_REPORT_SUPPLEMENT02.md RUN_PLAN_SCREEN_V3.md V3_REPORT_SUPPLEMENT01.md RUN_PLAN_V3.md'
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, b)); print("ok")
