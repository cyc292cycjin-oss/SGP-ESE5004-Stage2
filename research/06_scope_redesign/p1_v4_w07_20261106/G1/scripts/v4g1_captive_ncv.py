"""V4 W07 G1 step 2 and decision 207 (Malaysia): captive power and coal net calorific value.

    python scripts/v4g1_captive_ncv.py        (WSL pypsa-earth python; after v4g1_base.py)

Captive (decision 204 items 1-2, S2 section 5): UNSD 2019 autoproducer combustible output against the fuel recorded in transformation (UNdata export
and, in addition, the SDMX response of this session, which also has 'other vegetal material and residues' in autoproducer transformation), at the
technology-data v0.15.0 2050 efficiencies (upper bound for 2019 plants) and at 100 %; NEB 2019 self-generation input and output; GEM GIPT 2026-09:
MY units with 'Captive Industry Type' and MY gas / oil units with CHP, operating at the end of 2019 (S1 operating rule). If the inequality holds and
GIPT has no 2019 captive coal, option (b) is not triggered (C = 0).
NCV (decision 207): default = UNSD country value; MY hard coal from the SDMX CONVERSION_FACTOR (all flows 2010-2022); NEB 29.3076 TJ/kt is the
tce definition and is not used (207 item 6); the evidence row lists the independent physical evidence on disk.
Outputs tables/MY_CAPTIVE.csv, MY_CAPTIVE_GIPT_UNITS.csv, MY_NCV.csv, tables/_captive_ncv_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g1_common as cm   # noqa: E402

OUT = cm.G1 / "tables"
EFF = {"gas": 0.60, "oil": 0.35, "biogas": 0.43, "solid biomass": 0.468, "coal": 0.356}   # technology-data v0.15.0 2050 (S2 screen; upper bound for 2019 plants)


def main():
    ev = cm.Ev("captive_ncv")
    base = json.loads((OUT / "_base_evidence.json").read_text())["extra"]; neb = base["neb_checks"]
    S = pd.read_csv(cm.G1 / "sdmx/MY_SDMX_OBS.csv", dtype={"commodity_code": str, "transaction_code": str})
    S19 = S[S.year == 2019].drop_duplicates(subset=["commodity_code", "transaction_code"])   # both responses (the 2019 all-commodity request and the coal / biomass series)

    def sd(com, tr):
        z = S19[(S19.commodity == com) & (S19.transaction_code == tr)]
        return float(z.value.iloc[0]) if len(z) else 0.0
    # ---- fuels in autoproducer transformation (TWh); UNSD gas TJ is gross calorific -> x 0.90 (model rule); the S2 screen used TJ / 3.6 without 0.90
    fuels_export = {"gas": 62031.898 * 0.9 / 3600, "biogas": 4425.242 / 3600, "oil": 69.486 * 43.0 / 3600}
    fuels_sdmx = dict(fuels_export, **{"solid biomass": sd("Other Vegetal Material and Residues", "08812") / 3600})
    gen_comb = sd("Total Electricity", "016C")   # GWh, autoproducer combustible
    rows = []
    for lab, F in (("UNdata export (model source)", fuels_export), ("SDMX 2019 (incl. other vegetal residues)", fuels_sdmx)):
        fmax = sum(v * EFF[k] for k, v in F.items()) * 1e3; f100 = sum(F.values()) * 1e3
        rows.append(dict(dataset=lab, autoproducer_combustible_gwh=gen_comb, fuel_in_transformation_twh=sum(F.values()), max_gen_at_tech_eff_gwh=fmax, max_gen_at_100pct_gwh=f100,
                         implied_efficiency=gen_comb / f100, inequality_result="holds" if gen_comb <= fmax else ("violates efficiency bound" if gen_comb <= f100 else "violates 100 %"),
                         fuels=";".join(f"{k} {v:.3f} TWh" for k, v in F.items())))
    rows.append(dict(dataset="NEB 2019 self-generation (table 29)", autoproducer_combustible_gwh=neb["selfgen_output_gwh"] - 11.0,
                     fuel_in_transformation_twh=neb["selfgen_gas_input_twh"] + neb["selfgen_biomass_input_twh"] + neb["selfgen_biogas_input_twh"] + neb["selfgen_diesel_input_twh"],
                     implied_efficiency=(neb["selfgen_output_gwh"] - 11.0) / 1e3 / (neb["selfgen_gas_input_twh"] + neb["selfgen_biomass_input_twh"] + neb["selfgen_biogas_input_twh"] + neb["selfgen_diesel_input_twh"]),
                     inequality_result="holds", fuels=f"gas {neb['selfgen_gas_input_twh']:.3f} (output {neb['selfgen_gas_output_gwh']:.0f} GWh, {neb['selfgen_gas_output_gwh'] / 1e3 / neb['selfgen_gas_input_twh']:.3f}); biomass {neb['selfgen_biomass_input_twh']:.3f} (output {neb['selfgen_biomass_output_gwh']:.0f} GWh); biogas {neb['selfgen_biogas_input_twh']:.3f}; diesel {neb['selfgen_diesel_input_twh']:.3f}"))
    INQ = pd.DataFrame(rows)
    # ---- GIPT 2026-09
    g = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", low_memory=False)
    g = g[g.iso.eq(cm.CC)].copy()
    sy = pd.to_numeric(g["Start year"], errors="coerce"); ry = pd.to_numeric(g["Retired year"], errors="coerce")
    g["op_2019"] = g.Status.isin(["operating", "retired", "mothballed"]) & (sy <= 2019) & ~(ry <= 2019)
    capt = g[g["Captive Industry Type"].notna()]
    chp = g[g.CHP.astype(str).str.lower().isin(["yes", "y", "true"]) & g.Type.astype(str).str.contains("oil|gas|coal|bio", case=False)]
    U = pd.concat([capt.assign(selected="captive industry type"), chp[~chp.index.isin(capt.index)].assign(selected="CHP (no captive field)")])
    keep = ["selected", "Type", "Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Status", "Start year", "Retired year", "Technology", "Fuel (combustion only)", "CHP",
            "Captive Industry Type", "Captive Industry Use", "Owner(s)", "Subnational unit (state, province)", "Latitude", "Longitude", "op_2019", "GEM unit/phase ID"]
    U[keep].to_csv(OUT / "MY_CAPTIVE_GIPT_UNITS.csv", index=False)
    capt_coal19 = float(capt[capt.op_2019 & capt.Type.str.contains("coal", case=False)]["Capacity (MW)"].sum())
    capt_all19 = float(capt[capt.op_2019]["Capacity (MW)"].sum())
    chp19 = float(chp[chp.op_2019]["Capacity (MW)"].sum())
    gas_chp_neb = float(neb["cogeneration_gas_mw"])
    # ---- captive table (A6 schema)
    C = pd.DataFrame([dict(country=cm.CC, inequality_result=f"holds: UNdata export {INQ.implied_efficiency.iloc[0]:.3f}, SDMX {INQ.implied_efficiency.iloc[1]:.3f}, NEB gas self-generation {neb['selfgen_gas_output_gwh'] / 1e3 / neb['selfgen_gas_input_twh']:.3f} (bound 0.60)",
                           gipt_captive_MW_2019=capt_coal19, gipt_captive_all_fuels_MW_2019=capt_all19, gipt_chp_MW_2019=chp19, neb_cogeneration_gas_MW_2019=gas_chp_neb,
                           C_low_twh=0.0, C_central_twh=0.0, C_high_twh=0.0, C_low_t=0.0, C_central_t=0.0, C_high_t=0.0, E_twh=0.0,
                           central_rule="not triggered: inequality holds and GIPT has no captive coal unit operating at the end of 2019; NEB 2019 self-generation gas input 15.50 TWh = UNSD autoproducer transformation gas 15.51 TWh (fuel for the electricity of co-generation is in transformation, not in industry); the steam part of co-generation is industrial heat demand by definition and stays",
                           option_b_effect_2050_twh=0.0)])
    C.to_csv(OUT / "MY_CAPTIVE.csv", index=False, float_format="%.6f")
    INQ.to_csv(OUT / "MY_CAPTIVE_INEQUALITY.csv", index=False, float_format="%.6f")
    for r in INQ.itertuples():
        k = r.dataset.split(" (")[0].replace(" ", "_")
        for f in ("autoproducer_combustible_gwh", "fuel_in_transformation_twh", "max_gen_at_tech_eff_gwh", "max_gen_at_100pct_gwh", "implied_efficiency"):
            v = getattr(r, f)
            if v == v:
                ev.put(f"captive.{k}.{f}", v, "GWh" if f.endswith("gwh") else ("TWh" if f.endswith("twh") else "-"), r.dataset, "EXACT" if f in ("max_gen_at_tech_eff_gwh", "max_gen_at_100pct_gwh", "implied_efficiency") else "VERIFIED", "B")
    for k, v in dict(gipt_captive_coal_2019_mw=capt_coal19, gipt_captive_all_2019_mw=capt_all19, gipt_chp_2019_mw=chp19, neb_cogeneration_gas_mw=gas_chp_neb,
                     neb_selfgen_gas_minus_unsd_autoproducer_gas_twh=neb["selfgen_gas_input_twh"] - 62031.898 * 0.9 / 3600).items():
        ev.put(f"captive.{k}", v, "MW" if k.endswith("mw") else "TWh", "GEM GIPT 2026-09 (S1 operating rule) / NEB 2019 table 10, 29 / UNSD", "VERIFIED" if not k.startswith("neb_selfgen") else "EXACT", "B")
    ev.put("captive.C_central", 0.0, "TWh", "option (b) not triggered for MY", "PROPOSED", "B")

    # =============================================== NCV ======================================================================
    conv = cm.frozen_conv()
    v3gj = lambda name: float(conv[name]) * 3.6e3 if name in conv else np.nan   # TWh/kt -> GJ/t
    ref = pd.read_csv(cm.W11 / "ncv/NCV_REFERENCE_VALUES.csv")
    nat = ref[(ref.country == cm.CC) & ref.source.str.startswith("Malaysia National Energy Balance")].set_index("item").gj_per_unit
    apec = ref[(ref.country == cm.CC) & ref.source.str.startswith("APEC")].set_index("item").gj_per_unit
    cf19 = S19.groupby("commodity").conversion_factor.agg(lambda s: ";".join(sorted({f"{x:g}" for x in s.dropna()})))
    cf_years = S[S.commodity.eq("Hard Coal")].groupby("year").conversion_factor.agg(lambda s: ";".join(sorted({f"{x:g}" for x in s.dropna()})))
    coal_rank = pd.read_csv(cm.W11 / "ncv/GIPT_COAL_RANK_CAPACITY.csv").set_index("Country/area").loc["Malaysia"]
    IPCC = {"Hard coal": "other bituminous 25.8 (19.9-30.5)", "Coke-oven coke": "28.2", "Fuelwood": "wood 15.6 GJ/t (mass basis, not convertible)", "Bagasse": "11.6 (other primary solid biomass)",
            "Charcoal": "29.5", "Gas Oil/ Diesel Oil": "43.0", "Fuel oil": "40.4", "Liquefied petroleum gas (LPG)": "47.3", "Motor Gasoline": "44.3", "Natural gas": "48.0 GJ/t (TJ reported: GCV x 0.90)"}
    rows = [dict(commodity="Hard coal", v3=v3gj("Hard coal"), unsd_country=26.394, national=nat.get("Hard coal"), ipcc=IPCC["Hard coal"],
                 physical_evidence=(f"UNSD SDMX CONVERSION_FACTOR 26.394 for every MY hard-coal flow 2010-2022 ({';'.join(f'{y}:{v}' for y, v in cf_years.items())}); "
                                    f"UNSD 2014 country table MY production / imports 26.4 (W11, VERIFIED); APEC 2022 MY other bituminous 26.394 (TRANSCRIBED, same value, not independent); "
                                    f"GIPT operating coal capacity bituminous {coal_rank.share_known_bituminous:.1%} of known; NEB 2019 industry 'coal & coke' 1,706 ktoe = 2,706,669 t x 26.394 GJ/t (NEB applies the UNSD value); "
                                    "no on-disk evidence conflicting with 26.394"),
                 proposed=26.394, proposed_status="207 default (UNSD country value, B); NEB 29.3076 = 1 tce definition, not used (207 item 6); sensitivity W11 inferred 28.544 and IPCC 25.8 (= v3)",
                 used_in_t_v2="UNSD NMM hard coal 1,232.691 kt (Estimate) -> cement deduction"),
            dict(commodity="Coke-oven coke", v3=v3gj("Coke oven coke") if "Coke oven coke" in conv else 28.2, unsd_country=26.377, national=nat.get("Coke/oven coke"), ipcc=IPCC["Coke-oven coke"],
                 physical_evidence="SDMX 26.377 all years 2015-2022; APEC 2022 26.377", proposed=26.377, proposed_status="no effect on T_v2: MY coke is only transformation in blast furnaces (outside T_v2)",
                 used_in_t_v2="no (transformation)"),
            dict(commodity="Fuelwood (GJ/m3)", v3=v3gj("Fuelwood"), unsd_country=9.135, national=nat.get("Fuelwood"), ipcc=IPCC["Fuelwood"], physical_evidence="SDMX 9.135",
                 proposed=np.nan, proposed_status="no change (households only; no MY industry fuelwood)", used_in_t_v2="no"),
            dict(commodity="Bagasse", v3=v3gj("Bagasse"), unsd_country=7.7221, national=np.nan, ipcc=IPCC["Bagasse"], physical_evidence="SDMX 7.7221", proposed=np.nan,
                 proposed_status="no change (5.8 kt, 0.012 TWh)", used_in_t_v2="yes (industry)"),
            dict(commodity="Charcoal", v3=v3gj("Charcoal"), unsd_country=29.5, national=nat.get("Charcoal"), ipcc=IPCC["Charcoal"], physical_evidence="SDMX 29.5; APEC 28.889",
                 proposed=np.nan, proposed_status="no change (no industry use)", used_in_t_v2="no"),
            *[dict(commodity=c, v3=v3gj(k), unsd_country=float(str(cf19.get(s, "nan")).split(";")[0]), national=nat.get(n), ipcc=IPCC[c], physical_evidence=f"SDMX {cf19.get(s, '')}",
                   proposed=np.nan, proposed_status="no change: UNSD uses the standard value = v3 (W11); NEB value within 2-4 % (sensitivity only)", used_in_t_v2="yes")
              for c, k, s, n in (("Gas Oil/ Diesel Oil", "Gas Oil/ Diesel Oil", "Gas Oil/ Diesel Oil", "Gas Oil/Diesel"), ("Fuel oil", "Fuel oil", "Fuel Oil", "Residual Fuel Oil"),
                                 ("Liquefied petroleum gas (LPG)", "Liquefied petroleum gas (LPG)", "Liquified Petroleum Gas", "Liquefied Petroleum Gas (LPG)"),
                                 ("Motor Gasoline", "Motor Gasoline", "Motor Gasoline", "Petrol"))],
            dict(commodity="Natural gas", v3=np.nan, unsd_country=1.0, national=np.nan, ipcc=IPCC["Natural gas"], physical_evidence="reported in TJ (gross); model x 0.90 (UNSD rule)",
                 proposed=np.nan, proposed_status="no change", used_in_t_v2="yes")]
    N = pd.DataFrame(rows)
    N.to_csv(OUT / "MY_NCV.csv", index=False, float_format="%.6g")
    for r in N.itertuples():
        for k in ("v3", "unsd_country", "national", "proposed"):
            v = getattr(r, k)
            if v == v and v is not None:
                ev.put(f"ncv.{r.commodity}.{k}", float(v), "GJ/t", {"v3": "FROZEN_UPSTREAM_CONVERSIONS.json", "unsd_country": "UNSD SDMX CONVERSION_FACTOR (G1/sdmx)",
                                                                     "national": "NEB 2019 p.80 (via W11 NCV_REFERENCE_VALUES.csv)", "proposed": "decision 207 rule"}[k],
                       "VERIFIED" if k != "proposed" else "PROPOSED", "B")
    d_coal_twh = 1232.691 * (26.394 - v3gj("Hard coal")) / 3600
    ev.put("ncv.hard_coal.delta_2019_nmm_twh", d_coal_twh, "TWh", "1,232.691 kt x (26.394 - 25.8012) GJ/t", "EXACT", "B")
    ev.extra["coal_delta_2019_mwh"] = d_coal_twh * 1e6
    ev.extra["coal_delta_2019_mwh_w11_inferred"] = 1232.691 * (28.5444055156 - v3gj("Hard coal")) / 3600 * 1e6
    ev.write(OUT / "_captive_ncv_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
    print(INQ.to_string()); print(C.T.to_string())
    print(U[["selected", "Type", "Plant / Project name", "Capacity (MW)", "Status", "Start year", "CHP", "Captive Industry Type", "Subnational unit (state, province)", "op_2019"]].to_string())
    print(N[["commodity", "v3", "unsd_country", "national", "proposed"]].to_string()); print("d_coal_twh", d_coal_twh)


if __name__ == "__main__":
    main()
