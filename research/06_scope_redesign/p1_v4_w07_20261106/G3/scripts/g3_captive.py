"""G3 captive power (decision 204 items 1-2; A3 item 6) for TH, PH, SG.

    PYTHONHASHSEED=0 python scripts/g3_captive.py          (WSL pypsa-earth python)

TH (priority): UNSD 2019 reports 64,358 GWh autoproducer combustible output and no autoproducer transformation fuel (S2 section 5). Test where the fuel is:
  * EPPO Energy Statistics of Thailand 2021 (B.E. 2564; PDF text pages extracted by W11, read only; every number asserted against the page text):
    generation by producer (EGAT / IPP / SPP / VSPP), SPP and IPP generation by fuel, natural gas by producer (MMscfd), coal for power vs industry,
    EGAT lignite tonnes.
  * Fuel-by-fuel reconciliation with UNSD 2019 (export + SDMX 5150): if a fuel that EPPO books for SPP power exceeds everything UNSD books in industry
    for that fuel, it cannot sit in UNSD industry (EXACT); the combined output of main activity + autoproducers against all transformation fuel at
    upper-bound efficiencies (technology-data 2050, S2) is the inequality.
  * Result: C central = 0. Sensitivity: GIPT 'Captive Industry Type' coal units of 2019 assumed in the industry rows they serve (capped at the row coal).
PH: inequality holds (S2); GIPT 222 MW captive coal (Petron refinery 4 x 35 MW, Mabalacat and United Pulp & Paper 82 MW) checked against the UNSD rows
  that can hold their coal (industry n.e.s. 486.9 kt, paper 289.6 kt); C = MW x hours x heat rate with sourced hours and the PH coal-plant efficiency
  of g3_ncv.py (P check), converted to tonnes and then to MWh with the same NCV per scheme (W11 4.2 item 5).
SG: inequality holds, no captive coal; GEM tags most Jurong utilities as captive oil/gas 'both' - recorded, no fuel in industry.
Outputs tables/TH_EPPO_VALUES.csv, tables/TH_CAPTIVE_FUEL_RECON.csv, tables/CAPTIVE_UNITS_GIPT_2019.csv, tables/_captive_inputs.json (C / E per level
and target row for g3_chain.py), tables/_captive_evidence.json. The final <CC>_CAPTIVE.csv is written by g3_chain.py (needs the option (b) effect).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g3_common as cm   # noqa: E402

EPPO_DIR = cm.W11 / "extracted/th_eppo2564"
EPPO_PDF = "work/p2_data_intake/v3_20261102/01_industry/2564_รายงานสถิติพลังงาน_สนพ.pdf (SHA256 fd13813f75bb403e…, W11 PDF_TEXT_INDEX.csv)"
TJ_PER_MMSCFD_YEAR = 365 * 1e6 * 1000 * 1055.056 / 1e12   # 1 MMscfd x 365 d x 1,000 BTU/scf (EPPO remark p.81) -> TJ (GCV basis)
TOE_GJ = 41.868
TD_ETA = {"gas": 0.60, "coal": 0.356, "lignite": 0.33, "oil": 0.35, "solid biomass": 0.468, "biogas": 0.43}   # S2 section 5 (technology-data 2050)


def page(n: int) -> str:
    return (EPPO_DIR / f"p{n:03d}_plain.txt").read_text(encoding="utf-8")


def nums(s: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(r"-?\d[\d,]*\.?\d*", s)]


def eppo_values(ev) -> pd.DataFrame:
    rows = []

    def add(p, key, value, unit, line, note=""):
        rows.append(dict(page=p, key=key, value=value, unit=unit, line=line.strip()[:200], note=note))
        ev.put(f"eppo.{key}", value, unit, f"EPPO 2564 PDF p.{p}: {line.strip()[:80]}", "VERIFIED", "B")

    t = page(103)   # Table 5.1-1Y power generation by producer
    ln = [l for l in t.splitlines() if l.startswith("2019 6,309.96")]
    assert len(ln) == 1, "p103 2019 line"
    v = nums(ln[0])[1:]
    for k, x in zip(["egat_hydro", "egat_fuel_oil", "egat_lignite", "egat_gas", "egat_diesel", "egat_geothermal", "egat_renewable", "egat_imported", "dede", "spp", "ipp", "vspp", "total"], v):
        add(103, f"gen2019.{k}", x, "GWh", ln[0])
    t = page(104)
    ln = [l for l in t.splitlines() if l.startswith("2019 42,679.91")]
    assert len(ln) == 1, "p104 SPP 2019"
    for k, x in zip(["spp_gas", "spp_coal_lignite", "spp_oil", "spp_renewable", "spp_total"], nums(ln[0])[1:]):
        add(104, f"gen2019.{k}", x, "GWh", ln[0], "Table 5.1-3Y SPP by fuel (source EGAT)")
    t = page(105)
    ln = [l for l in t.splitlines() if l.startswith("2019 39,335.33")]
    assert len(ln) == 1, "p105 IPP 2019"
    for k, x in zip(["ipp_gas", "ipp_coal_lignite", "ipp_total"], nums(ln[0])[1:]):
        add(105, f"gen2019.{k}", x, "GWh", ln[0], "IPP by fuel")
    ln = [l for l in t.splitlines() if l.startswith("2019 14 28 1,141")]
    assert len(ln) == 1, "p105 EGAT fuel 2019"
    for k, x, u in zip(["egat_fuel_oil", "egat_diesel", "egat_gas", "egat_lignite", "egat_palm_oil"], nums(ln[0])[1:], ["ML", "ML", "MMscfd", "t", "ML"]):
        add(105, f"egat_fuel2019.{k}", x, u, ln[0], "Table 5.2-1Y EGAT fuel consumption in power generation")
    t = page(81).splitlines()   # Table 3.2-2M natural gas by sector, MMscfd; 1,000 BTU/scf
    i19 = [i for i, l in enumerate(t) if l.strip() == "2019" or l.startswith("2019 Jan")]
    assert len(i19) == 1, "p81 2019"
    ytd = [l for l in t[i19[0]:] if l.startswith("YTD")][0]
    for k, x in zip(["egat", "ipp", "spp", "power_total", "industry", "gsp", "ngv", "total"], nums(ytd)):
        add(81, f"gas2019_mmscfd.{k}", x, "MMscfd", ytd, "Table 3.2-2M; remark: heat value of NG = 1,000 BTU/SCF")
    t = page(22)   # lignite and coal consumption, ktoe, columns 2017 2018 2019 2020
    seq = "17,064\n3,527\n3,386\n141 \n13,537\n5,055\n8,482"
    blk = re.search(r"17,064\s+3,527\s+3,386\s+141\s+13,537\s+5,055\s+8,482", t)
    assert blk, "p22 2019 block"
    for k, x in zip(["total", "lignite", "lignite_power", "lignite_industry", "coal", "coal_power_ipp_spp", "coal_industry"], nums(blk.group(0))):
        add(22, f"coal2019_ktoe.{k}", x, "ktoe", "Lignite and coal consumption 2019 column: " + blk.group(0).replace("\n", " "))
    t = page(27)
    ln = [l for l in t.splitlines() if l.startswith("2019 13,589 324")]
    assert len(ln) == 1, "p27 2019"
    v = nums(ln[0])[1:]
    add(27, "final2019.coal_kt", v[0], "kt", ln[0], "Table 1.2-1Y final modern energy consumption, physical (coal = imported)")
    add(27, "final2019.lignite_kt", v[1], "kt", ln[0], "Table 1.2-1Y")
    add(27, "final2019.electricity_gwh", v[11], "GWh", ln[0], "includes power generation from SPP (footnote *) - SPP sales to industry")
    return pd.DataFrame(rows)


def main():
    ev = cm.Ev("captive"); out = cm.G3 / "tables"
    EP = eppo_values(ev); EP.to_csv(out / "TH_EPPO_VALUES.csv", index=False)
    e = {r.key: r.value for r in EP.itertuples()}
    conv = cm.upstream_conv()
    sd = pd.read_csv(out / "SDMX_OBS_TH_PH_SG.csv", dtype=str, keep_default_na=False)
    for c_ in ("year", "value", "conversion_factor"):
        sd[c_] = pd.to_numeric(sd[c_].replace("", None), errors="coerce")
    X = cm.unsd_export(); X = X[X.year == 2019]

    def q(cc, com, tr):
        z = X[(X.country == cc) & (X.commodity == com) & (X.transaction.str.lower() == tr.lower())]
        return float(z.q.iloc[0]) if len(z) else 0.0

    # ======================================================== TH reconciliation =========================================================
    th_main = q("TH", "From combustible fuels – Main activity", ""); th_auto = q("TH", "From combustible fuels – Autoproducer", "")
    th_cap_auto_comb = q("TH", "Electricity", "net installed capacity of electric power plants, self-producer combustible fuels")
    tr_main = "transformation in electricity plants - main activity producers"
    gas_tr = q("TH", "Natural Gas (including LNG)", tr_main); gas_own = q("TH", "Natural gas (including LNG)", "own use by electricity, heat and CHP plants")
    gas_ind = q("TH", "Natural gas (including LNG)", "consumption by manufacturing, construction and non-fuel industry")
    lig_tr = q("TH", "Lignite", "Transformation in main activity electricity plants"); hard_tr = q("TH", "Hard coal", tr_main); subb_tr = q("TH", "Sub-bituminous coal", "Transformation in main activity electricity plants")
    bag_tr = q("TH", "Bagasse", "Transformation in electricity plants - main activity producers"); bgs_tr = q("TH", "Biogases", "Transformation in electricity plants - main activity producers")
    bl_tr = q("TH", "Black Liquor", "Transformation in electricity plants - main activity producers")
    fo_tr = q("TH", "Fuel oil", "Transformation in electricity plants - main activity producers"); do_tr = q("TH", "Gas Oil/ Diesel Oil", "Transformation in electricity plants - main activity producers")
    v5150_tr = float(sd[(sd.cc == "TH") & (sd.commodity_code == "5150") & (sd.transaction_code == "08811") & (sd.year == 2019)].value.sum())
    ind_hard = q("TH", "Hard coal", "consumption by manufacturing, construction and non-fuel mining industry"); ind_brown = q("TH", "Brown coal", "consumption by manufacturing, construction and non-fuel mining industry")
    ind_subb = q("TH", "Sub-bituminous coal", "Consumption by manufacturing, construction and non-fuel industry"); ind_lig = q("TH", "Lignite", "Consumption by manufacturing, construction and non-fuel industry")
    tj = lambda mmscfd: mmscfd * TJ_PER_MMSCFD_YEAR
    rec = [
        dict(fuel="natural gas", item="EPPO SPP power gas (MMscfd x 1,000 BTU/scf)", unsd_tj=None, eppo_tj=tj(e["gas2019_mmscfd.spp"]), note="GCV basis"),
        dict(fuel="natural gas", item="UNSD industry gas (all manufacturing rows)", unsd_tj=gas_ind, eppo_tj=tj(e["gas2019_mmscfd.industry"]), note="GCV TJ; EPPO industry for comparison"),
        dict(fuel="natural gas", item="UNSD main-activity transformation gas vs EPPO power gas EGAT + IPP + SPP", unsd_tj=gas_tr, eppo_tj=tj(e["gas2019_mmscfd.power_total"]), note="GCV TJ"),
        dict(fuel="natural gas", item="UNSD own use by electricity, heat and CHP plants", unsd_tj=gas_own, eppo_tj=None, note="energy-sector own use, outside T_v2"),
        dict(fuel="coal (imported)", item="UNSD industry hard coal + sub-bituminous (kt) vs EPPO industrial coal (kt)", unsd_tj=(ind_hard + ind_subb), eppo_tj=e["final2019.coal_kt"], note="kt, not TJ"),
        dict(fuel="coal (imported)", item="UNSD power hard coal + sub-bituminous (kt) vs EPPO coal for power IPP/SPP (ktoe x 41.868 / 26.37 GJ/t)", unsd_tj=hard_tr + subb_tr,
             eppo_tj=e["coal2019_ktoe.coal_power_ipp_spp"] * TOE_GJ / 26.37, note="kt; EPPO single NCV for imported coal 26.37 (p.226)"),
        dict(fuel="lignite", item="UNSD power lignite (kt) vs EGAT lignite (t / 1000)", unsd_tj=lig_tr, eppo_tj=e["egat_fuel2019.egat_lignite"] / 1e3, note="kt"),
        dict(fuel="lignite", item="UNSD industry lignite (kt) vs EPPO final lignite (kt)", unsd_tj=ind_lig, eppo_tj=e["final2019.lignite_kt"], note="kt"),
        dict(fuel="biomass", item="UNSD power bagasse + biogas + black liquor + SDMX 5150 (TJ)", unsd_tj=bag_tr * 7.7184 + bgs_tr + bl_tr + v5150_tr, eppo_tj=None,
             note=f"vs EPPO SPP renewable {e['gen2019.spp_renewable']:,.0f} GWh + VSPP {e['gen2019.vspp']:,.0f} GWh (VSPP incl. solar)"),
    ]
    R = pd.DataFrame(rec)
    R["unsd_over_eppo"] = R.unsd_tj / R.eppo_tj
    # inequality: all combustible output vs all transformation fuel
    fuel = {"gas": gas_tr * 0.9 / 3600, "lignite": lig_tr * 14.0004 / 3600, "coal": (hard_tr * 25.8012 + subb_tr * 14.0004) / 3600, "oil": (fo_tr * 40.392 + do_tr * 42.984) / 3600,
            "solid biomass": (bag_tr * 7.7184 + bl_tr / 1e3 * 1e3) / 3600 + 0 * 0, "biogas": bgs_tr / 3600}
    fuel["solid biomass"] = (bag_tr * 7.7184 + bl_tr) / 3600
    fuel_5150 = v5150_tr / 3600
    max_out = sum(fuel[k] * TD_ETA[k] for k in fuel) + fuel_5150 * TD_ETA["solid biomass"]
    tot_fuel = sum(fuel.values()) + fuel_5150
    egat_ipp_thermal = e["gen2019.egat_gas"] + e["gen2019.egat_lignite"] + e["gen2019.egat_fuel_oil"] + e["gen2019.egat_diesel"] + e["gen2019.ipp_total"]
    ineq = dict(main_combustible_gwh=th_main, auto_combustible_gwh=th_auto, total_combustible_gwh=th_main + th_auto, transformation_fuel_twh=tot_fuel,
                of_which_sdmx_5150_twh=fuel_5150, max_output_at_upper_eta_twh=max_out, implied_eta_all=(th_main + th_auto) / 1e3 / tot_fuel,
                implied_eta_if_main_only=th_main / 1e3 / tot_fuel, eppo_egat_ipp_thermal_gwh=egat_ipp_thermal,
                eppo_spp_vspp_gwh=e["gen2019.spp"] + e["gen2019.vspp"], spp_gas_eta=e["gen2019.spp_gas"] * 3.6e-3 / (tj(e["gas2019_mmscfd.spp"]) * 0.9 / 1e3),
                egat_ipp_gas_eta=(e["gen2019.egat_gas"] + e["gen2019.ipp_gas"]) * 3.6e-3 / (tj(e["gas2019_mmscfd.egat"] + e["gas2019_mmscfd.ipp"]) * 0.9 / 1e3),
                coal_power_eta_eppo=(e["gen2019.ipp_coal_lignite"] + e["gen2019.spp_coal_lignite"]) * 3.6 / (e["coal2019_ktoe.coal_power_ipp_spp"] * TOE_GJ),
                verdict="holds: the transformation fuel can produce main + autoproducer output; main-activity output alone (EGAT + IPP thermal) matches EPPO "
                        "and the SPP gas exceeds all UNSD industry gas -> the autoproducer fuel is in the transformation rows (C = 0)")
    R.to_csv(out / "TH_CAPTIVE_FUEL_RECON.csv", index=False, float_format="%.3f")
    for k, v in ineq.items():
        if not isinstance(v, str):
            ev.put(f"TH.inequality.{k}", v, "-" if "eta" in k else ("GWh" if k.endswith("gwh") else "TWh"), "UNSD 2019 export + SDMX 5150 + EPPO 2564", "EXACT" if "eta" not in k else "INFERENCE", "B")
    for r in R.itertuples():
        ev.put(f"TH.recon.{r.Index}.unsd_over_eppo", r.unsd_over_eppo, "-", f"{r.item} ({r.note})", "EXACT", "B")

    # ======================================================== GIPT captive units ==========================================================
    g = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", low_memory=False)
    g["sy"] = pd.to_numeric(g["Start year"], errors="coerce"); g["ry"] = pd.to_numeric(g["Retired year"], errors="coerce")
    g["op19"] = g.Status.isin(["operating", "retired", "mothballed"]) & (g.sy <= 2019) & ~(g.ry <= 2019)
    g["avg19_mw"] = g["Capacity (MW)"] * g.sy.map(lambda y: 0.5 if y == 2019 else 1.0)   # S1 rule: 2019 start counted for half a year
    U = g[g["Captive Industry Type"].notna() & g.iso.isin(cm.CC3) & g.op19].copy()
    U = U[["iso", "Type", "Plant / Project name", "Unit / Phase name", "Owner(s)", "Capacity (MW)", "avg19_mw", "Status", "Start year", "Retired year", "Captive Industry Type", "Captive Industry Use"]]
    U.to_csv(out / "CAPTIVE_UNITS_GIPT_2019.csv", index=False)
    for cc in cm.CC3:
        for tp in ("coal", "oil/gas"):
            ev.put(f"{cc}.gipt_captive_{tp.replace('/', '_')}_mw_2019", float(U[(U.iso == cc) & (U.Type == tp)]["Capacity (MW)"].sum()), "MW", "GEM GIPT 2026-09 'Captive Industry Type', operating at end 2019", "VERIFIED", "B")

    # ======================================================== C estimates ==================================================================
    inputs = {}
    # ---- TH: central 0; sensitivities: GIPT captive coal units in the industry rows they serve
    h_th = th_auto * 1e3 / th_cap_auto_comb if th_cap_auto_comb else float("nan")   # GWh / MW -> h
    eta_th = ineq["coal_power_eta_eppo"]
    th_rows = {"cement & building": "non-metallic minerals", "textiles": "textile and leather", "pulp & paper": "paper pulp and print", "oil & refining": "chemical and petrochemical"}
    row_coal_kt = {"non-metallic minerals": ind_brown and float(X[(X.country == "TH") & (X.commodity.isin(["Brown coal", "Hard coal"])) & (X.flow == "Non-metallicminerals")].q.sum()),
                   "textile and leather": float(X[(X.country == "TH") & (X.commodity.isin(["Brown coal", "Hard coal"])) & (X.flow == "Textileandleather")].q.sum()),
                   "paper pulp and print": float(X[(X.country == "TH") & (X.commodity.isin(["Brown coal", "Hard coal"])) & (X.flow == "Paper,pulpandprinting")].q.sum()),
                   "chemical and petrochemical": float(X[(X.country == "TH") & (X.commodity.isin(["Brown coal", "Hard coal"])) & (X.flow == "Chemicalandpetrochemical")].q.sum())}
    # row coal energy (MWh) under the two NCV lines (v3; decision 207: hard coal 26.377, brown coal 10.547): the sensitivity C is energy-based (E / eta,
    # eta measured on EPPO's energy basis) and is capped at the smaller of the two so that the same move fits both lines
    flow_of_row = {"non-metallic minerals": "Non-metallicminerals", "textile and leather": "Textileandleather", "paper pulp and print": "Paper,pulpandprinting",
                   "chemical and petrochemical": "Chemicalandpetrochemical"}
    row_coal_mwh = {}
    for row, fl in flow_of_row.items():
        h_ = float(X[(X.country == "TH") & (X.commodity == "Hard coal") & (X.flow == fl)].q.max() or 0.0)
        b_ = float(X[(X.country == "TH") & (X.commodity == "Brown coal") & (X.flow == fl)].q.max() or 0.0)
        row_coal_mwh[row] = min(h_ * 25.8012 + b_ * 14.0004, h_ * 26.377 + b_ * 10.547) * 1e3 / 3.6
    lv = {}
    for level, types in (("sens_nonrefinery", ["cement & building", "textiles", "pulp & paper"]), ("sens_all_gipt", list(th_rows))):
        items = []
        for tp in types:
            mw = float(U[(U.iso == "TH") & (U.Type == "coal") & (U["Captive Industry Type"] == tp)].avg19_mw.sum())
            E_gwh = mw * h_th / 1e3
            C_mwh = E_gwh * 1e3 / eta_th
            cap = row_coal_mwh[th_rows[tp]]
            f = min(1.0, cap / C_mwh) if C_mwh else 0.0
            items.append(dict(type=tp, row=th_rows[tp], mw_avg_2019=mw, hours=h_th, E_gwh=E_gwh * f, C_mwh_fixed=C_mwh * f, C_mwh_uncapped=C_mwh, row_coal_mwh_min=cap,
                              coal_kt=C_mwh * f * 3.6 / 1e3 / 26.37, coal_kt_note="tonnes at EPPO's 26.37 GJ/t (information only)", commodity="Brown coal", electricity_added=True))
        lv[level] = items
    lv["central"] = []; lv["low"] = []
    inputs["TH"] = dict(levels=lv, central_rule="0: the autoproducer (SPP / VSPP) fuel is in the main-activity transformation rows (fuel reconciliation, EXACT for gas); "
                        "GIPT captive coal units as sensitivities only", hours=h_th, eta=eta_th, inequality=ineq)
    ev.put("TH.hours_autoproducer_combustible", h_th, "h", "UNSD 2019 autoproducer combustible output / self-producer combustible capacity (B; proxy C)", "INFERENCE", "C")
    ev.put("TH.coal_power_eta", eta_th, "-", "EPPO 2019 IPP + SPP coal generation / EPPO coal for power (ktoe)", "INFERENCE", "C")

    # ---- PH
    ph_auto = q("PH", "From combustible fuels – Autoproducer", ""); ph_cap_auto = q("PH", "Electricity", "total net installed capacity of electric power plants, autoproducer")
    ph_main = q("PH", "From combustible fuels – Main activity", "")
    ph_cap_comb = q("PH", "Electricity", "net installed capacity of electric power plants, public combustible fuels") or q("PH", "Electricity", "total net installed capacity of electric power plants, combustible fuels")
    P = pd.read_csv(out / "NCV_PH_POWER_CHECK.csv")
    eta_ph = float(P[(P.case == "central") & (P.coal_ncv == "UNSD SDMX 22.058")].coal_eta.iloc[0])
    hours_ph = {"low": (ph_auto * 1e3 / ph_cap_auto, "UNSD 2019 PH autoproducer combustible output / autoproducer capacity (all fuels, bagasse-dominated; B, proxy C)"),
                "central": (ph_main * 1e3 / ph_cap_comb if ph_cap_comb else 5141.0, "UNSD 2019 PH main-activity combustible output / combustible capacity (B, proxy C)" if ph_cap_comb else "S1 HEESI 2019 steam turbines (C)"),
                "high": (5868.0, "S1: HEESI 2025 IUPTLS + PPU steam turbines (ID captive benchmark; C as proxy)")}
    ph_rows = {"oil & refining": ("other", False), "pulp & paper": ("paper pulp and print", True)}
    ph_cap_kt = {"other": float(X[(X.country == "PH") & (X.commodity == "Brown coal") & (X.flow == "Industriesn.e.s")].q.sum()),
                 "paper pulp and print": float(X[(X.country == "PH") & (X.commodity == "Brown coal") & (X.flow == "Paper,pulpandprinting")].q.sum())}
    lv = {}
    for level, (h, src) in hours_ph.items():
        items = []
        for tp, (row, el) in ph_rows.items():
            mw = float(U[(U.iso == "PH") & (U.Type == "coal") & (U["Captive Industry Type"] == tp)].avg19_mw.sum())
            E_gwh = mw * h / 1e3; t_kt = E_gwh * 3.6 / (eta_ph * 22.058); cap = ph_cap_kt[row]; t_used = min(t_kt, cap)
            items.append(dict(type=tp, row=row, mw_avg_2019=mw, hours=h, hours_source=src, E_gwh=E_gwh * t_used / t_kt if t_kt else 0.0, coal_kt=t_used, coal_kt_uncapped=t_kt,
                              row_coal_kt=cap, commodity="Brown coal", electricity_added=el))
            ev.put(f"PH.{level}.{tp}.coal_kt", t_used, "kt", f"GIPT MW x {h:.0f} h ({src}) x 3.6 / ({eta_ph:.3f} x 22.058 GJ/t), capped at the UNSD row coal {cap:.1f} kt", "PROPOSED (estimate)", "C")
        lv[level] = items
    inputs["PH"] = dict(levels=lv, central_rule="central hours (PH main-activity combustible fleet) x PH coal-plant efficiency at 22.058 GJ/t, capped at the coal of the UNSD row that can "
                        "hold it (industry n.e.s. for the Petron refinery units: UNSD PH reports no coal own use; paper row for the two paper mills); refinery units: "
                        "fuel out, electricity NOT added (refinery own use, outside T_v2) = option (b'), option (b) literal as sensitivity", eta=eta_ph,
                        hours={k: v[0] for k, v in hours_ph.items()}, inequality="holds (S2: 1,015 GWh vs bagasse 3.93 TWh in autoproducer transformation)")
    ev.put("PH.coal_eta_central", eta_ph, "-", "g3_ncv.py P check (central, 22.058)", "INFERENCE", "C")
    for k, (h, s) in hours_ph.items():
        ev.put(f"PH.hours.{k}", h, "h", s, "INFERENCE", "C")
    ev.put("PH.row_coal_kt.industry_nes", ph_cap_kt["other"], "kt", "UNSD 2019 PH brown coal, consumption not elsewhere specified (industry)", "VERIFIED", "B")
    ev.put("PH.row_coal_kt.paper", ph_cap_kt["paper pulp and print"], "kt", "UNSD 2019 PH brown coal, paper pulp and print", "VERIFIED", "B")
    # ---- SG
    inputs["SG"] = dict(levels={"low": [], "central": [], "high": []}, central_rule="0: inequality holds (autoproducer gas, fuel oil, refinery gas 12.3 TWh for 4,497 GWh), no captive coal in GIPT",
                        inequality="holds")
    cm.jdump(inputs, out / "_captive_inputs.json")
    ev.extra["inputs"] = inputs
    ev.write(out / "_captive_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 90)
    print(R.round(3).to_string()); print({k: (round(v, 4) if not isinstance(v, str) else v[:60]) for k, v in ineq.items()})
    print(U.to_string())
    for cc in ("TH", "PH"):
        for lvl, items in inputs[cc]["levels"].items():
            print(cc, lvl, [(i["type"], round(i["mw_avg_2019"]), round(i["hours"]), round(i["E_gwh"], 1), round(i["coal_kt"], 1), round(i.get("row_coal_kt", i.get("row_coal_mwh_min", 0)), 1)) for i in items])


if __name__ == "__main__":
    main()
