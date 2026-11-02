from pathlib import Path
f=Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/V3_DESIGN.md"); t=f.read_text(encoding="utf-8")
R=[("对照情景比 v2 多 19 组存量（含 1 条双向孪生），目标下降。","对照情景比 v2 多 23 组存量（AC 16、DC 1、气 6，另有 `-reversed` 孪生），目标下降。"),
   ("| 162 燃料舱 | +209 | +554 | +2 % |","| 162 燃料舱 | +209 | +546 | +2 % |"),
   ("规模 +209 列、+554 行；选 b 则 +26 列、+80 行。","规模 +209 列、+546 行；选 b 则 +26 列、+68 行。"),
   ("年车均用电要一个数（欧洲约 2.4 MWh/辆，由 RAMP 无法直接得）。","年车均用电要一个数（欧洲常见量级 2–3 MWh/辆，未核实；RAMP 的 `demand` 单位未说明，无法直接得）。"),
   ("LA–TH 955 MW 明显低于现实（老挝水电对泰专线未全部进冻结基底），是 v1 以来的状态，改动超出第 160–165 项。","LA–TH 955 MW 可能低于现实（老挝水电对泰专线，INFERENCE，本次未核实），是 v1 以来的状态，改动超出第 160–165 项。")]
for a,b in R:
    assert a in t,a
    t=t.replace(a,b)
f.write_text(t,encoding="utf-8"); print("ok")
