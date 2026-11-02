"""Supplement 03: archive of the smoke, run record, progress."""
import shutil
from pathlib import Path
s = open("/home/jin/v3/sm_arch_s2.py", encoding="utf-8").read().replace("smoke_s2", "smoke_s3").replace("path_check3", "path_check4").replace("PATH_CHECK3_STATUS", "PATH_CHECK4_STATUS").replace("Supplement 02", "Supplement 03").replace("the two smoke runs", "the two one-way smoke runs")
exec(compile(s, "arch", "exec"))
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read(); assert "## 18." not in s
s = s.rstrip("\n") + """

## 18. 补充 03 运行记录（求解后追加，第 17 节未改）

用户 2026-11-03 确认 WLS 空闲、AnyConnect 未连接（WSL 时钟 2026-11-02 20:05 UTC）。提交 `7e5baa3f`，两次串行，20:06:06–20:22:18 UTC，间隔 330 s，额度 2 / 2，没有重试。

| 运行 | 终止状态 | 目标值（bn） | GATES_V6 | 峰值（GiB） |
|---|---|---:|---|---:|
| `integrated` | optimal | 329.1463 | `ACCEPTED_LAYER2` | 7.24 |
| `no_new_xb` | optimal | 341.6165 | `ACCEPTED_LAYER2` | 5.82 |

验收两次都通过，B6 12.4702 bn。失败闸门都在第 17.2 节的预告内。第 17.3 节有一项方向相反：`no_new_xb` 的 LA–TH 出口是 15.94 TWh，不是"明显低于 12.49 TWh"。预测原文不改，详见 `V3_REPORT_SUPPLEMENT03.md`。第 17.4 节不改。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "\n## 恢复点"
b = "| 补充 03 冒烟 | 完成：两次 optimal，验收通过，B6 12.47 bn | 求解 `7e5baa3f` |\n\n## 恢复点"
assert s.count(a) == 1; s = s.replace(a, b).replace("|\n\n| 补充 03 冒烟", "|\n| 补充 03 冒烟")
a = "补充 03：运行 `bash /home/jin/v3/smoke_s3.sh --confirmed <确认时间>`，之后 `dry_s3.sh`、`pkg_s3.sh`、全量测试、`V3_REPORT_SUPPLEMENT03.md`。"
b = "补充 03：冒烟完成，接下来 `dry_s3.sh`、`pkg_s3.sh`、全量测试、`V3_REPORT_SUPPLEMENT03.md`。"
assert s.count(a) == 1; s = s.replace(a, b)
a = "补充 03 为 0 / 2，"; b = "补充 03 为 2 / 2，"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
