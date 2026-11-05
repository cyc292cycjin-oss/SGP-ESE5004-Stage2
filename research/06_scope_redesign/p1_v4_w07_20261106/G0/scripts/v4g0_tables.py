"""V4 W07 G0 item 5: the A6 unified tables for Indonesia (country code ID), built from the G0 chain results and the S1 / S2 / W11 deliverables.

    PYTHONHASHSEED=0 python scripts/v4g0_tables.py          (WSL pypsa-earth python; scratch chain for the captive-level runs; repository read only)

ID_SUBSECTORS_V4.csv   final main case (NCV 20.29, captive (b) central, nickel 2023 by product, cement (ii), steel spatial, pulp/paper closed loop,
                       ethylene incl. LINE, fuelwood 2010-2017 mean): activity, base year, 2019 deduction and row, 2050 carriers, closed-loop biomass
ID_CAPTIVE.csv         UNSD 2019 autoproducer inequality and option (b) at each NCV scheme x level (C re-converted from tonnes; E unchanged)
ID_BIOMASS_CHECK.csv   UNSD 2019 biomass items / flows, series notes, FAOSTAT comparison, proposed main and sensitivity
ID_NCV.csv             coal and other fuels: v3, UNSD country, national handbook, IPCC, physical evidence, proposed
ID_NODE_SHARES.csv     v4 against v3 node shares per sub-sector (steel, pulp/paper, ethylene changed; the rest unchanged)
ID_MISSING_DATA.csv    data the user could provide (nothing downloaded)
Also evidence/_tables_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g0_common as cm   # noqa: E402

W = cm.WORK
COLS = [("electricity", "elec"), ("heat", "heat_lt150"), ("heat_medium_a", "heat_150_200"), ("heat_medium_b", "heat_200_400"), ("heat_high", "heat_gt400"),
        ("oil", "oil"), ("gas", "gas"), ("coal", "coal"), ("biomass", "biomass"), ("hydrogen", "H2"), ("ammonia", "ammonia"), ("methanol", "methanol")]


def carriers(v: dict, scale: float = 1.0) -> dict:
    return {c: float(v.get(k, 0.0)) * scale / 1e6 for k, c in COLS}


def subsectors(ev):
    D = json.loads((W / "evidence/_chain_detail.json").read_text())
    x = D["details"]["by_product|207"]["8"]
    S = pd.read_csv(W / "ID_OTHER_SHARE_STEPS.csv"); fin = S[(S.path == "main") & (S.ncv_scheme.astype(str) == "207") & (S.step.astype(str) == "8")].iloc[0]
    pz = pd.DataFrame(x["pz"]); pz["mwh_2019"] = pz.mwh_2019.astype(float)
    rule = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country").loc["ID"]
    nfp = pd.read_csv(cm.REPO / "research_inputs/industry_v3/NONFERROUS_PRODUCTION_V3.csv"); nfp = nfp[nfp.country == "ID"].set_index("commodity")
    NU = pd.read_csv(W / "ID_NICKEL_UNIT_ENERGY.csv"); NU = NU[NU["mode"] == "by_product"].set_index("product")
    PPF = pd.read_csv(cm.S2D / "s2/ID_PULP_PAPER_FAOSTAT.csv")
    ETH = pd.read_csv(cm.S2D / "s2/ID_ETHYLENE.csv")
    r50 = pd.read_csv(cm.REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)
    tday = pd.read_csv(cm.REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")
    ec = x["explicit_carriers"]
    rows = []

    def add(sub, route, act_src, by, a_base, a_2050, sec_src, e19, row19, vec, closed=0.0, grade="C", note=""):
        r = dict(subsector=sub, route=route, activity_source=act_src, base_year=by, activity_base=a_base, activity_2050=a_2050, sec_source=sec_src,
                 energy_2019_deducted_TWh=e19, deducted_from_row=row19, energy_2050_TWh=sum(carriers(vec).values()) if vec else 0.0, **carriers(vec or {}),
                 closed_loop_biomass_TWh=closed, grade=grade, note=note)
        rows.append(r)
    st19 = float(pz[pz.subsector == "iron and steel"].mwh_2019.sum()) / 1e6
    add("steel", "2019: UNSD iron and steel row (unchanged); 2050: 30 % H2-DRI + EAF, 70 % scrap EAF (v3)", "worldsteel 2024 crude steel (t)", 2024,
        float(rule.steel_base_mt) * 1e6, float(rule.steel_2050_mt) * 1e6, "PyPSA-Eur v2025.07.0 2050 ratios (JRC-IDEES 2021)", st19,
        "UNSD iron and steel (replaced; at NCV 20.29 its hard coal 160 kt changes)", ec["steel"], grade="B/C",
        note="total unchanged; spatial allocation per S2 (2.81 Mt gap to the IMIP node, ID_NODE_SHARES.csv); 2050 carriers include the chlor-alkali H2 credit of the v3 decomposition")
    ce19 = float(pz[pz.subsector == "cement"].mwh_2019.sum()) / 1e6
    add("cement", "2019: kiln fuel on EDGAR clinker / 0.656, grinding electricity on USGS 2019 cement 71.9 Mt (correction ii); 2050: PyPSA-Eur cement", "USGS MYB 2023 cement (t)",
        int(rule.cement_base_year), float(rule.cement_base_mt) * 1e6, float(rule.cement_2050_mt) * 1e6, "PyPSA-Eur 'Cement' 0.8655 MWh/t (JRC-IDEES)", ce19,
        "'other' (ID has no UNSD non-metallic minerals row)", ec["cement"], grade="B/C", note="correction (ii) +1.52 TWh in 2019 'other' electricity")
    add("ammonia", "product load at the national bus (v3); feedstock gas deducted from NEU (DFX F2.4)", "USGS MYB 2022 nitrogen 2019 (t NH3)", int(rule.ammonia_base_year),
        float(rule.ammonia_base_mt) * 1e6, float(rule.ammonia_2050_mt) * 1e6, "5.166 MWh NH3 / t (product)", 0.0, "chemicals row: EU27 ammonia share not generated (DFX F2)", ec["ammonia"], grade="B")
    for com in ("nickel_npi_ni_content", "nickel_ferronickel_ni_content", "nickel_matte_ni_content"):
        u = NU.loc[com]
        vec = {"electricity": u.electricity_2050_twh * 1e6, "heat_high": u.heat_gt400_2050_twh * 1e6}
        add(f"nickel ({com.split('_')[1]})", f"Wei et al. 2020 {u.wei_case} (mining and auxiliary materials excluded); fuel -> >400 C useful heat x 0.90",
            "USGS MYB 2023 Indonesia table 1, Ni content (t)", 2023, float(u.q_2023_t_ni), float(u.q_2050_t_ni), f"Wei 2020 Table 8 / Table 3: el {u.electricity_mwh_per_t_ni:.3f}, fuel {u.fuel_mwh_per_t_ni:.3f} MWh/t Ni",
            0.0, "none (D163-6 a conservation: 'other' = T_v2 - explicit)", vec, grade="B (activity) / C (unit energy)",
            note="NPI on Case 4 (blast furnace) by the instruction; see ID_NICKEL_CHECKS.csv and ID_DECISIONS.md" if "npi" in com else "Case 3-FeNi (RKEF)")
    nsum = sum(ec["nonferrous_nickel"].values()) / 1e6; nrow = sum(NU.total_2050_twh)
    if abs(nsum - nrow) > 1e-6:
        raise SystemExit(f"nickel rows {nrow} != chain explicit nickel {nsum}")
    for key, com, sec in (("nonferrous_alumina", "alumina", "Alumina production"), ("nonferrous_aluminium_primary", "aluminium_primary", "Aluminium - primary production"),
                          ("nonferrous_copper", "copper_smelter", "Other non-ferrous metals")):
        add(key.replace("nonferrous_", ""), "v3 main (2019 base; not changed in W07)", "USGS MYB 2023 Indonesia table 1 (t)", 2019, float(nfp.at[com, "q_2019_t"]),
            float(nfp.at[com, "q_2019_t"]) * cm.growth(2019), f"PyPSA-Eur 2050 '{sec}'", 0.0, "none (conservation)", ec[key], grade="B/C")
    # pulp and paper by group (closed loop: only purchased energy explicit). S2 wrote ID_PULP_PAPER_FAOSTAT.csv with 6 significant digits, so the
    # group vectors are rescaled per carrier to the chain's explicit pulp/paper vector (exact; relative change < 1e-6)
    grp_vec = {}
    for grp, sec in (("pulp", "Pulp production"), ("paper", "Paper production")):
        q50_ = float(PPF[PPF.group == grp].q_2050_main_t.sum()); col_ = r50[sec]
        grp_vec[grp] = {"electricity": float(col_["elec"]) * q50_, "heat": float(col_["heat"]) * q50_, "gas": float(col_["methane"]) * q50_,
                        "coal": float(col_["coal"] + col_["coke"]) * q50_, "hydrogen": float(col_["hydrogen"]) * q50_}
    pp_scale = {k: (ec["pulp_paper"].get(k, 0.0) / s if s else 1.0) for k in grp_vec["pulp"] for s in [grp_vec["pulp"][k] + grp_vec["paper"][k]]}
    ev.put("sub.pulp_paper.rescale_max_rel", max(abs(v - 1) for k, v in pp_scale.items() if grp_vec["pulp"][k] + grp_vec["paper"][k]), "-",
           "group vectors from S2 FAOSTAT table (6 significant digits) rescaled to the chain vector", "EXACT", "-")
    for grp, sec in (("pulp", "Pulp production"), ("paper", "Paper production")):
        g = PPF[PPF.group == grp]
        q19, q50 = float(g.q_2019_t.sum()), float(g.q_2050_main_t.sum())
        col = r50[sec]; cars = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat"); tf = float(sum(col[c] for c in cars)); T = float(tday.at[sec, "today_total_mwh_per_t"])
        e19 = {c: float(col[c]) / tf * T * q19 for c in cars}
        purchased19 = (e19["elec"] + e19["heat"] + e19["coal"] + e19["coke"] + e19["methane"]) / 1e6
        v = {k: x * pp_scale[k] for k, x in grp_vec[grp].items()}
        add(f"pulp_paper ({grp})", "closed-loop rule (206-3): only purchased energy explicit; biomass (black liquor, bark) outside T_v2 and not deducted from 'other'",
            "FAOSTAT FO (t), base year = last year with new information per item", "per item (chemical pulp 2023 A; dissolving pulp 2021 E; most paper items 2017 X)",
            float(g.q_base_t.sum()), q50, f"2019: FAOSTAT 2019 x JRC-IDEES EU27 2019 today ({T:.3f} MWh/t), PyPSA-Eur structure; 2050: PyPSA-Eur 2050 '{sec}'", purchased19,
            "'other' (ID has no UNSD paper row): electricity from electricity, non-biomass heat spread over the bucket's coal / oil / gas", v,
            closed=float(col["biomass"]) * q50 / 1e6, note=f"2019 closed-loop biomass {e19['biomass'] / 1e6:.2f} TWh (not deducted); 2019 production {q19 / 1e3:,.0f} kt")
    pp_chain = sum(ec["pulp_paper"].values()) / 1e6; pp_rows = sum(r["energy_2050_TWh"] for r in rows if r["subsector"].startswith("pulp_paper"))
    if abs(pp_chain - pp_rows) > 1e-6:
        raise SystemExit(f"pulp/paper rows {pp_rows} != chain {pp_chain}")
    e25 = ETH[ETH.level.str.startswith("central, base 2025")].iloc[0]; ec19 = ETH[ETH.level == "central"].iloc[0]
    add("ethylene (HVC)", "energy use only (feedstock in NEU); 2050 PyPSA-Eur HVC without naphtha", "SFI 2025-12 capacity 2025 incl. LINE (860 + 1,000 kt ethylene) x 0.85 x HVC/ethylene 1.697",
        2025, float(e25.hvc_2050_t) / float(e25.growth_2019_2050), float(e25.hvc_2050_t), "JRC-IDEES EU27 HVC energy use 3.269 MWh/t (2019); PyPSA-Eur HVC 6.103 MWh/t (2050)",
        float(ec19.energy_2019_twh), "UNSD chemicals row (dispersed), spread rule; no effect on 'other'", ec["ethylene"], grade="C",
        note="2019 deduction = 860 kt x 0.85 (LINE not in 2019); excl. LINE 2050 13.79 TWh is a sensitivity")
    ch19 = float(pz[pz.subsector == "chemical and petrochemical"].mwh_2019.sum()) / 1e6
    add("dispersed (UNSD chemicals row remainder)", "UNSD row x EU27 weights x PyPSA-Eur (v3)", "UNSD 2019 chemicals row (energy)", 2019, None, None, "s3_0 fallback", ch19,
        "UNSD chemicals row after the ethylene deduction", ec["dispersed"], grade="C")
    o19 = float(pz[pz.subsector == "other"].mwh_2019.sum()) / 1e6
    add("other (residual)", "UNSD 'other' row after all deductions x ATS multiplier, useful-heat bands; v3 conservation scale", "UNSD 2019 n.e.s. industry (v2 basis after cement)",
        2019, None, None, "s3_0 bands (JRC-IDEES OIS shares)", o19, "-", x["other"], grade="C",
        note=f"other share of T_v2 {float(fin.other_share) * 100:.1f} %; 2019 v2-basis 'other' {o19:.2f} TWh")
    add("captive coal power (option b; transfer, not a sub-sector)", "2019: C leaves the UNSD 'other' coal, E enters 'other' electricity; multiplier unchanged", "GEM GIPT 2026-09 captive units (S1)",
        2019, None, None, "S1 central rule (nickel mid, others low)", float(fin.C_twh) - float(fin.E_twh), "'other' coal -C (at 20.29 GJ/t), electricity +E", None, grade="C",
        note=f"C {float(fin.C_twh):.2f} TWh coal, E {float(fin.E_twh):.2f} TWh electricity (2019)")
    add("fuelwood row (2010-2017 mean; transfer)", "UNSD 'fuelwood n.e.s. industry' 65,253 -> 29,510 thousand m3", "UNSD 2005-2022 series (S2 section 3)", 2019, 65253.0, 29509.6, "9.144 GJ/m3 (v3)",
        90.788325, "'other' biomass", None, grade="B/C", note="2020-2021 mean and UNSD 2019 as sensitivities")
    T = pd.DataFrame(rows)
    expl = sum(r["energy_2050_TWh"] for r in rows if not r["subsector"].startswith(("other", "captive", "fuelwood")))
    tv2 = expl + T[T.subsector == "other (residual)"].energy_2050_TWh.iloc[0]
    if abs(tv2 - float(fin.T_v2_2050_TWh)) > 1e-6:
        raise SystemExit(f"sub-sector sum {tv2} != T_v2 {fin.T_v2_2050_TWh}")
    T.to_csv(W / "ID_SUBSECTORS_V4.csv", index=False, float_format="%.6f")
    for r in T.itertuples():
        ev.put(f"sub.{r.subsector}.energy_2050", r.energy_2050_TWh, "TWh", "ID_SUBSECTORS_V4.csv (final main case)", "PROPOSED (quantified)", r.grade)
        ev.put(f"sub.{r.subsector}.energy_2019_deducted", r.energy_2019_deducted_TWh, "TWh", "ID_SUBSECTORS_V4.csv", "PROPOSED (quantified)", r.grade)
    ev.put("sub.check_sum_equals_T_v2", tv2, "TWh", "sum of explicit + other = T_v2 of the final main case", "EXACT", "C")
    return T, fin


def captive(ev):
    sys.path.insert(0, str(W / "scripts"))
    import v4g0_chain as gc   # noqa: E402
    R = gc.Runner()
    cap = pd.read_csv(cm.S2D / "s1/ID_CAPTIVE_COAL_2019.csv"); tot = cap[cap.group == "合计"].set_index("level"); ni = cap[cap.v3_subsector == "nickel"].set_index("level")
    af = pd.read_csv(cm.S2D / "s2/ASEAN11_AUTOPRODUCER_FUEL_2019.csv"); af = af[af.iso == "ID"]
    scr = pd.read_csv(cm.S2D / "s2/ASEAN11_CAPTIVE_SCREEN.csv").set_index("iso").loc["ID"]
    heesi_met = 10064.75; ni_fuel19_twh = 476738 * R.ne["fuel_mwh_per_t_ni"] / 1e6
    rows = []
    for ncv in ("207", "v3", "unsd", "ipcc"):
        F = cm.NCV[ncv]
        fuel = float(sum(r.twh * (F / cm.NCV_V3 if r.commodity == "Hard coal" else 1.0) for r in af.itertuples()))
        r0, _ = R.scenario(f"ncv only {ncv}", ncv=ncv)
        for lv in ("low", "central", "mid", "high"):
            r1, _ = R.scenario(f"ncv {ncv} + captive {lv}", ncv=ncv, captive=lv)
            C = R.captive[lv]["C_v3_mwh"] * F / cm.NCV_V3 / 1e6; E = R.captive[lv]["E_mwh"] / 1e6
            ni_coal_kt = float(ni.at[lv, "coal_kt"]); ni_proc_kt = ni_fuel19_twh * 1e6 / (F / 3.6) / 1e3
            rows.append(dict(ncv_scheme=ncv, ncv_gj_t=F, level=lv,
                             inequality_result=f"UNSD 2019 autoproducer combustible output {float(scr.autoproducer_combustible_gwh):,.0f} GWh > transformation fuel {fuel:.2f} TWh at 100 % (EXACT): violated",
                             autoproducer_fuel_twh=fuel, autoproducer_combustible_gwh=float(scr.autoproducer_combustible_gwh), gipt_captive_MW_2019=float(scr.gipt_captive_coal_2019_mw),
                             gipt_captive_MW_2019_avg=float(tot.at[lv, "mw"]), C_kt=float(tot.at[lv, "coal_in_industry_kt"]), C_TWh=C, E_TWh=E, eta_implied=E / C,
                             central_rule="nickel mid, all other sectors low (S1 cross-checks: HEESI pulp & paper coal sales, BPS paper self-generation, national top-down residual; tonnes and GWh, NCV-independent)",
                             option_b_effect_2050_T_v2_TWh=r1["T_v2_2050_twh"] - r0["T_v2_2050_twh"], option_b_effect_2050_other_TWh=r1["other_2050_twh"] - r0["other_2050_twh"],
                             industry_2019_change_TWh=-(C - E), nickel_coal_check_ratio=(ni_coal_kt + ni_proc_kt) / heesi_met,
                             nickel_coal_check_note=f"nickel captive coal {ni_coal_kt:,.0f} kt + Wei Case 3 process fuel 2019 {ni_fuel19_twh:.2f} TWh = {ni_proc_kt:,.0f} kt at {F:.2f} GJ/t vs HEESI iron, steel & metallurgy sales 10,065 kt"))
    R.ch.restore(); R.ch.unpatch()
    T = pd.DataFrame(rows); T.to_csv(W / "ID_CAPTIVE.csv", index=False, float_format="%.6f")
    for r in T.itertuples():
        for k in ("C_TWh", "E_TWh", "eta_implied", "option_b_effect_2050_T_v2_TWh", "autoproducer_fuel_twh", "nickel_coal_check_ratio"):
            ev.put(f"captive.{r.ncv_scheme}.{r.level}.{k}", getattr(r, k), "TWh" if k.endswith("TWh") or k.endswith("twh") else "-", "ID_CAPTIVE.csv (scratch chain; S1 tonnes)",
                   "EXACT" if k == "autoproducer_fuel_twh" else "PROPOSED (quantified)", "C")
    return T


def biomass_check(ev):
    U = pd.read_csv(cm.S2D / "s2/ID_BIOMASS_UNSD_2019.csv")
    B = {r["key"]: r["value"] for r in json.loads((cm.S2D / "s2/_biomass_evidence.json").read_text())["numbers"]}
    f = {"Fuelwood": B["3.factor.Fuelwood"], "Bagasse": B["3.factor.Bagasse"], "Charcoal": B["3.factor.Charcoal"], "Biodiesel": B["3.factor.Biodiesel"]}
    SE = pd.read_csv(cm.S2D / "s2/ID_FUELWOOD_SERIES.csv").set_index("year")
    keep = [("Fuelwood", "Consumption not elsewhere specified (industry)"), ("Fuelwood", "Consumption by chemical and petrochemical"), ("Fuelwood", "Consumption by households"),
            ("Fuelwood", "Production"), ("Fuelwood", "Imports"), ("Fuelwood", "Exports"), ("Fuelwood", "Final energy consumption"), ("Bagasse", "Consumption not elsewhere specified (industry)"),
            ("Charcoal", "Consumption not elsewhere specified (industry)"), ("Biodiesel", "Consumption not elsewhere specified (industry)"), ("Biogases", "Consumption by Households")]
    rows = []
    for com, fl in keep:
        z = U[(U.commodity == com) & (U.transaction == fl)].iloc[0]
        twh = float(z.q) * f[com] if com in f else float(z.q) / 3600.0
        note, fao, pm, ps = "", "", "keep (UNSD 2019)", ""
        if com == "Fuelwood" and fl.startswith("Consumption not"):
            note = (f"footnote '{z.footnote}'; 2005-2017 {SE.loc[2005:2017].unsd_industry_nes_km3.min():,.0f}-{SE.loc[2005:2017].unsd_industry_nes_km3.max():,.0f}, 2018 {SE.at[2018, 'unsd_industry_nes_km3']:,.0f}, "
                    f"2019 {SE.at[2019, 'unsd_industry_nes_km3']:,.0f}, 2020 {SE.at[2020, 'unsd_industry_nes_km3']:,.0f}, 2021 {SE.at[2021, 'unsd_industry_nes_km3']:,.0f}, 2022 {SE.at[2022, 'unsd_industry_nes_km3']:,.0f} thousand m3; "
                    f"households fell {SE.at[2017, 'unsd_households_km3']:,.0f} -> {SE.at[2018, 'unsd_households_km3']:,.0f} in 2018 (reallocation, INFERENCE)")
            fao = f"FAOSTAT wood fuel (non-coniferous, E) 2019 {SE.at[2019, 'fao_wood_fuel_km3']:,.0f} thousand m3 for all uses; UNSD production / FAO = {SE.at[2019, 'unsd_production_over_fao']:.2f} (FAO excludes processing residues)"
            pm = f"2010-2017 mean {B['3.series.industry_mean_2010_2017_km3']:,.0f} thousand m3 ({B['3.series.industry_mean_2010_2017_km3'] * f['Fuelwood']:.2f} TWh)"
            ps = f"2020-2021 mean {B['3.series.industry_mean_2020_2021_km3']:,.0f} ({B['3.series.industry_mean_2020_2021_km3'] * f['Fuelwood']:.2f} TWh); UNSD 2019 {float(z.q):,.0f} ({twh:.2f} TWh)"
        elif com == "Fuelwood" and fl == "Consumption by households":
            note = "halved in 2018 while industry doubled; residential side is W12 / buildings scope"; pm = "not changed in G0"
        elif com == "Fuelwood" and fl in ("Imports", "Exports"):
            note = "UNSD fuelwood trade only in 2018-2019"; fao = "FAOSTAT wood fuel trade 2019 < 1 thousand m3 (S2 3.2)"; pm = "-"
        elif com == "Fuelwood":
            pm = "-"
        elif com == "Bagasse":
            note = f"footnote '{z.footnote}'; production = n.e.s. industry; 0.239 t per t cane (2010-2022 0.19-0.31)"
            fao = "FAOSTAT sugar cane 2019 29.1 Mt (X) x IRENA 2017 process factor 0.2 = 5.82 Mt (UNSD 1.20x)"
            pm = "keep in T_v2 (sugar-mill heat; supply potential holds the same bagasse on the same bus)"
            ps = "closed loop like black liquor and palm residues (-35.24 TWh T_v2 2050); then net bagasse out of the supply potential too"
        elif com == "Charcoal":
            pm = "keep"
        elif com == "Biodiesel":
            pm = "keep (B20 blending)"
        rows.append(dict(commodity=com, flow=fl, unit=z.Unit, q_2019=float(z.q), value_2019=twh, value_unit="TWh", series_note=note, faostat_compare=fao, proposed_main=pm,
                         proposed_sensitivity=ps))
    rows.append(dict(commodity="Black liquor (5140)", flow="all", unit="-", q_2019=0.0, value_2019=0.0, value_unit="TWh", series_note="not reported for ID (UNSD code list has 5140)",
                     faostat_compare="bottom-up 51.99 TWh (chemical + dissolving pulp x 22 GJ/t, ETSAP; S2)", proposed_main="closed loop: outside T_v2; pulp/paper biomass listed separately (2019 45.99, 2050 95.42 TWh)",
                     proposed_sensitivity="S2 spread rule (biomass in T_v2): -109.10 TWh 'other' vs main"))
    rows.append(dict(commodity="Other vegetal material and residues (5150)", flow="all", unit="-", q_2019=0.0, value_2019=0.0, value_unit="TWh", series_note="not reported for ID",
                     faostat_compare="palm mills: fibre 130.2 TWh, shell 56.5-57.9 TWh (FFB 217 Mt x IRENA 2022 Box 4 x 15 GJ/t; S2)", proposed_main="closed loop: outside T_v2 (not in UNSD, so no deduction)",
                     proposed_sensitivity="net the in-mill use out of the supply potential (ID_BIOMASS_POTENTIAL_CHECK.csv)"))
    T = pd.DataFrame(rows); T.to_csv(W / "ID_BIOMASS_CHECK.csv", index=False, float_format="%.6f")
    for r in T.itertuples():
        ev.put(f"biomass.{r.commodity}.{r.flow}", r.value_2019, "TWh", "UNdata 2019 export x pypsa-asean factor (S2 tables; the S2 column 'twh' of ID_BIOMASS_UNSD_2019.csv holds PWh)", "VERIFIED", "B")
    return T


def ncv_table(ev):
    PL = pd.read_csv(cm.W11D / "ncv/NCV_ID_COAL_PLAUSIBILITY.csv").set_index("ncv_label").pln_eta
    ref = pd.read_csv(cm.W11D / "ncv/NCV_FACTOR_SCHEMES.csv"); ref = ref[ref.country == "ID"]
    pe = "; ".join(f"PLN 2019 0.5607 t/MWh -> efficiency {v * 100:.1f} % at {k}" for k, v in PL.items())
    rows = [dict(commodity="Hard coal (all ID industry flows)", unit="GJ/t", v3=cm.NCV_V3, unsd_country=24.4800154511, national="HEESI 2019: Kalimantan coal 4.2 BOE/t = 24.666 (before 2023); HEESI 2025: average coal 3.4554 BOE/t = 20.293 (from 2023)",
                 ipcc="sub-bituminous 18.9 (11.5-26.0); other bituminous 25.8", physical_evidence=pe + "; GIPT operating coal units of known rank 84 % sub-bituminous; APEC 2022 ID other bituminous 20.10",
                 proposed="20.29 (decision 207 item 2) main; UNSD 24.48 and IPCC 18.9 sensitivities; v3 25.80 second full set",
                 effect_2019_TWh=-285.03 * (1 - 20.29 / cm.NCV_V3), effect_note="hard coal 39,770 kt; 2050 T_v2 -140.89 TWh (step alone, reading I), -47.70 TWh (reading II)"),
            dict(commodity="Coke-oven coke", unit="GJ/t", v3=28.20024, unsd_country=28.2, national="-", ipcc="28.2", physical_evidence="-", proposed="unchanged", effect_2019_TWh=0.0, effect_note="578.1 kt in industry"),
            dict(commodity="Brown coal briquettes", unit="GJ/t", v3=20.7, unsd_country=20.7, national="HEESI 2019 3.5638 BOE/t = 20.93", ipcc="20.7", physical_evidence="-",
                 proposed="unchanged (+1.1 %, outside industry)", effect_2019_TWh=0.0, effect_note="W11 (c)"),
            dict(commodity="Fuelwood", unit="GJ/m3", v3=9.144, unsd_country=9.14, national="HEESI 2.2979 BOE/t = 13.50 GJ/t (mass basis)", ipcc="wood 15.6 GJ/t (mass basis)",
                 physical_evidence="-", proposed="unchanged; volume decided first (S2 section 3 / fuelwood step)", effect_2019_TWh=0.0, effect_note="volume, not NCV, is the issue"),
            dict(commodity="Charcoal", unit="GJ/t", v3=29.484, unsd_country=29.5, national="HEESI 4.9713 BOE/t = 29.195", ipcc="29.5", physical_evidence="-", proposed="unchanged", effect_2019_TWh=0.0, effect_note="-1 %"),
            dict(commodity="Bagasse", unit="GJ/t", v3=7.718, unsd_country=7.72, national="-", ipcc="other primary solid biomass 11.6", physical_evidence="supply side d1_biomass 15 GJ/t (inconsistent; W12)",
                 proposed="unchanged on the demand side; W08 to unify with supply", effect_2019_TWh=0.0, effect_note="wet basis about 50 % moisture"),
            dict(commodity="Natural gas", unit="TJ (GCV) x 0.90", v3=0.9, unsd_country=0.9, national="-", ipcc="48.0 GJ/t", physical_evidence="UN balance TJ = export x standard (W11)", proposed="unchanged", effect_2019_TWh=0.0, effect_note=""),
            dict(commodity="Oil products", unit="GJ/t", v3=None, unsd_country=None, national="-", ipcc="= UNSD standard", physical_evidence="UN balance TJ = export x standard (W11)", proposed="unchanged", effect_2019_TWh=0.0, effect_note="")]
    T = pd.DataFrame(rows); T.to_csv(W / "ID_NCV.csv", index=False, float_format="%.6f")
    for r in ref.itertuples():
        ev.put(f"ncv.w11.{r.commodity}.{r.scheme}", float(r.gj_per_unit), "GJ/t", f"W11 NCV_FACTOR_SCHEMES.csv: {r.source}", str(r.status), str(r.grade))
    for k, v in PL.items():
        ev.put(f"ncv.pln_eta.{k}", float(v), "-", "W11 NCV_ID_COAL_PLAUSIBILITY.csv (PLN 2019 67,008,829 t / 119,520 GWh)", "INFERENCE", "C")
    return T


def node_shares(ev):
    import geopandas as gpd
    sys.path.insert(0, str(cm.S2D / "scripts"))
    v3s = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv"); v3s = v3s[v3s.country == "ID"]
    rows = []
    st = pd.read_csv(cm.S2D / "s2/ID_STEEL_NODE_SHARES_S2.csv")
    for r in st.itertuples():
        rows.append(dict(subsector="steel", node=r.node, share_v4=r.main, share_v3=r.v3_share, diff_pp=(r.main - r.v3_share) * 100,
                         note="S2 main: facility output / capacity x u <= 1, worldsteel 2024 gap 2.81 Mt to the IMIP node; v3 by capacity"))
    pp = pd.read_csv(cm.S2D / "s2/ID_PULP_PAPER_NODES.csv")
    for r in pp.itertuples():
        if r.pp_share_main > 0 or r.v3_other_share > 0:
            rows.append(dict(subsector="pulp_paper", node=r.node, share_v4=r.pp_share_main, share_v3=r.v3_other_share, diff_pp=r.diff_pp * 100,
                             note="new sub-sector: SFI 2025-07 mills (pulp by capacity x 0.666, paper by capacity, unknown mills equal); v3 column = 'other' share it leaves"))
    import v4s1_facilities as f1   # noqa: E402  (node_of only)
    regions = gpd.read_file(cm.MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
    E = pd.read_csv(cm.S2D / "s2/ID_ETHYLENE_UNITS_SFI.csv"); E = E[E.uid.isin(["GEPDIDN0001", "GEPDIDN0002"])].copy()
    E["lat"], E["lon"] = E.latitude.astype(float), E.longitude.astype(float)
    E["node"], E["how"] = f1.node_of(E, regions)
    E["w"] = E.cap.astype(float)
    en = E.groupby("node").w.sum() / E.w.sum()
    dsp = v3s[v3s.subsector == "dispersed"].set_index("node").share
    for n_ in sorted(set(en.index) | set(dsp[dsp > 0].index)):
        rows.append(dict(subsector="ethylene", node=n_, share_v4=float(en.get(n_, 0.0)), share_v3=float(dsp.get(n_, 0.0)), diff_pp=(float(en.get(n_, 0.0)) - float(dsp.get(n_, 0.0))) * 100,
                         note=f"new sub-sector: SFI CAP (860 kt) + LINE (1,000 kt) by capacity, node by point in region ({'; '.join(E.how.unique())}); v3 column = 'dispersed' (chemicals row) share"))
    for sub in sorted(v3s.subsector.unique()):
        if sub in ("steel",):
            continue
        for r in v3s[v3s.subsector == sub].itertuples():
            note = "unchanged (v3 allocation)"
            if sub == "nonferrous_nickel":
                note = "unchanged: v3 allocation kept for the 2023 base and Case 4; growth after 2019 at Weda Bay / Obi (North Maluku) not reflected (INFERENCE)"
            if sub == "other":
                note = "unchanged (DOSE 2019 manufacturing output x node electricity share)"
            rows.append(dict(subsector=sub, node=r.node, share_v4=r.share, share_v3=r.share, diff_pp=0.0, note=note))
    T = pd.DataFrame(rows); T.to_csv(W / "ID_NODE_SHARES.csv", index=False, float_format="%.6f")
    for sub, g in T.groupby("subsector"):
        if abs(g.share_v4.sum() - 1) > 1e-6 and sub not in ("pulp_paper", "ethylene"):
            raise SystemExit(f"{sub} shares sum {g.share_v4.sum()}")
        ev.put(f"node.{sub}.sum_v4", float(g.share_v4.sum()), "-", "ID_NODE_SHARES.csv", "EXACT", "-")
        ev.put(f"node.{sub}.max_abs_diff_pp", float(g.diff_pp.abs().max()), "pp", "ID_NODE_SHARES.csv", "PROPOSED (quantified)", "C")
    return T


def missing(ev):
    rows = [dict(item="Chandra Asri annual report 2019 (cracker throughput) and LOTTE LINE start-up status", purpose="replace the utilisation assumption 0.85; confirm LINE 2025 operation",
                 url_if_known="https://www.chandra-asri.com (investor relations, annual reports)", priority="medium"),
            dict(item="Nickel unit energy closer to Indonesian RKEF NPI (11-14 % Ni) and HPAL / MHP (Norgate & Jahanshahi 2011; Nickel Institute LCA; Wei et al. other cases)",
                 purpose="choose between Wei Case 3 (RKEF FeNi) and Case 4 (blast-furnace NPI) for NPI; MHP route", url_if_known="", priority="high"),
            dict(item="IMIP / IWIP 2019-2023 output by product (NPI, stainless, matte) and park power allocation", purpose="split captive power between nickel and stainless steel; check Case 4",
                 url_if_known="", priority="medium"),
            dict(item="Palm kernel shell exports and in-mill fuel use (GAPKI, BPS, ERIA)", purpose="net the in-mill PKS from the supply potential (closed-loop rule)", url_if_known="", priority="high"),
            dict(item="APKI pulp and paper energy statistics (fuel by type incl. coal for boilers)", purpose="check the purchased fuel of pulp and paper (closed loop: 0.66 TWh non-biomass in 2019)",
                 url_if_known="", priority="medium"),
            dict(item="UNSD methodology note on Indonesian fuelwood estimates (2018 reallocation)", purpose="fuelwood main value", url_if_known="https://unstats.un.org/unsd/energystats/", priority="medium"),
            dict(item="UNSD SDMX CONVERSION_FACTOR for ID hard coal (UNSD 2019 country value)", purpose="confirm 24.48 (W11 derivation) as the UNSD sensitivity; not needed for the 20.29 main",
                 url_if_known="https://data.un.org/WS/rest/ (same interface as unsd_targeted)", priority="low"),
            dict(item="UN Comtrade HS 2523 clinker / cement trade ID 2019", purpose="clinker ratio (cement correction ii)", url_if_known="https://comtradeplus.un.org", priority="low"),
            dict(item="HEESI coal NCV by consumer (industry vs PLN) or ESDM coal quality statistics", purpose="physical evidence for 20.29 vs 24.48 in industry (PLN evidence only)", url_if_known="", priority="medium")]
    T = pd.DataFrame(rows); T.to_csv(W / "ID_MISSING_DATA.csv", index=False)
    ev.put("missing.items", len(T), "items", "ID_MISSING_DATA.csv", "VERIFIED", "-")
    return T


def main():
    ev = cm.Ev("tables")
    S, fin = subsectors(ev); C = captive(ev); B = biomass_check(ev); N = ncv_table(ev); ND = node_shares(ev); M = missing(ev)
    ev.write(W / "evidence/_tables_evidence.json")
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 50)
    print(S[["subsector", "energy_2019_deducted_TWh", "energy_2050_TWh", "elec", "heat_gt400", "closed_loop_biomass_TWh"]].round(3).to_string())
    print(C[["ncv_scheme", "level", "C_TWh", "E_TWh", "eta_implied", "option_b_effect_2050_T_v2_TWh", "autoproducer_fuel_twh", "nickel_coal_check_ratio"]].round(3).to_string())
    print(B[["commodity", "flow", "q_2019", "value_2019"]].round(3).to_string())
    print(ND[ND.subsector.isin(["ethylene"])].round(4).to_string())


if __name__ == "__main__":
    main()
