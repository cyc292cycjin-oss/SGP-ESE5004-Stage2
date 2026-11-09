"""W19a sections 2.1-2.2: KH_CO2_ACCOUNT.csv and evidence/KH_CAP_BRACKET.json.

Inputs (read only): the D2a extraction caches of the v3.1 2920x3h F1 / F2 solutions (SHA256 of the solved networks and dual files
checked = cache meta), cache/CO2_ACCOUNT_ALL_LONG.csv from w19a_1_kh_co2_account.py, the exported CO2_FLOWS.json, and
evidence/KH_NC_CROSSCHECK.json / KH_LINK_LIMITS.json from w19a_2*.py.

Bounds used (min LP, value function V(b) convex in the right-hand side b; y = dual of the cap, y <= 0):
  lower: V(b + db) - V(b) >= y * db                                   (first order is a lower bound on dZ; EXACT)
  upper: V(b + db) - V(b) <= -(cost removed by a feasible re-route)    (feasible point of the relaxed LP; EXACT given the
         re-route is feasible: KH sequestration links extendable, p_nom_max = inf, capital cost 0; storage annuity 30 EUR/t in
         KH and TH alike, so moving tonnes from the TH store to the KH store is cost neutral)
Neighbour re-routing beyond KH's own exports (VN, LA) is an estimate from node prices and route unit costs (INFERENCE).
"""
import json
from pathlib import Path

import pandas as pd

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109")
CACHE = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107/cache")
EXP = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_results_v31/unpacked/export")
RUNS = {"F1": "7508ec72ddce9a9d_v1", "F2": "4cc51892d748805f_v1"}
FIRST_ORDER = dict(source="work/p1_v4_d2b_20261108/rerank/IMPACT_FIRST_ORDER.csv (= D2a)", notch_low=1.8e6, notch_high=9.0e8,
                   dZ_F1=-9343344418.42972, dZ_F2=-11506309019.14156, dB6=-2162964600.7118397, owen_KH=-9343344418.43, rank=3,
                   w10_rank=259, w10_reading="global row only (dual -0): degenerate")


