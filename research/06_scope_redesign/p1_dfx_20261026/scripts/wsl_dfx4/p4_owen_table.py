"""DFX phase 4: Owen dual-form (alpha main) table for the report, from DFX_PHASE4_RESULTS.json and BATCH3_REFERENCE_VALUES.json (exact values).
    python p4_owen_table.py <DFX_PHASE4_RESULTS.json> <BATCH3_REFERENCE_VALUES.json>"""
import json, sys
res = json.load(open(sys.argv[1])); ref = json.load(open(sys.argv[2]))
a = ref["batch3"]["owen_alpha_main_eur"]; fo = ref["first_order"]["by_country_bn"]
w1 = res["runs"]["V1"]["owen_alpha_main_eur"]; w2 = res["runs"]["V2"]["owen_alpha_main_eur"]
f = lambda x, s="{:.3f}": "—" if x is None else s.format(x)
print("| 参与者 | V1 份额 | V2 份额 | **受益 V2−V1** | R3 份额 | R4 份额 | 受益 R4−R3 | 受益 R2−R1 | 受益变化（对 R4−R3） | 一阶预测变化 |")
print("|---|---|---|---|---|---|---|---|---|---|")
t = dict(v1=0, v2=0, b=0, r3=0, r4=0, b34=0, b12=0)
for p in ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER"):
    v1, v2 = w1[p] / 1e9, w2[p] / 1e9; r3, r4 = a["R3"][p] / 1e9, a["R4"][p] / 1e9; b12 = (a["R2"][p] - a["R1"][p]) / 1e9
    b = v2 - v1; b34 = r4 - r3
    for k, v in (("v1", v1), ("v2", v2), ("b", b), ("r3", r3), ("r4", r4), ("b34", b34), ("b12", b12)): t[k] += v
    print(f"| {p} | {v1:.3f} | {v2:.3f} | **{b:+.3f}** | {r3:.3f} | {r4:.3f} | {b34:+.3f} | {b12:+.3f} | {b - b34:+.3f} | {f(fo.get(p), '{:+.3f}')} |")
print(f"| 合计 | {t['v1']:.3f} | {t['v2']:.3f} | **{t['b']:+.3f}** | {t['r3']:.3f} | {t['r4']:.3f} | {t['b34']:+.3f} | {t['b12']:+.3f} | {t['b'] - t['b34']:+.3f} | {sum(fo.values()):+.3f} |")
print()
print("objective constants (bn): V1", res["runs"]["V1"]["objective_eur"] / 1e9 - 268.430712, "V2", res["runs"]["V2"]["objective_eur"] / 1e9 - 282.884342)
print("11-country benefit sum", sum(w2[p] - w1[p] for p in w1 if p != "BUNKER") / 1e9)
