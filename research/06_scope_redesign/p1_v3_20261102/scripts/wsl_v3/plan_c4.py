"""Supplement 04: archive of the smoke, run record, progress."""
import shutil
from pathlib import Path
s = open("/home/jin/v3/sm_arch_s2.py", encoding="utf-8").read().replace("smoke_s2", "smoke_s4").replace("path_check3", "path_check5").replace("PATH_CHECK3_STATUS", "PATH_CHECK5_STATUS").replace("Supplement 02", "Supplement 04")
exec(compile(s, "arch", "exec"))
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read(); assert "## 20." not in s
s = s.rstrip("\n") + """

## 20. 补充 04 运行记录（求解后追加，第 19 节未改）

用户原话见第 19.3 节，启动前 WSL 到令牌服务器的 TCP 预检通过，无其他求解或 pytest。提交 `f4a8b5e1`，两次串行，21:53:47–22:09:50 UTC（2026-11-02，即 11-03 上午 SGT），间隔 333 s，额度 2 / 2，没有重试，没有改参数。

| 运行 | 终止状态 | 目标值（bn） | GATES_V6 | 峰值（GiB） |
|---|---|---:|---|---:|
| `integrated` | optimal | 329.1921 | `ACCEPTED_LAYER2` | 7.31 |
| `no_new_xb` | optimal | 341.7188 | `ACCEPTED_LAYER2` | 5.81 |

验收两次都通过，B6 12.5267 bn。失败闸门都在第 19.3 节的预告内。两个目标值都在第 19.4 节写下的结构界内。第 19.4 节有两项落在区间外：一体化总成本上升 0.0458 bn（预测不超过 0.03 bn）；LA 受益 −0.1229 bn（预测 −0.12 到 +0.03 bn，方向对，略低于下限）。预测原文不改，详见 `V3_REPORT_SUPPLEMENT04.md`。第 19.5 节不改。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "\n## 恢复点"
b = "| 补充 04 冒烟 | 完成：两次 optimal，验收通过，B6 12.53 bn | 求解 `f4a8b5e1` |\n\n## 恢复点"
assert s.count(a) == 1; s = s.replace(a, b).replace("|\n\n| 补充 04 冒烟", "|\n| 补充 04 冒烟")
a = "补充 04：运行 `bash /home/jin/v3/smoke_s4.sh --confirmed <确认时间>`（用户已答复不必再问，见 `RUN_PLAN_V3.md` 第 19.3 节），之后 `dry_s4.sh`、`pkg_s4.sh`、全量测试、`V3_REPORT_SUPPLEMENT04.md`。"
b = "补充 04：冒烟完成，接下来 `dry_s4.sh`、`pkg_s4.sh`、全量测试、`V3_REPORT_SUPPLEMENT04.md`。"
assert s.count(a) == 1; s = s.replace(a, b)
a = "补充 04 为 0 / 2，"; b = "补充 04 为 2 / 2，"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
