"""D1 section 3 (decisions 22, 34): 2050 final energy demand by country x sector x carrier.

Base year 2019: the frozen UNSD reconstruction (research_inputs/assembly_v1/sources/
BASE_RECONSTRUCTION.json, decision A maximum-overlap baseline values where accepted) for fuels,
and the UNSD 2019 electricity transactions (electricity.json) by sector.
Growth: ASEAN totals per sector follow AEO8 BAS 2050 (Appendix C.3, Mtoe x 11.63 TWh/Mtoe).
Country allocation (R3, decision 57, S2 supplement 02): 2019 country-sector energy x r_c, where
r_c = G_c / G_ASEAN and G_c = (AEO8 C.8 final energy per capita ATS 2050 x D.1 population 2050) /
(same product 2022); calibrated per sector so that the ASEAN-10 sum equals the AEO8 BAS 2050 sector
total (Timor-Leste is outside the AEO8 tables and keeps the GDP relative factor). The former GDP
allocation (WDI + SSP2 chain) and the population allocation are written as sensitivity files
(research.demand.country_allocation: aeo8_ats_relative | gdp | population).
Carrier shares inside each country-sector are held at 2019 values (no tuning to AEO8 by-fuel
totals; the comparison is reported as a cross-check). Electricity rows are flagged because the
network already carries the 2050 final electricity load (Astar, 2,617.8 TWh).
Non-energy use grows with the country industry multiplier; international bunkers stay at 2019
(research-layer convention) and the four missing shipping bunkers are DATA_PENDING.
A population-allocated variant is written as a sensitivity file.
"""
from __future__ import annotations

import json

import pandas as pd

from d1_common import (ASEAN, ASEAN10, DEMAND_DIR, ISO2_FROM_ISO3, REG_DIR, ROOT, SRC_DIR, Registry, read_csv, sha256, src_sha,
                       write_csv, write_json)

SCRIPT = "scripts_project/d1_demand_2050.py"
A1 = ROOT / "research_inputs" / "assembly_v1"
BASE_JSON = A1 / "sources" / "BASE_RECONSTRUCTION.json"
BLEND_JSON = A1 / "sources" / "ASSEMBLY_V1_BLEND_BASELINE.json"
ELEC_JSON = A1 / "sources" / "electricity.json"
REGISTRY_JSON = A1 / "registry.json"
FROZEN_BUNKER_JSON = A1 / "sources" / "FROZEN_ACCEPTED_BUNKER_2019.json"
AEO8_CSV = "AEO8_2050_ASEAN_TOTALS.csv"
AEO8_COUNTRY_CSV = "AEO8_2050_BY_COUNTRY.csv"   # R3: C.8 per-capita indicators + D.1 population (PDF p.189-190)
AEO8_COUNTRY_NAME = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao PDR": "LA", "Malaysia": "MY", "Myanmar": "MM",
                     "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Vietnam": "VN"}
