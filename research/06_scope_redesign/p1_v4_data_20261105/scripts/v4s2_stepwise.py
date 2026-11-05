"""V4 S2 section 4: the Indonesian 'other' bucket from v3 (80.8 %) to all corrections, step by step, with the fuelwood low value as a separate line.

    PYTHONHASHSEED=0 python scripts/v4s2_stepwise.py          (WSL pypsa-earth python; scratch chain, repository read only)

Main path = the cumulative steps of section 1 (s2/ID_S2_COMBINED.csv). Fuelwood-low line = the same steps with the UNSD 'fuelwood - n.e.s.
industry' row at its 2010-2017 mean (section 3, before the 2018 break), run in the scratch chain. The 30-40 % reference band (decision 203,
PyPSA-Eur Europe) is drawn only as a reference. Remaining-gap table: candidate sources with an indicative 2050 size where the data allow it
(fuelwood options and NIUPPER from chain runs; coal heating value (W11), IBS sub-sectors and sugar as 2019 energy x the bucket's own 2050
conversion per carrier, INFERENCE). Outputs s2/ID_OTHER_SHARE_STEPS.csv, s2/ID_OTHER_GAP_SOURCES.csv, s2/fig_s2_other_share_steps.png,
s2/_stepwise_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s2_common as cm   # noqa: E402

STEPS = [("v3", "v3", {}), ("+1", "1 captive b central", dict(b="central")), ("+2", "1+2", dict(b="central", ni="nf2023")),
         ("+3", "1+2+3", dict(b="central", ni="nf2023", cem=True)), ("+4", "1+2+3+4", dict(b="central", ni="nf2023", cem=True, steel=True)),
         ("+5", "all (1-5)", dict(b="central", ni="nf2023", cem=True, steel=True, prod=True))]
LABELS_ZH = {"v3": "v3", "+1": "+1 自备煤 (b)", "+2": "+2 镍 2023 基年", "+3": "+3 水泥 (ii)", "+4": "+4 钢（只换空间）", "+5": "+5 纸浆造纸、乙烯"}
BLUE, ORANGE = "#2a78d6", "#eb6834"   # dataviz reference palette slots 1-2 (validated, light mode)


def main():
    W = cm.WORK; out = W / "s2"; ev = cm.Ev("4")
    D = pd.read_csv(out / "ID_S2_COMBINED.csv").set_index("scenario")
    B = json.loads((out / "_biomass_evidence.json").read_text()); bv = {r["key"]: r["value"] for r in B["numbers"]}
    fw19 = bv["3.unsd2019.Fuelwood.Consumption not elsewhere specified (industry)"]; pre = bv["3.series.industry_mean_2010_2017_km3"]
    f_fw = bv["3.factor.Fuelwood"]   # TWh per thousand m3
    d_mwh = (fw19 - pre) * f_fw * 1e6
    import v4s2_chain as chn
    R = chn.Runner(); R.reproduce()
    rows = []
    for code, scen, kw in STEPS:
        m = D.loc[scen]
        lo = R.scenario(f"{scen} + fuelwood 2010-2017 mean", extra_moves=[("other", "biomass", d_mwh)], **kw)
        rows.append(dict(step=code, label=LABELS_ZH[code], scenario=scen, T_2050_twh=m.T_2050_twh, other_2050_twh=m.other_2050_twh, other_share=m.other_share,
                         step_delta_other_twh=None, fw_low_T_2050_twh=lo["T_2050_twh"], fw_low_other_2050_twh=lo["other_2050_twh"], fw_low_other_share=lo["other_share"]))
    R.ch.restore(); R.ch.unpatch()
    S = pd.DataFrame(rows)
    S["step_delta_other_twh"] = S.other_2050_twh.diff().fillna(0.0); S["step_delta_share_pp"] = (S.other_share.diff().fillna(0.0)) * 100
    S["fw_low_step_delta_other_twh"] = S.fw_low_other_2050_twh.diff().fillna(0.0)
    S["band_low_twh"] = 0.30 * S.T_2050_twh; S["band_high_twh"] = 0.40 * S.T_2050_twh
    S.to_csv(out / "ID_OTHER_SHARE_STEPS.csv", index=False, float_format="%.6f")
    for r in S.itertuples():
        for k in ("T_2050_twh", "other_2050_twh", "other_share", "step_delta_other_twh", "step_delta_share_pp", "fw_low_T_2050_twh", "fw_low_other_2050_twh", "fw_low_other_share"):
            ev.put(f"step.{r.step}.{k}", getattr(r, k), "-" if k.endswith("share") else ("pp" if k.endswith("pp") else "TWh"), "s2/ID_OTHER_SHARE_STEPS.csv (scratch chain)",
                   "EXACT" if r.step == "v3" and not k.startswith("fw") else "PROPOSED (quantified)", "C")
    # ---- remaining gap to the 30-40 % reference (combined case)
    allc = D.loc["all (1-5)"]; T = float(allc.T_2050_twh); O = float(allc.other_2050_twh)
    hb = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv").set_index("carrier")
    mult = float(pd.read_csv(cm.REPO / cm.D1_REL, keep_default_na=False).query("country == 'ID' and sector == 'Industry'").multiplier_total.astype(float).iloc[0])
    k = {c: mult * (0.9 * sum(float(hb.at[c, f"share_{u}"]) for u in ("low", "medium_a", "medium_b", "high")) + float(hb.at[c, "share_mechanical"])) for c in cm.FUELS}
    k["electricity"] = mult
    ev.put("conv.k_coal_from_bands", k["coal"], "TWh2050/TWh2019", "multiplier x (0.9 x heat shares + mechanical), INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv", "EXACT", "C")
    ev.put("conv.k_coal_from_step1", (float(-D.loc["1 captive b central"].d_T_2050_twh) + float(R.captive["central"][1]) / 1e6 * mult) / (R.captive["central"][0] / 1e6), "TWh2050/TWh2019",
           "(-dT step 1 + E x multiplier) / C", "EXACT", "C")
    for c, v in k.items():
        ev.put(f"conv.k_{c}", v, "TWh2050/TWh2019", "bucket conversion before the v3 scale", "EXACT", "C")
    SP = pd.read_csv(W / "s1/ID_OTHER_BUCKET_SPLIT_PROPOSED.csv")
    ibs = SP[SP.label.str.startswith("IBS 2019 attributable") & ~SP.label.str.contains("paper and printing")]
    ibs50 = float(sum(ibs[f"{c}_twh"].sum() * k[c] for c in cm.CARS19))
    sug = SP[SP.label.str.contains("bagasse")].iloc[0]; sug50 = float(sug.biomass_twh * k["biomass"])
    oc19 = float(allc.other_2019_coal_twh)
    FWO = pd.read_csv(out / "ID_FUELWOOD_OPTIONS.csv").set_index("candidate")
    gap = [dict(source="target band", item="'other' at 30 % / 40 % of T_v2 (combined case)", d2050_low_twh=0.30 * T - O, d2050_high_twh=0.40 * T - O, basis="decision 203: reference only, not a target",
                needs="-", status="EXACT"),
           dict(source="section 3", item="UNSD fuelwood row -> 2020-2021 mean / 2010-2017 mean / HEESI traded biomass",
                d2050_low_twh=float(FWO.loc["HEESI industrial biomass 2019 (traded only), firewood 2.2979 BOE/t"].all_other_2050_twh) - O,
                d2050_high_twh=float(FWO.loc["UNSD mean 2020-2021"].all_other_2050_twh) - O, basis="s2/ID_FUELWOOD_OPTIONS.csv (chain runs)", needs="user decision (section 3)", status="PROPOSED (quantified)"),
           dict(source="nickel unit energy", item="NIUPPER (26 MWh/t NPI gross) instead of Wei Case 3", d2050_low_twh=float(D.loc["all, nickel NIUPPER"].other_2050_twh) - O, d2050_high_twh=0.0,
                basis="s2/ID_S2_COMBINED.csv (chain run)", needs="NPI unit-energy literature (user)", status="PROPOSED (quantified)"),
           dict(source="coal heating value (W11)", item="remaining 'other' coal of 2019 at HEESI 24.67 / 20.29 GJ/t instead of 25.8", d2050_low_twh=-oc19 * (1 - 20.29 / 25.8) * k["coal"],
                d2050_high_twh=-oc19 * (1 - 24.67 / 25.8) * k["coal"], basis=f"other 2019 coal of the combined case {oc19:.2f} TWh x (1 - ratio) x k_coal {k['coal']:.3f}",
                needs="W11 (heating values); not changed in S2", status="INFERENCE (indicative)"),
           dict(source="sub-sectors in the UNSD 'other' row", item="IBS 2019 attributable food, textiles, wood, rubber, NMM w/o cement, machinery, transport eq., other manufacturing (lower bound)",
                d2050_low_twh=-ibs50, d2050_high_twh=-ibs50, basis="S1 split table x the bucket's 2050 conversion per carrier", needs="explicit routes for these sub-sectors (W07/W08); IBS covers 12 %",
                status="INFERENCE (indicative)"),
           dict(source="sub-sectors in the UNSD 'other' row", item="sugar mills (bagasse 13.38 TWh, v2 basis)", d2050_low_twh=-sug50, d2050_high_twh=-sug50,
                basis="S1 split table x k_biomass", needs="decision on an explicit sugar sub-sector", status="INFERENCE (indicative)"),
           dict(source="nickel MHP route", item="HPAL / MHP (180 kt Ni 2023, not in the v3 routes)", d2050_low_twh=float("nan"), d2050_high_twh=float("nan"),
                basis="no unit energy on disk", needs="HPAL unit-energy literature (user)", status="-"),
           dict(source="growth rule", item="uniform ATS multiplier 2.62 on the 2019 bucket vs physical-output growth of explicit products", d2050_low_twh=float("nan"), d2050_high_twh=float("nan"),
                basis="e.g. pulp/paper 2050 / 2019 energy = 2.08 vs 2.62", needs="W08 design choice", status="INFERENCE")]
    G = pd.DataFrame(gap); G.to_csv(out / "ID_OTHER_GAP_SOURCES.csv", index=False, float_format="%.6f")
    for r in G.itertuples():
        for kk in ("d2050_low_twh", "d2050_high_twh"):
            v = getattr(r, kk)
            if pd.notna(v):
                ev.put(f"gap.{r.source}.{r.item[:50]}.{kk}", v, "TWh", r.basis, r.status, "C")
    ev.put("gap.ibs_2019_twh", float(ibs.total_twh.sum()), "TWh", "s1/ID_OTHER_BUCKET_SPLIT_PROPOSED.csv block 3 without paper/printing", "VERIFIED (lower bound)", "B/C")
    ev.put("gap.other_2019_coal_combined", oc19, "TWh", "s2/ID_S2_COMBINED.csv", "EXACT", "C")
    pp19 = [r["value"] for r in json.loads((out / "_products_evidence.json").read_text())["numbers"] if r["key"] == "2.pp.2019.energy_total"][0]
    ev.put("gap.pulp_paper_growth_ratio", float(allc.sub_2050_pulp_paper_twh) / pp19, "-", "pulp/paper 2050 (explicit) / 2019 energy (section 2)", "EXACT", "C")
    # ---- figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fp = Path("/mnt/c/Windows/Fonts/simhei.ttf")
    if fp.exists():
        font_manager.fontManager.addfont(str(fp)); plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(fp)).get_name()
    plt.rcParams["axes.unicode_minus"] = False
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw=dict(width_ratios=[1.15, 1]))
    x = list(range(len(S)))
    for ax in (a1, a2):
        ax.set_facecolor("#fcfcfb"); ax.grid(axis="y", color="#e4e3df", lw=0.8); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_xticks(x); ax.set_xticklabels(S.label, rotation=20, ha="right", fontsize=9)
    a1.axhspan(30, 40, color="#d9d8d3", alpha=0.6, lw=0); a1.text(len(S) - 1, 35, "PyPSA-Eur 欧洲 30–40 %（只作参照）", ha="right", va="center", fontsize=8.5, color="#55544f")
    a1.plot(x, S.other_share * 100, color=BLUE, lw=2, marker="o", ms=8, label="主线（UNSD 燃料木材保留）")
    a1.plot(x, S.fw_low_other_share * 100, color=ORANGE, lw=2, marker="s", ms=8, ls="--", label="燃料木材低值（2010–2017 年均）")
    for xi, v in zip(x, S.other_share * 100):
        a1.annotate(f"{v:.1f}", (xi, v), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5, color="#2c2b28")
    a1.annotate(f"{S.fw_low_other_share.iloc[-1] * 100:.1f}", (x[-1], S.fw_low_other_share.iloc[-1] * 100), textcoords="offset points", xytext=(0, -15), ha="center", fontsize=8.5, color="#2c2b28")
    a1.set_ylim(25, 85); a1.set_ylabel("“其他”桶占 T_v2(ID) 的比例，2050（%）"); a1.set_title("（a）“其他”占比", loc="left", fontsize=11)
    a1.legend(frameon=False, fontsize=8.5, loc="lower left")
    w = 0.38
    a2.bar([i - w / 2 for i in x], S.other_2050_twh, width=w - 0.02, color=BLUE, label="主线")
    a2.bar([i + w / 2 for i in x], S.fw_low_other_2050_twh, width=w - 0.02, color=ORANGE, label="燃料木材低值")
    for i, v in zip(x, S.other_2050_twh):
        a2.text(i - w / 2, v + 15, f"{v:,.0f}", ha="center", fontsize=7.5, color="#2c2b28", rotation=90, va="bottom")
    a2.set_ylim(0, 1800); a2.set_ylabel("“其他”桶，2050（TWh）"); a2.set_title("（b）“其他”能量", loc="left", fontsize=11)
    a2.legend(frameon=False, fontsize=8.5, loc="upper right")
    fig.suptitle("印尼工业“其他”桶：从 v3 到 S2 全部修正（逐步累加，临时副本量化，未实施）", fontsize=12, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(out / "fig_s2_other_share_steps.png", dpi=150, facecolor="white"); plt.close(fig)
    ev.write(out / "_stepwise_evidence.json")
    pd.set_option("display.width", 250)
    print(S.round(3).to_string()); print(G.round(2).to_string()); print({c: round(v, 4) for c, v in k.items()})


if __name__ == "__main__":
    main()
