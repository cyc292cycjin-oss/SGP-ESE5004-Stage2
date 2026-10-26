"""M08b B1 (M08-5; decisions 126, 129, 134): activity anchors from ACE AEO8 (2024) ATS and the 'aeo8_ats_anchor' demand table.

Only activity levels are anchored (S4R supplement 01 section 2); carrier structures stay endogenous:
  * country totals: AEO8 Table C.8 ATS 2050 per capita (TFEC kgoe, electricity kWh) x Table D.1 population 2050; TL (outside AEO8) =
    simple mean of the KH / LA / MM per-capita values x UN WPP 2024 median 2050 population (UN Data Portal export, 1,889,249.5);
  * sector split (DFX F1, DFX_RULES section 1; replaces the normalised weights of M08b B1): RAS biproportional fitting of the 10 AEO8 countries -
    seeds = 2019 sector ENERGY USE (D1 table base_2019_mwh; non-energy use excluded), row targets = the country ATS TFEC anchors, column targets =
    Table C.3 ATS 2050 sector values (Mtoe x 11.63e6) scaled by k = sum(country anchors) / sum(C.3) (rounding of C.8 x D.1 vs C.3); convergence
    1e-10 on rows and columns, at most 1,000 iterations, zero seeds stay zero; TL (outside AEO8) keeps the normalised weights (2019 sector energy use
    x C.3 ATS growth), non-energy use excluded;
  * non-energy use (DFX F1.2): outside the TFEC envelope (AEO8 Appendix E: TFEC excludes non-energy use); 2050 NEU = 2019 NEU x the industry
    multiplier (energy-use industry anchor / 2019 industry energy use); TL has no 2019 industry energy use -> NEU multiplier = KH / LA / MM mean (TL rule);
  * base electricity load = ATS electricity x share of residential + commercial + agriculture/others + transport (2019 rail / existing
    electric road; EV is a separate load) = the S4J-1 base-load scope used in S4R (966 TWh);
  * transport = RAS transport anchor; the table's transport fuel rows carry (transport anchor - transport electricity anchor), so the
    transport sector total equals the anchor and the electricity part is not counted twice; EV / FCEV / ICE shares per the current method;
  * industry multiplier = industry anchor / 2019 industry energy use: methanol, HVC, chlorine, the energy fallback, feedstock;
  * physical output (cement, crude steel): min(base x G^((2050 - base year) / 28 x elasticity), saturation x population 2050, plan cap)
    with G = AEO8 Table D.2 real GDP 2050 / 2022 (TL = mean of KH / LA / MM); plan values only as caps;
  * ammonia (DFX F2, DFX_RULES section 2): 2050 production = USGS Minerals Yearbook 2022 Nitrogen T12 2019 production (kt N x 17/14 as in PyPSA-Eur
    build_ammonia_production, reproduced resource ammonia_production.csv) x G^((2050 - 2019) / 28 x elasticity), no saturation, no plan cap; countries
    not listed by USGS -> 0; the ammonia load is built from this production in s3_0_industry.py (replacing the EU27 chemicals-weight share);
  * ammonia feedstock gas (DFX F2.4): the NEU natural-gas rows of a country are reduced by 2050 ammonia production x AMMONIA_GAS_MWH_PER_T
    (PyPSA-Eur config MWh_CH4_per_tNH3_SMR 10.8, the SMR route total gas = upper bound of the feedstock share; JRC-IDEES has no ammonia row), floored at 0;
  * residential / commercial / agriculture fuel rows (supplement 01 section 3, decision 137): sector fuel = sector TFEC anchor - sector electricity anchor;
    the 2019 carrier structure of the sector's fuel rows (cooking LPG, biomass, ...) is scaled proportionally (the ratio table has one multiplier per
    sector, so this is also its carrier structure); a negative value is set to 0 and listed (country, sector, value), never filled from another
    source; a positive value without any 2019 fuel row (no carrier structure) is also left at 0 and listed.
International bunkers stay UNSD 2019 constants (decision 10; sector InternationalBunkers, not anchored).

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
from d1_common import ASEAN, ASEAN10, DEMAND_DIR, NEU_GAS_ACCOUNT, ROOT, SRC_DIR, sha256, write_json   # noqa: E402
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
# DFX F2: ammonia production (ktNH3/a) = PyPSA-Eur resources/ammonia_production.csv reproduced from the USGS Minerals Yearbook 2022 Nitrogen table T12
# (s3_0_industry_ratios.build_ammonia_production: kt N x 17/14); countries without a USGS row are NaN -> 0
AMMONIA_CSV = SRC_DIR / "jrc_idees_2021" / "ammonia_production.csv"
AMMONIA_GAS_MWH_PER_T = 10.8          # DFX F2.4: PyPSA-Eur v2025.07.0 config.default.yaml line 850 MWh_CH4_per_tNH3_SMR (SMR route total natural gas; upper bound of the feedstock share)
AMMONIA_GAS_MWH_PER_T_STOICH = 4.92   # DFX F2.4 sensitivity (not run): stoichiometric feedstock, technology-data Haber-Bosch hydrogen-input 1.1484 x 5.166 / 1.2055 MWh_H2 per MWh_CH4
RAS_TOL, RAS_MAX_ITER = 1e-10, 1000   # DFX F1.3

SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
NEU_SECTOR = "NonEnergyUse"
C3_ITEM = {"Industry": "Industry", "Transport": "Transport", "Residential": "Residential", "Commercial": "Commercial", "AgricultureOthers": "Agriculture and Others"}
BASE_SECTORS = ["Residential", "Commercial", "AgricultureOthers", "Transport"]   # S4J-1 TABLE_BASE_SECTORS (decision 104)
FUEL_SECTORS = {"residential": "Residential", "commercial": "Commercial", "agriculture": "AgricultureOthers"}   # supplement 01 section 3: fuel rows anchored
RES_ELEC_ATS_MTOE = (29.0, 33.2)   # AEO8 section 3.1.3 p.61: ATS residential electricity 2022 -> 2050 (Mtoe); the only sector electricity value printed
TL_PEERS = ("KH", "LA", "MM")
ELASTICITY, ELASTICITY_RANGE = 0.5, (0.3, 0.8)            # industry_output_elasticity (assumption, grade C)
SATURATION = {"cement": 1.0, "steel": 0.6}                # t/cap/a (assumptions, grade C); ammonia: none (DFX F2.1)
SATURATION_RANGE = {"cement": (0.6, 1.2), "steel": (0.4, 0.8)}
BASE_YEAR = {"cement": 2023, "steel": 2024, "ammonia": 2019}
PRODUCTS = ("cement", "steel", "ammonia")
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


def ras_split(seed: np.ndarray, row: np.ndarray, col: np.ndarray, tol: float = RAS_TOL, max_iter: int = RAS_MAX_ITER):
    """DFX F1.3 (DFX_RULES section 1.3): biproportional fitting (RAS) of a non-negative seed matrix to row and column targets.

    Rows are rescaled first, then columns, until the largest relative row and column error is <= tol; zero seeds stay zero (multiplicative).
    Returns (X, iterations, row_error, column_error); raises RuntimeError when the tolerance is not reached within max_iter."""
    X = np.array(seed, dtype=float).copy()
    row = np.asarray(row, dtype=float); col = np.asarray(col, dtype=float)
    if X.shape != (len(row), len(col)):
        raise ValueError(f"RAS: seed {X.shape} does not match {len(row)} rows x {len(col)} columns")
    if (X < 0).any() or (row <= 0).any() or (col <= 0).any():
        raise ValueError("RAS: negative seed or non-positive target")
    if abs(row.sum() / col.sum() - 1.0) > 1e-9:
        raise ValueError(f"RAS: row targets {row.sum():.6g} and column targets {col.sum():.6g} differ")
    if (X.sum(axis=1) <= 0).any() or (X.sum(axis=0) <= 0).any():
        raise ValueError("RAS: a row or column of the seed is all zero")
    for it in range(1, max_iter + 1):
        X = X * (row / X.sum(axis=1))[:, None]
        X = X * (col / X.sum(axis=0))[None, :]
        er = float(np.abs(X.sum(axis=1) / row - 1.0).max()); ec = float(np.abs(X.sum(axis=0) / col - 1.0).max())
        if max(er, ec) <= tol:
            return X, it, er, ec
    raise RuntimeError(f"RAS did not converge within {max_iter} iterations (row error {er:.3e}, column error {ec:.3e}) - stop condition (DFX_RULES section 1.3)")


def output_bases():
    """Cement 2023 (USGS MYB 2023 T22, thousand t), crude steel 2024 (worldsteel Steel Data Viewer, thousand t) and ammonia 2019 (USGS MYB 2022 Nitrogen
    T12 via the reproduced PyPSA-Eur ammonia_production.csv, thousand t NH3; DFX F2.1); countries not listed -> 0."""
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
    amm = pd.read_csv(AMMONIA_CSV, index_col=0)
    ycol = str(BASE_YEAR["ammonia"])
    nh3 = {c: float(amm.at[c, ycol]) for c in ASEAN if c in amm.index and pd.notna(amm.at[c, ycol])}
    rows = []
    for c in ASEAN:
        cv, flag = cem.get(c, (0.0, ""))
        rows.append(dict(country=c, cement_base_year=BASE_YEAR["cement"], cement_base_kt=cv, cement_flag=flag,
                         cement_source=("USGS Minerals Yearbook 2023 Cement, Table 22 (advance release)" + (" - e = estimated" if "e" in flag else "")) if c in cem else "not in USGS MYB 2023 T22 -> 0 (S4R supplement 01)",
                         cement_grade=("C" if "e" in flag else "B") if c in cem else "B",
                         steel_base_year=BASE_YEAR["steel"], steel_base_kt=st.get(c, 0.0),
                         steel_source="worldsteel Steel Data Viewer, total production of crude steel (export 2026-10-20; unit not stated, thousand t)" if c in st else "not in the worldsteel table -> 0 (S4R supplement 01)",
                         steel_grade="B",
                         ammonia_base_year=BASE_YEAR["ammonia"], ammonia_base_kt=nh3.get(c, 0.0),
                         ammonia_source=("USGS Minerals Yearbook 2022 Nitrogen, Table 12 (thousand t contained N x 17/14 -> kt NH3; PyPSA-Eur build_ammonia_production reproduction)" if c in nh3
                                         else "not listed in USGS MYB 2022 Nitrogen T12 -> 0 (DFX F2.1)"),
                         ammonia_grade="B"))
    return rows


def physical_output(bases, pop, g):
    """Cement / steel: min(growth, per-capita saturation, plan cap); ammonia (DFX F2.1): growth rule only (no saturation, no plan cap)."""
    plan = {(p["country"], p["product"]): p["cap_mt"] for p in PLAN}
    rows = []
    for b in bases:
        c = b["country"]; r = dict(country=c, population_2050_million=pop[c], gdp_growth_2022_2050=g[c])
        for prod in PRODUCTS:
            base_mt = b[f"{prod}_base_kt"] / 1e3
            yrs = 2050 - BASE_YEAR[prod]
            gf = lambda e: max(g[c], 1.0) ** (yrs / 28.0 * e)
            growth = base_mt * gf(ELASTICITY)
            if prod == "ammonia":
                out = growth; bind = "growth" if base_mt > 0 else "no_usgs_production"
                r.update({f"{prod}_base_mt": base_mt, f"{prod}_base_year": BASE_YEAR[prod], f"{prod}_growth_factor": gf(ELASTICITY), f"{prod}_growth_rule_mt": growth,
                          f"{prod}_percap_cap_mt": "", f"{prod}_plan_cap_mt": "", f"{prod}_2050_mt": out, f"{prod}_binding": bind,
                          f"{prod}_2050_elasticity_low_mt": base_mt * gf(ELASTICITY_RANGE[0]), f"{prod}_2050_elasticity_high_mt": base_mt * gf(ELASTICITY_RANGE[1]),
                          f"{prod}_2050_saturation_low_mt": out, f"{prod}_2050_saturation_high_mt": out, f"{prod}_2050_without_plan_mt": out,
                          f"{prod}_2050_constant_2019_mt": base_mt})   # registered alternative (not run): 2019 production held constant
                continue
            cap_pc = SATURATION[prod] * pop[c]; cap_plan = plan.get((c, prod), np.inf)
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
    A_tfec = {c: a8[c]["tfec_pc_kgoe"] * a8[c]["pop_2050_million"] * 1e3 * 11.63 for c in ASEAN}   # kgoe/person x million persons = 1e3 toe; x 11.63 MWh/toe
    A_el = {c: a8[c]["elec_pc_kwh"] * a8[c]["pop_2050_million"] * 1e3 for c in ASEAN}                # kWh/person x million persons -> MWh
    t19 = {c: {s: float(base[(dem.country == c) & (dem.sector == s)].sum()) for s in SECTORS} for c in ASEAN}   # DFX F1.2: energy use only, NEU excluded
    neu19 = {c: float(base[(dem.country == c) & (dem.sector == NEU_SECTOR)].sum()) for c in ASEAN}
    # ---- DFX F1.3: RAS sector split of the 10 AEO8 countries ------------------------------------------------------------------------
    seed = np.array([[t19[c][s] for s in SECTORS] for c in ASEAN10])
    row_t = np.array([A_tfec[c] for c in ASEAN10])
    col_printed = np.array([c3[s][1] for s in SECTORS]) * MWH_PER_MTOE
    k_scale = float(row_t.sum() / col_printed.sum())
    col_t = col_printed * k_scale
    X, ras_it, ras_er, ras_ec = ras_split(seed, row_t, col_t)
    tfa = {c: {s: float(X[i, j]) for j, s in enumerate(SECTORS)} for i, c in enumerate(ASEAN10)}
    w_tl = {s: t19["TL"][s] * g_tfec[s] for s in SECTORS}; w_tl_sum = sum(w_tl.values())   # TL: normalised weights (outside AEO8), NEU excluded
    tfa["TL"] = {s: A_tfec["TL"] * w_tl[s] / w_tl_sum for s in SECTORS}
    # ---- physical output first: the ammonia feedstock gas deduction (DFX F2.4) needs the 2050 ammonia production -------------------------
    bases = output_bases()
    pop = {c: a8[c]["pop_2050_million"] for c in ASEAN}
    out_rows = physical_output(bases, pop, g); out_by = {r["country"]: r for r in out_rows}
    m_ind_raw = {c: (tfa[c]["Industry"] / t19[c]["Industry"] if t19[c]["Industry"] > 0 else None) for c in ASEAN}
    peer_mult = float(np.mean([m_ind_raw[p] for p in TL_PEERS]))
    anchors, new = [], dem.copy()
    for c in ASEAN:
        m = dem.country == c
        el19 = {s: float(base[m & is_el & (dem.sector == s)].sum()) for s in SECTORS}
        w_el = {s: el19[s] * g_el[s] for s in SECTORS}; w_el_sum = sum(w_el.values())
        share = {s: w_el[s] / w_el_sum for s in SECTORS}
        tr_anchor = tfa[c]["Transport"]
        ind_anchor = tfa[c]["Industry"]
        if m_ind_raw[c] is not None:
            m_ind = m_neu = m_ind_raw[c]; mult_src = "ras_industry_anchor / 2019 industry energy use"
        else:   # TL: no 2019 industry energy use (industry rows stay 0); NEU grows with the KH / LA / MM mean industry multiplier (TL rule)
            m_ind, m_neu = 0.0, peer_mult; mult_src = "no 2019 industry energy use: industry rows 0; NEU multiplier = mean of the KH / LA / MM industry multipliers (TL rule)"
        el_anchor = {s: A_el[c] * share[s] for s in SECTORS}
        tr_fuel_base = float(base[m & (dem.sector == "Transport") & ~is_el].sum())
        tr_fuel_target = tr_anchor - el_anchor["Transport"]
        if tr_fuel_target < 0 or tr_fuel_base <= 0:
            raise ValueError(f"{c}: transport fuel anchor {tr_fuel_target} / 2019 base {tr_fuel_base} not usable")
        m_tr = tr_fuel_target / tr_fuel_base
        fuel = {}   # supplement 01 section 3: sector fuel anchor = sector TFEC anchor - sector electricity anchor; negative / no 2019 structure -> 0 (listed)
        for key, s in FUEL_SECTORS.items():
            tfa_s = tfa[c][s]; raw = tfa_s - el_anchor[s]; fb = float(base[m & (dem.sector == s) & ~is_el].sum())
            zeroed = "negative" if raw < 0 else ("no_2019_fuel_rows" if (raw > 0 and fb <= 0) else "")
            used = 0.0 if zeroed else raw
            fuel[s] = dict(key=key, tfec_anchor=tfa_s, raw=raw, used=used, base=fb, mult=(used / fb if fb > 0 else 0.0), zeroed=zeroed)
        rows_note = "126,129,134"
        for i in dem.index[m]:
            sec, car, b = dem.at[i, "sector"], dem.at[i, "carrier"], base[i]
            orig_blank = dem.at[i, "value_2050_mwh"] == ""
            note = rows_note
            if sec in BASE_SECTORS and car == "electricity":
                mult = el_anchor[sec] / el19[sec] if el19[sec] > 0 else 0.0   # = anchor x (row base / sector base 2019)
                how = f"ats_anchor: base electricity load = AEO8 ATS electricity x normalised {sec} weight (2019 electricity x ATS sector growth), split by 2019 account share"
            elif sec == "Transport":
                mult = m_tr
                how = "ats_anchor (DFX F1 RAS): transport fuel = (RAS transport anchor - transport electricity anchor) x 2019 fuel share (service level; EV/FCEV/ICE shares per the current method)"
            elif sec == "Industry":
                mult = m_ind
                how = "ats_anchor (DFX F1 RAS): 2019 x ATS industry multiplier (RAS industry energy-use anchor / 2019 industry energy use); steel, cement and ammonia by the physical output rule in s3_0_industry.py"
            elif sec == NEU_SECTOR:
                mult = m_neu
                how = "ats_anchor (DFX F1.2): non-energy use outside the TFEC envelope = 2019 x the industry multiplier" + (" (TL: KH / LA / MM mean)" if c == "TL" else "")
            elif sec in fuel:
                f = fuel[sec]; mult = f["mult"]; note = rows_note + ",137"
                how = (f"ats_anchor (supplement 01 section 3; DFX F1 RAS): {sec} fuel = RAS {sec} TFEC anchor - {sec} electricity anchor, x 2019 carrier share of the sector fuel rows"
                       + (f"; anchor {f['raw']:.6g} MWh set to 0 ({f['zeroed']}; registry demand_sector_fuel_anchor_zeroed)" if f["zeroed"] else ""))
            else:
                continue   # international bunkers: UNSD 2019 constants (decision 10), not anchored
            if orig_blank:
                continue
            v = b * mult
            new.at[i, "value_2050_mwh"] = repr(float(v))
            new.at[i, "multiplier_total"] = repr(float(mult)); new.at[i, "country_multiplier"] = repr(float(mult)); new.at[i, "sector_calibration_k"] = "1.0"
            new.at[i, "growth_method"] = how
            if str(dem.at[i, "in_existing_electricity_load"]).lower() == "true":
                new.at[i, "existing_electricity_load_2050_mwh"] = repr(float(v))
            refs = [x.strip() for x in str(dem.at[i, "decision_ref"]).replace(";", ",").split(",") if x.strip()]
            new.at[i, "decision_ref"] = ",".join(refs + [x for x in note.split(",") if x not in refs])
        # ---- DFX F2.4: ammonia feedstock gas deducted from the NEU natural-gas rows (floored at 0; the truncated amount is reported) ------------
        nh3_t = float(out_by[c]["ammonia_2050_mt"]) * 1e6
        gas_ded = nh3_t * AMMONIA_GAS_MWH_PER_T
        gas_idx = [i for i in dem.index[m & (dem.sector == NEU_SECTOR) & (dem.carrier == "gas") & (dem.account == NEU_GAS_ACCOUNT)] if new.at[i, "value_2050_mwh"] != ""]
        gas_before = float(sum(float(new.at[i, "value_2050_mwh"]) for i in gas_idx))
        gas_after = max(0.0, gas_before - gas_ded); gas_trunc = max(0.0, gas_ded - gas_before) if gas_ded > 0 else 0.0
        if gas_ded > 0 and gas_before > 0:
            fac = gas_after / gas_before
            for i in gas_idx:
                new.at[i, "value_2050_mwh"] = repr(float(float(new.at[i, "value_2050_mwh"]) * fac))
                new.at[i, "growth_method"] = (new.at[i, "growth_method"] + f"; minus ammonia feedstock gas {nh3_t:.6g} t NH3 x {AMMONIA_GAS_MWH_PER_T} MWh/t = {gas_ded:.6g} MWh (DFX F2.4), "
                                              + (f"truncated at 0 ({gas_trunc:.6g} MWh not deductible)" if gas_trunc > 0 else "not truncated"))
        old_base = float(pd.to_numeric(dem[m & is_el & dem.sector.isin(BASE_SECTORS)].value_2050_mwh, errors="coerce").fillna(0).sum())
        old_tr = float(pd.to_numeric(dem[m & (dem.sector == "Transport")].value_2050_mwh, errors="coerce").fillna(0).sum())
        neu_new = float(pd.to_numeric(new[m & (dem.sector == NEU_SECTOR)].value_2050_mwh, errors="coerce").fillna(0).sum())
        anchors.append(dict(country=c, population_2050_million=a8[c]["pop_2050_million"], population_source=a8[c]["pop_source"],
                            ats_tfec_pc_2050_kgoe=a8[c]["tfec_pc_kgoe"], ats_elec_pc_2050_kwh=a8[c]["elec_pc_kwh"],
                            ats_tfec_2050_mwh=A_tfec[c], ats_elec_2050_mwh=A_el[c],
                            **{f"elec_2019_{s}_mwh": el19[s] for s in SECTORS}, **{f"elec_share_{s}": share[s] for s in SECTORS},
                            **{f"tfec_2019_{s}_mwh": t19[c][s] for s in SECTORS},
                            **{f"ras_sector_anchor_{s}_mwh": tfa[c][s] for s in SECTORS}, ras_member=c in ASEAN10,
                            base_share_of_ats_elec=sum(share[s] for s in BASE_SECTORS),
                            base_load_anchor_mwh=sum(el_anchor[s] for s in BASE_SECTORS),
                            base_load_buildings_agri_mwh=sum(el_anchor[s] for s in ("Residential", "Commercial", "AgricultureOthers")),
                            residential_elec_anchor_mwh=el_anchor["Residential"], commercial_elec_anchor_mwh=el_anchor["Commercial"],
                            agri_other_elec_anchor_mwh=el_anchor["AgricultureOthers"], transport_elec_anchor_mwh=el_anchor["Transport"],
                            industry_elec_ats_implied_mwh=el_anchor["Industry"],
                            transport_anchor_mwh=tr_anchor, transport_fuel_anchor_mwh=tr_fuel_target, transport_fuel_multiplier=m_tr,
                            industry_anchor_mwh=ind_anchor, industry_multiplier=m_ind, industry_multiplier_source=mult_src,
                            neu_multiplier=m_neu, neu_2019_mwh=neu19[c], neu_2050_mwh=neu_new,
                            ammonia_2050_t=nh3_t, neu_gas_2050_before_deduction_mwh=gas_before, ammonia_feedstock_gas_deduction_mwh=min(gas_ded, gas_before),
                            ammonia_feedstock_gas_truncated_mwh=gas_trunc, neu_gas_2050_mwh=gas_after,
                            base_load_ratio_table_mwh=old_base, transport_ratio_table_mwh=old_tr,
                            base_load_nonnegative=bool(sum(el_anchor[s] for s in BASE_SECTORS) >= 0),
                            **{k: v for f in fuel.values() for k, v in ((f"{f['key']}_tfec_anchor_mwh", f["tfec_anchor"]), (f"{f['key']}_fuel_anchor_raw_mwh", f["raw"]),
                                                                        (f"{f['key']}_fuel_anchor_mwh", f["used"]), (f"{f['key']}_fuel_2019_mwh", f["base"]),
                                                                        (f"{f['key']}_fuel_multiplier", f["mult"]), (f"{f['key']}_fuel_zeroed", f["zeroed"]),
                                                                        (f"{f['key']}_fuel_ratio_table_mwh", float(pd.to_numeric(dem[m & (dem.sector == FUEL_SECTORS[f['key']]) & ~is_el].value_2050_mwh, errors="coerce").fillna(0).sum())))}))
    an = pd.DataFrame(anchors)
    an.to_csv(ANCHORS, index=False, float_format="%.12g")
    new.to_csv(ANCHOR_TABLE, index=False)
    pd.DataFrame(bases).to_csv(OUTPUT_BASE, index=False, float_format="%.12g")
    pd.DataFrame(PLAN).to_csv(PLAN_CAPS, index=False)
    out = pd.DataFrame(out_rows)
    out.to_csv(OUTPUT_2050, index=False, float_format="%.12g")
    ten = an[an.country != "TL"]
    tot = dict(base_load_anchor_11_twh=float(an.base_load_anchor_mwh.sum() / 1e6), base_load_buildings_agri_11_twh=float(an.base_load_buildings_agri_mwh.sum() / 1e6),
               base_load_ratio_table_11_twh=float(an.base_load_ratio_table_mwh.sum() / 1e6), transport_anchor_11_twh=float(an.transport_anchor_mwh.sum() / 1e6),
               transport_anchor_10_twh=float(ten.transport_anchor_mwh.sum() / 1e6), transport_ratio_table_11_twh=float(an.transport_ratio_table_mwh.sum() / 1e6),
               **{f"ras_sector_anchor_10_{s}_twh": float(ten[f"ras_sector_anchor_{s}_mwh"].sum() / 1e6) for s in SECTORS},
               **{f"sector_anchor_11_{s}_twh": float(an[f"ras_sector_anchor_{s}_mwh"].sum() / 1e6) for s in SECTORS},
               residential_elec_10_twh=float(ten.residential_elec_anchor_mwh.sum() / 1e6), aeo8_ats_residential_elec_2050_twh=RES_ELEC_ATS_MTOE[1] * MWH_PER_MTOE / 1e6,
               ats_tfec_10_mtoe=float(ten.ats_tfec_2050_mwh.sum() / MWH_PER_MTOE), ats_elec_10_twh=float(ten.ats_elec_2050_mwh.sum() / 1e6),
               neu_2019_11_twh=float(an.neu_2019_mwh.sum() / 1e6), neu_2050_11_twh=float(an.neu_2050_mwh.sum() / 1e6),
               cement_2050_11_mt=float(out.cement_2050_mt.sum()), steel_2050_11_mt=float(out.steel_2050_mt.sum()), ammonia_2050_11_mt=float(out.ammonia_2050_mt.sum()),
               ammonia_feedstock_gas_deducted_11_twh=float(an.ammonia_feedstock_gas_deduction_mwh.sum() / 1e6), ammonia_feedstock_gas_truncated_11_twh=float(an.ammonia_feedstock_gas_truncated_mwh.sum() / 1e6),
               all_base_loads_nonnegative=bool(an.base_load_nonnegative.all()),
               **{f"{k}_fuel_anchor_11_twh": float(an[f"{k}_fuel_anchor_mwh"].sum() / 1e6) for k in FUEL_SECTORS},
               **{f"{k}_fuel_ratio_table_11_twh": float(an[f"{k}_fuel_ratio_table_mwh"].sum() / 1e6) for k in FUEL_SECTORS},
               fuel_anchor_zeroed=[dict(country=r.country, sector=FUEL_SECTORS[k], reason=r[f"{k}_fuel_zeroed"], anchor_mwh=float(r[f"{k}_fuel_anchor_raw_mwh"]))
                                   for _, r in an.iterrows() for k in FUEL_SECTORS if r[f"{k}_fuel_zeroed"]])
    srcs = {p.name: sha256(p) for p in (RATIO_TABLE, SRC_DIR / AEO8_COUNTRY_CSV, SRC_DIR / AEO8_CSV, D2_CSV, WPP_CSV, USGS_XLSX, WORLDSTEEL_XLSX, AMMONIA_CSV)}
    ras = dict(rule="DFX_RULES section 1.3: RAS biproportional fitting, rows first then columns, zero seeds stay zero", countries=list(ASEAN10), sectors=list(SECTORS),
               seed="D1 table base_2019_mwh by sector (energy use; NonEnergyUse excluded)", row_targets="country ATS TFEC anchors (C.8 x D.1)",
               column_targets_printed_mtoe={s: c3[s][1] for s in SECTORS}, k_scale=k_scale, sum_row_targets_mwh=float(row_t.sum()), sum_column_targets_printed_mwh=float(col_printed.sum()),
               column_targets_mwh={s: float(col_t[j]) for j, s in enumerate(SECTORS)}, tolerance=RAS_TOL, max_iterations=RAS_MAX_ITER, iterations=ras_it, row_error=ras_er, column_error=ras_ec,
               tl="outside AEO8: normalised weights (2019 sector energy use x C.3 ATS growth), NEU excluded; TL industry multiplier undefined -> NEU multiplier = KH / LA / MM mean")
    ammonia = dict(rule="DFX F2.1: 2050 production = USGS 2019 production (kt N x 17/14) x max(G, 1)^((2050 - 2019) / 28 x elasticity), no saturation, no plan cap; USGS-unlisted countries 0",
                   source=AMMONIA_CSV.name, source_sha256=srcs[AMMONIA_CSV.name], base_year=BASE_YEAR["ammonia"], elasticity=ELASTICITY, elasticity_range=ELASTICITY_RANGE,
                   mwh_nh3_per_t="ratio table Ammonia column ammonia row (5.166, PyPSA-Eur MWh_NH3_per_tNH3), applied in s3_0_industry.py",
                   feedstock_gas_mwh_per_t=AMMONIA_GAS_MWH_PER_T, feedstock_gas_source="PyPSA-Eur v2025.07.0 config.default.yaml line 850 MWh_CH4_per_tNH3_SMR (SMR route total natural gas: upper bound of the feedstock share; JRC-IDEES-2021 has no ammonia row)",
                   feedstock_gas_mwh_per_t_stoichiometric=AMMONIA_GAS_MWH_PER_T_STOICH, feedstock_gas_account=NEU_GAS_ACCOUNT, truncation="floored at 0, truncated amount reported per country",
                   production_2050_kt={r["country"]: r["ammonia_2050_mt"] * 1e3 for r in out_rows}, production_2019_kt={b["country"]: b["ammonia_base_kt"] for b in bases})
    write_json(dict(script=SCRIPT, sources=srcs, c3_ats_mtoe=c3, sector_growth_electricity=g_el, sector_growth_tfec=g_tfec, residential_electricity_ats_mtoe=RES_ELEC_ATS_MTOE,
                    gdp_growth_2022_2050=g, tl_rule=f"per capita = mean({', '.join(TL_PEERS)}) ATS 2050; population UN WPP 2024 median 2050", elasticity=ELASTICITY,
                    elasticity_range=ELASTICITY_RANGE, saturation_t_per_cap=SATURATION, saturation_range=SATURATION_RANGE, base_year=BASE_YEAR, plan_caps=PLAN, totals=tot,
                    ras=ras, ammonia=ammonia, neu=dict(rule="DFX F1.2: NEU outside the TFEC envelope; 2050 = 2019 x industry multiplier (energy-use anchor / 2019 industry energy use)"),
                    outputs={p.name: sha256(p) for p in (ANCHORS, ANCHOR_TABLE, OUTPUT_BASE, PLAN_CAPS, OUTPUT_2050)}), EVIDENCE)
    pd.set_option("display.width", 250)
    show = an.set_index("country")[["ats_elec_2050_mwh", "base_share_of_ats_elec", "base_load_anchor_mwh", "base_load_ratio_table_mwh", "transport_anchor_mwh", "transport_ratio_table_mwh", "industry_multiplier", "neu_2050_mwh"]].copy()
    show.iloc[:, [0, 2, 3, 4, 5, 7]] /= 1e6
    print(show.round(3).to_string())
    print(out.set_index("country")[["cement_2050_mt", "cement_binding", "steel_2050_mt", "steel_binding", "ammonia_base_mt", "ammonia_2050_mt"]].round(3).to_string())
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in tot.items()})
    print(f"RAS: k = {k_scale:.12f}, {ras_it} iterations, row error {ras_er:.2e}, column error {ras_ec:.2e}")


if __name__ == "__main__":
    main()