ALLOCATION_FILES = {"aeo8_ats_relative": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "gdp": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_GDP_SENSITIVITY.csv",
                    "population": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_POP_SENSITIVITY.csv"}
GROWTH_CSV = "GROWTH_CHAIN_2019_2050_WDI_SSP2.csv"
BUNKER_EB_CSV = "UNSD_EB_2019_BUNKERS_BN_KH_LA_TL.csv"  # S2-0.4 (batch 6)
AEO8_PDF_SHA = "48c2a81913ed785cb0e14a55e332ea7bc87f912f7fabfbc8c654e09b66b11c06"
MWH_PER_MTOE = 11.63e6
SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
AEO8_LABEL = {"Industry": "Industry", "Transport": "Transport", "Residential": "Residential",
              "Commercial": "Commercial", "AgricultureOthers": "Agriculture and Others"}
ACCOUNT_SECTOR = {
    "IndustryFinalEnergy": "Industry", "RoadResidualFuel": "Transport", "DomesticAviationFuel": "Transport",
    "DomesticShippingFuel": "Transport", "RailNonElectric": "Transport", "TransportNEC": "Transport",
    "TransportEmbeddedFuelParent": "Transport", "ResidentialFuel": "Residential", "ServicesFuel": "Commercial",
    "AgricultureFinalEnergy": "AgricultureOthers", "OtherNEC": "AgricultureOthers",
    "InternationalAviationBunker": "InternationalBunkers", "InternationalShippingBunker": "InternationalBunkers"}
NONENERGY_CARRIER = {
    "Bitumen": "oil", "Ethane": "oil", "Fuel oil": "oil", "Gas Oil/ Diesel Oil": "oil",
    "Liquefied petroleum gas (LPG)": "oil", "Lubricants": "oil", "Motor Gasoline": "oil", "Naphtha": "oil",
    "Natural gas liquids": "oil", "Paraffin waxes": "oil", "Petroleum coke": "oil",
    "Natural gas (including LNG)": "gas", "Brown coal": "coal", "Brown coal briquettes": "coal",
    "Coke-oven coke": "coal", "Hard coal": "coal"}
ELEC_TX = {"Electricity - Final energy consumption": "final",
           "Electricity - Consumption by manufacturing, construction and non-fuel industry": "Industry",
           "Electricity - Consumption by households": "Residential",
           "Electricity - Consumption by commercial and public services": "Commercial",
           "Electricity - Consumption in agriculture, forestry and fishing": "Agriculture",
           "Electricity - Consumption by transport": "Transport", "Electricity - Consumption by rail": "Rail",
           "Electricity - Consumption not elsewhere specified (other)": "NEC",
           "Electricity - Consumption by other": "Other"}
AEO8_FUEL = {"coal": ["Coal"], "oil": ["Oil"], "gas": ["Natural Gas"], "biomass": ["Bioenergy", "Traditional Biomass"],
             "electricity": ["Electricity"]}


def load_aeo8():
    df = pd.read_csv(SRC_DIR / AEO8_CSV, dtype=str)
    df["value"] = df["value_as_printed"].str.replace(",", "").astype(float)
    sec = {s: {} for s in SECTORS}
    for s in SECTORS:
        d = df[(df.table == "C.3 TFEC by Sector") & (df.item == AEO8_LABEL[s])]
        sec[s]["2050"] = float(d[(d.scenario == "BAS") & (d.year == "2050")].value.iloc[0])
        sec[s]["2022"] = float(d[d.scenario.str.startswith("historical (as printed in BAS")].value.iloc[0])
    fuel = {}
    d = df[(df.table == "C.2 TFEC by Fuel")]
    for item in d.item.unique():
        fuel[item] = dict(y2050=float(d[(d.item == item) & (d.scenario == "BAS") & (d.year == "2050")].value.iloc[0]),
                          y2022=float(d[(d.item == item) & (d.scenario == "historical")].value.iloc[0]))
    total_2050 = float(df[(df.table == "C.3 TFEC by Sector") & (df.item == "Total") & (df.scenario == "BAS") & (df.year == "2050")].value.iloc[0])
    return sec, fuel, total_2050


def load_aeo8_country():
    """R3: per-country AEO8 C.8 final energy per capita (printed 'ktoe/1000 persons' = kgoe per person) and D.1 population (million).
    G_c = (pc_2050 ATS x pop_2050) / (pc_2022 x pop_2022); the sum of pc x pop is checked against the AEO8 ASEAN totals."""
    rows = read_csv(SRC_DIR / AEO8_COUNTRY_CSV)
    num = lambda v: float(str(v).replace(",", ""))
    pc, pop = {}, {}
    for r in rows:
        c = AEO8_COUNTRY_NAME.get(r["country"])
        if r["indicator"] == "Final energy per capita (TFEC/Pop)" and c and r["year"] in ("2022", "2050") and r["scenario"] in ("historical", "ATS"):
            pc[(c, r["year"])] = num(r["value_as_printed"])
        if r["indicator"] == "Population" and r["year"] in ("2022", "2050"):
            pop[(AEO8_COUNTRY_NAME.get(r["country"], r["country"]), r["year"])] = num(r["value_as_printed"])
    tfec = {(c, y): pc[(c, y)] * pop[(c, y)] * 1e-3 for c in AEO8_COUNTRY_NAME.values() for y in ("2022", "2050")}  # kgoe/person x million persons x 1e-3 = Mtoe
    sum22, sum50 = sum(tfec[(c, "2022")] for c in AEO8_COUNTRY_NAME.values()), sum(tfec[(c, "2050")] for c in AEO8_COUNTRY_NAME.values())
    G = {c: tfec[(c, "2050")] / tfec[(c, "2022")] for c in AEO8_COUNTRY_NAME.values()}
    G_asean = sum50 / sum22
    r = {c: G[c] / G_asean for c in G}
    return dict(per_capita_kgoe=pc, population_million=pop, tfec_mtoe=tfec, sum_2022_mtoe=sum22, sum_2050_mtoe=sum50, G=G, G_asean=G_asean, r=r,
                asean_population_million={y: pop.get(("ASEAN", y)) for y in ("2022", "2050")})


def electricity_by_sector(records):
    """UNSD 2019 electricity (million kWh -> MWh) by country and model sector."""
    out = {}
    for c in ASEAN:
        q = {}
        for r in records:
            if r["Country"] != c:
                continue
            k = ELEC_TX.get(r["Commodity - Transaction"])
            if k:
                q[k] = float(r["Quantity"]) * 1e3
        final = q.get("final", 0.0)
        H, C, A = q.get("Residential", 0.0), q.get("Commercial", 0.0), q.get("Agriculture", 0.0)
        T = q.get("Transport", q.get("Rail", 0.0))
        if "Industry" in q:
            I = q["Industry"]
            nec = final - I - H - C - A - T
            method = "industry row reported; NEC = final - industry - households - commercial - agriculture - transport"
        else:
            I = max(final - q.get("Other", H + C + A) - T, 0.0)
            nec = max(final - I - H - C - A - T, 0.0)
            method = "industry row missing: industry = final - other - transport"
        if nec < -1e-6 * max(final, 1.0):
            method += f"; negative residual {nec:.0f} MWh clipped to 0"
            nec = 0.0
        out[c] = dict(Industry=I, Residential=H, Commercial=C, Transport=T, AgricultureOthers=A + max(nec, 0.0),
                      final=final, method=method)
    return out


def main():
    base = json.loads(BASE_JSON.read_text())
    blend = json.loads(BLEND_JSON.read_text())["records"]
    blend_by_base = {v["BaseAccountID"]: v for v in blend.values()}
    elec = json.loads(ELEC_JSON.read_text())
    registry = json.loads(REGISTRY_JSON.read_text())["records"]
    astar = {r["Country"]: float(r["Value"]) for r in registry if r.get("Account") == "Astar" and r.get("Year") == 2050}
    aeo8_sec, aeo8_fuel, aeo8_total = load_aeo8()
    aeo8c = load_aeo8_country()
    aeo8_2022_total = next(float(r["value_as_printed"].replace(",", "")) for r in read_csv(SRC_DIR / AEO8_CSV) if r["table"] == "C.2 TFEC by Fuel" and r["item"] == "Total" and r["scenario"] == "historical" and r["year"] == "2022")
    aeo8_2050_ats_total = next(float(r["value_as_printed"].replace(",", "")) for r in read_csv(SRC_DIR / AEO8_CSV) if r["table"] == "C.2 TFEC by Fuel" and r["item"] == "Total" and r["scenario"] == "ATS" and r["year"] == "2050")
    growth = {ISO2_FROM_ISO3[r["Country Code"]]: r for r in pd.read_csv(SRC_DIR / GROWTH_CSV, dtype=str).to_dict("records")}
    shas = dict(base=sha256(BASE_JSON), blend=sha256(BLEND_JSON), elec=sha256(ELEC_JSON), registry=sha256(REGISTRY_JSON),
                aeo8_csv=src_sha(AEO8_CSV), aeo8_country_csv=src_sha(AEO8_COUNTRY_CSV), growth=src_sha(GROWTH_CSV), frozen_bunker=sha256(FROZEN_BUNKER_JSON))
    # ---- 2019 base rows -----------------------------------------------------------------------
    rows = []
    for a in base["accounts"]:
        c, acc, car = a["Country"], a["Account"], a["Carrier"]
        sector = ACCOUNT_SECTOR[acc]
        st = a["Status"]
        if a["AccountID"] in blend_by_base:
            val, bst = float(blend_by_base[a["AccountID"]]["BaseMWh"]), "ACCEPTED_BLEND_BASELINE_A"
        elif st == "NUMERIC_INPUT_READY":
            val, bst = float(a["ValueMWh"]), st
        elif st in ("SOURCE_BOUNDED_ZERO", "BOUNDARY_EXCLUSION"):
            val, bst = 0.0, st
        else:  # UNRESOLVED / UNRESOLVED_BIOFUEL_OVERLAP: raw reconstruction sum retained, flagged
            val, bst = (float(a["ValueMWh"]) if a.get("ValueMWh") not in (None, "") else 0.0), st
        rows.append(dict(country=c, sector=sector, carrier=car, account=acc, base_2019_mwh=val, base_status=bst,
                         base_source="BASE_RECONSTRUCTION.json" + ("+ASSEMBLY_V1_BLEND_BASELINE.json" if bst.startswith("ACCEPTED") else ""),
                         base_source_sha256=shas["base"] + ("|" + shas["blend"] if bst.startswith("ACCEPTED") else "")))
    es = electricity_by_sector(elec["records"])
    for c in ASEAN:
        for s in SECTORS:
            rows.append(dict(country=c, sector=s, carrier="electricity", account="UNSD_electricity_" + s,
                             base_2019_mwh=es[c][s], base_status="NUMERIC_INPUT_READY",
                             base_source="electricity.json (UNSD 2019 Electricity transactions)", base_source_sha256=shas["elec"]))
    for ne in base["nonenergy_reference"]:
        rows.append(dict(country=ne["Country"], sector="NonEnergyUse", carrier=NONENERGY_CARRIER[ne["Commodity"]],
                         account="NonEnergy:" + ne["Commodity"], base_2019_mwh=float(ne["MWh"]), base_status="NONENERGY_REFERENCE",
                         base_source="BASE_RECONSTRUCTION.json nonenergy_reference", base_source_sha256=shas["base"]))
    df = pd.DataFrame(rows)
    # ---- S2-0.4 (batch 6): UNSD Energy Balance 2019 for BN/KH/LA/TL: marine bunkers show no flow ("---") -> 0, grade A
    eb = {(r["iso2"], r["flow"]): r for r in read_csv(SRC_DIR / BUNKER_EB_CSV)}
    eb_sha = src_sha(BUNKER_EB_CSV)
    eb_countries = sorted({k[0] for k in eb})
    for i in df.index[(df.sector == "InternationalBunkers") & (df.account == "InternationalShippingBunker") & df.country.isin(eb_countries)]:
        r = eb[(df.at[i, "country"], "International marine bunkers")]
        df.at[i, "base_2019_mwh"] = float(r["value_MWh"]); df.at[i, "base_status"] = "UNSD_EB_2019_NO_FLOW_ZERO"
        df.at[i, "base_source"] = "UNSD Energy Balance 2019 export (" + r["source_file"] + "): " + r["note"]; df.at[i, "base_source_sha256"] = eb_sha
    # ---- multipliers -------------------------------------------------------------------------------
    def allocate(g):
        tfec = df[df.sector.isin(SECTORS)]
        base_cs = tfec.groupby(["country", "sector"]).base_2019_mwh.sum()
        k, cal = {}, {}
        for s in SECTORS:
            target = aeo8_sec[s]["2050"] * MWH_PER_MTOE
            w = sum(base_cs.get((c, s), 0.0) * g[c] for c in ASEAN10)
            k[s] = target / w
            cal[s] = dict(target_mwh=target, weighted_base_asean10_mwh=w, k=k[s],
                          base_2019_asean10_mwh=sum(base_cs.get((c, s), 0.0) for c in ASEAN10))
        return g, k, cal

    def build(g, label, weight_key):
        g, k, cal = allocate(g)
        out = []
        for r in df.to_dict("records"):
            c, s = r["country"], r["sector"]
            if s in SECTORS:
                mult, method = g[c] * k[s], f"AEO8_BAS_sector_total x {label} share (2019 energy x {weight_key}), k_sector calibration"
            elif s == "NonEnergyUse":
                mult, method = g[c] * k["Industry"], f"industry multiplier ({label})"
            else:  # international bunkers
                mult, method = 1.0, "CONSTANT_2019 (research-layer convention ASSEMBLY_V1_BUNKER_CONSTANT_2019)"
            pending = s == "InternationalBunkers" and r["base_status"] not in ("NUMERIC_INPUT_READY", "ACCEPTED_BLEND_BASELINE_A", "SOURCE_BOUNDED_ZERO", "UNSD_EB_2019_NO_FLOW_ZERO")
            out.append(dict(r, aeo8_sector=AEO8_LABEL.get(s, "outside TFEC" if s != "NonEnergyUse" else "outside TFEC (non-energy use)"),
                            growth_method=method, country_multiplier=g[c], sector_calibration_k=k.get(s, k["Industry"] if s == "NonEnergyUse" else 1.0),
                            multiplier_total=mult, value_2050_mwh=("" if pending else r["base_2019_mwh"] * mult),
                            in_existing_electricity_load=r["carrier"] == "electricity" and s in SECTORS,
                            existing_electricity_load_2050_mwh=astar.get(c, "") if (r["carrier"] == "electricity" and s in SECTORS) else "",
                            status="DATA_PENDING" if pending else ("SOURCE_ZERO" if r["base_status"] == "UNSD_EB_2019_NO_FLOW_ZERO" else ("FLAGGED_BASE_" + r["base_status"] if r["base_status"].startswith("UNRESOLVED") else "REGISTERED")),
                            decision_ref="22,34" if s in SECTORS else ("22 (non-energy)" if s == "NonEnergyUse" else "10,22 (bunkers)")))
        return pd.DataFrame(out), g, k, cal

    g_gdp_in = {c: float(growth[c]["gdp_19_50"]) for c in ASEAN}
    g_pop_in = {c: float(growth[c]["pop_19_50"]) for c in ASEAN}
    g_aeo8_in = {c: (aeo8c["r"][c] if c in aeo8c["r"] else float(growth[c]["gdp_rel_ASEAN"])) for c in ASEAN}   # TL: GDP relative factor (not in AEO8)
    main_df, g_aeo8, k_aeo8, cal_aeo8 = build(g_aeo8_in, "AEO8 ATS per-capita x population relative factor", "aeo8_ats_rel")
    gdp_df, g_gdp, k_gdp, cal_gdp = build(g_gdp_in, "GDP", "gdp_19_50")
    pop_df, g_pop, k_pop, cal_pop = build(g_pop_in, "population", "pop_19_50")
    cols = ["country", "sector", "carrier", "account", "aeo8_sector", "base_2019_mwh", "base_status", "growth_method",
            "country_multiplier", "sector_calibration_k", "multiplier_total", "value_2050_mwh", "in_existing_electricity_load",
            "existing_electricity_load_2050_mwh", "status", "decision_ref", "base_source", "base_source_sha256"]
    order = {s: i for i, s in enumerate(SECTORS + ["NonEnergyUse", "InternationalBunkers"])}
    for d in (main_df, gdp_df, pop_df):
        d["_o"] = d.sector.map(order)
        d.sort_values(["country", "_o", "carrier", "account"], inplace=True)
    write_csv(main_df.to_dict("records"), DEMAND_DIR / ALLOCATION_FILES["aeo8_ats_relative"], cols)
    write_csv(gdp_df.to_dict("records"), DEMAND_DIR / ALLOCATION_FILES["gdp"], cols)
    write_csv(pop_df.to_dict("records"), DEMAND_DIR / ALLOCATION_FILES["population"], cols)
    # ---- cross-checks ----------------------------------------------------------------------------------
    def num(d):
        return pd.to_numeric(d.value_2050_mwh, errors="coerce").fillna(0.0)
    m = main_df.copy(); m["v"] = num(m)
    tf = m[m.sector.isin(SECTORS)]
    checks = {}
    sec_tot = {s: float(tf[(tf.sector == s) & tf.country.isin(ASEAN10)].v.sum()) for s in SECTORS}
    checks["sector_totals_asean10_vs_aeo8_bas_2050"] = {s: dict(model_mwh=sec_tot[s], aeo8_mtoe=aeo8_sec[s]["2050"],
                                                                aeo8_mwh=aeo8_sec[s]["2050"] * MWH_PER_MTOE,
                                                                rel_diff=sec_tot[s] / (aeo8_sec[s]["2050"] * MWH_PER_MTOE) - 1) for s in SECTORS}
    checks["total_asean10_vs_aeo8_total_2050"] = dict(model_mwh=sum(sec_tot.values()), aeo8_mtoe=aeo8_total,
                                                       aeo8_mwh=aeo8_total * MWH_PER_MTOE, tl_mwh_outside=float(tf[tf.country == "TL"].v.sum()))
    e = tf[tf.carrier == "electricity"]
    e_c = e.groupby("country").v.sum()
    checks["electricity_vs_existing_astar_2050"] = dict(
        by_country={c: dict(table_mwh=float(e_c.get(c, 0.0)), astar_mwh=astar.get(c), ratio=(float(e_c.get(c, 0.0)) / astar[c]) if astar.get(c) else None) for c in ASEAN},
        table_total_asean11_mwh=float(e_c.sum()), astar_total_asean11_mwh=float(sum(astar.values())),
        aeo8_electricity_2050_mwh=aeo8_fuel["Electricity"]["y2050"] * MWH_PER_MTOE,
        note="electricity rows are already in the network load (Astar); do not add them as new loads")
    base_tf = df[df.sector.isin(SECTORS)]
    base_sec_10 = {s: float(base_tf[(base_tf.sector == s) & base_tf.country.isin(ASEAN10)].base_2019_mwh.sum()) for s in SECTORS}
    checks["implied_2019_to_2022_ratio_aeo8_2022_over_unsd_2019_asean10"] = {
        s: dict(unsd_2019_mwh=base_sec_10[s], aeo8_2022_mwh=aeo8_sec[s]["2022"] * MWH_PER_MTOE,
                ratio=aeo8_sec[s]["2022"] * MWH_PER_MTOE / base_sec_10[s] if base_sec_10[s] else None) for s in SECTORS}
    car_tot = tf[tf.country.isin(ASEAN10)].groupby("carrier").v.sum()
    checks["carrier_totals_asean10_vs_aeo8_c2_2050_untuned"] = {
        car: dict(model_mwh=float(car_tot.get(car, 0.0)), aeo8_mwh=sum(aeo8_fuel[l]["y2050"] for l in labels) * MWH_PER_MTOE,
                  ratio=float(car_tot.get(car, 0.0)) / (sum(aeo8_fuel[l]["y2050"] for l in labels) * MWH_PER_MTOE))
        for car, labels in AEO8_FUEL.items()}
    checks["carrier_totals_asean10_vs_aeo8_c2_2050_untuned"]["unclassified_fuel"] = dict(model_mwh=float(car_tot.get("unclassified_fuel", 0.0)))
    shares, comparison = [], []
    for s in SECTORS:
        b = base_tf[base_tf.sector == s].groupby("country").base_2019_mwh.sum()
        v = tf[tf.sector == s].groupby("country").v.sum()
        gg = gdp_df[gdp_df.sector == s].copy(); gg["v"] = num(gg); vg = gg.groupby("country").v.sum()
        p = pop_df[pop_df.sector == s].copy(); p["v"] = num(p); vp = p.groupby("country").v.sum()
        for c in ASEAN:
            shares.append(dict(sector=s, country=c, share_2019=float(b.get(c, 0.0) / b.sum()), share_2050_aeo8=float(v.get(c, 0.0) / v.sum()),
                               share_2050_gdp=float(vg.get(c, 0.0) / vg.sum()), share_2050_pop=float(vp.get(c, 0.0) / vp.sum()),
                               multiplier_aeo8=g_aeo8[c] * k_aeo8[s], multiplier_gdp=g_gdp[c] * k_gdp[s], multiplier_pop=g_pop[c] * k_pop[s]))
            comparison.append(dict(sector=s, country=c, base_2019_mwh=float(b.get(c, 0.0)), value_2050_aeo8_mwh=float(v.get(c, 0.0)), value_2050_gdp_mwh=float(vg.get(c, 0.0)),
                                   value_2050_pop_mwh=float(vp.get(c, 0.0)), ratio_aeo8_over_gdp=(float(v.get(c, 0.0)) / float(vg.get(c, 0.0)) if vg.get(c, 0.0) else None)))
    for s in ["NonEnergyUse"]:
        for c in ASEAN:
            a = float(num(m[(m.sector == s) & (m.country == c)]).sum()); gg = gdp_df[(gdp_df.sector == s) & (gdp_df.country == c)]; gv = float(num(gg).sum())
            pp = pop_df[(pop_df.sector == s) & (pop_df.country == c)]; pv = float(num(pp).sum())
            comparison.append(dict(sector=s, country=c, base_2019_mwh=float(df[(df.sector == s) & (df.country == c)].base_2019_mwh.sum()), value_2050_aeo8_mwh=a,
                                   value_2050_gdp_mwh=gv, value_2050_pop_mwh=pv, ratio_aeo8_over_gdp=(a / gv if gv else None)))
    write_csv(shares, DEMAND_DIR / "DEMAND_2050_COUNTRY_SHARES_2019_2050.csv", list(shares[0].keys()))
    write_csv(comparison, DEMAND_DIR / "DEMAND_2050_ALLOCATION_COMPARISON.csv", list(comparison[0].keys()))
    checks["r3_aeo8_country_allocation"] = dict(
        per_capita_kgoe={f"{c}_{y}": v for (c, y), v in aeo8c["per_capita_kgoe"].items()}, population_million={f"{c}_{y}": v for (c, y), v in aeo8c["population_million"].items()},
        tfec_mtoe={f"{c}_{y}": v for (c, y), v in aeo8c["tfec_mtoe"].items()}, sum_2022_mtoe=aeo8c["sum_2022_mtoe"], sum_2050_mtoe=aeo8c["sum_2050_mtoe"],
        aeo8_c2_total_2022_mtoe=aeo8_2022_total, aeo8_c2_total_2050_ats_mtoe=aeo8_2050_ats_total,
        rel_diff_2022=aeo8c["sum_2022_mtoe"] / aeo8_2022_total - 1, rel_diff_2050=aeo8c["sum_2050_mtoe"] / aeo8_2050_ats_total - 1,
        G=aeo8c["G"], G_asean=aeo8c["G_asean"], r=aeo8c["r"], tl_factor=dict(value=g_aeo8_in["TL"], method="GDP relative factor (gdp_rel_ASEAN), TL not in AEO8"),
        unit_reading="C.8 prints 'ktoe/1000 persons'; read as kgoe per person (sum of per-capita x population reproduces the C.2 ASEAN totals)")
    unres = df[df.base_status.str.startswith("UNRESOLVED")]
    checks["unresolved_base_accounts"] = dict(rows=int(len(unres)), mwh_2019=float(unres.base_2019_mwh.sum()),
                                              by_country={c: float(unres[unres.country == c].base_2019_mwh.sum()) for c in ASEAN if len(unres[unres.country == c])})
    pend = main_df[main_df.status == "DATA_PENDING"]
    checks["data_pending_rows"] = [f"{r.country}:{r.sector}:{r.account}:{r.carrier}" for r in pend.itertuples()]
    frozen = json.loads(FROZEN_BUNKER_JSON.read_text())["values"]
    bunk = main_df[main_df.sector == "InternationalBunkers"]
    checks["bunkers_vs_frozen_accepted_2019"] = [dict(key=k, frozen_mwh=float(v), table_mwh=(float(bunk[(bunk.country == k.split(":")[0]) & (bunk.account == k.split(":")[3])].value_2050_mwh.iloc[0]) if len(bunk[(bunk.country == k.split(":")[0]) & (bunk.account == k.split(":")[3]) & (bunk.value_2050_mwh != "")]) else None)) for k, v in frozen.items()]
    checks["electricity_sector_split_method"] = {c: es[c]["method"] for c in ASEAN}
    checks["calibration_aeo8"] = cal_aeo8
    checks["calibration_gdp"] = cal_gdp
    checks["calibration_pop"] = cal_pop
    checks["country_allocation_main"] = "aeo8_ats_relative"
    checks["mtoe_to_mwh"] = MWH_PER_MTOE
    write_json(dict(script=SCRIPT, sources=shas, aeo8_pdf_sha256=AEO8_PDF_SHA, checks=checks), DEMAND_DIR / "DEMAND_2050_CROSSCHECKS.json")
    # ---- registry rows (country-sector totals + method constants) -----------------------------------------
    reg = Registry(SCRIPT)
    src = f"BASE_RECONSTRUCTION.json:{shas['base']}; electricity.json:{shas['elec']}; AEO8 pdf:{AEO8_PDF_SHA}; growth chain:{shas['growth']}"
    for s in SECTORS:
        reg.add(f"demand_aeo8_bas_2050_{s}", f"AEO8 BAS 2050 TFEC {AEO8_LABEL[s]} (ASEAN-10 total)", aeo8_sec[s]["2050"], "Mtoe", "A",
                "8th ASEAN Energy Outlook, Appendix C.3 TFEC by Sector", "PDF p.184 (printed 182), BAS 2050", f"AEO8 pdf:{AEO8_PDF_SHA}; extraction:{shas['aeo8_csv']}",
                decision_ref="22,34")
        reg.add(f"demand_sector_calibration_k_{s}", f"Sector calibration factor k = AEO8 BAS 2050 {s} / sum(ASEAN10 2019 base x r_c) with r_c the AEO8 ATS relative factor (R3, decision 57); "
                f"GDP allocation k = {k_gdp[s]:.6g}, population allocation k = {k_pop[s]:.6g}",
                k_aeo8[s], "ratio", "B", "derived", "d1_demand_2050.allocate", src, sensitivity_low=min(k_gdp[s], k_pop[s]), sensitivity_high=max(k_gdp[s], k_pop[s]), decision_ref="22,34,57")
    for c in ASEAN:
        tot = float(tf[tf.country == c].v.sum())
        alt = [float(pd.to_numeric(x[(x.country == c) & x.sector.isin(SECTORS)].value_2050_mwh, errors="coerce").sum()) for x in (gdp_df, pop_df)]
        reg.add(f"demand_tfec_2050_{c}", f"{c} total final energy 2050 (all carriers incl. electricity already in Astar), AEO8 ATS relative allocation (R3); GDP allocation {alt[0]:.6g}, population allocation {alt[1]:.6g} MWh/a",
                tot, "MWh/a", "B", "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "sum over sectors and carriers", src, country=c,
                sensitivity_low=min([tot] + alt), sensitivity_high=max([tot] + alt), decision_ref="22,34,57")
        reg.add(f"demand_gdp_multiplier_2019_2050_{c}", f"{c} GDP (PPP, constant 2021 intl$) multiplier 2019->2050 from WDI 2019-2025 and SSP2 2025-2050 (sensitivity allocation after R3)",
                g_gdp[c], "ratio", "B", "extraction/GROWTH_CHAIN_2019_2050_WDI_SSP2.csv (WDI raw4 + IIASA SSP2 2025)", f"row {ISO2_FROM_ISO3 and c}: gdp_19_50",
                shas["growth"], country=c, sensitivity_low=g_pop[c], decision_ref="34", status="SENSITIVITY")
        if c in aeo8c["G"]:
            reg.add(f"demand_aeo8_ats_growth_2022_2050_{c}", f"{c} G_c = (AEO8 C.8 final energy per capita ATS 2050 {aeo8c['per_capita_kgoe'][(c, '2050')]:.6g} kgoe x D.1 population 2050 {aeo8c['population_million'][(c, '2050')]:.6g} M) / "
                    f"(2022: {aeo8c['per_capita_kgoe'][(c, '2022')]:.6g} kgoe x {aeo8c['population_million'][(c, '2022')]:.6g} M); per-capita printed as 'ktoe/1000 persons' read as kgoe/person",
                    aeo8c["G"][c], "ratio", "B", "8th ASEAN Energy Outlook, Appendix C.8 Energy Indicators and Table D.1 Population", "PDF p.189 (printed 187) C.8; PDF p.190 (printed 188) D.1",
                    f"AEO8 pdf:{AEO8_PDF_SHA}; extraction:{shas['aeo8_country_csv']}", country=c, decision_ref="57")
            reg.add(f"demand_aeo8_ats_relative_factor_{c}", f"{c} r_c = G_c / G_ASEAN ({aeo8c['G_asean']:.6g}); replaces the GDP relative factor in the country allocation (R3, decision 57)",
                    aeo8c["r"][c], "ratio", "B", "derived", "d1_demand_2050.load_aeo8_country", f"AEO8 pdf:{AEO8_PDF_SHA}; extraction:{shas['aeo8_country_csv']}", country=c,
                    sensitivity_low=min(aeo8c["r"][c], float(growth[c]["gdp_rel_ASEAN"])), sensitivity_high=max(aeo8c["r"][c], float(growth[c]["gdp_rel_ASEAN"])), decision_ref="57")
        else:
            reg.add(f"demand_aeo8_ats_relative_factor_{c}", f"{c} not in the AEO8 tables: GDP relative factor gdp_rel_ASEAN kept as r_c (R3, decision 57)", g_aeo8_in[c], "ratio", "B",
                    "extraction/GROWTH_CHAIN_2019_2050_WDI_SSP2.csv", "column gdp_rel_ASEAN", shas["growth"], country=c, decision_ref="57")
        reg.add(f"demand_country_multiplier_2019_2050_{c}", f"{c} country multiplier applied in the main table = r_c x k_sector (Industry value shown; other sectors differ by k)",
                g_aeo8[c] * k_aeo8["Industry"], "ratio", "B", "derived", "d1_demand_2050.allocate (main = aeo8_ats_relative)", src, country=c,
                sensitivity_low=min(g_gdp[c] * k_gdp["Industry"], g_pop[c] * k_pop["Industry"]), sensitivity_high=max(g_gdp[c] * k_gdp["Industry"], g_pop[c] * k_pop["Industry"]), decision_ref="57")
    reg.add("demand_aeo8_percapita_sum_check_2022", f"Sum over AEO8 countries of C.8 final energy per capita x D.1 population, 2022 = {aeo8c['sum_2022_mtoe']:.4f} Mtoe vs C.2 ASEAN total {aeo8_2022_total} Mtoe (unit reading check)",
            aeo8c["sum_2022_mtoe"], "Mtoe", "B", "8th ASEAN Energy Outlook C.8 x D.1 vs C.2", "PDF p.189-190 vs p.183", f"AEO8 pdf:{AEO8_PDF_SHA}; extraction:{shas['aeo8_country_csv']}", decision_ref="57", status="REFERENCE_ONLY")
    reg.add("demand_aeo8_percapita_sum_check_2050", f"Sum over AEO8 countries of C.8 final energy per capita ATS 2050 x D.1 population 2050 = {aeo8c['sum_2050_mtoe']:.4f} Mtoe vs C.2 ASEAN ATS total {aeo8_2050_ats_total} Mtoe",
            aeo8c["sum_2050_mtoe"], "Mtoe", "B", "8th ASEAN Energy Outlook C.8 x D.1 vs C.2", "PDF p.189-190 vs p.183", f"AEO8 pdf:{AEO8_PDF_SHA}; extraction:{shas['aeo8_country_csv']}", decision_ref="57", status="REFERENCE_ONLY")
    reg.add("demand_country_allocation_mode", "Main country allocation = aeo8_ats_relative (R3, decision 57); gdp and population allocations are sensitivity files (research.demand.country_allocation)",
            "aeo8_ats_relative", "flag", "B", "S2 supplement 02 R3", "configs/research/baseline.yaml research.demand.country_allocation", f"AEO8 pdf:{AEO8_PDF_SHA}", decision_ref="57")
    reg.add("demand_mtoe_to_mwh", "Mtoe -> MWh conversion used for AEO8 totals (1 toe = 11.63 MWh)", MWH_PER_MTOE, "MWh/Mtoe", "A",
            "IEA toe definition; research convention", "configs/research/baseline.yaml: mtoe_method ASSEMBLY_V1_MTOE_CONVENTION_11P63_TWH", shas["aeo8_csv"])
    reg.add("demand_2019_2022_bridge", "AEO8 prints only 2005 and 2022 historical values; 2019 (UNSD) -> 2050 uses the AEO8 2050 absolute level; the implied "
            "AEO8-2022 / UNSD-2019 ratios are reported in DEMAND_2050_CROSSCHECKS.json as a consistency check, not applied",
            "ABSOLUTE_2050_ANCHOR", "method", "B", "AEO8 Appendix C.3 columns 2005, 2022, 2025..2050", "PDF p.184", f"AEO8 pdf:{AEO8_PDF_SHA}", decision_ref="22")
    for r in pend.itertuples():
        reg.add(f"demand_bunker_pending_{r.country}_{r.account}", f"{r.country} {r.account} 2019 value missing in UNSD export (no international marine "
                "bunker transaction) -> download list", None, "MWh/a", "A", "UNSD Energy Statistics Database", "no 2019 row", shas["base"], country=r.country,
                decision_ref="10", status="DATA_PENDING")
    aviation_check = []
    for c in eb_countries:
        r = eb[(c, "International marine bunkers")]
        reg.add(f"demand_bunker_marine_zero_{c}", f"{c} international marine bunkers 2019 = 0 (UNSD Energy Balance shows no flow '---'; {r['note']}); closes D1 DATA_PENDING",
                0.0, "MWh/a", "A", "UNSD Energy Balance Visualization 2019 export (raw6/" + r["source_file"].split("/")[-1] + ")", f"flow {r['flow']}, commodity {r['commodity']}, unsd_notation {r['unsd_notation']}",
                eb_sha, country=c, decision_ref="10, S2-0.4", status="SOURCE_ZERO")
        a = eb[(c, "International aviation bunkers")]
        base_av = df[(df.country == c) & (df.account == "InternationalAviationBunker")].base_2019_mwh.sum()
        eb_av = float(a["value_MWh"])
        aviation_check.append(dict(country=c, unsd_eb_2019_aviation_mwh=eb_av, unsd_eb_tj=float(a["value_TJ"]), research_layer_2019_aviation_mwh=float(base_av),
                                   rel_diff=(eb_av / base_av - 1) if base_av else None, eb_estimate_flag=a["estimate_flag"]))
        reg.add(f"demand_bunker_aviation_check_{c}", f"{c} international aviation bunkers 2019: UNSD Energy Balance {eb_av:,.0f} MWh ({a['value_TJ']} TJ{'; UNSD estimate' if a['estimate_flag'] == '*' else ''}) vs research-layer UNSD export {base_av:,.0f} MWh; "
                f"relative difference {((eb_av / base_av - 1) * 100) if base_av else float('nan'):+.3f} % (rounding of TJ); research-layer value kept", eb_av, "MWh/a", "A",
                "UNSD Energy Balance Visualization 2019 export", f"flow {a['flow']}", eb_sha, country=c, decision_ref="10, S2-0.4", status="REFERENCE_ONLY")
    checks["bunkers_aviation_unsd_eb_vs_research_layer"] = aviation_check
    write_json(dict(script=SCRIPT, sources=dict(shas, bunker_eb=eb_sha), aeo8_pdf_sha256=AEO8_PDF_SHA, checks=checks), DEMAND_DIR / "DEMAND_2050_CROSSCHECKS.json")
    reg.write(REG_DIR / "fragments" / "demand_2050.csv")
    # ---- console summary -----------------------------------------------------------------------------------
    print("sector calibration k (GDP):", {s: round(k_gdp[s], 4) for s in SECTORS})
    for s in SECTORS:
        ck = checks["sector_totals_asean10_vs_aeo8_bas_2050"][s]
        print(f"  {s:18s} model {ck['model_mwh']/1e6:9.1f} TWh vs AEO8 {ck['aeo8_mwh']/1e6:9.1f} TWh (rel {ck['rel_diff']:+.2e}); 2022/2019 implied {checks['implied_2019_to_2022_ratio_aeo8_2022_over_unsd_2019_asean10'][s]['ratio']:.3f}")
    ce = checks["electricity_vs_existing_astar_2050"]
    print(f"electricity table {ce['table_total_asean11_mwh']/1e6:.1f} TWh vs Astar {ce['astar_total_asean11_mwh']/1e6:.1f} TWh vs AEO8 {ce['aeo8_electricity_2050_mwh']/1e6:.1f}")
    for car, v in checks["carrier_totals_asean10_vs_aeo8_c2_2050_untuned"].items():
        if "aeo8_mwh" in v:
            print(f"  carrier {car:12s} model {v['model_mwh']/1e6:8.1f} TWh vs AEO8 {v['aeo8_mwh']/1e6:8.1f} (ratio {v['ratio']:.2f})")
    print("unresolved base accounts:", checks["unresolved_base_accounts"]["rows"], "rows", round(checks["unresolved_base_accounts"]["mwh_2019"] / 1e6, 2), "TWh")
    print("DATA_PENDING:", checks["data_pending_rows"])


if __name__ == "__main__":
    main()