def main():
    lg = pd.read_csv(D / "cache" / "CO2_ACCOUNT_ALL_LONG.csv", keep_default_na=False)
    lg["value"] = pd.to_numeric(lg.value, errors="coerce").fillna(0.0)
    flows = {r: json.loads((EXP / r / "CO2_FLOWS.json").read_text()) for r in RUNS}
    nc = json.loads((D / "evidence" / "KH_NC_CROSSCHECK.json").read_text())
    links = {r: pd.read_csv(CACHE / k / "links.csv", index_col=0, low_memory=False) for r, k in RUNS.items()}
    rows = []

    def row(section, item, f1, f2, unit, tag, source, note=""):
        rows.append(dict(section=section, item=item, F1=f1, F2=f2, unit=unit, tag=tag, source=source, note=note))

    def kh(run, section=None, item=None, partner=None, note_contains=None):
        x = lg[(lg.run == run) & (lg.country == "KH")]
        if section is not None:
            x = x[x.section == section]
        if item is not None:
            x = x[x["item"] == item]
        if partner is not None:
            x = x[x.partner == partner]
        if note_contains is not None:
            x = x[x.note.str.contains(note_contains, regex=False)]
        return float(x.value.sum())

    src_cache = "D2a cache links.csv flow0 x efficiency (cache = solved nc, SHA256 checked); cross-checked by direct nc read (KH_NC_CROSSCHECK.json)"
    # A. capture and use at KH 'co2 stored' buses
    for car, cls in (("DAC", "DAC"), ("industry biomass boiler CC", "BECCS"), ("industry biomass CC", "BECCS"), ("biomass EOP CC", "BECCS"),
                     ("process emissions CC", "industrial CCS"), ("SMR CC", "industrial CCS"), ("CCGT CC", "power CCS")):
        v = [float(lg[(lg.run == r) & (lg.country == "KH") & (lg.section == "source") & (lg.note == car)].value.sum()) for r in RUNS]
        row("A capture into KH co2 stored", f"{cls}: {car}", v[0], v[1], "tCO2/a", "VERIFIED", src_cache)
    for car in ("methanolisation", "Fischer-Tropsch", "Sabatier"):
        v = [float(lg[(lg.run == r) & (lg.country == "KH") & (lg.section == "use") & (lg.note == car)].value.sum()) for r in RUNS]
        row("A capture into KH co2 stored", f"utilisation (CO2 use): {car}", v[0], v[1], "tCO2/a", "VERIFIED", src_cache)
    tot = [float(lg[(lg.run == r) & (lg.country == "KH") & (lg.section.isin(["source", "use"]))].value.sum()) for r in RUNS]
    row("A capture into KH co2 stored", "net capture (sources - use)", tot[0], tot[1], "tCO2/a", "EXACT", "sum of the rows above")
    # B. sinks
    inj = [-kh(r, section="sink") for r in RUNS]
    row("B sinks", "domestic injection (CO2 sequestration links -> co2 sequestered KH)", inj[0], inj[1], "tCO2/a", "VERIFIED", src_cache)
    cap = [nc[r]["stores"]["KH"]["e_nom_max"] for r in RUNS]
    row("B sinks", "injection cap co2_injection_cap_unified_KH (Store e_nom_max)", cap[0], cap[1], "tCO2/a", "VERIFIED",
        "solved nc stores_e_nom_max; registry value 1,800,000 (grade C, IJGGC 2014 low case / 50 a)")
    row("B sinks", "cap utilisation (Store e at last snapshot / e_nom_max)", nc["F1"]["stores"]["KH"]["e_last"] / cap[0], nc["F2"]["stores"]["KH"]["e_last"] / cap[1],
        "-", "VERIFIED", "solved nc stores_t_e")
    for p in ("TH", "LA", "VN"):
        v = [-kh(r, section="pipeline", item="export", partner=p) for r in RUNS]
        row("B sinks", f"pipeline export to {p}", v[0], v[1], "tCO2/a", "VERIFIED", src_cache)
    v = [kh(r, section="pipeline", item="import") for r in RUNS]
    row("B sinks", "pipeline import (all partners)", v[0], v[1], "tCO2/a", "VERIFIED", src_cache)
    v = [-kh(r, section="CO2 ship", item="export", partner="TH") for r in RUNS]
    row("B sinks", "ship export to TH (co2 sequestered TH)", v[0], v[1], "tCO2/a", "VERIFIED", src_cache)
    v = [-float(lg[(lg.run == r) & (lg.country == "KH") & (lg.section == "CO2 ship") & (lg["item"] == "export") & (lg.partner != "TH")].value.sum()) for r in RUNS]
    row("B sinks", "ship export to BN / ID / MY / PH / VN (sum)", v[0], v[1], "tCO2/a", "VERIFIED", src_cache)
    v = [float(lg[(lg.run == r) & (lg.country == "KH") & (lg.section.isin(["CO2 ship", "CO2 transit ship"])) & (lg["item"] == "import")].value.sum()) for r in RUNS]
    row("B sinks", "ship / transit-ship imports into KH co2 stored buses", v[0], v[1], "tCO2/a", "VERIFIED", src_cache)
    inflow_store = {}
    for r in RUNS:
        k = links[r]
        m = (k.bus1.astype(str) == "co2 sequestered KH") & (k.carrier.isin(["CO2 ship", "CO2 transit ship"]))
        inflow_store[r] = float((k[m].flow0 * k[m].efficiency).sum())
    row("B sinks", "ships of other countries into co2 sequestered KH (sum)", inflow_store["F1"], inflow_store["F2"], "tCO2/a", "VERIFIED",
        "cache links.csv: CO2 ship / transit ship with bus1 = co2 sequestered KH")
    v = [-kh(r, section="CO2 export extra-ASEAN") for r in RUNS]
    row("B sinks", "export extra-ASEAN", v[0], v[1], "tCO2/a", "VERIFIED", src_cache)
    v = [kh(r, section="check") for r in RUNS]
    row("B sinks", "balance residual of KH co2 stored buses", v[0], v[1], "tCO2/a", "EXACT", "sum of all port flows minus node buffer change")
    # C. duals and prices
    for key, lab in (("store_e_nom_upper", "Store-ext-e_nom-upper dual, co2 sequestered KH"), ("global_row", "global row research_co2_storage_cap-KH dual"),
                     ("country_co2_limit", "research_country_co2_limit-KH dual")):
        row("C duals", lab, nc["F1"]["duals"]["KH"][key], nc["F2"]["duals"]["KH"][key], "EUR/tCO2", "VERIFIED", "DUALS_BY_CONSTRAINT.nc (raw linopy sign)")
    td = [nc[r]["duals"]["KH"]["store_e_nom_upper"] + nc[r]["duals"]["KH"]["global_row"] for r in RUNS]
    row("C duals", "cap dual, total = global row + Store bound (decision 219)", td[0], td[1], "EUR/tCO2", "EXACT", "sum of the two rows")
    row("C duals", "dual difference F2 - F1", td[1] - td[0], td[1] - td[0], "EUR/tCO2", "EXACT", "")
    pr = [float(lg[(lg.run == r) & (lg.country == "KH") & (lg["item"] == "co2 sequestered bus price (EUR/t, time-weighted mean)")].value.sum()) for r in RUNS]
    row("C duals", "price of bus co2 sequestered KH (= -(30 + |cap dual|))", pr[0], pr[1], "EUR/tCO2", "VERIFIED", "cache buses.csv lam_mean")
    row("C duals", "co2 sequestered Store capital cost KH (= TH)", nc["F1"]["stores"]["KH"]["capital_cost"], nc["F2"]["stores"]["KH"]["capital_cost"], "EUR/(tCO2 a)",
        "VERIFIED", f"TH: {nc['F1']['stores']['TH']['capital_cost']} / {nc['F2']['stores']['TH']['capital_cost']}")
    # D. marginal route reconstruction
    k1, k2 = links["F1"], links["F2"]
    a = k1.at["CO2 pipeline KH2 0 -> KH2 2", "capital_cost"] / 8760.0
    b = k1.at["CO2 pipeline KH2 2 -> TH2 3", "capital_cost"] / 8760.0
    row("D marginal route", "F1: KH2 0 -> KH2 2 pipeline + KH2 2 -> TH2 3 pipeline, annuity per t at full use", a + b, None, "EUR/tCO2", "EXACT",
        f"{a:.4f} + {b:.4f}; equals the F1 cap dual (|y| = {abs(td[0]):.4f})")
    s0 = k2.at["KH2 0 co2 ship to TH", "marginal_cost"]
    row("D marginal route", "F2: KH2 0 -> co2 sequestered TH ship, marginal cost", None, s0, "EUR/tCO2", "EXACT", f"equals the F2 cap dual (|y| = {abs(td[1]):.4f})")
    util = k1.at["CO2 pipeline KH2 4 -> TH2 3", "flow0_pos"] / (k1.at["CO2 pipeline KH2 4 -> TH2 3", "p_nom_opt"] * 8760.0)
    row("D marginal route", "F1: KH2 4 -> TH2 3 pipeline utilisation (flow / (p_nom_opt x 8760))", util, None, "-", "EXACT", "")
    # E. bracket for the relaxation that ends KH's own exports
    exp1 = -kh("F1", section="pipeline", item="export") - float(lg[(lg.run == "F1") & (lg.country == "KH") & (lg.section == "CO2 ship") & (lg["item"] == "export")].value.sum())
    exp2 = -kh("F2", section="pipeline", item="export") - float(lg[(lg.run == "F2") & (lg.country == "KH") & (lg.section == "CO2 ship") & (lg["item"] == "export")].value.sum())
    db = max(exp1, exp2)
    xb1 = [n for n in ("CO2 pipeline KH2 2 -> TH2 3", "CO2 pipeline KH2 4 -> TH2 3", "CO2 pipeline KH2 1 -> TH2 1", "CO2 pipeline KH2 0 -> KH2 2")]
    ann1 = float((k1.loc[xb1, "capital_cost"] * k1.loc[xb1, "p_nom_opt"]).sum())
    ship2 = [n for n in k2.index if n.startswith("KH2") and "co2 ship to" in n]
    fr2 = float((k2.loc[ship2, "marginal_cost"] * k2.loc[ship2, "flow0"]).sum())
    lo1, lo2 = td[0] * db, td[1] * db
    row("E bracket (cap + db, db = KH exports)", "db = KH cross-border exports (max of F1, F2)", db, db, "tCO2/a", "EXACT", f"F1 {exp1:.1f}, F2 {exp2:.1f}")
    row("E bracket (cap + db, db = KH exports)", "lower bound dZ >= y * db", lo1, lo2, "EUR", "EXACT", "convexity of V(b)")
    row("E bracket (cap + db, db = KH exports)", "upper bound dZ <= -(transport cost removed by re-routing KH exports to KH storage)", -ann1, -fr2, "EUR", "EXACT",
        "F1: annuity of KH2 2->TH2 3, KH2 4->TH2 3, KH2 1->TH2 1, KH2 0->KH2 2 pipelines; F2: freight of KH2 * co2 ship to * links; storage annuity 30 EUR/t both sides")
    row("E bracket (cap + db, db = KH exports)", "dB6 = dZ(F2) - dZ(F1), interval", lo2 - (-ann1), -fr2 - lo1, "EUR", "EXACT", "[low, high] in the F1 / F2 columns")
    # F. neighbour re-routing beyond KH's exports (INFERENCE)
    vn1_exp = -float(lg[(lg.run == "F1") & (lg.country == "VN") & (lg.section == "pipeline") & (lg["item"] == "export")].value.sum())
    vn2_exp = -float(lg[(lg.run == "F2") & (lg.country == "VN") & (lg.section == "CO2 ship") & (lg["item"] == "export")].value.sum())
    vn_y = [nc[r]["duals"]["VN"]["store_e_nom_upper"] for r in RUNS]
    c_pipe = k1.at["CO2 pipeline KH2 0 -> VN2 0", "capital_cost"] / 8760.0
    c_ship = k2.at["VN2 0 co2 ship to KH", "marginal_cost"]
    sv1, sv2 = abs(vn_y[0]) - c_pipe, abs(vn_y[1]) - c_ship
    row("F neighbours (INFERENCE)", "VN cap dual (VN cap binding, 106.068 Mt/a)", vn_y[0], vn_y[1], "EUR/tCO2", "VERIFIED", "DUALS_BY_CONSTRAINT.nc")
    row("F neighbours (INFERENCE)", "VN cross-border exports (F1 pipeline VN2 3 -> LA2 3 -> TH2 1; F2 ship VN2 0 -> TH)", vn1_exp, vn2_exp, "tCO2/a", "VERIFIED", src_cache)
    row("F neighbours (INFERENCE)", "VN -> KH route unit cost (F1 pipeline VN2 0 - KH2 0 at full use; F2 ship VN2 0 -> KH)", c_pipe, c_ship, "EUR/tCO2", "EXACT", "cache links.csv")
    row("F neighbours (INFERENCE)", "saving per t if VN's exports go to a non-binding KH store", sv1, sv2, "EUR/tCO2", "INFERENCE", "|VN dual| - route cost")
    row("F neighbours (INFERENCE)", "VN re-routing saving (exports x saving per t)", -vn1_exp * sv1, -vn2_exp * sv2, "EUR", "INFERENCE", "linear estimate; no re-solve")
    la_save = 1.67 * 1.0e6
    row("F neighbours (INFERENCE)", "LA re-routing saving, upper estimate (F1 LA2 4 -> KH2 1 saves <= 1.67 EUR/t on <= 1 Mt; F2 none)", -la_save, 0.0, "EUR", "INFERENCE",
        "LA2 4 price -37.39 vs 30 + 5.72; LA2 3 cheaper to TH; F2 LA -> KH transit ship 25.6-28.7 EUR/t above LA's alternative")
    row("F neighbours (INFERENCE)", "other countries: PH, SG, MM, TL, ID, MY, BN, TH would not re-route (route to KH + 30 > |node price|)", 0.0, 0.0, "EUR", "INFERENCE",
        "node prices vs ship-to-KH marginal costs (w19a_explore_routes.py)")
    full1 = (lo1 - vn1_exp * sv1 - la_save, -ann1 - vn1_exp * sv1)
    full2 = (lo2 - vn2_exp * sv2, -fr2 - vn2_exp * sv2)
    row("G cap non-binding (INFERENCE)", "dZ when the KH cap no longer binds, [low, high] (F1 and F2 rows)", full1[0], full2[0], "EUR", "INFERENCE", f"high end F1 {full1[1]:.4g}, F2 {full2[1]:.4g}")
    row("G cap non-binding (INFERENCE)", "dZ high end", full1[1], full2[1], "EUR", "INFERENCE", "")
    row("G cap non-binding (INFERENCE)", "dB6 interval [low, high]", full2[0] - full1[1], full2[1] - full1[0], "EUR", "INFERENCE", "F1 column = low, F2 column = high")
    row("G cap non-binding (INFERENCE)", "cap level at which KH stops binding (1.8 + KH exports + VN exports [+ LA <= 1])", 1.8e6 + exp1 + vn1_exp + 1.0e6, 1.8e6 + exp2 + vn2_exp, "tCO2/a",
        "INFERENCE", "F1 includes the LA upper estimate")
    # H. first order used by W10 / D2a / D2b
    row("H first order (D2a / D2b rerank)", "notch: low = main 1.8 Mt/a, high = registered 900 Mt/a (45 Gt / 50 a, IJGGC 2014 hydrodynamic case)", FIRST_ORDER["notch_low"], FIRST_ORDER["notch_high"],
        "tCO2/a", "VERIFIED", FIRST_ORDER["source"], "F1 column = notch low, F2 column = notch high")
    row("H first order (D2a / D2b rerank)", "dZ = y x (900 - 1.8) Mt", FIRST_ORDER["dZ_F1"], FIRST_ORDER["dZ_F2"], "EUR", "VERIFIED", FIRST_ORDER["source"])
    row("H first order (D2a / D2b rerank)", "dB6 first order; Owen KH (F1 column)", FIRST_ORDER["owen_KH"], FIRST_ORDER["dB6"], "EUR", "VERIFIED", FIRST_ORDER["source"],
        "F1 column = Owen KH, F2 column = dB6")
    row("H first order (D2a / D2b rerank)", "overstatement factor |first-order dZ| / |dZ cap non-binding, high-magnitude end|", FIRST_ORDER["dZ_F1"] / full1[0], FIRST_ORDER["dZ_F2"] / full2[0], "-",
        "INFERENCE", "")
    # I. PH (conclusion only)
    ph_y = [nc[r]["duals"]["PH"]["store_e_nom_upper"] for r in RUNS]
    ph_exp = [float(flows[r]["intra_asean_shipping"].get("PH->MY", {}).get("t", 0.0)) for r in RUNS]
    ph_fr = [float(flows[r]["intra_asean_shipping"].get("PH->MY", {}).get("freight_eur", 0.0)) for r in RUNS]
    row("I PH (conclusion only)", "PH cap dual (cap 1.344 Mt/a binding; registry has no range)", ph_y[0], ph_y[1], "EUR/tCO2", "VERIFIED", "DUALS_BY_CONSTRAINT.nc")
    row("I PH (conclusion only)", "PH ship exports to MY", ph_exp[0], ph_exp[1], "tCO2/a", "VERIFIED", "CO2_FLOWS.json intra_asean_shipping PH->MY")
    row("I PH (conclusion only)", "PH freight to MY (= guaranteed saving if the PH cap rises by the export volume)", ph_fr[0], ph_fr[1], "EUR", "VERIFIED", "CO2_FLOWS.json")
    out = pd.DataFrame(rows)
    out.to_csv(D / "KH_CO2_ACCOUNT.csv", index=False)
    ev = dict(db=db, exports=dict(F1=exp1, F2=exp2), cap_dual=dict(F1=td[0], F2=td[1]), lower=dict(F1=lo1, F2=lo2), upper=dict(F1=-ann1, F2=-fr2),
              dB6_interval_own_exports=[lo2 + ann1, -fr2 - lo1], vn=dict(exports=[vn1_exp, vn2_exp], dual=vn_y, route=[c_pipe, c_ship], saving_per_t=[sv1, sv2]),
              cap_non_binding=dict(F1=full1, F2=full2, dB6=[full2[0] - full1[1], full2[1] - full1[0]]), first_order=FIRST_ORDER,
              ph=dict(dual=ph_y, exports=ph_exp, freight=ph_fr))
    (D / "evidence" / "KH_CAP_BRACKET.json").write_text(json.dumps(ev, indent=1), encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
    print(out[["section", "item", "F1", "F2", "unit", "tag"]].to_string())


if __name__ == "__main__":
    main()
