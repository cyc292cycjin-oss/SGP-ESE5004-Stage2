"""Supplement 02: the limitations that the review text itself states, committed before the smoke; the full text of decision 176 is not available."""
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"
p = D + "V3_RULES.md"; s = open(p, encoding="utf-8", newline="").read()
assert "## 10. 局限" not in s
s = s.rstrip("\n") + """

## 10. 局限（第 176 项，不完整）

**第 176 项全文（七条加"已核实非问题"）尚未到位。** 审阅决定要求全文在求解前提交，但原文不在工作目录和任何分支里。用户 2026-11-03 确认 WLS 空闲后，求解先进行，全文收到后补入本节，并在报告中说明这个顺序偏差。以下只是审阅决定和本补充已写明的内容，编号不对应第 176 项的七条。

- **VN 生物质（属第 176 项局限 (2)）：** 维持 PyPSA-Eur 2050 载体比例和第 133 项溢出规则，不另造规则。工业固定生物质 181.4 TWh，约为 APEC 2022 实际值（215 PJ，59.7 TWh）的 3 倍；固体潜力 125.77 TWh 全部被固定需求占满，溢出 71.86 TWh。
- **EV 车队代理：** 东盟两三轮车占比高，车队代理偏大；E2 的 10 bn 级效应来自一周放大，筛查看不到。
- **专线：** 不绑定电站、可双向、着陆节点取最近节点、线损用代理线型（第 2.3 节）。
- **`no_new_xb` E2：** 两种档案都是 suboptimal，按 C1 与 GATES_V6 判定。
"""
open(p, "w", encoding="utf-8", newline="").write(s)
p = D + "V3_PROGRESS.md"; s = open(p, encoding="utf-8", newline="").read()
a = "| 补充 02 第 2.3 节第 2 项 冒烟 | **等用户确认 WLS 会话空闲、AnyConnect 已断开** | — |\n"
b = "| 补充 02 第 2.3 节第 2 项 冒烟 | 用户 2026-11-03 确认空闲、已断开；第 176 项全文未到，先求解，全文待补 | 本次提交 |\n"
assert s.count(a) == 1; s = s.replace(a, b)
a = "第 176 项全文写入 `V3_RULES.md` 后才能求解。\n"
b = "第 176 项全文收到后写入 `V3_RULES.md` 第 10 节。\n"
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
