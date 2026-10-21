"""M08b B1 (M08-5; decisions 126, 129, 134): activity anchors from ACE AEO8 (2024) ATS and the 'aeo8_ats_anchor' demand table.

Only activity levels are anchored (S4R supplement 01 section 2); carrier structures stay endogenous:
  * country totals: AEO8 Table C.8 ATS 2050 per capita (TFEC kgoe, electricity kWh) x Table D.1 population 2050; TL (outside AEO8) =
    simple mean of the KH / LA / MM per-capita values x UN WPP 2024 median 2050 population (UN Data Portal export, 1,889,249.5);
  * sector split = normalised weights: 2019 sector quantity of the country (D1 table base_2019_mwh) x ATS regional sector growth
    2022 -> 2050 (Table C.3 ATS panel; residential electricity 29.0 -> 33.2 Mtoe from section 3.1.3 p.61), non-energy use counted
    with industry; the same method for the 11 countries;
  * base electricity load = ATS electricity x share of residential + commercial + agriculture/others + transport (2019 rail / existing
    electric road; EV is a separate load) = the S4J-1 base-load scope used in S4R (966 TWh);
  * transport = ATS TFEC x transport weight; the table's transport fuel rows carry (transport anchor - transport electricity anchor), so the
    transport sector total equals the anchor and the electricity part is not counted twice; EV / FCEV / ICE shares per the current method;
  * industry (incl. non-energy use) multiplier = industry anchor / 2019 industry: ammonia, methanol, HVC, the energy fallback, feedstock;
  * physical output (cement, crude steel): min(base x G^((2050 - base year) / 28 x elasticity), saturation x population 2050, plan cap)
    with G = AEO8 Table D.2 real GDP 2050 / 2022 (TL = mean of KH / LA / MM); plan values only as caps.
Residential / commercial / agriculture fuel rows and international bunkers stay as in the ratio table (not anchored).

    python scripts_project/m08b_demand.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import ASEAN, DEMAND_DIR, ROOT, SRC_DIR, sha256, write_json   # noqa: E402
from d1_demand_2050 import AEO8_COUNTRY_CSV, AEO8_COUNTRY_NAME, AEO8_CSV, MWH_PER_MTOE   # noqa: E402

SCRIPT = "scripts_project/m08b_demand.py"
M08B_SRC = DEMAND_DIR / "sources" / "m08b"
RATIO_TABLE = DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"   # aeo8_ats_relative x ratio: row structure and 2019 bases
ANCHOR_TABLE = DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
ANCHORS = DEMAND_DIR / "DEMAND_ANCHOR_AEO8_ATS.csv"
OUTPUT_BASE = DEMAND_DIR / "INDUSTRY_OUTPUT_BASE_M08B.csv"
PLAN_CAPS = DEMAND_DIR / "INDUSTRY_OUTPUT_PLAN_CAPS.csv"
OUTPUT_2050 = DEMAND_DIR / "INDUSTRY_OUTPUT_2050_M08B.csv"
EVIDENCE = DEMAND_DIR / "DEMAND_ANCHOR_M08B_EVIDENCE.json"
D2_CSV = M08B_SRC / "AEO8_TABLE_D2_REAL_GDP_PPP2017.csv"
WPP_CSV = M08B_SRC / "unpopulation_dataportal_20261020224306.csv"
USGS_XLSX = M08B_SRC / "myb1-2023-cemen-ERT.xlsx"
WORLDSTEEL_XLSX = M08B_SRC / "exp-2026-10-20_15_02_22.xlsx"

SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
C3_ITEM = {"Industry": "Industry", "Transport": "Transport", "Residential": "Residential", "Commercial": "Commercial", "AgricultureOthers": "Agriculture and Others"}
BASE_SECTORS = ["Residential", "Commercial", "AgricultureOthers", "Transport"]   # S4J-1 TABLE_BASE_SECTORS (decision 104)
RES_ELEC_ATS_MTOE = (29.0, 33.2)   # AEO8 section 3.1.3 p.61: ATS residential electricity 2022 -> 2050 (Mtoe); the only sector electricity value printed
TL_PEERS = ("KH", "LA", "MM")
ELASTICITY, ELASTICITY_RANGE = 0.5, (0.3, 0.8)            # industry_output_elasticity (assumption, grade C)
SATURATION = {"cement": 1.0, "steel": 0.6}                # t/cap/a (assumptions, grade C)
SATURATION_RANGE = {"cement": (0.6, 1.2), "steel": (0.4, 0.8)}
BASE_YEAR = {"cement": 2023, "steel": 2024}
USGS_NAMES = {"Brunei": "BN", "Burma": "MM", "Cambodia": "KH", "Indonesia": "ID", "Laos": "LA", "Malaysia": "MY", "Philippines": "PH",
              "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Vietnam": "VN"}
WORLDSTEEL_NAMES = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao PDR": "LA", "Laos": "LA", "Malaysia": "MY", "Myanmar": "MM",
                    "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN", "Vietnam": "VN"}
PLAN = [dict(country="VN", product="cement", cap_mt=150.0, source="Decision 1266/QD-TTg (2020-08-18) Annex I: total designed cement capacity <= 150 Mt/a (2030), held flat",
             locator="Cong bao 843-844 pp.34-35", role="cap only (never raises output)"),
        dict(country="VN", product="steel", cap_mt=70.0, source="Decision 261/QD-TTg (2026-02-09): 65-70 Mt crude steel 2050 (upper value as cap)",
             locator="MOIT summary page", role="cap only (never raises output)")]


def num(v) -> float:
    return float(str(v).replace(",", "").strip())


def aeo8_country():
    """C.8 ATS 2050 per capita (TFEC kgoe/person printed as 'ktoe/1000 persons', electricity kWh/person) and D.1 population 2050 (million)."""
    df = pd.read_csv(SRC_DIR / AEO8_COUNTRY_CSV, dtype=str)
    out = {}
    for name, c in AEO8_COUNTRY_NAME.items():
        d = df[df.country == name]
        pick = lambda ind, scen: num(d[(d.indicator == ind) & (d.scenario == scen) & (d.year == "2050")].value_as_printed.iloc[0])
        out[c] = dict(tfec_pc_kgoe=pick("Final energy per capita (TFEC/Pop)", "ATS"), elec_pc_kwh=pick("Electricity consumption per capita", "ATS"),
                      pop_2050_million=pick("Population", "all scenarios (constant)"), pop_source="AEO8 Table D.1 (PDF p.190)")
    w = pd.read_csv(WPP_CSV, encoding="utf-8-sig", dtype=str)
    r = w[(w.Iso2 == "TL") & (w.Time == "2050") & (w.Variant == "Median") & (w.Sex == "Both sexes")]
    if len(r) != 1:
        raise ValueError("UN WPP 2024: expected one TL 2050 median both-sexes row")
    out["TL"] = dict(tfec_pc_kgoe=float(np.mean([out[p]["tfec_pc_kgoe"] for p in TL_PEERS])), elec_pc_kwh=float(np.mean([out[p]["elec_pc_kwh"] for p in TL_PEERS])),
                     pop_2050_million=num(r.Value.iloc[0]) / 1e6, pop_source="UN WPP 2024 median variant 2050 (UN Data Portal export)")
    return out


def c3_ats():
    """Table C.3 ATS panel (Mtoe): 2022 as printed in the ATS panel and ATS 2050."""
    df = pd.read_csv(SRC_DIR / AEO8_CSV, dtype=str)
    d = df[df.table == "C.3 TFEC by Sector"]
    out = {}
    for s, item in C3_ITEM.items():
        e = d[d["item"] == item]
        out[s] = (num(e[e.scenario == "historical (as printed in ATS panel)"].value_as_printed.iloc[0]), num(e[(e.scenario == "ATS") & (e.year == "2050")].value_as_printed.iloc[0]))
    return out


def gdp_growth():
    """AEO8 Table D.2 real GDP (PPP 2017) 2050 / 2022; TL = mean of KH / LA / MM (TL rule)."""
    d = pd.read_csv(D2_CSV, dtype=str)
    names = dict(AEO8_COUNTRY_NAME)
    g = {names[r.country]: num(r.y2050) / num(r.y2022) for r in d.itertuples() if r.country in names}
    g["TL"] = float(np.mean([g[p] for p in TL_PEERS]))
    return g


def output_bases():
    """Cement 2023 (USGS MYB 2023 T22, thousand t) and crude steel 2024 (worldsteel Steel Data Viewer, thousand t); countries not listed -> 0."""
    t = pd.read_excel(USGS_XLSX, "T22", header=None)
    hdr = [str(v).strip().removesuffix(".0") for v in t.iloc[5]]   # header mixes '2021' strings and 2022.0 floats
    col = hdr.index("2023")
    cem = {}
    for i in range(6, len(t)):
        name = str(t.iat[i, 0]).strip()
        key = next((k for k in USGS_NAMES if name == k or (name.startswith(k) and name[len(k):].isdigit())), None)   # footnote digits ('Burma4')
        if key:
            cem[USGS_NAMES[key]] = (num(t.iat[i, col]), "" if pd.isna(t.iat[i, col + 1]) else str(t.iat[i, col + 1]).strip())
    s = pd.read_excel(WORLDSTEEL_XLSX, header=None)
    hdr = [str(v).strip() for v in s.iloc[2]]
    scol = next(j for j, v in enumerate(hdr) if v in ("2024", "2024.0"))
    st = {}
    for i in range(3, len(s)):
        name = str(s.iat[i, 0]).strip()
        if name in WORLDSTEEL_NAMES:
            st[WORLDSTEEL_NAMES[name]] = num(s.iat[i, scol])
    rows = []
    for c in ASEAN:
        cv, flag = cem.get(c, (0.0, ""))
        rows.append(dict(country=c, cement_base_year=BASE_YEAR["cement"], cement_base_kt=cv, cement_flag=flag,
                         cement_source=("USGS Minerals Yearbook 2023 Cement, Table 22 (advance release)" + (" - e = estimated" if "e" in flag else "")) if c in cem else "not in USGS MYB 2023 T22 -> 0 (S4R supplement 01)",
                         cement_grade=("C" if "e" in flag else "B") if c in cem else "B",
                         steel_base_year=BASE_YEAR["steel"], steel_base_kt=st.get(c, 0.0),
                         steel_source="worldsteel Steel Data Viewer, total production of crude steel (export 2026-10-20; unit not stated, thousand t)" if c in st else "not in the worldsteel table -> 0 (S4R supplement 01)",
                         steel_grade="B"))
    return rows


def physical_output(bases, pop, g):
    plan = {(p["country"], p["product"]): p["cap_mt"] for p in PLAN}
    rows = []
    for b in bases:
        c = b["country"]; r = dict(country=c, population_2050_million=pop[c], gdp_growth_2022_2050=g[c])
        for prod, base_mt in (("cement", b["cement_base_kt"] / 1e3), ("steel", b["steel_base_kt"] / 1e3)):
            yrs = 2050 - BASE_YEAR[prod]
            gf = lambda e: max(g[c], 1.0) ** (yrs / 28.0 * e)
            growth = base_mt * gf(ELASTICITY); cap_pc = SATURATION[prod] * pop[c]; cap_plan = plan.get((c, prod), np.inf)
            out = min(growth, cap_pc, cap_plan)
            bind = "growth" if out == growth else ("per-capita" if out == cap_pc else "plan")
            r.update({f"{prod}_base_mt": base_mt, f"{prod}_base_year": BASE_YEAR[prod], f"{prod}_growth_factor": gf(ELASTICITY), f"{prod}_growth_rule_mt": growth,
                      f"{prod}_percap_cap_mt": cap_pc, f"{prod}_plan_cap_mt": cap_plan if np.isfinite(cap_plan) else "", f"{prod}_2050_mt": out, f"{prod}_binding": bind,
                      f"{prod}_2050_elasticity_low_mt": min(base_mt * gf(ELASTICITY_RANGE[0]), cap_pc, cap_plan),
                      f"{prod}_2050_elasticity_high_mt": min(base_mt * gf(ELASTICITY_RANGE[1]), cap_pc, cap_plan),
                      f"{prod}_2050_saturation_low_mt": min(growth, SATURATION_RANGE[prod][0] * pop[c], cap_plan),
                      f"{prod}_2050_saturation_high_mt": min(growth, SATURATION_RANGE[prod][1] * pop[c], cap_plan),
                      f"{prod}_2050_without_plan_mt": min(growth, cap_pc)})
        rows.append(r)
    return rows


def main():
    dem = pd.read_csv(RATIO_TABLE, dtype=str, keep_default_na=False)
    base = pd.to_numeric(dem.base_2019_mwh, errors="coerce").fillna(0.0)
    a8 = aeo8_country(); c3 = c3_ats(); g = gdp_growth()
    g_el = {s: c3[s][1] / c3[s][0] for s in SECTORS}; g_el["Residential"] = RES_ELEC_ATS_MTOE[1] / RES_ELEC_ATS_MTOE[0]
    g_tfec = {s: c3[s][1] / c3[s][0] for s in SECTORS}
    is_el = dem.carrier == "electricity"
    anchors, new = [], dem.copy()
    for c in ASEAN:
        m = dem.country == c
        A_el = a8[c]["elec_pc_kwh"] * a8[c]["pop_2050_million"] * 1e3                 # kWh/person x million persons -> MWh
        A_tfec = a8[c]["tfec_pc_kgoe"] * a8[c]["pop_2050_million"] * 1e3 * 11.63      # kgoe/person x million persons = 1e3 toe; x 11.63 MWh/toe
        el19 = {s: float(base[m & is_el & (dem.sector == s)].sum()) for s in SECTORS}
        w_el = {s: el19[s] * g_el[s] for s in SECTORS}; w_el_sum = sum(w_el.values())
        share = {s: w_el[s] / w_el_sum for s in SECTORS}
        t19 = {s: float(base[m & (dem.sector == s)].sum()) for s in SECTORS}
        t19["Industry"] += float(base[m & (dem.sector == "NonEnergyUse")].sum())
        w_t = {s: t19[s] * g_tfec[s] for s in SECTORS}; w_t_sum = sum(w_t.values())
        tr_anchor = A_tfec * w_t["Transport"] / w_t_sum
        ind_anchor = A_tfec * w_t["Industry"] / w_t_sum
        m_ind = ind_anchor / t19["Industry"]
        el_anchor = {s: A_el * share[s] for s in SECTORS}
        tr_fuel_base = float(base[m & (dem.sector == "Transport") & ~is_el].sum())
        tr_fuel_target = tr_anchor - el_anchor["Transport"]
        if tr_fuel_target < 0 or tr_fuel_base <= 0:
            raise ValueError(f"{c}: transport fuel anchor {tr_fuel_target} / 2019 base {tr_fuel_base} not usable")
        m_tr = tr_fuel_target / tr_fuel_base
        rows_note = "126,129,134"
        for i in dem.index[m]:
            sec, car, b = dem.at[i, "sector"], dem.at[i, "carrier"], base[i]
            orig_blank = dem.at[i, "value_2050_mwh"] == ""
            if sec in BASE_SECTORS and car == "electricity":
                mult = el_anchor[sec] / el19[sec] if el19[sec] > 0 else 0.0   # = anchor x (row base / sector base 2019)
                how = f"ats_anchor: base electricity load = AEO8 ATS electricity x normalised {sec} weight (2019 electricity x ATS sector growth), split by 2019 account share"
            elif sec == "Transport":
                mult = m_tr
                how = "ats_anchor: transport fuel = (ATS transport anchor - transport electricity anchor) x 2019 fuel share (service level; EV/FCEV/ICE shares per the current method)"
            elif sec in ("Industry", "NonEnergyUse"):
                mult = m_ind
                how = "ats_anchor: 2019 x ATS industry multiplier (industry anchor incl. non-energy use / 2019); steel and cement by the physical output rule in s3_0_industry.py"
            else:
                continue   # residential / commercial / agriculture fuels and international bunkers: ratio table unchanged (not anchored)
            if orig_blank:
                continue
            v = b * mult
            new.at[i, "value_2050_mwh"] = repr(float(v))
            new.at[i, "multiplier_total"] = repr(float(mult)); new.at[i, "country_multiplier"] = repr(float(mult)); new.at[i, "sector_calibration_k"] = "1.0"
            new.at[i, "growth_method"] = how
            if str(dem.at[i, "in_existing_electricity_load"]).lower() == "true":
                new.at[i, "existing_electricity_load_2050_mwh"] = repr(float(v))
            refs = [x.strip() for x in str(dem.at[i, "decision_ref"]).replace(";", ",").split(",") if x.strip()]
            new.at[i, "decision_ref"] = ",".join(refs + [x for x in rows_note.split(",") if x not in refs])
        old_base = float(pd.to_numeric(dem[m & is_el & dem.sector.isin(BASE_SECTORS)].value_2050_mwh, errors="coerce").fillna(0).sum())
        old_tr = float(pd.to_numeric(dem[m & (dem.sector == "Transport")].value_2050_mwh, errors="coerce").fillna(0).sum())
        anchors.append(dict(country=c, population_2050_million=a8[c]["pop_2050_million"], population_source=a8[c]["pop_source"],
                            ats_tfec_pc_2050_kgoe=a8[c]["tfec_pc_kgoe"], ats_elec_pc_2050_kwh=a8[c]["elec_pc_kwh"],
                            ats_tfec_2050_mwh=A_tfec, ats_elec_2050_mwh=A_el,
                            **{f"elec_2019_{s}_mwh": el19[s] for s in SECTORS}, **{f"elec_share_{s}": share[s] for s in SECTORS},
                            **{f"tfec_2019_{s}_mwh": t19[s] for s in SECTORS},
                            base_share_of_ats_elec=sum(share[s] for s in BASE_SECTORS),
                            base_load_anchor_mwh=sum(el_anchor[s] for s in BASE_SECTORS),
                            base_load_buildings_agri_mwh=sum(el_anchor[s] for s in ("Residential", "Commercial", "AgricultureOthers")),
                            residential_elec_anchor_mwh=el_anchor["Residential"], commercial_elec_anchor_mwh=el_anchor["Commercial"],
                            agri_other_elec_anchor_mwh=el_anchor["AgricultureOthers"], transport_elec_anchor_mwh=el_anchor["Transport"],
                            industry_elec_ats_implied_mwh=el_anchor["Industry"],
                            transport_anchor_mwh=tr_anchor, transport_fuel_anchor_mwh=tr_fuel_target, transport_fuel_multiplier=m_tr,
                            industry_anchor_mwh=ind_anchor, industry_multiplier=m_ind,
                            base_load_ratio_table_mwh=old_base, transport_ratio_table_mwh=old_tr,
                            base_load_nonnegative=bool(sum(el_anchor[s] for s in BASE_SECTORS) >= 0)))
    an = pd.DataFrame(anchors)
    an.to_csv(ANCHORS, index=False, float_format="%.10g")
    new.to_csv(ANCHOR_TABLE, index=False)
    bases = output_bases()
    pd.DataFrame(bases).to_csv(OUTPUT_BASE, index=False, float_format="%.10g")
    pd.DataFrame(PLAN).to_csv(PLAN_CAPS, index=False)
    pop = {r["country"]: r["population_2050_million"] for r in anchors}
    out = pd.DataFrame(physical_output(bases, pop, g))
    out.to_csv(OUTPUT_2050, index=False, float_format="%.10g")
    ten = an[an.country != "TL"]
    tot = dict(base_load_anchor_11_twh=float(an.base_load_anchor_mwh.sum() / 1e6), base_load_buildings_agri_11_twh=float(an.base_load_buildings_agri_mwh.sum() / 1e6),
               base_load_ratio_table_11_twh=float(an.base_load_ratio_table_mwh.sum() / 1e6), transport_anchor_11_twh=float(an.transport_anchor_mwh.sum() / 1e6),
               transport_ratio_table_11_twh=float(an.transport_ratio_table_mwh.sum() / 1e6),
               residential_elec_10_twh=float(ten.residential_elec_anchor_mwh.sum() / 1e6), aeo8_ats_residential_elec_2050_twh=RES_ELEC_ATS_MTOE[1] * MWH_PER_MTOE / 1e6,
               ats_tfec_10_mtoe=float(ten.ats_tfec_2050_mwh.sum() / MWH_PER_MTOE), ats_elec_10_twh=float(ten.ats_elec_2050_mwh.sum() / 1e6),
               cement_2050_11_mt=float(out.cement_2050_mt.sum()), steel_2050_11_mt=float(out.steel_2050_mt.sum()), all_base_loads_nonnegative=bool(an.base_load_nonnegative.all()))
    srcs = {p.name: sha256(p) for p in (RATIO_TABLE, SRC_DIR / AEO8_COUNTRY_CSV, SRC_DIR / AEO8_CSV, D2_CSV, WPP_CSV, USGS_XLSX, WORLDSTEEL_XLSX)}
    write_json(dict(script=SCRIPT, sources=srcs, c3_ats_mtoe=c3, sector_growth_electricity=g_el, sector_growth_tfec=g_tfec, residential_electricity_ats_mtoe=RES_ELEC_ATS_MTOE,
                    gdp_growth_2022_2050=g, tl_rule=f"per capita = mean({', '.join(TL_PEERS)}) ATS 2050; population UN WPP 2024 median 2050", elasticity=ELASTICITY,
                    elasticity_range=ELASTICITY_RANGE, saturation_t_per_cap=SATURATION, saturation_range=SATURATION_RANGE, base_year=BASE_YEAR, plan_caps=PLAN, totals=tot,
                    outputs={p.name: sha256(p) for p in (ANCHORS, ANCHOR_TABLE, OUTPUT_BASE, PLAN_CAPS, OUTPUT_2050)}), EVIDENCE)
    pd.set_option("display.width", 250)
    show = an.set_index("country")[["ats_elec_2050_mwh", "base_share_of_ats_elec", "base_load_anchor_mwh", "base_load_ratio_table_mwh", "transport_anchor_mwh", "transport_ratio_table_mwh", "industry_multiplier"]].copy()
    show.iloc[:, [0, 2, 3, 4, 5]] /= 1e6
    print(show.round(3).to_string())
    print(out.set_index("country")[["cement_base_mt", "cement_growth_rule_mt", "cement_percap_cap_mt", "cement_2050_mt", "cement_binding", "steel_base_mt", "steel_growth_rule_mt", "steel_percap_cap_mt", "steel_2050_mt", "steel_binding"]].round(2).to_string())
    print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in tot.items()})


if __name__ == "__main__":
    main()
