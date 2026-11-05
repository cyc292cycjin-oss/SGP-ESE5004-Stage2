"""G3 NCV (decision 207) for TH, PH, SG: UNSD SDMX country values, national handbooks, IPCC defaults and physical evidence.

    PYTHONHASHSEED=0 python scripts/g3_ncv.py          (WSL pypsa-earth python)

Rule (decision 207): default = UNSD country NCV (W11 scheme (b)); where two or more independent pieces of physical evidence conflict with it, use
the evidence value and keep the UNSD value as sensitivity. MY / TH / LA: UNSD SDMX CONVERSION_FACTOR (sdmx/, A5). For TH the SDMX response gives two
sets: parent rows (Hard coal 26.377, Brown coal 10.547 on consumption and transformation flows) and child rows (IPCC defaults: sub-bituminous 18.9,
lignite 11.9, other bituminous 25.8, anthracite 26.7). The model base uses the parent rows (reconstruct_base_accounts: children already in the parent),
so the UNSD country value applied to the model quantity is the parent value (it also reproduces W11's balance-derived TH production factor 10.504).
Physical evidence (only data on disk):
  K  cement-kiln heat balance 2019: fuels of the UNSD non-metallic-minerals row (coal at each scheme, biomass incl. SDMX 5150) per t clinker against the
     kiln range 2.9 GJ/t (ETSAP BAT thermal, route map) to 4.2 GJ/t (2.9 x ODA non-metallic fuel factor 1.792 / 1.24, see code) - clinker between
     EDGAR 2.A.1 / 0.52 and 0.95 x USGS cement (upper bound of the clinker in domestic cement, clinker trade not on disk);
  S  coal tonnes of the non-metallic row per t USGS cement 2015-2021 (TH): the 2018 reclassification of ~9.5 Mt imported coal from 'hard coal' to
     'sub-bituminous' keeps the tonnes per t cement (0.21-0.25 t/t) but changes UNSD's energy by ~60 %, so only one NCV level is physically consistent;
  P  power-sector check (PH): main-activity combustible output 84,021 GWh against the main-activity fuels; gas at CCGT 0.50-0.57, oil 0.35-0.40 -> the
     coal plants' implied efficiency at each coal NCV against the technology-data 2050 coal efficiency 0.356 (upper bound for 2019 plants).
Outputs <CC>_NCV.csv, tables/NCV_KILN_BALANCE.csv, tables/NCV_TH_NMM_SERIES.csv, tables/NCV_PH_POWER_CHECK.csv, tables/_ncv_evidence.json and
tables/_ncv_schemes.json (factor dictionaries used by g3_chain.py). Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g3_common as cm   # noqa: E402

# schemes (GJ per t; key = commodity as in the UNdata export / BASE_RECONSTRUCTION)
SCHEMES = {
    "TH": {"207": {"Hard coal": 26.377, "Brown coal": 10.547},                                            # UNSD SDMX parent rows (consumption flows)
           "sens_children_ipcc": {"Sub-bituminous coal": 18.9, "Lignite": 11.9, "Other bituminous coal": 25.8, "Anthracite": 26.7},   # SDMX children = IPCC
           "sens_eppo": {"Sub-bituminous coal": 26.37, "Other bituminous coal": 26.37, "Anthracite": 31.4, "Lignite": 18.2}},          # EPPO / DEDE
    "PH": {"207": {"Brown coal": 22.058}, "sens_ipcc_subbit": {"Brown coal": 18.9}, "sens_apec": {"Brown coal": 22.098}},
    "SG": {"207": {}},
}
KILN_BAT = 2.9            # GJ/t clinker thermal, ETSAP v2.1.0 BAT (S0 route map / COVERAGE_ETSAP_BAT_SEC.csv)
ODA_NMM_FUEL = 1.792      # ETSAP ODA non-metallic minerals fuel factor (S0 4.6), used only to bound a statistical upper kiln value
TD_ETA = {"coal": 0.356, "gas_ccgt": 0.60}   # technology-data v0.15.0 2050 efficiencies (S2 section 5; upper bounds for 2019 plants)


def main():
    ev = cm.Ev("ncv"); out = cm.G3 / "tables"
    conv = cm.upstream_conv()
    sd = pd.read_csv(cm.G3 / "tables/SDMX_OBS_TH_PH_SG.csv", dtype=str, keep_default_na=False)   # transaction code 'NA' (final consumption) is a code
    for c_ in ("year", "value", "conversion_factor"):
        sd[c_] = pd.to_numeric(sd[c_].replace("", None), errors="coerce")
    usgs = pd.read_csv(cm.G3 / "tables/USGS_TABLE1_TH_PH.csv")
    cem = usgs[usgs.item == "cement_hydraulic"].set_index(["country", "year"]).value_t
    S = pd.read_csv(cm.REPO / "research_inputs/demand_v5" / cm.SUMMARY).set_index("country")
    E = cm.export_2019_flows()
    ref = pd.read_csv(cm.W11 / "ncv/NCV_REFERENCE_VALUES.csv")
    rm = pd.read_csv(cm.S2W / "evidence/COVERAGE_ETSAP_BAT_SEC.csv") if (cm.S2W / "evidence/COVERAGE_ETSAP_BAT_SEC.csv").exists() else None
    ev.put("kiln.bat_thermal", KILN_BAT, "GJ/t clinker", "ETSAP v2.1.0 BAT clinker heat 2.9 GJ/t (S0 V4_DATA_SCOPE 4.6)", "VERIFIED", "C")
    kiln_hi = KILN_BAT * ODA_NMM_FUEL / 1.24   # 4.19: ODA fuel factor applies to the whole NMM sector (cement + lime + glass + ceramics); /1.24 removes
    # the non-cement share of EU-type NMM fuel (INFERENCE, rough); used only as an upper plausibility bound
    ev.put("kiln.upper_bound", kiln_hi, "GJ/t clinker", "2.9 x ODA NMM fuel factor 1.792 / 1.24 (rough statistical upper bound, INFERENCE)", "INFERENCE", "C")

    def sdmx_cf(cc, code, tr="1214B", year=2019):
        z = sd[(sd.cc == cc) & (sd.commodity_code == code) & (sd.transaction_code == tr) & (sd.year == year)]
        return (float(z.conversion_factor.iloc[0]), float(z.value.iloc[0])) if len(z) else (None, 0.0)

    rows_k, rows_n = [], []
    # ------------------------------------------------------------------ K: kiln balance (TH, PH) -------------------------------------------------
    for cc in ("TH", "PH"):
        nmm = E[(E.country == cc) & (E.flow == "Non-metallicminerals")].set_index("commodity").q
        clk_edgar = float(S.at[cc, "clinker_2019_t"]) / 1e6; clk_hi = 0.95 * float(cem[(cc, 2019)]) / 1e6
        bio = 0.0
        for com, code in (("Fuelwood", "5110"), ("Biogases", None), ("Bagasse", "5120")):
            if com in nmm.index:
                bio += float(nmm[com]) * (conv[com] * 1e6 * 3.6 / 1e3 if com in conv else 0.0) / 1e3 if com != "Biogases" else float(nmm[com]) / 1e3
        v5150 = float(sd[(sd.cc == cc) & (sd.commodity_code == "5150") & (sd.transaction_code == "1214B") & (sd.year == 2019)].value.sum()) / 1e3   # PJ (TJ in SDMX)
        oth = {"gas_pj": float(nmm.get("Natural gas (including LNG)", nmm.get("Natural Gas (including LNG)", 0.0))) * 0.9 / 1e3}
        schemes = {"v3": {}} | {k: v for k, v in SCHEMES[cc].items()}
        for sname, fac in schemes.items():
            sch = cm.NCV(sname, {(cc, k): v for k, v in fac.items()})
            pj = 0.0; parts = []
            for com in ("Hard coal", "Brown coal", "Coke-oven coke", "Coke Oven Coke"):
                if com in nmm.index and (com in conv or com == "Coke Oven Coke"):
                    c_ = "Coke-oven coke" if com == "Coke Oven Coke" else com
                    if com == "Coke Oven Coke" and "Coke-oven coke" in nmm.index:
                        continue
                    e = sch.energy(cc, c_, float(nmm[com]), "Non-metallicminerals", E) * 3.6 / 1e6   # PJ
                    pj += e; parts.append(f"{com} {float(nmm[com]):.1f} kt = {e:.2f} PJ")
            for clk_name, clk in (("EDGAR", clk_edgar), ("0.95 x USGS cement", clk_hi)):
                spec_solid = (pj + bio + v5150) / clk
                rows_k.append(dict(country=cc, ncv_scheme=sname, clinker_basis=clk_name, clinker_mt=clk, coal_pj=pj, biomass_export_pj=bio, sdmx_5150_pj=v5150,
                                   solid_fuel_gj_per_t_clinker=spec_solid, coal_only_gj_per_t_clinker=pj / clk, kiln_bat=KILN_BAT, kiln_upper=kiln_hi,
                                   verdict=("below BAT: coal NCV too low" if spec_solid < KILN_BAT else ("above upper bound: coal NCV too high" if spec_solid > kiln_hi else "inside the physical range")),
                                   coal_detail="; ".join(parts), gas_pj_not_counted=oth["gas_pj"]))
    K = pd.DataFrame(rows_k); K.to_csv(out / "NCV_KILN_BALANCE.csv", index=False, float_format="%.4f")
    for r in K.itertuples():
        ev.put(f"kiln.{r.country}.{r.ncv_scheme}.{r.clinker_basis}.solid_gj_t", r.solid_fuel_gj_per_t_clinker, "GJ/t clinker",
               "UNSD 2019 NMM row (export + SDMX 5150) / clinker", "INFERENCE", "C")

    # ------------------------------------------------------------------ S: TH series 2015-2021 (SDMX) ---------------------------------------------
    srows = []
    for y in range(2015, 2022):
        z = sd[(sd.cc == "TH") & (sd.transaction_code == "1214B") & (sd.year == y)]
        t = {code: float(z[z.commodity_code == code].value.sum()) for code in ("0100", "0200", "0210", "0220", "0129", "0110", "0311")}
        cf = {code: (float(z[z.commodity_code == code].conversion_factor.iloc[0]) if (z.commodity_code == code).any() else None) for code in ("0100", "0200")}
        coal_t = t["0100"] + t["0200"]
        pj_unsd = (t["0100"] * (cf["0100"] or 0) + t["0200"] * (cf["0200"] or 0)) / 1e3
        c_ = float(cem.get(("TH", y), float("nan")))
        rec = dict(year=y, hard_coal_kt=t["0100"], brown_coal_kt=t["0200"], of_which_subbit_kt=t["0210"], of_which_lignite_kt=t["0220"],
                   cf_hard_coal=cf["0100"], cf_brown_coal=cf["0200"], coal_kt=coal_t, unsd_coal_pj=pj_unsd, usgs_cement_mt=c_ / 1e6,
                   coal_t_per_t_cement=coal_t * 1e3 / c_, unsd_coal_gj_per_t_cement=pj_unsd * 1e3 / (c_ / 1e6) / 1e3)
        for nm, x in (("at_10_547", 10.547), ("at_18_9", 18.9), ("at_26_377", 26.377)):
            rec[f"coal_gj_per_t_cement_{nm}"] = coal_t * x / (c_ / 1e3)
        srows.append(rec)
    SS = pd.DataFrame(srows); SS.to_csv(out / "NCV_TH_NMM_SERIES.csv", index=False, float_format="%.4f")
    for r in SS.itertuples():
        ev.put(f"th_series.{r.year}.coal_t_per_t_cement", r.coal_t_per_t_cement, "t/t", "SDMX NMM coal (0100 + 0200) / USGS cement", "VERIFIED", "B")
        ev.put(f"th_series.{r.year}.unsd_coal_gj_per_t_cement", r.unsd_coal_gj_per_t_cement, "GJ/t", "SDMX NMM coal x SDMX CONVERSION_FACTOR / USGS cement", "EXACT", "B")

    # ------------------------------------------------------------------ P: PH power check -----------------------------------------------------------
    ex = cm.unsd_export(("PH",)); ex = ex[ex.year == 2019]
    def x(com, tr):
        z = ex[(ex.commodity == com) & (ex.transaction.str.lower() == tr.lower())]
        return float(z.q.iloc[0]) if len(z) else 0.0
    out_main = float(ex[ex.commodity == "From combustible fuels – Main activity"].q.iloc[0])
    coal_kt = x("Brown coal", "Transformation in main activity electricity plants")
    gas_tj = x("Natural Gas (including LNG)", "transformation in electricity plants - main activity producers") * 0.9
    oil_pj = (x("Fuel oil", "Transformation in electricity plants - main activity producers") * 40.4 + x("Gas Oil/ Diesel Oil", "Transformation in electricity plants - main activity producers") * 43.0
              + x("Biodiesel", "Transformation in electricity plants - main activity producers") * 36.8) / 1e3
    prow = []
    for g_eta, o_eta, lab in ((0.50, 0.35, "low gas/oil efficiency"), (0.535, 0.375, "central"), (0.57, 0.40, "high gas/oil efficiency")):
        coal_gwh = out_main - (gas_tj / 1e3 * g_eta + oil_pj * o_eta) / 3.6 * 1e3
        for nm, ncv in (("v3 14.0", 14.0004), ("UNSD SDMX 22.058", 22.058), ("IPCC sub-bit 18.9", 18.9), ("APEC 22.098", 22.098)):
            fuel_pj = coal_kt * ncv / 1e3
            eta = coal_gwh * 3.6 / 1e3 / fuel_pj
            prow.append(dict(case=lab, gas_eta=g_eta, oil_eta=o_eta, main_combustible_gwh=out_main, gas_pj_ncv=gas_tj / 1e3, oil_pj=oil_pj, coal_kt=coal_kt,
                             coal_gwh_residual=coal_gwh, coal_ncv=nm, coal_fuel_pj=fuel_pj, coal_eta=eta,
                             verdict=("impossible (> 0.45, ultra-supercritical)" if eta > 0.45 else ("above the technology-data 2050 coal efficiency 0.356" if eta > TD_ETA["coal"] else "plausible"))))
    P = pd.DataFrame(prow); P.to_csv(out / "NCV_PH_POWER_CHECK.csv", index=False, float_format="%.4f")
    for r in P.itertuples():
        ev.put(f"ph_power.{r.case}.{r.coal_ncv}.coal_eta", r.coal_eta, "-", "UNSD 2019 PH main-activity output and fuels (export)", "INFERENCE", "C")
    ev.put("ph_power.main_combustible_gwh", out_main, "GWh", "UNSD 2019 PH 'From combustible fuels – Main activity'", "VERIFIED", "B")
    ev.put("ph_power.coal_kt", coal_kt, "kt", "UNSD 2019 PH brown coal, transformation in main activity electricity plants", "VERIFIED", "B")

    # ------------------------------------------------------------------ NCV tables per country ------------------------------------------------------
    eppo = {r.item.strip(): float(r.value) for r in ref[ref.source.str.contains("EPPO", na=False)].itertuples()} if "item" in ref.columns else {}
    def cf19(cc, code):
        z = sd[(sd.cc == cc) & (sd.commodity_code == code) & (sd.year == 2019) & sd.conversion_factor.notna()]
        if not len(z):
            return ""
        vals = z.groupby("conversion_factor").transaction_code.apply(lambda s: ",".join(sorted(s)[:6])).to_dict()
        return "; ".join(f"{k:g} ({v})" for k, v in vals.items())
    tables = {
        "TH": [("Hard coal (parent; model row)", "Hard coal", "0100", "EPPO 2564: imported coal 26.37; anthracite 31.40 (p.226)", "parent: no single IPCC value (other bituminous 25.8, anthracite 26.7)"),
               ("Brown coal (parent; model row: 9,653 kt sub-bituminous + 324 kt lignite in industry)", "Brown coal", "0200", "EPPO 2564: Mae Moh 10.47, Li 18.42, Krabi 10.88, Chae Khon 15.11 (p.227); EPPO industrial lignite 141 ktoe / 324 kt = 18.2", "sub-bituminous 18.9 (11.5-26.0); lignite 11.9 (5.5-21.6)"),
               ("Sub-bituminous coal (child)", "Sub-bituminous coal", "0210", "EPPO: one value for all imported coal 26.37", "18.9 (11.5-26.0)"),
               ("Lignite (child)", "Lignite", "0220", "see brown coal", "11.9 (5.5-21.6)"),
               ("Other bituminous coal (child)", "Other bituminous coal", "0129", "26.37 (imported coal)", "25.8 (19.9-30.5)"),
               ("Anthracite (child)", "Anthracite", "0110", "31.40", "26.7 (21.6-32.2)"),
               ("Coke-oven coke", "Coke-oven coke", "0311", "27.63", "28.2")],
        "PH": [("Brown coal (model row; mostly imported Indonesian sub-bituminous)", "Brown coal", "0200", "no PH handbook on disk; APEC 2022 sub-bituminous 22.098 (TRANSCRIBED, W11)", "sub-bituminous 18.9 (11.5-26.0)")],
        "SG": [("Hard coal (other bituminous)", "Hard coal", "0100", "APEC 2022 other bituminous 25.800 (TRANSCRIBED, W11)", "25.8"),
               ("Petroleum coke", "Petroleum coke", "4694", "-", "32.5")],
    }
    for cc, items in tables.items():
        rows = []
        for label, com, code, national, ipcc in items:
            v3 = conv.get(com, conv.get(com.replace("Petroleum coke", "Petroleum Coke"), None))
            v3 = v3 * 1e6 * 3.6 / 1e3 if v3 else None
            prop = SCHEMES[cc]["207"].get(com)
            if cc == "TH" and com in ("Hard coal", "Brown coal"):
                kk = K[(K.country == "TH")].groupby("ncv_scheme").solid_fuel_gj_per_t_clinker.agg(["min", "max"])
                s17, s19 = SS.set_index("year").loc[2017], SS.set_index("year").loc[2019]
                phys = (f"K: solid fuel of the non-metallic row per t clinker (NCV_KILN_BALANCE.csv; range 2.9-{kiln_hi:.1f}): 10.547 {kk.at['207', 'min']:.1f}-{kk.at['207', 'max']:.1f} (inside), "
                        f"v3 {kk.at['v3', 'min']:.1f}-{kk.at['v3', 'max']:.1f}, children/IPCC {kk.at['sens_children_ipcc', 'min']:.1f}-{kk.at['sens_children_ipcc', 'max']:.1f}, "
                        f"EPPO {kk.at['sens_eppo', 'min']:.1f}-{kk.at['sens_eppo', 'max']:.1f} (above); S: {SS.coal_t_per_t_cement.min():.2f}-{SS.coal_t_per_t_cement.max():.2f} t coal per t cement "
                        f"2017-2021 across the 2018 reclassification while UNSD's own energy per t cement falls from {s17.unsd_coal_gj_per_t_cement:.1f} GJ (2017, hard coal 26.377) "
                        f"to {s19.unsd_coal_gj_per_t_cement:.1f} GJ (2019, brown coal 10.547) (NCV_TH_NMM_SERIES.csv) - the 2017 level is physically impossible; both support "
                        "the low UNSD parent value, neither the rank label (sub-bituminous) nor EPPO's single import value")
                proposed = f"{prop} (UNSD SDMX parent, decision 207 default; physical evidence does not conflict)"
            elif cc == "TH" and com == "Coke-oven coke":
                phys = "-"; proposed = "unchanged (= v3 = UNSD 28.2)"
            elif cc == "TH":
                phys = "children are not used by the model rows (parents only); listed for the sensitivity 'children / IPCC' (= W11 scheme d)"
                proposed = "not used (parent rows carry the energy)"
            elif cc == "PH":
                pp = P.groupby("coal_ncv").coal_eta.agg(["min", "max"]); kp = K[(K.country == "PH")].groupby("ncv_scheme").solid_fuel_gj_per_t_clinker.agg(["min", "max"])
                phys = (f"P: coal plants' implied efficiency at 14.0 {pp.at['v3 14.0', 'min']:.2f}-{pp.at['v3 14.0', 'max']:.2f} (impossible), at 22.058 "
                        f"{pp.at['UNSD SDMX 22.058', 'min']:.2f}-{pp.at['UNSD SDMX 22.058', 'max']:.2f} (plausible), at 18.9 {pp.at['IPCC sub-bit 18.9', 'min']:.2f}-{pp.at['IPCC sub-bit 18.9', 'max']:.2f} "
                        f"(above the 2050 technology-data value 0.356) (NCV_PH_POWER_CHECK.csv); K: NMM solid fuel per t clinker {kp.at['207', 'min']:.1f}-{kp.at['207', 'max']:.1f} at 22.058, "
                        f"{kp.at['v3', 'min']:.1f}-{kp.at['v3', 'max']:.1f} at 14.0 - below BAT 2.9 in both (the NMM row is short of the clinker energy: the v3 cement gap), "
                        "the higher value is the less inconsistent -> both pieces of evidence point to the UNSD value, none conflicts with it")
                proposed = f"{prop} (UNSD SDMX; physical evidence agrees)"
            else:
                phys = "-"; proposed = "unchanged (= v3 = UNSD)"
            rows.append(dict(commodity=label, v3=v3, unsd_country=cf19(cc, code), national=national, ipcc=ipcc, physical_evidence=phys, proposed=proposed))
            ev.put(f"{cc}.{com}.v3", v3, "GJ/t", "pypsa-asean get_conv_factors (frozen)", "VERIFIED", "B")
        pd.DataFrame(rows).to_csv(cm.G3 / f"{cc}_NCV.csv", index=False, float_format="%.4f")
    for (cc, code) in (("TH", "0100"), ("TH", "0200"), ("TH", "0210"), ("TH", "0220"), ("TH", "0129"), ("TH", "0110"), ("PH", "0200"), ("SG", "0100"), ("SG", "4694")):
        cf, q = sdmx_cf(cc, code, "121")
        if cf is not None:
            ev.put(f"{cc}.sdmx.{code}.manufacturing_cf", cf, "GJ/t", f"UNSD SDMX 2019 CONVERSION_FACTOR, transaction 121 (sdmx/{cc}_2015_2022.xml)", "VERIFIED", "B")
    cm.jdump({cc: {k: {f"{cc}|{c}": v for c, v in d.items()} for k, d in s.items()} for cc, s in SCHEMES.items()}, out / "_ncv_schemes.json")
    ev.extra["schemes"] = SCHEMES
    ev.write(out / "_ncv_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(K[["country", "ncv_scheme", "clinker_basis", "clinker_mt", "coal_pj", "biomass_export_pj", "sdmx_5150_pj", "solid_fuel_gj_per_t_clinker", "verdict"]].round(3).to_string())
    print(SS.round(3).to_string())
    print(P[["case", "coal_ncv", "coal_gwh_residual", "coal_fuel_pj", "coal_eta", "verdict"]].round(3).to_string())


if __name__ == "__main__":
    main()
