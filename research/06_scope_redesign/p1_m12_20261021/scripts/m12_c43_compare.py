"""M12 C4.3 (item 133): pipeline check on the pre-correction 365x24h results - compare the allocation module's outputs with the S4P settlement-rule
table (aspect 8, ASPECT8_B6_BY_RULE.csv: disconnected - integrated by country and rule, bn EUR). READ ONLY; numbers are not conclusions.

    python m12_c43_compare.py --c43 <evidence/c43> --s4p <work/p1_step4p_20261020> --out <evidence/c43>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--c43", type=Path, required=True); ap.add_argument("--s4p", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    I = json.loads((a.c43 / "s4n_integrated/ALLOCATION.json").read_text()); D = json.loads((a.c43 / "s4o_disconnected/ALLOCATION.json").read_text())
    B = json.loads((a.c43 / "benefit/BENEFIT.json").read_text())
    S = pd.read_csv(a.s4p / "ASPECT8_B6_BY_RULE.csv", encoding="utf-8").set_index("entity")
    col = {c[:4].strip(): c for c in S.columns}
    pD = D["allocation_eur"]["0.5"]; r = I["s4p_rules"]["by_country_eur"]
    ours = {"(i)": {c: (pD[c] - r[c]["i_current_alpha_half"]) / 1e9 for c in COUNTRIES},
            "(ii)": {c: (pD[c] - r[c]["ii_rent_to_importer"]) / 1e9 for c in COUNTRIES},
            "(iii)": {c: (pD[c] - r[c]["iii_rent_to_exporter"]) / 1e9 for c in COUNTRIES},
            "(v)": {c: (pD[c] - r[c]["v_length_split"]) / 1e9 for c in COUNTRIES}}
    same_prop = {"(ii) same proportion": {c: (pD[c] - r[c]["ii_rent_to_importer_same_proportion"]) / 1e9 for c in COUNTRIES},
                 "(iii) same proportion": {c: (pD[c] - r[c]["iii_rent_to_exporter_same_proportion"]) / 1e9 for c in COUNTRIES}}
    rows, dev = [], {}
    for k, v in ours.items():
        sc = S[col[k]] if k in col else S[[c for c in S.columns if c.startswith(k)][0]]
        d = {c: v[c] - float(sc[c]) for c in COUNTRIES}
        dev[k] = max(abs(x) for x in d.values())
        for c in COUNTRIES:
            rows.append(dict(rule=k, country=c, m12_bn=v[c], s4p_bn=float(sc[c]), difference_bn=d[c]))
    owen_i = {c: B["owen"]["benefit_eur"][c] / 1e9 for c in COUNTRIES}
    res = dict(inputs=dict(integrated=I["solve_dir"], integrated_sha256=I.get("solved_network_sha256"), disconnected=D["solve_dir"], disconnected_sha256=D.get("solved_network_sha256"),
                           s4p_table=str(a.s4p / "ASPECT8_B6_BY_RULE.csv")),
               network_versions="integrated = S4N pilot (365x24h, optimal, S4M-3 network); disconnected = S4O-6 (365x24h, suboptimal, same S4M-3 network build); both pre-correction",
               bunker_player=dict(integrated=I.get("bunker_player_present"), disconnected=D.get("bunker_player_present"),
                                  note="both networks have the bunker account (ASEAN_BUNKER); it is the 12th player here"),
               max_abs_difference_bn=dev, owen_alpha_half_equals_rule_i=max(abs(owen_i[c] - ours["(i)"][c]) for c in COUNTRIES),
               same_proportion_counterparts_bn=same_prop, rows=rows,
               identity=dict(integrated=I["identity"], disconnected=D["identity"]), checks=dict(integrated=I["checks"], disconnected=D["checks"]),
               label="pipeline check only; pre-correction results, numbers are not conclusions")
    (a.out / "C43_S4P_COMPARISON.json").write_text(json.dumps(res, indent=1))
    L = ["# C4.3 修正前结果流程跑通：与 S4P 结算规则表对照（只验证流程，数值不作结论）", "",
         f"- 一体化 = S4N 试点（365×24h，optimal）；不互联 = S4O-6（365×24h，suboptimal）；两者来自同一网络版本（S4M-3 构建），都是修正前结果。两网络都有燃料舱账户，本步作为第 12 个参与者。",
         f"- 本模块按 S4P 规则 (i)(ii)(iii)(v) 重算的分国差额（不互联 − 一体化）与 `ASPECT8_B6_BY_RULE.csv` 的最大绝对偏差（bn）：" + "，".join(f"{k} {v:.2e}" for k, v in dev.items()),
         f"- Owen（α 0.5）受益与规则 (i) 的最大偏差 {res['owen_alpha_half_equals_rule_i']:.2e} bn（同一账本规则，应为 0）。", "",
         "| 国 | (i) = Owen α 0.5 | S4P (i) | (ii) | S4P (ii) | (ii) 同比例 | (iii) | S4P (iii) | (iii) 同比例 | (v) | S4P (v) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in COUNTRIES:
        g = lambda k: float(S[[x for x in S.columns if x.startswith(k + " ")][0]][c])   # noqa: E731
        L.append(f"| {c} | {ours['(i)'][c]:.3f} | {g('(i)'):.3f} | {ours['(ii)'][c]:.3f} | {g('(ii)'):.3f} | {same_prop['(ii) same proportion'][c]:.3f} | {ours['(iii)'][c]:.3f} | {g('(iii)'):.3f} | "
                 f"{same_prop['(iii) same proportion'][c]:.3f} | {ours['(v)'][c]:.3f} | {g('(v)'):.3f} |")
    (a.out / "C43_S4P_COMPARISON.md").write_text("\n".join(L) + "\n")
    print(json.dumps(dict(max_abs_difference_bn=dev, owen_vs_i=res["owen_alpha_half_equals_rule_i"])))


if __name__ == "__main__":
    main()
