"""D1 section 2 (decision 46, option A): two registered cost layers and the author's AEO8 rule.

Layer A (main):  technology-data v0.13.2 outputs/costs_2050.csv for every technology (EUR2020).
Layer B (sens.): AEO8 Appendix D.15 costs transformed exactly as pypsa-asean
                 scripts/append_cost_data.py does (USD -> EUR at the 2020 ECB mean rate, then the
                 D.17 2050 decline where the D.15 `technology` label equals a D.17 `Technology`
                 label), mapped to technology-data names with the author's rename_subtech table.
SMR (decision 46): AEO8 D.15 "Nuclear SMR" (not in the author's mapping) converted with the same
                 rule (no decline: "Nuclear" is not a D.17 technology); grade C, +-30 %.
Also: technology-data v0.13.4 / v0.15.0 vs v0.13.2 read-only comparison (no upgrade) and the
geothermal performance rows available in v0.13.2 for the existing ID 186 MW.
"""
from __future__ import annotations

import datetime as dt
import statistics
import sys
from pathlib import Path

import pandas as pd

from d1_common import (COST_DIR, REG_DIR, TECHNOLOGY_DATA_V0_13_2, UNIT_CONSTANTS, UPSTREAM, Registry,
                       sha256, write_csv, write_json)

SCRIPT = "scripts_project/d1_cost_layers.py"
SRC = COST_DIR / "sources"
D15, D17, D18 = SRC / "AEO8_Table_D15_Cost_Summary.csv", SRC / "AEO8_Table_D17_Declining_Factor.csv", SRC / "AEO8_Table_D18_Regional_Factor.csv"
TD_COSTS = TECHNOLOGY_DATA_V0_13_2 / "outputs" / "costs_2050.csv"
TD_CONFIG = TECHNOLOGY_DATA_V0_13_2 / "config.yaml"
AUTHOR_SCRIPT = UPSTREAM / "scripts" / "append_cost_data.py"
AUTHOR_OUTPUT = UPSTREAM / "resources" / "baseline-aims-3H-tutorial" / "costs_2050_sec.csv"
AEO8_PDF_SHA = "48c2a81913ed785cb0e14a55e332ea7bc87f912f7fabfbc8c654e09b66b11c06"
YEAR = 2050
# verbatim copy of pypsa-asean/scripts/append_cost_data.py lines 14-33 (commit in evidence/)
RENAME_SUBTECH = {
    "Coal average": "coal", "Oil average": "oil", "Gas Turbine": "OCGT", "Gas Combined Cycle": "CCGT",
    "Nuclear average": "nuclear", "Large Hydro": "hydro", "Small Hydro": "ror", "Geothermal average": "geothermal",
    "Solar average": "solar", "Solar PV": "solar-utility", "Solar PV Rooftop": "solar-rooftop",
    "Wind Onshore": "onwind", "Wind Offshore": "offwind", "Bioenergy average": "biomass", "Biogas": "biogas",
    "Lithium Ion Batteries": "battery inverter", "Pumped Hydro": "Pumped-Storage-Hydro-bicharger",
}
# technologies the research network references (S1 skeleton + S2 plan) and the parameters S2 reads
WATCH_TECHS = ["coal", "lignite", "oil", "OCGT", "CCGT", "nuclear", "hydro", "ror", "PHS", "geothermal", "solar",
               "solar-utility", "solar-rooftop", "onwind", "offwind", "biomass CHP", "biomass EOP", "biogas",
               "biogas upgrading", "battery inverter", "battery storage", "electrolysis", "fuel cell",
               "H2 (g) pipeline", "H2 (g) submarine pipeline", "hydrogen storage tank type 1", "SMR", "SMR CC",
               "direct air capture", "biomass CHP capture", "cement capture", "CO2 pipeline",
               "CO2 submarine pipeline", "CO2 storage tank", "Fischer-Tropsch", "BtL", "electric boiler steam",
               "industrial heat pump high temperature", "gas boiler steam", "biomass boiler steam", "gas", "coal",
               "solid biomass", "biogas", "uranium", "HVDC overhead", "HVDC submarine", "HVAC overhead"]
