"""Supplement 04 not started in this session: progress file, mirror list."""
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "\n## 恢复点"
b = "| 审阅决定 `V3_REVIEW_DECISIONS_SUPP03.md` | 已收，补充 04：专线只输送存量电站出力（第 179 项）；原会话上下文 78 %，按决定新开会话 | — |\n\n## 恢复点"
assert s.count(a) == 1; s = s.replace(a, b).replace("|\n\n| 审阅决定 `V3_REVIEW_DECISIONS_SUPP03.md`", "|\n| 审阅决定 `V3_REVIEW_DECISIONS_SUPP03.md`")
i = s.index("补充 03 完成，等审阅。"); j = s.index("## 计数")
s = s[:i] + "补充 04 未开始，按 `V3_REVIEW_DECISIONS_SUPP03.md` 第 2 节在新会话执行，先读 `V3_HANDOFF_SUPP04.md`。额度：本机 Gurobi 2 次，计算 2 小时，磁盘 20 GB。\n\n" + s[j:]
open(p, "w", encoding="utf-8", newline="").write(s)
p = "/home/jin/v3/mirror_s1.sh"; s = open(p, encoding="utf-8").read()
a = 'F="V3_REPORT_SUPPLEMENT03.md'; b = 'F="V3_HANDOFF_SUPP04.md V3_REPORT_SUPPLEMENT03.md'
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, b)); print("ok")
