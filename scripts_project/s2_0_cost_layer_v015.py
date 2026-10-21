"""S2-0.1 (decision 50): technology-data v0.15.0 cost layer rebased to EUR2020 -> new main layer.

* Source: PyPSA/technology-data tag v0.15.0 (commit 07e43575c7996a988c60964d00772376ab9bd10c),
  outputs/costs_2050.csv (release asset, copied to cost_layers_v5/sources/costs_2050_v0.15.0.csv).
* Currency base year: config.yaml `eur_year: 2025` (release notes v0.14.0: "Changed currency year
  from 2020 to 2025 ... using updated Eurostat inflation rates"; v0.15.0: the `currency_year`
  column now reflects the inflation-adjusted year). Every monetary row carries currency_year 2025
  except two rows (2020, 2019), which are rebased from their own year.
* M08-1 (decision 131; research.cost_layer.layers.technology_data_v0_15_0_2050_eur2020.rebase_index):
  - eea_hicp_rate (MAIN, default): the rebase uses the index technology-data used to inflate - Eurostat
    HICP prc_hicp_aind annual average rate of change, row "European Economic Area" (USD rows: "United
    States"), read from technology-data's own input inputs/prc_hicp_aind__custom_20097956_spreadsheet.xlsx
    and chained year by year exactly as scripts/_helpers.py get_factor (line 220 selects the row): EUR2025 ->
    EUR2020 = 1 / prod(1 + r, 2021..2025) = 1 / 1.25733. The +4.8 % residual of the former rebase vanishes.
    The user download (Eurostat default view, Sheet 6) is a cross-check of the rates (recorded in the manifest).
    Output: cost_layers_v5/technology_data_v0.15.0_EUR2020/ (the main layer path read by every consumer).
  - ea20_gdp_deflator (comparison, former S2-0 main): ECB EA20 GDP deflator (series
    MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N, 2020 = 100), factor = 100 / index(currency_year), applied to
    every monetary row including the USD rows (former behaviour, unchanged). Output:
    cost_layers_v5/technology_data_v0.15.0_EUR2020_ea20gdp/ (byte-identical CSVs to the former main layer).
  Both variants are written on every run; non-monetary rows are unchanged in both.
* Also writes the annualised wide table used by the network builder (same formula as the upstream
  prepare_costs: fixed = (annuity(lifetime, discount rate) + FOM/100) x investment; marginal =
  VOM + fuel / efficiency) and the v0.13.2 -> v0.15.0 comparison for the main technologies.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from d1_common import (COST_DIR, EA20_DEFLATOR_FILE, EA20_DEFLATOR_SERIES, EA20_DEFLATOR_URL, HICP_DOWNLOAD_FILE, HICP_DOWNLOAD_ORIGINAL_NAME,
                       HICP_EEA_ROW, HICP_TD_FILE, HICP_US_ROW, REG_DIR, ROOT, TECHNOLOGY_DATA_V0_13_2, Registry, ea20_deflator,
                       eurostat_download_rates, hicp_factor, hicp_rates, sha256, write_csv, write_json)

SCRIPT = "scripts_project/s2_0_cost_layer_v015.py"
SRC = COST_DIR / "sources"
V015 = SRC / "costs_2050_v0.15.0.csv"
V015_CONFIG = SRC / "technology_data_v0.15.0_config.yaml"
V015_NOTES = SRC / "technology_data_v0.15.0_release_notes.rst"
V0132 = TECHNOLOGY_DATA_V0_13_2 / "outputs" / "costs_2050.csv"
MAIN_INDEX = "eea_hicp_rate"                     # M08-1 (decision 131) main; config key rebase_index
OUT_DIRS = {"eea_hicp_rate": COST_DIR / "technology_data_v0.15.0_EUR2020",
            "ea20_gdp_deflator": COST_DIR / "technology_data_v0.15.0_EUR2020_ea20gdp"}
OUT = OUT_DIRS[MAIN_INDEX]
TD_HELPERS_SHA = "a386c21935cdd2541f38b0230529e6e01d6a00e0dc776521858d958cdfcb3786"   # technology-data v0.15.0 scripts/_helpers.py (tarball member, not copied)
TD_HELPERS_LINE = 220                            # row_to_use = "European Economic Area ..." (prepare_inflation_rate)
BY_YEAR_SRC = SRC / "technology_data_v0.15.0" / "outputs"   # costs_<year>.csv of the release (tarball members, SOURCES_SHA256.txt)
BY_YEARS = (2020, 2025, 2030, 2035, 2040, 2045, 2050)      # technology-data v0.15.0 config.yaml years
TAG = "v0.15.0"
TAG_COMMIT = "07e43575c7996a988c60964d00772376ab9bd10c"
TARBALL_SHA = "c4787c1d72b9ec9fae032d37f906a4d6c92d4adfe111c55680f59f62bb162ccb"  # github archive refs/tags/v0.15.0.tar.gz
RELEASE_ASSET_URL = "https://github.com/PyPSA/technology-data/releases/download/v0.15.0/costs_2050.csv"
EUR_YEAR = 2025
# upstream fill values (pypsa-asean configs/config.default.yaml costs.fill_values) used by prepare_costs
FILL = {"FOM": 0.0, "VOM": 0.0, "efficiency": 1.0, "fuel": 0.0, "investment": 0.0, "lifetime": 25.0,
        "CO2 intensity": 0.0, "discount rate": 0.07}
MAIN_TECHS = ["solar-utility", "solar-rooftop", "onwind", "offwind", "offwind-float", "HVDC submarine", "HVAC submarine",
              "HVDC overhead", "HVAC overhead", "nuclear", "uranium", "electrolysis", "battery storage", "battery inverter",
              "direct air capture", "CO2 pipeline", "CO2 submarine pipeline", "CO2 storage tank", "CCGT", "OCGT", "SMR",
              "SMR CC", "biogas", "biogas upgrading", "solid biomass", "digestible biomass", "biomass CHP", "biomass EOP",
              "biomass CHP capture", "cement capture", "Fischer-Tropsch", "gas", "coal", "oil", "waste CHP",
              "electric boiler steam", "industrial heat pump high temperature", "gas boiler steam", "biomass boiler",
              "H2 (g) pipeline", "hydrogen storage tank type 1 including compressor", "fuel cell", "H2 (g) submarine pipeline",
              "geothermal", "PHS", "hydro", "ror", "CO2 dense phase compression"]
PARAMS = ["investment", "FOM", "VOM", "lifetime", "efficiency", "fuel", "CO2 intensity"]


def annuity(n, r):
    n = np.asarray(n, dtype=float); r = np.asarray(r, dtype=float)
    return np.where(r > 0, r / (1.0 - 1.0 / (1.0 + r) ** n), 1.0 / n)


def monetary(unit: str) -> bool:
    return bool(re.search(r"EUR|USD", str(unit)))


def currency(unit: str) -> str:
    return "USD" if "USD" in str(unit) else "EUR"


def rebase_factor(index: str):
    """(currency_year, currency) -> factor to money of 2020 for research.cost_layer...rebase_index (M08-1, decision 131)."""
    if index == "ea20_gdp_deflator":   # former S2-0 main: EA20 GDP deflator on every monetary row (USD rows included, unchanged behaviour)
        defl = ea20_deflator()
        return lambda y, cur: defl[2020] / defl[y]
    if index == "eea_hicp_rate":       # technology-data's own index: EEA rate for EUR, United States rate for USD (prepare_inflation_rate)
        rates = {"EUR": hicp_rates(HICP_TD_FILE, HICP_EEA_ROW), "USD": hicp_rates(HICP_TD_FILE, HICP_US_ROW)}
        return lambda y, cur: hicp_factor(rates[cur], y, 2020)
    raise ValueError(f"rebase_index must be one of {sorted(OUT_DIRS)}, got {index!r}")


def rebase(df: pd.DataFrame, factor) -> pd.DataFrame:
    """factor: dict year -> EA20 deflator index (former signature) or callable (currency_year, currency) -> factor to 2020."""
    if isinstance(factor, dict):
        defl = factor
        factor = lambda y, cur: defl[2020] / defl[y]
    d = df.copy()
    d["monetary"] = d.unit.map(monetary)
    d["source_currency_year"] = d.currency_year
    fac = []
    for _, r in d.iterrows():
        if r.monetary:
            y = int(r.currency_year) if pd.notna(r.currency_year) else None
            if y is None:
                raise ValueError(f"monetary row without currency_year: {r.technology} {r.parameter}")
            fac.append(factor(y, currency(r.unit)))
        else:
            fac.append(1.0)
    d["conversion_factor"] = fac
    d["value_v0_15_0"] = d.value
    d["value"] = d.value * d.conversion_factor
    d.loc[d.monetary, "currency_year"] = 2020
    d["unit"] = [re.sub(r",\s*20\d\d", "" , str(u)) for u in d.unit]  # drop embedded year tags such as "EUR/kW_e, 2020"
    return d


def wide_prepared(long: pd.DataFrame) -> pd.DataFrame:
    """Upstream prepare_costs equivalent (Nyears = 1): per-kW units x 1e3; fill values; fixed and marginal_cost."""
    c = long[["technology", "parameter", "value", "unit"]].copy()
    per_kw = c.unit.astype(str).str.contains("/kW")
    c.loc[per_kw, "value"] = c.loc[per_kw, "value"] * 1e3
    w = c.pivot_table(index="technology", columns="parameter", values="value", aggfunc="sum")
    for k, v in FILL.items():
        if k not in w:
            w[k] = np.nan
        w[k] = w[k].fillna(v)
    w["fixed"] = (annuity(w.lifetime, w["discount rate"]) + w.FOM / 100.0) * w.investment
    w["marginal_cost"] = w.VOM + w.fuel / w.efficiency
    w["co2_emissions"] = w["CO2 intensity"]
    return w.sort_index()


def rel(p) -> str:
    p = Path(p)
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def rebase_manifest(index: str, monetary_rows: pd.DataFrame) -> dict:
    """The 'rebase' block of LAYER_MANIFEST.json for one rebase_index (both variants carry their own block)."""
    common = dict(index=index, monetary_rows=int(len(monetary_rows)), monetary_rows_by_source_year=monetary_rows.source_currency_year.value_counts().to_dict(),
                  usd_rows=int(monetary_rows.unit.map(currency).eq("USD").sum()))
    if index == "ea20_gdp_deflator":
        defl = ea20_deflator()
        return dict(common, role="comparison (former S2-0 main rebase, decision 50)",
                    method="EUR(currency_year) -> EUR2020 with the ECB EA20 GDP deflator, factor = index(2020)/index(currency_year); applied to every monetary row (USD rows included); non-monetary rows unchanged",
                    deflator_series=EA20_DEFLATOR_SERIES, deflator_url=EA20_DEFLATOR_URL, deflator_file=rel(EA20_DEFLATOR_FILE), deflator_sha256=sha256(EA20_DEFLATOR_FILE),
                    index_2019=defl[2019], index_2020=defl[2020], index_2025=defl[EUR_YEAR], factor_2025_to_2020=defl[2020] / defl[EUR_YEAR], factor_2019_to_2020=defl[2020] / defl[2019],
                    note="technology-data inflated 2020->2025 with Eurostat HICP (about +25.7 %); dividing by the EA20 GDP deflator (+20.0 %) leaves about +4.8 % on unchanged source values")
    eea, us = hicp_rates(HICP_TD_FILE, HICP_EEA_ROW), hicp_rates(HICP_TD_FILE, HICP_US_ROW)
    dl = eurostat_download_rates(HICP_DOWNLOAD_FILE, "Sheet 6", HICP_EEA_ROW)
    years = list(range(2016, EUR_YEAR + 1))
    diff = {y: (round(dl[y] - eea[y], 12) if y in dl and y in eea else None) for y in years}
    return dict(common, role="main (M08-1, decision 131: the index technology-data used to inflate)",
                method=("EUR(currency_year) -> EUR2020 with technology-data v0.15.0's own HICP input: factor = get_factor(rates, currency_year, 2020) = "
                        "prod(1 + r_y) for y = currency_year+1..2020, or 1 / prod(1 + r_y) for y = 2021..currency_year (missing years = series mean), "
                        "r = Eurostat prc_hicp_aind annual average rate of change, row 'European Economic Area' for EUR, 'United States' for USD rows (unit stays USD, year 2020); "
                        "non-monetary rows unchanged"),
                td_input_file=rel(HICP_TD_FILE), td_input_sha256=sha256(HICP_TD_FILE), td_helpers_sha256=TD_HELPERS_SHA,
                td_helpers_locator=f"scripts/_helpers.py line {TD_HELPERS_LINE} (prepare_inflation_rate row_to_use) and adjust_for_inflation.get_factor",
                eur_row=HICP_EEA_ROW, usd_row=HICP_US_ROW,
                eea_rates_2016_2025={y: eea.get(y) for y in years}, us_rates_2016_2025={y: us.get(y) for y in years},
                eea_inflation_factor_2020_2025=hicp_factor(eea, 2020, EUR_YEAR), factor_2025_to_2020=hicp_factor(eea, EUR_YEAR, 2020),
                factor_2019_to_2020=hicp_factor(eea, 2019, 2020), usd_factor_2025_to_2020=hicp_factor(us, EUR_YEAR, 2020),
                cross_check=dict(file=rel(HICP_DOWNLOAD_FILE), original_name=HICP_DOWNLOAD_ORIGINAL_NAME, sha256=sha256(HICP_DOWNLOAD_FILE), sheet="Sheet 6 (annual average rate of change)",
                                 eea_rate_difference_download_minus_td=diff, identical_2021_2025=all(diff[y] == 0.0 for y in range(2021, EUR_YEAR + 1))))


def build_variant(index: str, raw: pd.DataFrame):
    """Write one rebase variant (long table, prepared wide table, comparison, manifest) into OUT_DIRS[index]."""
    out = OUT_DIRS[index]
    long = rebase(raw, rebase_factor(index))
    out.mkdir(parents=True, exist_ok=True)
    long_out = out / "costs_2050_EUR2020.csv"
    long.to_csv(long_out, index=False, float_format="%.12g")
    wide = wide_prepared(long)
    wide_out = out / "costs_2050_EUR2020_prepared.csv"
    wide.to_csv(wide_out, float_format="%.12g")
    cmp_df = comparison(raw, long)
    write_csv(cmp_df.to_dict("records"), out / "COMPARISON_v0.13.2_vs_v0.15.0_EUR2020.csv", list(cmp_df.columns))
    # M08a A3 (decision 131, registry existing_fleet_cost_rule): the same rebase on every output year of the release, for the
    # existing stock priced by commissioning year (prepared tables only; the 2050 table equals the main prepared table)
    by_year = {}
    (out / "by_year").mkdir(exist_ok=True)
    for y in BY_YEARS:
        src_y = BY_YEAR_SRC / f"costs_{y}.csv"
        ry = pd.read_csv(src_y); ry["value"] = ry["value"].astype(float)
        wy = wide_prepared(rebase(ry, rebase_factor(index)))
        py = out / "by_year" / f"costs_{y}_EUR2020_prepared.csv"
        wy.to_csv(py, float_format="%.12g")
        by_year[str(y)] = dict(source=rel(src_y), source_sha256=sha256(src_y), prepared=rel(py), prepared_sha256=sha256(py))
    monetary_rows = long[long.monetary]
    manifest = dict(layer="technology_data_v0_15_0_2050_eur2020", rebase_index=index,
                    role=("main (decision 50; supersedes v0.13.2 main layer from D1); rebase index per M08-1 (decision 131)" if index == MAIN_INDEX
                          else "comparison variant (rebase_index ea20_gdp_deflator = former S2-0 rebase); not the main layer"),
                    technology_data=dict(tag=TAG, tag_commit=TAG_COMMIT, release_asset=RELEASE_ASSET_URL, costs_2050_csv=rel(V015), costs_2050_sha256=sha256(V015),
                                         source_tarball_sha256=TARBALL_SHA, config_yaml_sha256=sha256(V015_CONFIG), release_notes_sha256=sha256(V015_NOTES),
                                         eur_year=EUR_YEAR, eur_year_locator="config.yaml line 18 'eur_year: 2025'; docs/release_notes.rst v0.14.0 and v0.15.0 entries",
                                         upstream_inflation_index=f"Eurostat HICP annual average rate of change (prc_hicp_aind), scripts/_helpers.py line {TD_HELPERS_LINE} row 'European Economic Area', adjust_for_inflation"),
                    rebase=rebase_manifest(index, monetary_rows),
                    files=dict(long=rel(long_out), long_sha256=sha256(long_out), prepared=rel(wide_out), prepared_sha256=sha256(wide_out),
                               comparison=rel(out / "COMPARISON_v0.13.2_vs_v0.15.0_EUR2020.csv"), by_year=by_year),
                    prepared_table=dict(formula="fixed = (annuity(lifetime, discount rate) + FOM/100) x investment [EUR/MW]; marginal_cost = VOM + fuel/efficiency; per-kW units x 1e3",
                                        fill_values=FILL, source="pypsa-asean scripts/process_cost_data.prepare_costs; configs/config.default.yaml costs.fill_values"),
                    aeo8_overrides=False, smr_cost_source="see research.cost_layer.smr_cost_source", rows=int(len(long)))
    write_json(manifest, out / "LAYER_MANIFEST.json")
    return long, wide, cmp_df, manifest, long_out


def comparison(raw: pd.DataFrame, long: pd.DataFrame) -> pd.DataFrame:
    """v0.13.2 (EUR2020) vs v0.15.0 (as published and rebased) for the main technologies."""
    old = pd.read_csv(V0132); old["value"] = old.value.astype(float)
    o = old.set_index(["technology", "parameter"]); r15 = raw.set_index(["technology", "parameter"]); n15 = long.set_index(["technology", "parameter"])
    rows = []
    for t in MAIN_TECHS:
        for p in PARAMS:
            k = (t, p)
            a = float(o.loc[k, "value"]) if k in o.index else np.nan
            b = float(r15.loc[k, "value"]) if k in r15.index else np.nan
            c = float(n15.loc[k, "value"]) if k in n15.index else np.nan
            if np.isnan(a) and np.isnan(b):
                continue
            rows.append(dict(technology=t, parameter=p, v0_13_2_eur2020=a, v0_15_0_as_published=b,
                             v0_15_0_currency_year=(int(r15.loc[k, "currency_year"]) if k in r15.index and pd.notna(r15.loc[k, "currency_year"]) else ""),
                             v0_15_0_eur2020=c, change_pct_eur2020=((c / a - 1) * 100 if a and not np.isnan(a) and not np.isnan(c) else np.nan),
                             unit_v0_13_2=(o.loc[k, "unit"] if k in o.index else ""), unit_v0_15_0=(r15.loc[k, "unit"] if k in r15.index else ""),
                             source_v0_15_0=(str(r15.loc[k, "source"])[:80] if k in r15.index else "")))
    return pd.DataFrame(rows)


def main():
    raw = pd.read_csv(V015)
    raw["value"] = raw["value"].astype(float)
    variants = {idx: build_variant(idx, raw) for idx in OUT_DIRS}
    long, wide, cmp_df, manifest, long_out = variants[MAIN_INDEX]
    factor = manifest["rebase"]["factor_2025_to_2020"]
    defl = ea20_deflator(); factor_ea20 = defl[2020] / defl[EUR_YEAR]
    monetary_rows = long[long.monetary]
    hb = manifest["rebase"]
    # --- registry rows -------------------------------------------------------------------------------
    reg = Registry(SCRIPT)
    src = f"technology-data {TAG} ({TAG_COMMIT}) outputs/costs_2050.csv"
    sha = f"costs_2050.csv:{manifest['technology_data']['costs_2050_sha256']}; tarball:{TARBALL_SHA}"
    reg.add("cost_layer_C_technology_data_v0_15_0_2050_eur2020", "Main cost layer (decision 50): technology-data v0.15.0 costs_2050.csv rebased EUR2025 -> EUR2020 "
            "with the EEA HICP rate of change technology-data used to inflate (M08-1, decision 131; rebase_index eea_hicp_rate)",
            manifest["files"]["long_sha256"], "sha256", "B", src, rel(long_out), sha, decision_ref="50,46,131")
    lv = variants["ea20_gdp_deflator"]
    reg.add("cost_layer_C_technology_data_v0_15_0_2050_eur2020_ea20gdp", "Comparison variant of the main cost layer: the same table rebased with the EA20 GDP deflator "
            "(former S2-0 main rebase, rebase_index ea20_gdp_deflator); CSVs identical to the pre-M08-1 main layer", lv[3]["files"]["long_sha256"], "sha256", "B", src, rel(lv[4]), sha,
            decision_ref="50,131", status="SENSITIVITY")
    reg.add("technology_data_v0_15_0_tag_commit", "Git tag v0.15.0 resolves to this commit (GitHub API refs/tags/v0.15.0)", TAG_COMMIT, "sha1", "A", "https://api.github.com/repos/PyPSA/technology-data/git/ref/tags/v0.15.0",
            "object.sha", TARBALL_SHA, decision_ref="50")
    reg.add("technology_data_v0_15_0_costs_2050_sha256", "SHA256 of the downloaded release asset outputs/costs_2050.csv", manifest["technology_data"]["costs_2050_sha256"], "sha256", "A",
            RELEASE_ASSET_URL, "release asset", manifest["technology_data"]["costs_2050_sha256"], decision_ref="50")
    reg.add("technology_data_v0_15_0_eur_year", "Currency base year of technology-data v0.15.0 (config.yaml eur_year; release notes v0.14.0/v0.15.0)", EUR_YEAR, "year", "A",
            "technology-data v0.15.0 config.yaml, docs/release_notes.rst", "config.yaml:18; release_notes.rst lines 37, 42", sha256(V015_CONFIG), decision_ref="50")
    reg.add("deflator_ea20_gdp_2025", "EA20 GDP deflator index 2025 (2020 = 100), ECB Data Portal series " + EA20_DEFLATOR_SERIES, defl[EUR_YEAR], "index", "A",
            "ECB Data Portal, national accounts (MNA), GDP deflator euro area 20", EA20_DEFLATOR_URL, sha256(EA20_DEFLATOR_FILE), decision_ref="50")
    reg.add("deflator_ea20_gdp_2019", "EA20 GDP deflator index 2019 (2020 = 100)", defl[2019], "index", "A", "ECB Data Portal MNA", EA20_DEFLATOR_URL, sha256(EA20_DEFLATOR_FILE), decision_ref="50")
    reg.add("conv_eur2025_to_eur2020", "历史：已被 cost_layer_deflator_hicp 替代（M08-1，第 131 项）. EUR2025 -> EUR2020 = 100 / EA20 GDP deflator 2025 (former S2-0 main rebase; "
            "kept as the comparison variant rebase_index ea20_gdp_deflator, cost_layers_v5/technology_data_v0.15.0_EUR2020_ea20gdp)", factor_ea20, "EUR2020/EUR2025", "B", "ECB Data Portal MNA", "index(2020)/index(2025)",
            sha256(EA20_DEFLATOR_FILE), decision_ref="50, 131", status="REFERENCE_ONLY")
    reg.add("cost_layer_index_mismatch_note", "历史：已被 cost_layer_deflator_hicp 替代（M08-1：HICP 回算消除残余）. Former rebase: technology-data inflates with Eurostat HICP (2020->2025 +25.7 %) "
            "while the EA20 GDP deflator (+20.0 %) was used to deflate; unchanged source values appeared about +4.8 % above v0.13.2 (e.g. electrolysis 1,000 -> 1,047.7 EUR2020/kW)",
            hb["eea_inflation_factor_2020_2025"] / (defl[EUR_YEAR] / 100) - 1, "ratio", "B",
            "technology-data v0.15.0 scripts/_helpers.py prepare_inflation_rate (Eurostat prc_hicp_aind); COMPARISON csv", "electrolysis investment 1000.0 -> 1257.3346", sha, decision_ref="50, 131", status="REFERENCE_ONLY")
    td_in = f"{HICP_TD_FILE.name}:{sha256(HICP_TD_FILE)}; _helpers.py:{TD_HELPERS_SHA}"
    reg.add("cost_layer_deflator_hicp", "R6.1 / M08-1 (decision 131): EUR2025 -> EUR2020 rebase of technology-data v0.15.0 with the index technology-data used to inflate - Eurostat HICP "
            "prc_hicp_aind annual average rate of change, European Economic Area row (scripts/_helpers.py line 220), chained 2021-2025 (2.9, 9.2, 6.4, 2.6, 2.5 %): 1 / 1.25733; "
            "read from technology-data's own input file; the user download (Sheet 6) has identical EEA rates 2021-2025 (cross-check); USD rows (SOEC, carbon capture retrofits) with the "
            "United States row as technology-data does; replaces the EA20 GDP deflator rebase (conv_eur2025_to_eur2020, comparison variant) and removes the +4.8 % residual",
            factor, "EUR2020/EUR2025", "A", "Eurostat prc_hicp_aind (technology-data v0.15.0 inputs/prc_hicp_aind__custom_20097956_spreadsheet.xlsx, extracted 2026-02-13)",
            f"rebase_index eea_hicp_rate; {rel(HICP_TD_FILE)} Sheet 1 row EEA; LAYER_MANIFEST.json rebase", td_in, decision_ref="126, 50, 131")
    reg.add("hicp_eea_inflation_factor_2020_2025", "technology-data v0.15.0 inflation factor EUR2020 -> EUR2025 = prod(1 + EEA HICP annual rate of change 2021-2025) (get_factor); "
            "the rebase factor x this factor = 1 by construction; observed check: electrolysis investment v0.13.2 1,000 (EUR2020) -> v0.15.0 1,257.3346 (EUR2025)",
            hb["eea_inflation_factor_2020_2025"], "EUR2025/EUR2020", "A", "Eurostat prc_hicp_aind via technology-data v0.15.0 inputs", f"{rel(HICP_TD_FILE)} Sheet 1 row EEA 2021-2025", td_in, decision_ref="131")
    reg.add("hicp_us_factor_2025_to_2020", "USD2025 -> USD2020 for the 5 USD rows of technology-data v0.15.0 costs_2050 (SOEC investment, 4 carbon capture retrofits): 1 / prod(1 + United States "
            "HICP rate 2021-2025), 2025 missing in the input -> series mean as technology-data get_factor; the unit stays USD (not used by the network builder)",
            hb["usd_factor_2025_to_2020"], "USD2020/USD2025", "B", "Eurostat prc_hicp_aind via technology-data v0.15.0 inputs", f"{rel(HICP_TD_FILE)} Sheet 1 row United States", td_in, decision_ref="131")
    for _, r in cmp_df.iterrows():
        if r.parameter not in ("investment", "fuel", "lifetime", "efficiency", "FOM", "VOM"):
            continue
        if np.isnan(r.v0_15_0_eur2020):
            continue
        key = re.sub(r"[^A-Za-z0-9]+", "_", r.technology).strip("_") + "_" + r.parameter.replace(" ", "_")
        unit = str(r.unit_v0_15_0 or r.unit_v0_13_2)
        unit = re.sub(r",\s*20\d\d", "", unit)
        if monetary(unit):
            unit = unit.replace("EUR", "EUR2020")
        reg.add(f"cost_C_{key}", f"Layer C (technology-data v0.15.0 -> EUR2020) {r.technology} {r.parameter}; v0.13.2 = {r.v0_13_2_eur2020:.6g}" if not np.isnan(r.v0_13_2_eur2020) else f"Layer C {r.technology} {r.parameter} (new in v0.15.0)",
                r.v0_15_0_eur2020, unit, "B", src, f"technology {r.technology}, parameter {r.parameter}; x{factor:.6f} if monetary", sha, decision_ref="50")
    reg.write(REG_DIR / "fragments" / "cost_layer_v015.csv")
    write_json(dict(script=SCRIPT, manifest=manifest, comparison_rows=len(cmp_df)), REG_DIR / "fragments" / "cost_layer_v015.json")
    pd.set_option("display.width", 250)
    print("factor EUR2025->EUR2020", factor, "| monetary rows", len(monetary_rows), monetary_rows.source_currency_year.value_counts().to_dict())
    show = cmp_df[cmp_df.parameter.isin(["investment", "fuel"]) & cmp_df.technology.isin(["solar-utility", "onwind", "offwind", "HVDC submarine", "HVAC submarine", "nuclear", "uranium", "electrolysis", "battery storage", "direct air capture", "CO2 pipeline", "CO2 submarine pipeline", "gas", "coal", "oil", "geothermal"])]
    print(show[["technology", "parameter", "v0_13_2_eur2020", "v0_15_0_as_published", "v0_15_0_eur2020", "change_pct_eur2020"]].round(3).to_string(index=False))
    print("prepared wide table:", wide.shape, "| onwind fixed", round(float(wide.at["onwind", "fixed"]), 2), "| nuclear marginal", round(float(wide.at["nuclear", "marginal_cost"]), 3))


if __name__ == "__main__":
    main()
