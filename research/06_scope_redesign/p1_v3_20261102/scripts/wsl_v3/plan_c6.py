"""Supplement 05: archive of the smoke, run record, progress."""
import shutil
from pathlib import Path
s = open("/home/jin/v3/sm_arch_s2.py", encoding="utf-8").read().replace("smoke_s2", "smoke_s5").replace("path_check3", "path_check6").replace("PATH_CHECK3_STATUS", "PATH_CHECK6_STATUS").replace("Supplement 02", "Supplement 05")
exec(compile(s, "arch", "exec"))
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "RUN_PLAN_V3.md"; s = open(p, encoding="utf-8", newline="").read(); assert "## 22." not in s
s = s.rstrip("\n") + """

## 22. 补充 05 运行记录（求解后追加，第 21 节未改）

用户原话见第 21.3 节，启动前 WSL 到令牌服务器的 TCP 预检通过，无其他求解或 pytest。提交 `6c202ec5`，两次串行，2026-11-02 23:58:08 至 11-03 00:13:53 UTC，间隔 333 s，额度 2 / 2，没有重试，没有改参数。

| 运行 | 终止状态 | 目标值（bn） | GATES_V6 | 峰值（GiB） |
|---|---|---:|---|---:|
| `integrated` | optimal | 329.1998 | `ACCEPTED_LAYER2` | 7.35 |
| `no_new_xb` | optimal | 341.7664 | `ACCEPTED_LAYER2` | 5.70 |

验收两次都通过，B6 12.5665 bn。失败闸门都在第 21.3 节的预告内。两个目标值都在第 21.4 节写下的结构界内。第 21.4 节有两项低于区间下限：`no_new_xb` 的 LA 净出口 +5.23 TWh（预测 +5.5 到 +8.5）、专线合计流量 4.76 TWh（预测 5.0–7.8）。预测原文不改，详见 `V3_REPORT_SUPPLEMENT05.md`。第 21.5 节不改。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "\n## 恢复点"
b = "| 补充 05 冒烟 | 完成：两次 optimal，验收通过，B6 12.57 bn | 求解 `6c202ec5` |\n\n## 恢复点"
assert s.count(a) == 1; s = s.replace(a, b).replace("|\n\n| 补充 05 冒烟", "|\n| 补充 05 冒烟")
i = s.index("补充 05：运行 `bash /home/jin/v3/smoke_s5.sh"); j = s.index("## 计数")
s = s[:i] + "补充 05：冒烟完成，接下来 `dry_s5.sh`、`pkg_s5.sh`、相关测试、`V3_REPORT_SUPPLEMENT05.md`。\n\n" + s[j:]
a = "补充 05 为 0 / 2。"; b = "补充 05 为 2 / 2。"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
