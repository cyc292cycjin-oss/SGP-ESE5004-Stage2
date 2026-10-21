"""S2-1: research cost table for the network builder from the active cost layer (decisions 46, 50, 52).

The active layer (research.cost_layer.active) supplies every technology-data technology as an
annualised wide table (see s2_0_cost_layer_v015.py). Two grade-C rows that technology-data lacks
are appended from the D1 registry / AEO8 Appendix D: `nuclear SMR` (decision 46) and `geothermal`
investment/FOM/VOM (decision 52). External fossil fuel prices are the D1 registry WEO 2025 2050
values (EUR2020/MWh NCV) of the scenario research.fuels.price_scenario (S4C-0, decision 85: steps main,
nze low-price sensitivity, cps optional; one scenario for gas, oil and coal), not the technology-data
European fuel rows; lignite keeps the layer value (WEO Table 2.3 has no lignite price).
Every row of the resulting table is tagged with its source layer in the returned ledger.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

AEO8_PDF_SHA = "48c2a81913ed785cb0e14a55e332ea7bc87f912f7fabfbc8c654e09b66b11c06"
DISCOUNT = 0.07
FUEL_CARRIERS = ("gas", "oil", "coal")
# S4C-0 (decision 85): registry rows per WEO 2025 Table 2.3 scenario; the _main / _high_price suffixes are the D1 names (d1_fuel_prices.py)
FUEL_PRICE_IDS = {"steps": "fuel_price_{c}_STEPS_2050_high_price", "nze": "fuel_price_{c}_NZE_2050_main", "cps": "fuel_price_{c}_CPS_2050_optional"}


D15_FILE = Path("research_inputs/cost_layers_v5/sources/AEO8_Table_D15_Cost_Summary.csv")   # AEO8 Appendix D Table D.15 (kUSD/MW, kUSD/MW/a, USD/MWh)


def annuity(n, r):
    return r / (1.0 - 1.0 / (1.0 + r) ** n) if r > 0 else 1.0 / n


def _sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def smr_ratios(d15_path: Path) -> dict:
    """M08-2 (decision 131): AEO8 Table D.15 same-table ratios SMR / LWR (currency-year neutral) - investment 9,600 / 9,000,
    FOM share of investment (110.0 / 9,600) / (75.3 / 9,000), VOM 2.2 / 5.1."""
    t = pd.read_csv(d15_path).set_index("sub-technology")
    s, l = t.loc["Nuclear SMR"], t.loc["Nuclear LWR"]
    return dict(investment=float(s.capital_cost) / float(l.capital_cost),
                fom_share=(float(s.FOM) / float(s.capital_cost)) / (float(l.FOM) / float(l.capital_cost)),
                vom=float(s.VOM) / float(l.VOM))


def registry_value(reg: pd.DataFrame, pid: str) -> float:
    r = reg.loc[pid]
    if r["status"] == "DATA_PENDING":
        raise ValueError(f"registry value pending: {pid}")
    return float(r["value"])


def fuel_price_scenario(cfg: dict) -> str:
    """research.fuels.price_scenario (S4C-0, decision 85): steps (main) | nze (low-price sensitivity) | cps (optional)."""
    s = str(((cfg.get("research") or {}).get("fuels") or {}).get("price_scenario", "")).lower()
    if s not in FUEL_PRICE_IDS:
        raise ValueError(f"research.fuels.price_scenario must be one of {sorted(FUEL_PRICE_IDS)}, got {s!r}")
    return s


def fuel_price_ids(cfg: dict) -> dict:
    """{carrier: registry param_id} for gas, oil and coal, all from one WEO scenario (asserted)."""
    s = fuel_price_scenario(cfg)
    ids = {c: FUEL_PRICE_IDS[s].format(c=c) for c in FUEL_CARRIERS}
    tags = {pid.split("_")[3] for pid in ids.values()}   # fuel_price_<carrier>_<SCENARIO>_2050_<tag>
    if len(tags) != 1:
        raise AssertionError(f"fuel price scenarios differ across gas / oil / coal: {ids}")
    return ids


def fuel_price(cfg: dict, reg: pd.DataFrame, carrier: str) -> float:
    return registry_value(reg, fuel_price_ids(cfg)[carrier])


def layer_files(spec: dict) -> dict:
    """M08-1 (decision 131): a layer with rebase_variants resolves file / prepared_file by its rebase_index
    (eea_hicp_rate main | ea20_gdp_deflator comparison); other layers keep their own file / prepared_file."""
    variants = spec.get("rebase_variants")
    if not variants:
        return dict(spec)
    idx = spec.get("rebase_index")
    if idx not in variants:
        raise ValueError(f"rebase_index must be one of {sorted(variants)}, got {idx!r}")
    return dict(spec, **variants[idx])


def load_active_layer(repo: Path, cfg: dict):
    cl = cfg["research"]["cost_layer"]
    name = cl["active"]
    spec = layer_files(cl["layers"][name])
    if "prepared_file" not in spec:
        raise ValueError(f"cost layer {name} has no prepared (annualised) table; only layers with prepared_file can price the network")
    manifest = json.loads((repo / spec["file"]).read_text())
    if spec.get("rebase_variants") and (manifest.get("rebase") or {}).get("index") != spec["rebase_index"]:
        raise ValueError(f"layer manifest rebase index {(manifest.get('rebase') or {}).get('index')!r} differs from rebase_index {spec['rebase_index']!r}")
    wide = pd.read_csv(repo / spec["prepared_file"], index_col=0)
    return name, spec, manifest, wide


def build_research_costs(repo: Path, cfg: dict, registry_csv: Path):
    repo = Path(repo)
    name, spec, manifest, c = load_active_layer(repo, cfg)
    reg = pd.read_csv(registry_csv, dtype=str, keep_default_na=False).set_index("param_id")
    ledger = {"layer": name, "layer_file": spec["file"], "prepared_file": spec["prepared_file"], "rows": {}, "overrides": [],
              "rebase_index": (manifest.get("rebase") or {}).get("index", "ea20_gdp_deflator")}
    for t in c.index:
        ledger["rows"][t] = name
    # --- fuel prices: D1 registry (WEO 2025 2050 -> EUR2020/MWh NCV), decision D1-1; scenario per research.fuels.price_scenario (S4C-0, decision 85)
    ledger["fuel_price_scenario"] = fuel_price_scenario(cfg)
    for carrier, pid in fuel_price_ids(cfg).items():
        v = registry_value(reg, pid)
        ledger["overrides"].append(dict(technology=carrier, parameter="fuel", before=float(c.at[carrier, "fuel"]), after=v, source=pid, tier=reg.loc[pid, "tier"]))
        c.at[carrier, "fuel"] = v
        c.at[carrier, "marginal_cost"] = v / float(c.at[carrier, "efficiency"]) if float(c.at[carrier, "efficiency"]) else v
    cl = cfg["research"]["cost_layer"]
    f_aeo8 = float(cl.get("aeo8_price_year_factor", 1.0))   # M08-2 (decision 131): AEO8 D.15 price year DATA_PENDING -> factor (main 1.0, sensitivity 0.86)
    smr_source = cl.get("smr_cost_source", "aeo8_author_rule_2050")
    ufuel = float(c.at["uranium", "fuel"])
    if smr_source == "td_nuclear_x_aeo8_ratio":
        # --- SMR (M08-2, decision 131, registry nuclear_cost_rule): technology-data nuclear x AEO8 D.15 same-table ratios SMR / LWR
        q = smr_ratios(repo / D15_FILE)
        nuc = c.loc["nuclear"]
        inv = float(nuc.investment) * q["investment"]; fom = float(nuc.FOM) * q["fom_share"]; vom = float(nuc.VOM) * q["vom"]
        life = float(nuc.lifetime); eff = float(nuc.efficiency); rate = float(nuc["discount rate"])
        ledger["rows"]["nuclear SMR"] = ("technology-data v0.15.0 nuclear x AEO8 Table D.15 ratios SMR / LWR (investment 9,600 / 9,000, FOM share (110.0 / 9,600) / (75.3 / 9,000), "
                                         "VOM 2.2 / 5.1); lifetime, efficiency, discount rate = nuclear; fuel = layer uranium (registry nuclear_cost_rule, grade C)")
        ledger["smr_rule"] = dict(source=smr_source, ratios=q, d15_file=str(D15_FILE), d15_sha256=_sha(repo / D15_FILE))
    elif smr_source == "aeo8_author_rule_2050":
        # --- SMR (former, decision 46, grade C, AEO8 D.15 Nuclear SMR x ECB 2020 FX x aeo8_price_year_factor) ------------------------
        inv = registry_value(reg, "smr_investment") * 1e3 * f_aeo8  # EUR/kW -> EUR/MW
        fom = registry_value(reg, "smr_FOM"); vom = registry_value(reg, "smr_VOM") * f_aeo8
        life = registry_value(reg, "smr_lifetime_proxy"); eff = registry_value(reg, "smr_efficiency_proxy"); rate = DISCOUNT
        ledger["rows"]["nuclear SMR"] = "AEO8 Table D.15 Nuclear SMR via D1 registry (grade C, +-30 %); lifetime/efficiency proxies = technology-data nuclear; fuel = layer uranium"
        ledger["smr_rule"] = dict(source=smr_source, aeo8_price_year_factor=f_aeo8)
    else:
        raise ValueError(f"research.cost_layer.smr_cost_source must be td_nuclear_x_aeo8_ratio or aeo8_author_rule_2050, got {smr_source!r}")
    c.loc["nuclear SMR", ["investment", "FOM", "VOM", "lifetime", "efficiency", "fuel", "discount rate", "CO2 intensity"]] = [inv, fom, vom, life, eff, ufuel, rate, 0.0]
    c.at["nuclear SMR", "fixed"] = (annuity(life, rate) + fom / 100.0) * inv
    c.at["nuclear SMR", "marginal_cost"] = vom + ufuel / eff
    # --- geothermal (decision 52, grade C): AEO8 D.15 "Geothermal average" x FX, no decline; M08-2: new-build investment x aeo8_price_year_factor
    fx = registry_value(reg, "fx_usd_to_eur_2020")
    geo_inv_kusd, geo_fom_kusd, geo_vom_usd = 4100.0, 19.5, 0.3  # AEO8 Table D.15 row "Geothermal average" (kUSD/MW, kUSD/MW/a, USD/MWh)
    g_inv = geo_inv_kusd * fx * 1e3 * f_aeo8; g_fom = geo_fom_kusd / geo_inv_kusd * 100.0; g_vom = geo_vom_usd * fx
    c.at["geothermal", "aeo8_price_year_factor"] = f_aeo8   # add_existing_geothermal divides it out: the existing-stock FOM constant keeps the unscaled basis
    ledger["aeo8_price_year_factor"] = f_aeo8
    g_life = float(c.at["geothermal", "lifetime"]) if "geothermal" in c.index and np.isfinite(c.at["geothermal", "lifetime"]) else 30.0
    for k, v in [("investment", g_inv), ("FOM", g_fom), ("VOM", g_vom), ("lifetime", g_life), ("efficiency", 1.0), ("fuel", 0.0), ("discount rate", DISCOUNT)]:
        c.at["geothermal", k] = v
    c.at["geothermal", "fixed"] = (annuity(g_life, DISCOUNT) + g_fom / 100.0) * g_inv
    c.at["geothermal", "marginal_cost"] = g_vom
    ledger["rows"]["geothermal"] = ("AEO8 Table D.15 Geothermal average 4,100 kUSD/MW, FOM 19.5 kUSD/MW/a, VOM 0.3 USD/MWh x ECB 2020 FX (grade C, +-30 %); "
                                    "lifetime 30 a and CO2 intensity from technology-data geothermal; v0.15.0 has no geothermal investment/VOM")
    ledger["aeo8_source_sha256"] = AEO8_PDF_SHA
    # --- Fischer-Tropsch: technology-data v0.15.0 labels the investment unit 'EUR/kW_FT/year'; treated as EUR/kW_FT (per-kW rule x1e3 already applied)
    if "Fischer-Tropsch" in c.index:
        ledger["notes"] = ["Fischer-Tropsch investment unit label in v0.15.0 is 'EUR/kW_FT/year' (1,002.6); interpreted as EUR/kW_FT total investment (INFERENCE), annualised with lifetime 25 a"]
    # --- completeness for the builder -----------------------------------------------------------------
    for col in ["fixed", "marginal_cost", "efficiency", "lifetime", "VOM", "FOM", "investment", "fuel", "CO2 intensity", "discount rate"]:
        if col not in c:
            c[col] = np.nan
    c["co2_emissions"] = c["CO2 intensity"]
    return c, ledger


def cost(costs: pd.DataFrame, tech: str, key: str) -> float:
    if tech not in costs.index:
        raise KeyError(f"cost row missing: {tech}")
    v = costs.at[tech, key]
    if not np.isfinite(float(v)):
        raise ValueError(f"cost value missing: {tech}.{key}")
    return float(v)


def write_costs(costs: pd.DataFrame, ledger: dict, out_dir: Path):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "costs_active_research.csv"
    costs.to_csv(p, float_format="%.12g")
    (out_dir / "costs_active_research_ledger.json").write_text(json.dumps(ledger, indent=1, sort_keys=True, default=str) + "\n")
    return p
