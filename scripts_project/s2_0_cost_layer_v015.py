"""S2-0.1 (decision 50): technology-data v0.15.0 cost layer rebased to EUR2020 -> new main layer.

* Source: PyPSA/technology-data tag v0.15.0 (commit 07e43575c7996a988c60964d00772376ab9bd10c),
  outputs/costs_2050.csv (release asset, copied to cost_layers_v5/sources/costs_2050_v0.15.0.csv).
* Currency base year: config.yaml `eur_year: 2025` (release notes v0.14.0: "Changed currency year
  from 2020 to 2025 ... using updated Eurostat inflation rates"; v0.15.0: the `currency_year`
  column now reflects the inflation-adjusted year). Every monetary row carries currency_year 2025
  except two rows (2020, 2019), which are rebased from their own year.
* Rebase EUR2025 -> EUR2020 with the ECB EA20 GDP deflator (series
  MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N, 2020 = 100): factor = 100 / index(2025).
  technology-data itself inflated 2020 -> 2025 with Eurostat HICP (+25.7 %), so values whose
  source did not change come back about 4.8 % above v0.13.2; this residual is reported, not removed.
* Also writes the annualised wide table used by the network builder (same formula as the upstream
  prepare_costs: fixed = (annuity(lifetime, discount rate) + FOM/100) x investment; marginal =
  VOM + fuel / efficiency) and the v0.13.2 -> v0.15.0 comparison for the main technologies.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from d1_common import (COST_DIR, EA20_DEFLATOR_FILE, EA20_DEFLATOR_SERIES, EA20_DEFLATOR_URL, REG_DIR,
                       TECHNOLOGY_DATA_V0_13_2, Registry, ea20_deflator, sha256, write_csv, write_json)

SCRIPT = "scripts_project/s2_0_cost_layer_v015.py"
SRC = COST_DIR / "sources"
V015 = SRC / "costs_2050_v0.15.0.csv"
V015_CONFIG = SRC / "technology_data_v0.15.0_config.yaml"
V015_NOTES = SRC / "technology_data_v0.15.0_release_notes.rst"
V0132 = TECHNOLOGY_DATA_V0_13_2 / "outputs" / "costs_2050.csv"
OUT = COST_DIR / "technology_data_v0.15.0_EUR2020"
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


def rebase(df: pd.DataFrame, defl: dict) -> pd.DataFrame:
    d = df.copy()
    d["monetary"] = d.unit.map(monetary)
    d["source_currency_year"] = d.currency_year
    fac = []
    for _, r in d.iterrows():
        if r.monetary:
            y = int(r.currency_year) if pd.notna(r.currency_year) else None
            if y is None:
                raise ValueError(f"monetary row without currency_year: {r.technology} {r.parameter}")
            fac.append(defl[2020] / defl[y])
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


def main():
    defl = ea20_deflator()
    factor = defl[2020] / defl[EUR_YEAR]
    raw = pd.read_csv(V015)
    raw["value"] = raw["value"].astype(float)
    long = rebase(raw, defl)
    OUT.mkdir(parents=True, exist_ok=True)
    long_out = OUT / "costs_2050_EUR2020.csv"
    long.to_csv(long_out, index=False, float_format="%.12g")
    wide = wide_prepared(long)
    wide_out = OUT / "costs_2050_EUR2020_prepared.csv"
    wide.to_csv(wide_out, float_format="%.12g")
    # --- comparison with v0.13.2 (EUR2020) --------------------------------------------------------
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
    cmp_df = pd.DataFrame(rows)
    write_csv(cmp_df.to_dict("records"), OUT / "COMPARISON_v0.13.2_vs_v0.15.0_EUR2020.csv", list(cmp_df.columns))
    monetary_rows = long[long.monetary]
    manifest = dict(layer="technology_data_v0_15_0_2050_eur2020", role="main (decision 50; supersedes v0.13.2 main layer from D1)",
                    technology_data=dict(tag=TAG, tag_commit=TAG_COMMIT, release_asset=RELEASE_ASSET_URL, costs_2050_csv=str(V015), costs_2050_sha256=sha256(V015),
                                         source_tarball_sha256=TARBALL_SHA, config_yaml_sha256=sha256(V015_CONFIG), release_notes_sha256=sha256(V015_NOTES),
                                         eur_year=EUR_YEAR, eur_year_locator="config.yaml line 18 'eur_year: 2025'; docs/release_notes.rst v0.14.0 and v0.15.0 entries",
                                         upstream_inflation_index="Eurostat HICP annual (prc_hicp_aind), scripts/_helpers.py prepare_inflation_rate/adjust_for_inflation"),
                    rebase=dict(method="EUR(currency_year) -> EUR2020 with the ECB EA20 GDP deflator, factor = index(2020)/index(currency_year); non-monetary rows unchanged",
                                deflator_series=EA20_DEFLATOR_SERIES, deflator_url=EA20_DEFLATOR_URL, deflator_file=str(EA20_DEFLATOR_FILE), deflator_sha256=sha256(EA20_DEFLATOR_FILE),
                                index_2019=defl[2019], index_2020=defl[2020], index_2025=defl[EUR_YEAR], factor_2025_to_2020=factor, factor_2019_to_2020=defl[2020] / defl[2019],
                                monetary_rows=int(len(monetary_rows)), monetary_rows_by_source_year=monetary_rows.source_currency_year.value_counts().to_dict(),
                                note="technology-data inflated 2020->2025 with Eurostat HICP (about +25.7 %); dividing by the EA20 GDP deflator (+20.0 %) leaves about +4.8 % on unchanged source values"),
                    files=dict(long=str(long_out), long_sha256=sha256(long_out), prepared=str(wide_out), prepared_sha256=sha256(wide_out),
                               comparison=str(OUT / "COMPARISON_v0.13.2_vs_v0.15.0_EUR2020.csv")),
                    prepared_table=dict(formula="fixed = (annuity(lifetime, discount rate) + FOM/100) x investment [EUR/MW]; marginal_cost = VOM + fuel/efficiency; per-kW units x 1e3",
                                        fill_values=FILL, source="pypsa-asean scripts/process_cost_data.prepare_costs; configs/config.default.yaml costs.fill_values"),
                    aeo8_overrides=False, smr_cost_source="aeo8_author_rule_2050 (decision 46, unchanged)", rows=int(len(long)))
    write_json(manifest, OUT / "LAYER_MANIFEST.json")
    # --- registry rows -------------------------------------------------------------------------------
    reg = Registry(SCRIPT)
    src = f"technology-data {TAG} ({TAG_COMMIT}) outputs/costs_2050.csv"
    sha = f"costs_2050.csv:{manifest['technology_data']['costs_2050_sha256']}; tarball:{TARBALL_SHA}"
    reg.add("cost_layer_C_technology_data_v0_15_0_2050_eur2020", "Main cost layer (decision 50): technology-data v0.15.0 costs_2050.csv rebased EUR2025 -> EUR2020",
            manifest["files"]["long_sha256"], "sha256", "B", src, str(long_out), sha, decision_ref="50,46")
    reg.add("technology_data_v0_15_0_tag_commit", "Git tag v0.15.0 resolves to this commit (GitHub API refs/tags/v0.15.0)", TAG_COMMIT, "sha1", "A", "https://api.github.com/repos/PyPSA/technology-data/git/ref/tags/v0.15.0",
            "object.sha", TARBALL_SHA, decision_ref="50")
    reg.add("technology_data_v0_15_0_costs_2050_sha256", "SHA256 of the downloaded release asset outputs/costs_2050.csv", manifest["technology_data"]["costs_2050_sha256"], "sha256", "A",
            RELEASE_ASSET_URL, "release asset", manifest["technology_data"]["costs_2050_sha256"], decision_ref="50")
    reg.add("technology_data_v0_15_0_eur_year", "Currency base year of technology-data v0.15.0 (config.yaml eur_year; release notes v0.14.0/v0.15.0)", EUR_YEAR, "year", "A",
            "technology-data v0.15.0 config.yaml, docs/release_notes.rst", "config.yaml:18; release_notes.rst lines 37, 42", sha256(V015_CONFIG), decision_ref="50")
    reg.add("deflator_ea20_gdp_2025", "EA20 GDP deflator index 2025 (2020 = 100), ECB Data Portal series " + EA20_DEFLATOR_SERIES, defl[EUR_YEAR], "index", "A",
            "ECB Data Portal, national accounts (MNA), GDP deflator euro area 20", EA20_DEFLATOR_URL, sha256(EA20_DEFLATOR_FILE), decision_ref="50")
    reg.add("deflator_ea20_gdp_2019", "EA20 GDP deflator index 2019 (2020 = 100)", defl[2019], "index", "A", "ECB Data Portal MNA", EA20_DEFLATOR_URL, sha256(EA20_DEFLATOR_FILE), decision_ref="50")
    reg.add("conv_eur2025_to_eur2020", "EUR2025 -> EUR2020 = 100 / EA20 GDP deflator 2025", factor, "EUR2020/EUR2025", "B", "ECB Data Portal MNA", "index(2020)/index(2025)",
            sha256(EA20_DEFLATOR_FILE), decision_ref="50", sensitivity_low=factor * (120.01983 / 125.7) if False else None, sensitivity_high=None)
    reg.add("cost_layer_index_mismatch_note", "technology-data inflates with Eurostat HICP (2020->2025 about +25.7 %) while this layer deflates with the EA20 GDP deflator (+20.0 %); "
            "unchanged source values therefore appear about +4.8 % above v0.13.2 (e.g. electrolysis 1,000 -> 1,047.7 EUR2020/kW)", 1.2573 / (defl[EUR_YEAR] / 100) - 1, "ratio", "B",
            "technology-data v0.15.0 scripts/_helpers.py prepare_inflation_rate (Eurostat prc_hicp_aind); COMPARISON csv", "electrolysis investment 1000.0 -> 1257.3346", sha, decision_ref="50", status="REFERENCE_ONLY")
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
