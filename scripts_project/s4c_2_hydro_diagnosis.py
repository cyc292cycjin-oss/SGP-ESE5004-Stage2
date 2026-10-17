"""S4C-2 item 1 (decision 83): hydro inflow diagnosis per country, before any correction.

Mechanism to verify (author chain, pypsa-asean = this repository's PyPSA-Earth scripts, identical files):
  * config.default.yaml lines 440-445: renewable.hydro.normalization {method: irena, year: 2023}, multiplier 1.1;
  * scripts/build_renewable_profiles.py lines 267-303 (get_irena_annual_hydro_generation: IRENA Country sheet, 'Renewable hydropower'),
    382-520 (rescale_hydro: per country factor = IRENA generation of the year / summed annual runoff of the plants in the profile),
    600-681 (the plants are all powerplantmatching units with carrier 'hydro' inside the hydrobasins, incl. pumped storage; inflow x 1.1);
  * scripts/add_electricity.py lines 880-1000 (attach_hydro: only run-of-river and reservoir inflows enter the network, aggregated per bus);
so the national annual inflow given to the network's stock is at most IRENA 2023 generation x 1.1, spread over the plants that the
author chain knew; if that stock is incomplete the inflow per MW is inflated, and units added later (S4A-2 / S4B-1 GEM units, S4B-2
new-build proxies) that copy the per-MW inflow of their node / country count the national inflow a second time.

Data: frozen electric base (author network) and the S4C-1 integrated build (base + S4A / S4B additions), storage_units_t.inflow of the
'hydro existing' units, ror availability x p_nom of the 'ror existing' generators (3 h snapshots x weights); Ember yearly (CC BY 4.0, file of
decision 74, sources_s4b/ember), hydro generation and capacity 2019-2025, median; IRENA Statistics Extract 2025H2 (the author file),
'Renewable hydropower' generation and capacity 2023.

    python scripts_project/s4c_2_hydro_diagnosis.py --ember <csv> --irena <xlsx> --build results_project/s4c/build_s4c1/integrated --output research_inputs/hydro_v5
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

ROOT = Path(__file__).resolve().parents[1]
EB = ROOT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"
ISO = {"BN": "BRN", "KH": "KHM", "ID": "IDN", "LA": "LAO", "MY": "MYS", "MM": "MMR", "PH": "PHL", "SG": "SGP", "TH": "THA", "TL": "TLS", "VN": "VNM"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stock_table(n, tag):
    w = n.snapshot_weightings.generators
    su = n.storage_units; h = su[(su.carrier == "hydro existing")]
    inf = n.storage_units_t.inflow
    rows = []
    for name, z in h.iterrows():
        e = float((inf[name] * w).sum()) if name in inf else 0.0
        rows.append(dict(source=tag, component="StorageUnit", name=name, kind="reservoir", node=z.bus, country=str(z.country), p_nom=float(z.p_nom), annual_inflow_mwh=e,
                         max_hours=float(z.max_hours), resource_identity=str(z.get("resource_identity", ""))))
    g = n.generators; r = g[g.carrier == "ror existing"]
    pmax = n.generators_t.p_max_pu
    for name, z in r.iterrows():
        series = pmax[name] if name in pmax else pd.Series(float(z.p_max_pu), index=n.snapshots)
        rows.append(dict(source=tag, component="Generator", name=name, kind="ror", node=z.bus, country=str(z.country), p_nom=float(z.p_nom),
                         annual_inflow_mwh=float((series * float(z.p_nom) * w).sum()), max_hours=np.nan, resource_identity=str(z.get("resource_identity", ""))))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ember", type=Path, required=True); ap.add_argument("--irena", type=Path, required=True)
    ap.add_argument("--build", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    base = stock_table(pypsa.Network(str(EB)), "frozen_electric_base")
    nb = pypsa.Network(str(a.build / "integrated_2920_3h_unsolved.nc"))
    full = stock_table(nb, "build")
    full["origin"] = np.where(full.name.isin(base.name), "author_base", "added_s4a_s4b")
    # per-MW inflow check of the added units against their node / country stock
    # Ember
    e = pd.read_csv(a.ember)
    eh = e[(e["Electricity source"] == "Hydro") & e["ISO 3 code"].isin(ISO.values()) & e.Year.between(2019, 2025)]
    inv = {v: k for k, v in ISO.items()}
    eh = eh.assign(country=eh["ISO 3 code"].map(inv))
    ember = eh.pivot_table(index="country", columns="Year", values=["Generation (TWh)", "Capacity (GW)"], aggfunc="first")
    # IRENA (author normalisation source)
    ir = pd.read_excel(a.irena, sheet_name="Country")
    ir = ir[(ir.Technology == "Renewable hydropower") & (ir["Producer Type"] != "All types") & ir["ISO3 code"].isin(ISO.values())]
    irg = ir.groupby(["ISO3 code", "Year"])[["Electricity Generation (GWh)", "Electricity Installed Capacity (MW)"]].sum().reset_index()
    irg["country"] = irg["ISO3 code"].map(inv)
    rows = []
    for c in sorted(ISO):
        b = base[base.country == c]; f = full[full.country == c]; add = f[f.origin == "added_s4a_s4b"]
        gen = ember["Generation (TWh)"].loc[c] if c in ember.index else pd.Series(dtype=float)
        cap = ember["Capacity (GW)"].loc[c] if c in ember.index else pd.Series(dtype=float)
        cf_y = (gen / (8.76 * cap)).replace([np.inf, -np.inf], np.nan)
        i23 = irg[(irg.country == c) & (irg.Year == 2023)]
        ig = float(i23["Electricity Generation (GWh)"].sum()) / 1e3 if len(i23) else np.nan
        icap = float(i23["Electricity Installed Capacity (MW)"].sum()) / 1e3 if len(i23) else np.nan
        def cfx(x):
            return float(x.annual_inflow_mwh.sum() / (x.p_nom.sum() * 8760)) if x.p_nom.sum() > 0 else np.nan
        rows.append(dict(country=c,
                         base_reservoir_mw=float(b[b.kind == "reservoir"].p_nom.sum()), base_ror_mw=float(b[b.kind == "ror"].p_nom.sum()),
                         base_inflow_twh=float(b.annual_inflow_mwh.sum() / 1e6), base_inflow_reservoir_twh=float(b[b.kind == "reservoir"].annual_inflow_mwh.sum() / 1e6),
                         base_inflow_ror_twh=float(b[b.kind == "ror"].annual_inflow_mwh.sum() / 1e6), base_cf=cfx(b),
                         added_reservoir_mw=float(add[add.kind == "reservoir"].p_nom.sum()), added_ror_mw=float(add[add.kind == "ror"].p_nom.sum()),
                         added_inflow_twh=float(add.annual_inflow_mwh.sum() / 1e6), added_cf=cfx(add),
                         build_mw=float(f.p_nom.sum()), build_inflow_twh=float(f.annual_inflow_mwh.sum() / 1e6), build_cf=cfx(f),
                         ember_gen_median_twh=float(gen.median()) if len(gen.dropna()) else np.nan, ember_cap_median_gw=float(cap.median()) if len(cap.dropna()) else np.nan,
                         ember_cf_median=float(cf_y.median()) if len(cf_y.dropna()) else np.nan, ember_years=",".join(str(int(y)) for y in gen.dropna().index),
                         irena_2023_gen_twh=ig, irena_2023_cap_gw=icap,
                         ratio_base_inflow_to_irena2023_x1_1=(float(b.annual_inflow_mwh.sum() / 1e6) / (ig * 1.1) if ig and ig > 0 else np.nan),
                         ratio_build_inflow_to_irena2023_x1_1=(float(f.annual_inflow_mwh.sum() / 1e6) / (ig * 1.1) if ig and ig > 0 else np.nan),
                         ratio_base_cap_to_irena2023_cap=(float(b.p_nom.sum() / 1e3) / icap if icap and icap > 0 else np.nan),
                         ratio_build_inflow_to_ember_x1_1=(float(f.annual_inflow_mwh.sum() / 1e6) / (float(gen.median()) * 1.1) if len(gen.dropna()) and gen.median() > 0 else np.nan)))
    t = pd.DataFrame(rows)
    a.output.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.output / "HYDRO_INFLOW_DIAGNOSIS_S4C2.csv", index=False)
    full.to_csv(a.output / "HYDRO_STOCK_COMPONENTS_S4C2.csv", index=False)
    ember_long = eh[["country", "Year", "Generation (TWh)", "Capacity (GW)"]].sort_values(["country", "Year"])
    ember_long.to_csv(a.output / "HYDRO_EMBER_2019_2025.csv", index=False)
    irg.to_csv(a.output / "HYDRO_IRENA_RENEWABLE_HYDRO.csv", index=False)
    ev = dict(electric_base=dict(path=str(EB.relative_to(ROOT)), sha256=sha(EB)), build=str(a.build), ember=dict(file=str(a.ember), sha256=sha(a.ember)),
              irena=dict(file=str(a.irena), sha256=sha(a.irena)), totals=dict(base_mw=float(base.p_nom.sum()), base_inflow_twh=float(base.annual_inflow_mwh.sum() / 1e6),
              build_mw=float(full.p_nom.sum()), build_inflow_twh=float(full.annual_inflow_mwh.sum() / 1e6)))
    (a.output / "HYDRO_INFLOW_DIAGNOSIS_S4C2.json").write_text(json.dumps(ev, indent=1, default=str) + "\n")
    pd.set_option("display.width", 280); pd.set_option("display.max_columns", 40)
    show = ["country", "base_reservoir_mw", "base_ror_mw", "base_inflow_twh", "base_cf", "added_reservoir_mw", "added_ror_mw", "added_inflow_twh", "added_cf", "build_inflow_twh", "build_cf",
            "ember_gen_median_twh", "ember_cap_median_gw", "ember_cf_median", "irena_2023_gen_twh", "irena_2023_cap_gw", "ratio_base_inflow_to_irena2023_x1_1", "ratio_build_inflow_to_irena2023_x1_1",
            "ratio_base_cap_to_irena2023_cap", "ratio_build_inflow_to_ember_x1_1"]
    print(t[show].round(3).T.to_string())
    print(json.dumps(ev["totals"]))


if __name__ == "__main__":
    main()
