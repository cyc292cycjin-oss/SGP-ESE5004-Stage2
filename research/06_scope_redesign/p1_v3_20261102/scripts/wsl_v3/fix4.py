from pathlib import Path
f=Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/V3_XB_STOCK_CHECK.md"); t=f.read_text(encoding="utf-8")
for a,b in (("| **合计** | **2,870** | 2,870 | | **29,760** | **+26,890** | S8 合计与 S4 文字的 29.75 GW 相符 |","| **合计** | **2,870** | 2,870 | | **29,750** | **+26,880** | S8 合计与 S4 文字的 29.75 GW 相符 |"),
            ("网络存量与 APG existing **逐条完全一致**（10 对）。","网络存量与 APG existing **逐条完全一致**（8 对）。")):
    assert a in t; t=t.replace(a,b)
f.write_text(t,encoding="utf-8")