WATCH_PARAMS = ["investment", "FOM", "VOM", "lifetime", "efficiency", "fuel", "CO2 intensity"]


def ecb_annual_mean(year: int):
    """Replicates process_cost_data.get_yearly_currency_exchange_rate for USD->EUR (reference strategy)."""
    try:
        from currency_converter import CurrencyConverter
    except ImportError:
        return None, "currency_converter not importable"
    c = CurrencyConverter(fallback_on_missing_rate=True)
    dates = sorted(c._rates["USD"].keys())
    vals = [c.convert(1, "USD", "EUR", d) for d in dates if d.year == year]
    return statistics.mean(vals), f"currency_converter mean over {len(vals)} dates in {year}"


def author_rule(fx: float, year: int = YEAR) -> pd.DataFrame:
    """Exact re-implementation of append_cost_data.py lines 52-55 and 76-88 (year wildcard = 2050)."""
    d15 = pd.read_csv(D15)
    declining = pd.read_csv(D17).set_index(["Technology", "Parameter"])[str(year)].unstack()
    app = d15.copy()
    app[["capital_cost", "FOM", "VOM"]] = app[["capital_cost", "FOM", "VOM"]].astype(float)
    app[["capital_cost", "FOM", "VOM"]] *= fx
    for t in declining.index:
        app.loc[app.technology == t, "capital_cost"] *= 1 - declining.loc[t, "Capex"]
        app.loc[app.technology == t, "VOM"] *= 1 - declining.loc[t, "Opex"]
    rows = []
    for i, r in app.iterrows():
        src = d15.loc[i]
        matched = r.technology in declining.index
        rows.append(dict(
            aeo8_technology=r.technology, aeo8_subtechnology=r["sub-technology"],
            technology_data_name=RENAME_SUBTECH.get(r["sub-technology"], ""),
            in_author_mapping=r["sub-technology"] in RENAME_SUBTECH, decline_label_matched=matched,
            capex_decline_2050=float(declining.loc[r.technology, "Capex"]) if matched else 0.0,
            opex_decline_2050=float(declining.loc[r.technology, "Opex"]) if matched else 0.0,
            source_capital_kusd_per_mw=float(src.capital_cost), source_fom_kusd_per_mw_a=float(src.FOM),
            source_vom_usd_per_mwh=float(src.VOM),
            investment_eur2020_per_kw=float(r.capital_cost), fom_pct_per_year=float(r.FOM / r.capital_cost * 100),
            vom_eur2020_per_mwh=float(r.VOM), fx_usd_to_eur_2020=fx))
    return pd.DataFrame(rows)


