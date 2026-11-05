"""V4 W07 G0 item 3 (read only): does the repository biomass supply potential contain the residues that the closed-loop rule (decision 206
item 3) takes out of T_v2 - palm fibre, palm kernel shell, empty fruit bunches, black liquor, bark, bagasse - and would that double count the
in-mill own use?

    PYTHONHASHSEED=0 python scripts/v4g0_biomass_potential.py          (WSL pypsa-earth python; repository read only)

Reads research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv (written by scripts_project/d1_biomass.py), the IRENA 2017 Table R-3 factors the
script parsed (sources/IRENA2017_TABLE_R3_PARSED.csv), the constants of d1_biomass.py (by text, asserted), the s3_0 overflow columns of the
repository summary, and the S2 bottom-up in-mill estimates (s2/ID_BIOMASS_COMPARISON.csv, s2/ID_SUGAR_PALM_CHECK.csv). Nothing is changed.
Outputs ID_BIOMASS_POTENTIAL_CHECK.csv, evidence/_biomass_potential_evidence.json.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g0_common as cm   # noqa: E402

D1B = cm.REPO / "scripts_project/d1_biomass.py"
POT = cm.REPO / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv"
R3 = cm.REPO / "research_inputs/biomass_v5/sources/IRENA2017_TABLE_R3_PARSED.csv"


def main():
    ev = cm.Ev("biopot")
    src = D1B.read_text()
    need = {"PALM": 'PALM = dict(EFB=0.21, fibre=0.144, PKS=0.064, POME=0.583)', "LHV": "LHV_RESIDUE_GJ_T = 15.0", "PROCESS": "HARVEST_MAIN, HARVEST_HIGH, PROCESS = 0.25, 0.50, 0.90",
            "own_use": "mill self-consumption is not deducted here", "competing": "PKS and fibre are largely used as in-mill fuel today (competing use)"}
    lines = {k: next((i + 1 for i, l in enumerate(src.splitlines()) if v in l), None) for k, v in need.items()}
    if None in lines.values():
        raise SystemExit(f"d1_biomass.py text changed: {lines}")
    cats_in_code = sorted(set(re.findall(r'"(oil_palm_[a-z]+|[a-z]+_residues|msw_organic_biogas|logging_residues|wood_processing_residues)"', src)))
    has_bl = bool(re.search(r"black.?liquor", src, re.I)); has_bark = bool(re.search(r"\bbark\b", src, re.I))
    P = pd.read_csv(POT); P = P[P.country == "ID"].copy()
    for c in ("potential_main_mwh", "potential_low_mwh", "potential_high_mwh", "mass_main_t"):
        P[c] = pd.to_numeric(P[c], errors="coerce")
    r3 = pd.read_csv(R3); sc = r3[(r3.country == "ID") & (r3.commodity == "Sugar cane")].iloc[0]
    hf, pf = float(sc.hf), float(sc.pf)
    proc_share = pf * 0.90 / (hf * 0.25 + pf * 0.90)   # share of the sugarcane_residues mass that is process residue (bagasse), sugar cane only
    summ = pd.read_csv(cm.REPO / "research_inputs/demand_v5" / cm.SUMMARY).set_index("country").loc["ID"]
    pot_solid = float(P[P.feedstock_group != "biogas"].potential_main_mwh.fillna(0).sum())
    # S2 bottom-up in-mill use 2019 (INFERENCE, C)
    bc = pd.read_csv(cm.S2D / "s2/ID_BIOMASS_COMPARISON.csv")
    sp = pd.read_csv(cm.S2D / "s2/ID_SUGAR_PALM_CHECK.csv"); p19 = sp[(sp.check == "palm") & (sp.year == 2019)].iloc[0]
    g = lambda cat, col="potential_main_mwh": float(P[P.category == cat][col].iloc[0]) / 1e6 if (P.category == cat).any() else 0.0
    import json
    pe = {r["key"]: r["value"] for r in json.loads((cm.S2D / "s2/_products_evidence.json").read_text())["numbers"]}
    be = {r["key"]: r["value"] for r in json.loads((cm.S2D / "s2/_biomass_evidence.json").read_text())["numbers"]}
    bl19 = float(pe["2.pp.2019.black_liquor_etsap"])   # chemical + dissolving pulp x 22 GJ/t (ETSAP), S2 2.1
    bag19 = float(be["3.unsd2019.Bagasse.Consumption not elsewhere specified (industry)"]) * float(be["3.factor.Bagasse"])
    rows = [
        dict(residue="black liquor (chemical pulp)", d1_category="(none)", in_potential="no", potential_2050_main_twh=0.0, potential_2050_high_twh=0.0,
             unsd_id_2019="5140 not reported", in_T_v2_g0="no (pulp/paper biomass 2019 45.99, 2050 95.42 TWh closed loop, listed separately)",
             inmill_use_2019_twh_s2=bl19, overlap="none: neither in supply nor in T_v2 - consistent with the closed-loop rule",
             w08="none needed"),
        dict(residue="bark / wood chips used in pulp mills", d1_category="(none; FAOSTAT 'Wood residues' is the wood-processing category)", in_potential="no (bark not a category)",
             potential_2050_main_twh=0.0, potential_2050_high_twh=0.0, unsd_id_2019="5110 fuelwood may contain wood residues (IRES 511); no bark item",
             in_T_v2_g0="only if inside the UNSD fuelwood row (2010-2017 mean 74.95 TWh in G0)", inmill_use_2019_twh_s2=float("nan"),
             overlap="none on the supply side", w08="none needed"),
        dict(residue="oil palm mesocarp fibre", d1_category="oil_palm_fibre", in_potential="yes", potential_2050_main_twh=g("oil_palm_fibre"), potential_2050_high_twh=g("oil_palm_fibre", "potential_high_mwh"),
             unsd_id_2019="5150 not reported", in_T_v2_g0="no (closed loop; UNSD has no item)", inmill_use_2019_twh_s2=float(p19.fibre_twh),
             overlap="YES: fibre is burned in the mill boilers (S2 2.4, IRENA 2022 p.39; d1_biomass note 'competing use'); the in-mill heat is outside T_v2, so offering the fibre as free supply double counts it",
             w08="net the in-mill use out of the potential (fibre: practically all) or add the mill heat demand back; not both"),
        dict(residue="palm kernel shell (PKS)", d1_category="oil_palm_pks", in_potential="yes", potential_2050_main_twh=g("oil_palm_pks"), potential_2050_high_twh=g("oil_palm_pks", "potential_high_mwh"),
             unsd_id_2019="5150 not reported", in_T_v2_g0="no", inmill_use_2019_twh_s2=float(p19.shell_twh_15gj),
             overlap="PARTLY: part of the shell is burned in-mill, part is sold or exported (export volume not on disk); the in-mill part double counts",
             w08="net the in-mill share (data needed: PKS export / sales, MISSING_DATA)"),
        dict(residue="empty fruit bunches (EFB)", d1_category="oil_palm_efb", in_potential="yes", potential_2050_main_twh=g("oil_palm_efb"), potential_2050_high_twh=g("oil_palm_efb", "potential_high_mwh"),
             unsd_id_2019="5150 not reported", in_T_v2_g0="no", inmill_use_2019_twh_s2=0.0,
             overlap="low: EFB is mostly returned to the plantation as mulch, not a mill fuel (S2 2.4 counts fibre and shell only)", w08="keep; check mulch competition separately"),
        dict(residue="oil palm trunk (replanting)", d1_category="oil_palm_trunk", in_potential="yes", potential_2050_main_twh=g("oil_palm_trunk"), potential_2050_high_twh=g("oil_palm_trunk", "potential_high_mwh"),
             unsd_id_2019="-", in_T_v2_g0="no", inmill_use_2019_twh_s2=0.0, overlap="none (field residue)", w08="none"),
        dict(residue="palm oil mill effluent (POME, biogas)", d1_category="oil_palm_pome", in_potential="yes (biogas route)", potential_2050_main_twh=g("oil_palm_pome"),
             potential_2050_high_twh=g("oil_palm_pome", "potential_high_mwh"), unsd_id_2019="biogas: households only (525.5 TJ)", in_T_v2_g0="no",
             inmill_use_2019_twh_s2=float("nan"), overlap="small: captured POME biogas partly fuels mill engines; quantity not on disk", w08="note only"),
        dict(residue="bagasse (sugar mills)", d1_category=f"sugarcane_residues (process share {proc_share:.3f} of the category mass: IRENA R-3 sugar cane hf {hf:g} x 0.25, pf {pf:g} x 0.90)",
             in_potential="yes (inside sugarcane_residues)", potential_2050_main_twh=g("sugarcane_residues") * proc_share, potential_2050_high_twh=float("nan"),
             unsd_id_2019="5120 reported: 6,964.7 kt, 14.93 TWh (n.e.s. industry), in T_v2", in_T_v2_g0="yes (main); sensitivity 'bagasse closed loop' removes it",
             inmill_use_2019_twh_s2=bag19,
             overlap="not now: demand (UNSD bagasse in T_v2) and supply share the national biomass bus (d1_biomass own-use logic). Becomes a double count if bagasse is treated as closed loop without netting the supply",
             w08="if bagasse goes closed loop: remove the bagasse part of sugarcane_residues from the potential at the same time"),
        dict(residue="wood processing residues (sawdust, offcuts)", d1_category="wood_processing_residues", in_potential="yes", potential_2050_main_twh=g("wood_processing_residues"),
             potential_2050_high_twh=g("wood_processing_residues", "potential_high_mwh"), unsd_id_2019="inside 5110 fuelwood (IRES 511; INFERENCE)",
             in_T_v2_g0="yes, as far as inside the fuelwood row", inmill_use_2019_twh_s2=float("nan"),
             overlap="handled: d1_biomass does not deduct mill self-consumption because it sits in the UNSD industry biomass demand on the same bus",
             w08="none (keep consistent with the fuelwood-row decision)")]
    T = pd.DataFrame(rows)
    T["source"] = "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv (d1_biomass.py); S2 s2/ID_SUGAR_PALM_CHECK.csv / ID_BIOMASS_COMPARISON.csv for in-mill use"
    T.to_csv(cm.WORK / "ID_BIOMASS_POTENTIAL_CHECK.csv", index=False, float_format="%.6f")
    ev.put("d1_biomass.lines", 0, "-", "; ".join(f"{k} line {v}" for k, v in lines.items()), "VERIFIED", "-")
    ev.put("d1_biomass.has_black_liquor_category", int(has_bl), "bool", "regex over d1_biomass.py", "VERIFIED", "-")
    ev.put("d1_biomass.has_bark_category", int(has_bark), "bool", "regex over d1_biomass.py", "VERIFIED", "-")
    ev.put("potential.ID_solid_main_total", pot_solid / 1e6, "TWh", "BIOMASS_POTENTIAL_2050.csv ID non-biogas potential_main_mwh", "VERIFIED", "C")
    ev.put("potential.ID_s3_0_solid_potential_used", float(summ.solid_biomass_potential_main_mwh) / 1e6, "TWh", "repository summary solid_biomass_potential_main_mwh (s3_0 overflow test)", "VERIFIED", "C")
    for c in [x for x in summ.index if "overflow" in x]:
        ev.put(f"potential.ID_v3_{c}", float(summ[c]) / 1e6 if summ[c] == summ[c] else 0.0, "TWh", f"repository {cm.SUMMARY}", "VERIFIED", "C")
    ev.put("sugarcane.process_share", proc_share, "-", "IRENA 2017 R-3 ID sugar cane: pf x 0.90 / (hf x 0.25 + pf x 0.90)", "EXACT", "C")
    for r in P.itertuples():
        ev.put(f"potential.ID.{r.category}.main", (r.potential_main_mwh or 0) / 1e6 if r.potential_main_mwh == r.potential_main_mwh else 0.0, "TWh",
               f"BIOMASS_POTENTIAL_2050.csv; {str(r.potential_method)[:120]}", "VERIFIED", str(r.potential_tier))
    for r in T.itertuples():
        ev.put(f"row.{r.residue}.potential_2050_main", r.potential_2050_main_twh, "TWh", r.d1_category, "VERIFIED" if r.in_potential.startswith("yes") else "VERIFIED (absent)", "C")
    ev.extra.update(categories_in_code=cats_in_code, id_categories=P[["category", "feedstock_group", "potential_main_mwh", "status", "notes"]].astype(str).to_dict("records"),
                    s2_bottom_up=bc.astype(str).to_dict("records"))
    ev.write(cm.WORK / "evidence/_biomass_potential_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
    print(P[["category", "feedstock_group", "potential_main_mwh", "potential_high_mwh", "mass_main_t", "status"]].assign(main_twh=P.potential_main_mwh / 1e6).to_string())
    print(T[["residue", "in_potential", "potential_2050_main_twh", "potential_2050_high_twh", "inmill_use_2019_twh_s2"]].round(2).to_string())
    print("solid potential", pot_solid / 1e6, "proc share", proc_share, lines, has_bl, has_bark, cats_in_code)
    print(summ[[x for x in summ.index if "overflow" in x or "potential" in x]])


if __name__ == "__main__":
    main()
