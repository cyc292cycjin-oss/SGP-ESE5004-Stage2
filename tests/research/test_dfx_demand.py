"""DFX v3 (DFX_RULES.md; instruction F0.3, F1.5, F2.5, F3, F4.3, F5.2): the v2 demand - RAS sector split with NEU outside the TFEC envelope,
ammonia by USGS production, HVC scope, registry = build inputs, changed files inside the executed code lists, structural equivalence v1 / v2.

No build, no solve. The network-level checks run only when the DFX builds are present (main checkout results_project/dfx_v3/builds_v1 and
builds_v2, git-ignored); they are skipped elsewhere."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from d1_common import ASEAN, ASEAN10, HVC_FEEDSTOCK_ACCOUNTS, NEU_GAS_ACCOUNT   # noqa: E402
from m08b_demand import AMMONIA_GAS_MWH_PER_T, BASE_YEAR, BASE_SECTORS, ELASTICITY, FUEL_SECTORS, RAS_TOL, RES_ELEC_ATS_MTOE, SECTORS, TL_PEERS, aeo8_country, c3_ats, gdp_growth, ras_split   # noqa: E402

DEM = ROOT / "research_inputs" / "demand_v5"
REG = ROOT / "research_inputs" / "registry_v5"
DFX = ROOT / "research" / "06_scope_redesign" / "p1_dfx_20261026"
RES = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3")
MWH_PER_MTOE = 11.63e6
NON_HVC_OIL_ACCOUNTS = ("NonEnergy:Bitumen", "NonEnergy:Lubricants", "NonEnergy:Paraffin waxes", "NonEnergy:Petroleum coke", "NonEnergy:Gas Oil/ Diesel Oil", "NonEnergy:Motor Gasoline", "NonEnergy:Fuel oil")
TOL = 1e-9


def rel(a, b):
    return abs(a - b) / max(1.0, abs(b))


@pytest.fixture(scope="module")
def data():
    an = pd.read_csv(DEM / "DEMAND_ANCHOR_AEO8_ATS.csv", keep_default_na=False).set_index("country")
    t = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    t["v"] = pd.to_numeric(t.value_2050_mwh, errors="coerce").fillna(0.0); t["b"] = pd.to_numeric(t.base_2019_mwh, errors="coerce").fillna(0.0)
    ratio = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", keep_default_na=False)
    ratio["b"] = pd.to_numeric(ratio.base_2019_mwh, errors="coerce").fillna(0.0)
    out = pd.read_csv(DEM / "INDUSTRY_OUTPUT_2050_M08B.csv", keep_default_na=False).set_index("country")
    summ = pd.read_csv(DEM / "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
    reg = pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    ev = json.loads((DEM / "DEMAND_ANCHOR_M08B_EVIDENCE.json").read_text(encoding="utf-8"))
    rules = json.loads((DFX / "DFX_RULES_NUMBERS.json").read_text(encoding="utf-8"))
    return dict(an=an, t=t, ratio=ratio, out=out, summ=summ, reg=reg, ev=ev, rules=rules)


# ---------------------------------------------------------------------------------------------------------------------------------------------
# F1: RAS sector split, NEU outside the envelope
# ---------------------------------------------------------------------------------------------------------------------------------------------
def test_f1_ras_identities(data):
    """F1.5: sum of the 10-country sector anchors = sum of the country anchors; each sector = k x C.3 ATS 2050; transport about 2,654 TWh;
    the registered prototype values (DFX_RULES_NUMBERS.json) are reproduced."""
    an, ev, rules = data["an"], data["ev"], data["rules"]; a8 = aeo8_country(); c3 = c3_ats()
    A = {c: a8[c]["tfec_pc_kgoe"] * a8[c]["pop_2050_million"] * 1e3 * 11.63 for c in ASEAN10}
    ten = an.loc[ASEAN10]
    for c in ASEAN10:
        assert rel(an.at[c, "ats_tfec_2050_mwh"], A[c]) <= TOL
        assert rel(sum(an.at[c, f"ras_sector_anchor_{s}_mwh"] for s in SECTORS), A[c]) <= TOL          # row constraint
    col_printed = {s: c3[s][1] * MWH_PER_MTOE for s in SECTORS}
    k = sum(A.values()) / sum(col_printed.values())
    assert rel(k, ev["ras"]["k_scale"]) <= TOL and rel(k, rules["k"]) <= TOL
    for s in SECTORS:
        assert rel(float(ten[f"ras_sector_anchor_{s}_mwh"].sum()), k * col_printed[s]) <= TOL         # column constraint
        assert rel(float(ten[f"ras_sector_anchor_{s}_mwh"].sum()) / 1e6, rules["sector_anchors_10_twh"][s]) <= 1e-9
    assert rel(float(sum(ten[f"ras_sector_anchor_{s}_mwh"].sum() for s in SECTORS)), sum(A.values())) <= TOL
    assert float(ten.ras_sector_anchor_Transport_mwh.sum()) / 1e6 == pytest.approx(2653.5, abs=0.5)   # F1.5: about 2,654 TWh
    assert ev["ras"]["iterations"] <= ev["ras"]["max_iterations"] and max(ev["ras"]["row_error"], ev["ras"]["column_error"]) <= RAS_TOL
    assert ev["ras"]["iterations"] == rules["iterations"]


def test_f1_ras_reproduced_from_the_tables(data):
    """Independent RAS re-run from the ratio-table 2019 energy use (NEU excluded) reproduces the anchor table (<= 1e-9); zero seeds absent."""
    an, ratio = data["an"], data["ratio"]; a8 = aeo8_country(); c3 = c3_ats()
    seed = np.array([[float(ratio[(ratio.country == c) & (ratio.sector == s)].b.sum()) for s in SECTORS] for c in ASEAN10])
    assert (seed > 0).all()
    row = np.array([a8[c]["tfec_pc_kgoe"] * a8[c]["pop_2050_million"] * 1e3 * 11.63 for c in ASEAN10])
    col = np.array([c3[s][1] for s in SECTORS]) * MWH_PER_MTOE; col = col * row.sum() / col.sum()
    X, it, er, ec = ras_split(seed, row, col)
    for i, c in enumerate(ASEAN10):
        for j, s in enumerate(SECTORS):
            assert rel(X[i, j], an.at[c, f"ras_sector_anchor_{s}_mwh"]) <= TOL
    assert it == data["ev"]["ras"]["iterations"]
    with pytest.raises(RuntimeError):   # the stop condition: tolerance not reachable in the iteration budget
        ras_split(seed, row, col, tol=1e-300, max_iter=3)


def test_f1_neu_outside_the_envelope(data):
    """F1.2 / F1.5: NEU is in no energy-use anchor (seeds, industry anchor, sector anchors are energy use only); 2050 NEU = 2019 NEU x the industry
    multiplier (energy-use anchor / 2019 industry energy use); TL: industry rows 0 and NEU by the KH / LA / MM mean multiplier."""
    an, t, ratio = data["an"], data["t"], data["ratio"]
    for c in ASEAN:
        r = ratio[ratio.country == c]
        for s in SECTORS:
            assert rel(an.at[c, f"tfec_2019_{s}_mwh"], float(r[r.sector == s].b.sum())) <= TOL                 # energy use only
        neu19 = float(r[r.sector == "NonEnergyUse"].b.sum())
        assert rel(an.at[c, "neu_2019_mwh"], neu19) <= TOL and rel(an.at[c, "industry_anchor_mwh"], an.at[c, "ras_sector_anchor_Industry_mwh"]) <= TOL
        ind19 = an.at[c, "tfec_2019_Industry_mwh"]
        if ind19 > 0:
            assert rel(an.at[c, "industry_multiplier"], an.at[c, "industry_anchor_mwh"] / ind19) <= TOL and an.at[c, "neu_multiplier"] == an.at[c, "industry_multiplier"]
        else:   # TL
            assert c == "TL" and an.at[c, "industry_multiplier"] == 0 and float(t[(t.country == c) & (t.sector == "Industry")].v.sum()) == 0
            assert rel(an.at[c, "neu_multiplier"], float(np.mean([an.at[p, "industry_multiplier"] for p in TL_PEERS]))) <= TOL
        tc = t[(t.country == c) & (t.sector == "NonEnergyUse") & (t.value_2050_mwh != "")]
        non_gas = tc[~((tc.carrier == "gas") & (tc.account == NEU_GAS_ACCOUNT))]
        assert np.allclose(non_gas.v, non_gas.b * an.at[c, "neu_multiplier"], rtol=1e-9, atol=1e-6)       # NEU rows (gas rows: F2.4 below)
        assert rel(an.at[c, "neu_2050_mwh"], float(tc.v.sum())) <= TOL
    assert data["reg"].at["demand_neu_outside_tfec", "value"] == "outside_envelope"


def test_f1_downstream_rules_unchanged(data):
    """F1.4: electricity anchors by the M08b method, transport fuel = RAS transport anchor - transport electricity anchor, sector fuel anchors =
    RAS sector anchor - electricity anchor with negatives zeroed and listed (8 negative cells + TL commercial without 2019 fuel rows)."""
    an, t, ratio, reg, rules = data["an"], data["t"], data["ratio"], data["reg"], data["rules"]; a8 = aeo8_country(); c3 = c3_ats()
    g_el = {s: c3[s][1] / c3[s][0] for s in SECTORS}; g_el["Residential"] = RES_ELEC_ATS_MTOE[1] / RES_ELEC_ATS_MTOE[0]
    zeroed = []
    for c in ASEAN:
        r = ratio[ratio.country == c]; tc = t[t.country == c]
        el19 = {s: float(r[(r.carrier == "electricity") & (r.sector == s)].b.sum()) for s in SECTORS}; w = {s: el19[s] * g_el[s] for s in SECTORS}
        A_el = a8[c]["elec_pc_kwh"] * a8[c]["pop_2050_million"] * 1e3
        ela = {s: A_el * w[s] / sum(w.values()) for s in SECTORS}
        assert rel(an.at[c, "base_load_anchor_mwh"], sum(ela[s] for s in BASE_SECTORS)) <= TOL
        fuel = float(tc[(tc.sector == "Transport") & (tc.carrier != "electricity")].v.sum())
        assert rel(fuel, an.at[c, "ras_sector_anchor_Transport_mwh"] - ela["Transport"]) <= TOL
        for key, s in FUEL_SECTORS.items():
            raw = an.at[c, f"ras_sector_anchor_{s}_mwh"] - ela[s]
            assert rel(an.at[c, f"{key}_fuel_anchor_raw_mwh"], raw) <= TOL
            rows = tc[(tc.sector == s) & (tc.carrier != "electricity") & (tc.value_2050_mwh != "")]
            if raw < 0 or float(rows.b.sum()) <= 0:
                assert float(rows.v.sum()) == 0 and an.at[c, f"{key}_fuel_zeroed"] in ("negative", "no_2019_fuel_rows")
                if raw != 0:
                    zeroed.append((c, key))
            else:
                assert rel(float(rows.v.sum()), raw) <= TOL and (rows.v >= 0).all()
    expected = sorted((cc, k) for cc in ASEAN for k in FUEL_SECTORS if rules["countries"][cc][f"{k}_zeroed"])
    assert sorted(zeroed) == expected == sorted([("BN", "residential"), ("BN", "commercial"), ("MY", "residential"), ("MY", "commercial"), ("SG", "residential"), ("SG", "commercial"),
                                                 ("TH", "residential"), ("TL", "commercial"), ("VN", "residential")])
    assert reg.at["demand_sector_fuel_anchor_zeroed", "value"] == f"{len(zeroed)} cells" and reg.at["demand_sector_split_ras", "value"] == "ras_c3_ats_2050"
    assert float(an.base_load_anchor_mwh.sum()) / 1e6 == pytest.approx(966.9, abs=0.1)   # electricity anchors unchanged (S4R / M08b value)


# ---------------------------------------------------------------------------------------------------------------------------------------------
# F2: ammonia by production, NEU gas deduction
# ---------------------------------------------------------------------------------------------------------------------------------------------
def test_f2_ammonia_production_rule(data):
    """F2.1 / F2.5: 2050 ammonia = USGS 2019 production (reproduced ammonia_production.csv) x max(G, 1)^((2050 - 2019) / 28 x 0.5), no caps; MY > 0;
    countries not listed by USGS (incl. SG) = 0; the ammonia loads of the anchor-mode tables = production x 5.166 MWh/t; registry rows equal."""
    out, summ, reg, rules = data["out"], data["summ"], data["reg"], data["rules"]; g = gdp_growth()
    amm = pd.read_csv(REG / "sources" / "jrc_idees_2021" / "ammonia_production.csv", index_col=0)
    ratios = pd.read_csv(REG / "INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0); mwh_t = float(ratios.at["ammonia", "Ammonia"])
    assert mwh_t == pytest.approx(5.166) and BASE_YEAR["ammonia"] == 2019
    for c in ASEAN:
        base = float(amm.at[c, "2019"]) if (c in amm.index and pd.notna(amm.at[c, "2019"])) else 0.0
        assert rel(float(out.at[c, "ammonia_base_mt"]), base / 1e3) <= TOL
        want = base / 1e3 * max(g[c], 1.0) ** ((2050 - 2019) / 28 * ELASTICITY)
        assert rel(float(out.at[c, "ammonia_2050_mt"]), want) <= TOL and str(out.at[c, "ammonia_percap_cap_mt"]) == "" and str(out.at[c, "ammonia_plan_cap_mt"]) == ""
        assert rel(float(out.at[c, "ammonia_2050_mt"]) * 1e3, rules["ammonia"][c]["nh3_2050_kt"]) <= 1e-9
        for sfx in ("", "_OTHER_USEFUL_HEAT_BANDS", "_TD_SENSITIVITY"):
            s = pd.read_csv(DEM / f"INDUSTRY_2050_SUMMARY_aeo8_ats_anchor{sfx}.csv").set_index("country")
            assert rel(float(s.at[c, "pe_ammonia_mwh"]), float(out.at[c, "ammonia_2050_mt"]) * 1e6 * mwh_t) <= TOL
        assert float(summ.at[c, "pe_ammonia_eu27_share_dropped_mwh"]) >= 0 and summ.at[c, "ammonia_rule"] == "usgs_2019_x_growth_rule"
        assert rel(float(reg.at[f"industry_ammonia_2050_{c}", "value"]), float(summ.at[c, "pe_ammonia_mwh"])) <= TOL
        assert rel(float(reg.at[f"industry_ammonia_output_2050_{c}", "value"]), float(out.at[c, "ammonia_2050_mt"]) * 1e6) <= TOL
    assert float(out.at["MY", "ammonia_2050_mt"]) > 0 and float(out.at["ID", "ammonia_2050_mt"]) > float(out.at["VN", "ammonia_2050_mt"]) > 0
    assert all(float(out.at[c, "ammonia_2050_mt"]) == 0 for c in ("BN", "KH", "LA", "MM", "PH", "SG", "TH", "TL"))
    assert float(out.ammonia_2050_mt.sum()) == pytest.approx(18.996, abs=0.001)
    # sensitivity modes keep the EU27 chemicals-weight method
    rel_s = pd.read_csv(DEM / "INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv").set_index("country")
    assert (rel_s.ammonia_rule == "eu27_chemicals_weight").all() and (rel_s.ammonia_2050_t == 0).all()
    assert reg.at["industry_ammonia_output_rule", "value"] == "usgs_2019_x_growth_rule"


def test_f2_neu_gas_deduction(data):
    """F2.4: the NEU natural-gas rows carry max(0, 2019 x multiplier - NH3_2050 x 10.8 MWh/t); the truncated amounts are recorded (VN)."""
    an, t, out, reg, rules = data["an"], data["t"], data["out"], data["reg"], data["rules"]
    assert AMMONIA_GAS_MWH_PER_T == 10.8 and float(reg.at["industry_ammonia_feedstock_gas_per_t", "value"]) == 10.8
    for c in ASEAN:
        rows = t[(t.country == c) & (t.sector == "NonEnergyUse") & (t.carrier == "gas") & (t.account == NEU_GAS_ACCOUNT) & (t.value_2050_mwh != "")]
        before = float(rows.b.sum()) * an.at[c, "neu_multiplier"]
        ded = float(out.at[c, "ammonia_2050_mt"]) * 1e6 * AMMONIA_GAS_MWH_PER_T
        after = max(0.0, before - ded)
        assert rel(float(rows.v.sum()), after) <= TOL                                   # tables are written with 12 significant digits: relative tolerance
        assert rel(an.at[c, "ammonia_feedstock_gas_deduction_mwh"], min(ded, before)) <= TOL and rel(an.at[c, "ammonia_feedstock_gas_truncated_mwh"], (max(0.0, ded - before) if ded > 0 else 0.0)) <= TOL
        assert rel(float(reg.at[f"industry_ammonia_feedstock_gas_deducted_{c}", "value"]), an.at[c, "ammonia_feedstock_gas_deduction_mwh"]) <= TOL
        assert abs(an.at[c, "neu_gas_2050_mwh"] / 1e6 - rules["ammonia"][c]["neu_gas_after_twh"]) <= 2e-6 and abs(an.at[c, "ammonia_feedstock_gas_truncated_mwh"] / 1e6 - rules["ammonia"][c]["truncated_twh"]) <= 2e-6   # prototype JSON rounded to 1e-6 TWh
    assert an.at["VN", "ammonia_feedstock_gas_truncated_mwh"] > 0 and an.at["ID", "ammonia_feedstock_gas_truncated_mwh"] == 0 and an.at["MY", "ammonia_feedstock_gas_truncated_mwh"] == 0


# ---------------------------------------------------------------------------------------------------------------------------------------------
# F3: HVC scope
# ---------------------------------------------------------------------------------------------------------------------------------------------
def test_f3_hvc_accounts_exhaustive(data):
    """The NEU oil accounts of the demand table are exactly the HVC feedstock accounts plus the registered non-HVC products; the scope row exists."""
    t, reg = data["t"], data["reg"]
    accounts = set(t[(t.sector == "NonEnergyUse") & (t.carrier == "oil")].account)
    assert accounts == set(HVC_FEEDSTOCK_ACCOUNTS) | set(NON_HVC_OIL_ACCOUNTS)
    assert set(HVC_FEEDSTOCK_ACCOUNTS) == {"NonEnergy:Naphtha", "NonEnergy:Ethane", "NonEnergy:Liquefied petroleum gas (LPG)", "NonEnergy:Natural gas liquids"}
    assert reg.at["hvc_primary_fraction_scope", "value"] == "hvc_feedstock_accounts" and float(reg.at["share_HVC_primary_fraction_2050", "value"]) == 0.4
    from phase4_static import config
    assert config(ROOT, "integrated")["research"]["s2"]["industry"]["hvc_recycling_applies_to_naphtha"] is True


# ---------------------------------------------------------------------------------------------------------------------------------------------
# F4: registry = build inputs (tables always; network when present)
# ---------------------------------------------------------------------------------------------------------------------------------------------
def _table_value(sel: str, src: str):
    kv = dict(re.findall(r"(\w+)=([^\s]+)", sel))
    if src == "DEMAND_ANCHOR_AEO8_ATS.csv":
        an = pd.read_csv(DEM / src, keep_default_na=False).set_index("country")
        m = re.match(r"sum\((\w+)\) over ASEAN10", sel)
        return float(an.loc[ASEAN10, m.group(1)].sum()) if m else float(an.at[kv["country"], sel.split()[0]])
    if src.startswith("DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER"):
        t = pd.read_csv(DEM / src, keep_default_na=False); t["v"] = pd.to_numeric(t.value_2050_mwh, errors="coerce").fillna(0.0)
        m = t.v.notna()
        for k, v in kv.items():
            m &= t[k] == v
        return float(t[m].v.sum())
    if src == "INDUSTRY_OUTPUT_2050_M08B.csv":
        o = pd.read_csv(DEM / src, keep_default_na=False).set_index("country"); col = sel.split()[0]
        return float(o.at[kv["country"], col]) * (1e6 if "x 1e6" in sel else 1.0)
    if src.startswith("INDUSTRY_2050_SUMMARY"):
        s = pd.read_csv(DEM / src).set_index("country"); col = sel.split()[0]
        if "(all countries)" in sel:
            assert s[col].nunique() == 1
            return float(s[col].iloc[0])
        return float(s.at[kv["country"], col])
    if src == "PROCESS_EMISSIONS_2019_2050.csv":
        p = pd.read_csv(REG / src)
        r = p[(p.country == kv["country"]) & (p.group == kv["group"])]
        assert len(r) == 1
        return float(r.tco2_2050_ats_anchor.iloc[0])
    raise AssertionError(f"unknown map source {src}")


def test_f4_registry_rows_equal_the_tables(data):
    """F4.3: every mapped numeric registry row equals the value read back from the table the build reads (relative tolerance 1e-9)."""
    reg = data["reg"]; mp = pd.read_csv(REG / "REGISTRY_NETWORK_INPUT_MAP.csv", keep_default_na=False)
    rows = mp[mp.kind == "table"]
    assert len(rows) >= 150
    bad = []
    for r in rows.itertuples():
        want = _table_value(r.selector, r.source); have = float(reg.at[r.param_id, "value"])
        if rel(have, want) > TOL:
            bad.append((r.param_id, have, want))
    assert not bad, bad[:10]
    # the DMD D2 stale rows are gone: the per-country industry rows now carry the anchor-mode values
    summ = data["summ"]
    for c in ASEAN:
        for key, col in (("ammonia", "pe_ammonia_mwh"), ("methanol", "pe_methanol_mwh"), ("low_temperature_heat", "pe_heat_mwh")):
            assert rel(float(reg.at[f"industry_{key}_2050_{c}", "value"]), float(summ.at[c, col])) <= TOL
        assert rel(float(reg.at[f"demand_tfec_2050_{c}", "value"]), float(data["an"].at[c, "ats_tfec_2050_mwh"])) <= TOL
    for pid in ("cookstove_efficiency_basic_ID", "cookstove_efficiency_basic_TH", "cookstove_efficiency_basic_default", "cookstove_efficiency_modern", "clean_cooking_switch",
                "industry_useful_heat_efficiency", "hvc_primary_fraction_scope", "demand_node_allocation", "aeo8_c3_ats_2050_Transport", "demand_sector_split_ras", "industry_ammonia_output_rule",
                "industry_ammonia_feedstock_gas_per_t", "demand_neu_outside_tfec"):
        assert pid in reg.index and reg.at[pid, "status"] in ("REGISTERED", "REFERENCE_ONLY"), pid
    assert float(reg.at["aeo8_c3_ats_2050_Transport", "value"]) == 228.2 and float(reg.at["aeo8_c3_ats_2050_Industry", "value"]) == 387.0
    assert len(pd.read_csv(REG / "REGISTRY_CHANGELOG_DFX.csv", keep_default_na=False)) > 150


def _net(path):
    import pypsa
    return pypsa.Network(str(path))


def _load_table(n):
    w = n.snapshot_weightings.generators
    e = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum()
    L = n.loads[["bus", "carrier", "account", "country"]].copy()
    for c in ("account", "country", "carrier"):
        L[c] = L[c].fillna("").astype(str)
    L["mwh"] = e.reindex(L.index).fillna(0.0).values
    return L


@pytest.mark.skipif(not (RES / "builds_v2" / "integrated" / "integrated_2920_3h_unsolved.nc").exists(), reason="DFX v2 build not present")
def test_f4_registry_rows_equal_the_network(data):
    """F4.3 network level: the mapped loads of the built v2 network equal the registry rows (1e-8: p_set = annual / 8760 round trip); meta parameters equal."""
    reg = data["reg"]; mp = pd.read_csv(REG / "REGISTRY_NETWORK_INPUT_MAP.csv", keep_default_na=False)
    n = _net(RES / "builds_v2" / "integrated" / "integrated_2920_3h_unsolved.nc"); L = _load_table(n)
    bad = []
    for r in mp[mp.kind == "network"].itertuples():
        kv = dict(re.findall(r"(\w+)=([^=]+?)(?= \w+=|$)", r.selector.split(") ", 1)[1]))
        m = pd.Series(True, index=L.index)
        for k, v in kv.items():
            m &= L[k] == v.strip()
        want = float(L[m].mwh.sum()); have = float(reg.at[r.param_id, "value"])
        if abs(have - want) > 1e-8 * max(1.0, abs(have)):
            bad.append((r.param_id, have, want))
    assert not bad, bad[:10]
    par = n.meta["s2_demand_ledger"]["parameters"]
    assert par["cookstove_basic"]["ID"] == float(reg.at["cookstove_efficiency_basic_ID", "value"]) and par["cookstove_basic"]["TH"] == float(reg.at["cookstove_efficiency_basic_TH", "value"])
    assert par["cookstove_basic_default"] == float(reg.at["cookstove_efficiency_basic_default", "value"]) and par["cookstove_modern"] == float(reg.at["cookstove_efficiency_modern", "value"])
    assert par["hvc_primary_fraction"] == float(reg.at["share_HVC_primary_fraction_2050", "value"]) and par["hvc_primary_scope"] == list(HVC_FEEDSTOCK_ACCOUNTS)
    # F3 at the network level: oil feedstock loads = HVC accounts x 0.4 + other products x 1.0
    t = data["t"]
    for c in ASEAN:
        tc = t[(t.country == c) & (t.sector == "NonEnergyUse") & (t.carrier == "oil")]
        want = float(tc[tc.account.isin(HVC_FEEDSTOCK_ACCOUNTS)].v.sum()) * 0.4 + float(tc[~tc.account.isin(HVC_FEEDSTOCK_ACCOUNTS)].v.sum())
        have = float(L[(L.country == c) & (L.account == "NonEnergy:oil")].mwh.sum())
        assert abs(have - want) <= 1e-6 + 1e-8 * want


# ---------------------------------------------------------------------------------------------------------------------------------------------
# F0.3: changed files are inside the executed code lists
# ---------------------------------------------------------------------------------------------------------------------------------------------
def test_f0_changed_scripts_in_the_executed_lists():
    """F0.3: every scripts_project file changed by DFX (base commit 55ab07c0 -> HEAD, plus uncommitted changes) is in the actual-execution lists of the
    build, solve, post-processing, batch or data-chain runs (CODE_MAP_DATA.json executed_union)."""
    data = json.loads((DFX / "CODE_MAP_DATA.json").read_text(encoding="utf-8"))
    executed = set(data["executed_union"])
    out = subprocess.run(["git", "diff", "--name-only", "55ab07c0", "--", "scripts_project"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "scripts_project"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    changed = sorted(set(out) | set(untracked))
    assert changed, "no DFX change under scripts_project"
    outside = [p for p in changed if p not in executed]
    assert not outside, outside


# ---------------------------------------------------------------------------------------------------------------------------------------------
# F5.2: structural equivalence v1 / v2 (networks present only)
# ---------------------------------------------------------------------------------------------------------------------------------------------
ALLOWED_META = {"s2_demand_ledger", "demand_owners", "demand_identity", "research_config_sha256", "dust_cleanup", "s2_build", "research_inputs", "registry_sha256", "build"}


def _diff_networks(a, b):
    """Component-by-component comparison; returns the list of differences (component, kind, detail)."""
    diffs = []
    for ca in a.iterate_components():
        name = ca.name
        da, db = ca.df.copy(), b.df(name).copy()
        if name == "Load":
            continue
        if set(da.index) != set(db.index):
            diffs.append((name, "index", sorted(set(da.index) ^ set(db.index))[:20]))
            common = sorted(set(da.index) & set(db.index)); da, db = da.loc[common], db.loc[common]
        else:
            da, db = da.sort_index(), db.sort_index()
        cols = sorted(set(da.columns) | set(db.columns))
        for col in cols:
            if col not in da or col not in db:
                diffs.append((name, "column", col)); continue
            x, y = da[col], db[col]
            if x.dtype.kind in "fi" and y.dtype.kind in "fi":
                ne = ~(np.isclose(x.astype(float), y.astype(float), rtol=1e-12, atol=1e-9) | (x.isna() & y.isna()))
            else:
                ne = x.astype(str) != y.astype(str)
            if ne.any():
                diffs.append((name, "value", (col, list(da.index[ne])[:20], int(ne.sum()))))
        for attr, pa in ca.pnl.items():
            pb = b.pnl(name).get(attr)
            if pb is None or set(pa.columns) != set(pb.columns):
                if len(pa.columns) or (pb is not None and len(pb.columns)):
                    diffs.append((name, "pnl_columns", (attr, sorted(set(pa.columns) ^ set(pb.columns if pb is not None else []))[:20])))
                continue
            if len(pa.columns) and not np.allclose(pa.values, pb[pa.columns].values, rtol=1e-12, atol=1e-9, equal_nan=True):
                diffs.append((name, "pnl_value", attr))
    if not a.snapshots.equals(b.snapshots) or not a.snapshot_weightings.equals(b.snapshot_weightings):
        diffs.append(("snapshots", "value", ""))
    return diffs


@pytest.mark.skipif(not (RES / "builds_v2" / "integrated" / "integrated_2920_3h_unsolved.nc").exists() or not (RES / "builds_v1" / "integrated" / "integrated_2920_3h_unsolved.nc").exists(),
                    reason="DFX v1 / v2 builds not present")
@pytest.mark.parametrize("scenario,res", [("integrated", "2920_3h"), ("disconnected", "2920_3h"), ("integrated", "365_24h"), ("disconnected", "365_24h")])
def test_f5_structural_equivalence(scenario, res):
    """F5.2 / instruction section 2: v2 differs from v1 (same code path, same worktree) only in loads / loads_t.p_set and the listed derived fields:
    process-emission generators (EDGAR x the industry multiplier) and the demand-related meta keys."""
    a = _net(RES / "builds_v1" / scenario / f"{scenario}_{res}_unsolved.nc"); b = _net(RES / "builds_v2" / scenario / f"{scenario}_{res}_unsolved.nc")
    diffs = _diff_networks(a, b)
    allowed, other = [], []
    for d in diffs:
        name, kind, detail = d
        if name == "Generator" and kind == "value" and detail[0] == "p_nom" and all(i.endswith("process emissions source") for i in detail[1]) and detail[2] == len(detail[1]):
            allowed.append(d)
        else:
            other.append(d)
    assert not other, other[:10]
    # loads: same names, carriers and buses; p_set differs
    assert set(a.loads.index) == set(b.loads.index) and (a.loads.sort_index().carrier == b.loads.sort_index().carrier).all() and (a.loads.sort_index().bus == b.loads.sort_index().bus).all()
    assert not np.allclose(a.loads.sort_index().p_set.fillna(0).values, b.loads.sort_index().p_set.fillna(0).values)
    meta_diff = {k for k in set(a.meta) | set(b.meta) if json.dumps(a.meta.get(k), sort_keys=True, default=str) != json.dumps(b.meta.get(k), sort_keys=True, default=str)}
    assert meta_diff <= ALLOWED_META, meta_diff - ALLOWED_META
    (RES / "equivalence").mkdir(exist_ok=True)
    (RES / "equivalence" / f"EQUIVALENCE_{scenario}_{res}.json").write_text(json.dumps(dict(scenario=scenario, resolution=res, allowed=[list(map(str, d)) for d in allowed], other=[], meta_diff=sorted(meta_diff),
                                                                                             loads=len(a.loads), loads_changed=int((~np.isclose(a.loads.sort_index().p_set.fillna(0).values, b.loads.sort_index().p_set.fillna(0).values)).sum())), indent=1), encoding="utf-8")