def td_table(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["value"] = df["value"].astype(float)
    return df


def compare_versions(base: pd.DataFrame, others: dict) -> tuple[list, dict]:
    rows, summary = [], {}
    b = base.set_index(["technology", "parameter"])
    for ver, df in others.items():
        o = df.set_index(["technology", "parameter"])
        common = b.index.intersection(o.index)
        changed = 0
        for key in common:
            va, vb = float(b.loc[key, "value"]), float(o.loc[key, "value"])
            if abs(va - vb) > 1e-9 * max(1.0, abs(va)):
                changed += 1
                if key[0] in WATCH_TECHS and key[1] in WATCH_PARAMS:
                    rows.append(dict(version=ver, technology=key[0], parameter=key[1], v0_13_2=va, other=vb,
                                     change_pct=(vb / va - 1) * 100 if va else float("nan"),
                                     unit_v0_13_2=b.loc[key, "unit"], unit_other=o.loc[key, "unit"]))
        summary[ver] = dict(rows=len(df), rows_v0_13_2=len(base), common_rows=len(common), changed_rows=changed,
                            new_technologies=sorted(set(df.technology) - set(base.technology)),
                            removed_technologies=sorted(set(base.technology) - set(df.technology)))
    return rows, summary


def main():
    fx_const = UNIT_CONSTANTS["fx_usd_to_eur_2020"][0]
    fx_live, fx_note = ecb_annual_mean(2020)
    fx = fx_live if fx_live is not None else fx_const
    if fx_live is not None and abs(fx_live - fx_const) > 1e-12:
        raise SystemExit(f"FX mismatch: recomputed {fx_live} vs registered {fx_const}")
    layer_b = author_rule(fx)
    # --- verification against the author's actual output (costs_2050_sec.csv) ---------------------
    verification = []
    if AUTHOR_OUTPUT.exists():
        # author output is the wide costs table (technology x parameter), investment in EUR/MW
        out = pd.read_csv(AUTHOR_OUTPUT, index_col=0)
        for _, r in layer_b[layer_b.in_author_mapping].iterrows():
            t = r.technology_data_name
            for par, col, scale in [("investment", "investment_eur2020_per_kw", 1000.0), ("FOM", "fom_pct_per_year", 1.0),
                                    ("VOM", "vom_eur2020_per_mwh", 1.0)]:
                if t not in out.index or par not in out.columns or pd.isna(out.loc[t, par]):
                    verification.append(dict(technology=t, parameter=par, replicated=r[col] * scale, author_file=None,
                                             rel_diff=None, unit_author=None, note="not present in author output"))
                    continue
                v = float(out.loc[t, par])
                rep = r[col] * scale
                verification.append(dict(technology=t, parameter=par, replicated=rep, author_file=v,
                                         rel_diff=(rep - v) / v if v else (0.0 if rep == 0 else None),
                                         unit_author="EUR/MW" if par == "investment" else ("%/a" if par == "FOM" else "EUR/MWh"),
                                         note="author output costs_2050_sec.csv (wide table)"))
    ver_df = pd.DataFrame(verification)
    # --- SMR row (decision 46) -------------------------------------------------------------------
    smr = layer_b[layer_b.aeo8_subtechnology == "Nuclear SMR"].iloc[0]
    smr_row = dict(aeo8_technology="Nuclear", aeo8_subtechnology="Nuclear SMR", technology_data_name="nuclear SMR",
                   in_author_mapping=False, decline_label_matched=False, capex_decline_2050=0.0, opex_decline_2050=0.0,
                   source_capital_kusd_per_mw=smr.source_capital_kusd_per_mw, source_fom_kusd_per_mw_a=smr.source_fom_kusd_per_mw_a,
                   source_vom_usd_per_mwh=smr.source_vom_usd_per_mwh, investment_eur2020_per_kw=smr.investment_eur2020_per_kw,
                   fom_pct_per_year=smr.fom_pct_per_year, vom_eur2020_per_mwh=smr.vom_eur2020_per_mwh, fx_usd_to_eur_2020=fx)
    # --- Layer A manifest and coverage ----------------------------------------------------------------
    td = td_table(TD_COSTS)
    coverage = []
    for t in sorted(set(WATCH_TECHS)):
        have = set(td[td.technology == t].parameter)
        coverage.append(dict(technology=t, present=bool(have), investment="investment" in have, FOM="FOM" in have,
                             VOM="VOM" in have, lifetime="lifetime" in have, efficiency="efficiency" in have,
                             fuel="fuel" in have, parameters=";".join(sorted(have))))
    layer_a = dict(layer="technology_data_v0_13_2_2050", role="main (decision 46, option A)",
                   file=str(TD_COSTS), sha256=sha256(TD_COSTS), config_sha256=sha256(TD_CONFIG), currency_year=2020,
                   year=YEAR, aeo8_overrides=False, rows=int(len(td)),
                   note="All technologies from technology-data v0.13.2; the author's AEO8 append step is not applied. "
                        "SMR is taken from layer B in both layers (decision 46).",
                   missing_for_watch_list=[c["technology"] for c in coverage if not c["present"]],
                   generators_without_investment=[c["technology"] for c in coverage if c["present"] and not c["investment"]])
    # --- version comparison (read-only) --------------------------------------------------------------
    others = {}
    for ver in ["v0.13.4", "v0.15.0"]:
        p = SRC / f"costs_2050_{ver}.csv"
        if p.exists():
            others[ver] = td_table(p)
    cmp_rows, cmp_summary = compare_versions(td, others)
    for ver in others:
        cmp_summary[ver]["sha256"] = sha256(SRC / f"costs_2050_{ver}.csv")
    # --- write layer files --------------------------------------------------------------------------
    COST_DIR.mkdir(parents=True, exist_ok=True)
    b_rows = pd.concat([layer_b, pd.DataFrame([smr_row])], ignore_index=True)
    b_cols = list(b_rows.columns)
    write_csv(b_rows.to_dict("records"), COST_DIR / "LAYER_B_AEO8_AUTHOR_RULE_2050.csv", b_cols)
    write_json(layer_a, COST_DIR / "LAYER_A_TECHNOLOGY_DATA_V0_13_2_2050.json")
    write_csv(coverage, COST_DIR / "LAYER_A_COVERAGE_WATCHLIST.csv", list(coverage[0].keys()))
    if len(ver_df):
        write_csv(ver_df.to_dict("records"), COST_DIR / "LAYER_B_VERIFICATION_VS_AUTHOR_OUTPUT.csv", list(ver_df.columns))
    if cmp_rows:
        write_csv(cmp_rows, COST_DIR / "TECHNOLOGY_DATA_VERSION_COMPARISON_2050.csv", list(cmp_rows[0].keys()))
    # --- registry rows --------------------------------------------------------------------------------
    reg = Registry(SCRIPT)
    d15_sha, d17_sha, d18_sha = sha256(D15), sha256(D17), sha256(D18)
    aeo8_src = f"AEO8 pdf:{AEO8_PDF_SHA}; D15:{d15_sha}; D17:{d17_sha}"
    reg.add("cost_layer_A_technology_data_v0_13_2_2050", "Main cost layer: technology-data v0.13.2 costs_2050.csv, EUR2020, all technologies",
            layer_a["sha256"], "sha256", "A", "technology-data v0.13.2 outputs/costs_2050.csv", str(TD_COSTS), layer_a["sha256"], decision_ref="46")
    reg.add("cost_layer_B_aeo8_author_rule_2050", "Sensitivity cost layer: AEO8 D.15 x FX2020 x (1 - D.17 2050 decline where labels match), "
            "author mapping rename_subtech; file LAYER_B_AEO8_AUTHOR_RULE_2050.csv", sha256(COST_DIR / "LAYER_B_AEO8_AUTHOR_RULE_2050.csv"),
            "sha256", "B", "pypsa-asean scripts/append_cost_data.py:14-33,52-55,76-88; " + aeo8_src, "replicated in author_rule()",
            d15_sha, decision_ref="46", status="SENSITIVITY")
    for _, r in layer_b[layer_b.in_author_mapping].iterrows():
        t = r.technology_data_name
        key = t.replace(" ", "_").replace("-", "_")
        reg.add(f"cost_B_{key}_investment", f"Layer B {t} investment = {r.source_capital_kusd_per_mw:g} kUSD/MW x FX "
                f"x (1-{r.capex_decline_2050:g}) [decline label matched: {r.decline_label_matched}]", r.investment_eur2020_per_kw,
                "EUR2020/kW", "B", "AEO8 Table D.15/D.17 via author rule", f"D.15 row {r.aeo8_subtechnology}", aeo8_src,
                decision_ref="46", status="SENSITIVITY")
        reg.add(f"cost_B_{key}_FOM", f"Layer B {t} FOM = D.15 FOM x FX / declined capital x 100 (author formula; the "
                f"decline inflates FOM% when the label matches)", r.fom_pct_per_year, "%/a", "B",
                "AEO8 Table D.15 via author rule", f"D.15 row {r.aeo8_subtechnology}", aeo8_src, decision_ref="46", status="SENSITIVITY")
        reg.add(f"cost_B_{key}_VOM", f"Layer B {t} VOM = {r.source_vom_usd_per_mwh:g} USD/MWh x FX x (1-{r.opex_decline_2050:g})",
                r.vom_eur2020_per_mwh, "EUR2020/MWh", "B", "AEO8 Table D.15/D.17 via author rule", f"D.15 row {r.aeo8_subtechnology}",
                aeo8_src, decision_ref="46", status="SENSITIVITY")
    inv, fom, vom = smr_row["investment_eur2020_per_kw"], smr_row["fom_pct_per_year"], smr_row["vom_eur2020_per_mwh"]
    reg.add("smr_investment", "Nuclear SMR overnight cost: AEO8 D.15 9,600 kUSD/MW x ECB2020 FX; year-independent current cost "
            "(AEO8 gives no cost year; D.17 has no nuclear decline); +-30 % brackets technology-data nuclear v0.13.2 (8,594 EUR/kW) "
            "and v0.15.0 (10,806 EUR/kW)", inv, "EUR2020/kW", "C", "AEO8 Appendix D Table D.15 Nuclear SMR", "Table D.15 row Nuclear SMR",
            aeo8_src, sensitivity_low=inv * 0.7, sensitivity_high=inv * 1.3, decision_ref="46,38")
    reg.add("smr_FOM", "Nuclear SMR fixed O&M: 110.0 kUSD/MW/a / 9,600 kUSD/MW = 1.1458 %/a (currency-neutral)", fom, "%/a", "C",
            "AEO8 Table D.15 Nuclear SMR", "Table D.15", aeo8_src, sensitivity_low=fom * 0.7, sensitivity_high=fom * 1.3, decision_ref="46,38")
    reg.add("smr_VOM", "Nuclear SMR variable O&M: 2.2 USD/MWh x ECB2020 FX", vom, "EUR2020/MWh", "C", "AEO8 Table D.15 Nuclear SMR",
            "Table D.15", aeo8_src, sensitivity_low=vom * 0.7, sensitivity_high=vom * 1.3, decision_ref="46,38")
    nuc = td[td.technology == "nuclear"].set_index("parameter")
    reg.add("smr_lifetime_proxy", "Nuclear SMR lifetime not in AEO8; proxy = technology-data v0.13.2 nuclear lifetime", float(nuc.loc["lifetime", "value"]),
            "years", "C", "technology-data v0.13.2 costs_2050.csv nuclear", "parameter lifetime", layer_a["sha256"],
            sensitivity_low=30, sensitivity_high=60, decision_ref="46,38")
    reg.add("smr_efficiency_proxy", "Nuclear SMR thermal efficiency not in AEO8; proxy = technology-data v0.13.2 nuclear efficiency",
            float(nuc.loc["efficiency", "value"]), "p.u.", "C", "technology-data v0.13.2 costs_2050.csv nuclear", "parameter efficiency",
            layer_a["sha256"], sensitivity_low=0.30, sensitivity_high=0.36, decision_ref="46,38")
    geo = td[td.technology == "geothermal"].set_index("parameter")
    for par, unit in [("FOM", "%/a"), ("lifetime", "years"), ("CO2 intensity", "tCO2/MWh_th")]:
        reg.add(f"geothermal_existing_{par.replace(' ', '_')}", f"Existing geothermal (ID 186 MW) {par} from technology-data v0.13.2 geothermal",
                float(geo.loc[par, "value"]), unit, "B", "technology-data v0.13.2 costs_2050.csv geothermal",
                f"row geothermal,{par} ({geo.loc[par, 'source'][:60]})", layer_a["sha256"], country="ID", decision_ref="S1 stock, D1-1")
    for par in ["efficiency", "VOM", "investment"]:
        reg.add(f"geothermal_existing_{par}", f"technology-data v0.13.2 has no geothermal {par} row (only central geothermal heat source / "
                "organic rankine cycle); layer B offers AEO8 Geothermal average as sensitivity", None, "", "C",
                "technology-data v0.13.2 costs_2050.csv", "grep ^geothermal, -> CO2 intensity, FOM, district heat surcharge, district heat-input, lifetime",
                layer_a["sha256"], country="ID", decision_ref="S1 stock, D1-1", status="DATA_PENDING")
    reg.add("author_rule_fx_usd_eur_2020", "FX used by append_cost_data.py: get_yearly_currency_exchange_rate('USD','EUR',2020); the third "
            "positional argument is default_exchange_rate (fallback), the year comes from TECH_DATA_REFERENCE_YEAR = 2020; " + fx_note,
            fx, "EUR/USD", "B", "pypsa-asean scripts/process_cost_data.py:91-200", "get_yearly_currency_exchange_rate", sha256(AUTHOR_SCRIPT) if AUTHOR_SCRIPT.exists() else "n/a",
            decision_ref="46")
    for ver, s in cmp_summary.items():
        reg.add(f"technology_data_{ver.replace('.', '_')}_comparison", f"technology-data {ver} vs v0.13.2 (2050): {s['changed_rows']} of "
                f"{s['common_rows']} common rows differ; new technologies {len(s['new_technologies'])}, removed {len(s['removed_technologies'])}; "
                "read-only, no upgrade (user decides)", s["changed_rows"], "rows", "A", f"technology-data {ver} outputs/costs_2050.csv (GitHub release asset)",
                "TECHNOLOGY_DATA_VERSION_COMPARISON_2050.csv", s["sha256"], decision_ref="46", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "cost_layers.csv")
    write_json(dict(script=SCRIPT, fx=fx, fx_note=fx_note, layer_a=layer_a, verification=verification, version_summary=cmp_summary,
                    smr=smr_row, author_script_sha256=sha256(AUTHOR_SCRIPT) if AUTHOR_SCRIPT.exists() else None,
                    author_output_sha256=sha256(AUTHOR_OUTPUT) if AUTHOR_OUTPUT.exists() else None),
               REG_DIR / "fragments" / "cost_layers.json")
    print("FX", fx, fx_note)
    print(layer_b[layer_b.in_author_mapping][["technology_data_name", "decline_label_matched", "investment_eur2020_per_kw", "fom_pct_per_year", "vom_eur2020_per_mwh"]].to_string(index=False))
    print("SMR", smr_row["investment_eur2020_per_kw"], smr_row["fom_pct_per_year"], smr_row["vom_eur2020_per_mwh"])
    if len(ver_df):
        bad = ver_df[ver_df.rel_diff.abs() > 1e-6]
        print("verification vs author output: rows", len(ver_df), "max |rel diff|", ver_df.rel_diff.abs().max(), "mismatches", len(bad))
        if len(bad):
            print(bad.to_string(index=False))
    print("layer A missing watch techs:", layer_a["missing_for_watch_list"], "| without investment:", layer_a["generators_without_investment"])
    for ver, s in cmp_summary.items():
        print(ver, {k: v for k, v in s.items() if k != "sha256"})


def load_cost_layer(config: dict):
    """S2 entry point: returns (name, dict) for the active layer from research.cost_layer in the config."""
    from s2_costs import layer_files   # M08-1 (decision 131): rebase_index selects the variant files
    cl = config["research"]["cost_layer"]
    name = cl["active"]
    spec = layer_files(cl["layers"][name])
    path = Path(spec["file"])
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    if path.suffix == ".json":
        import json
        return name, dict(spec=spec, manifest=json.loads(path.read_text()), overrides=None)
    df = pd.read_csv(path)
    df = df[df.technology_data_name != ""].dropna(subset=["technology_data_name"])
    return name, dict(spec=spec, manifest=None, overrides=df)


if __name__ == "__main__":
    sys.exit(main())
