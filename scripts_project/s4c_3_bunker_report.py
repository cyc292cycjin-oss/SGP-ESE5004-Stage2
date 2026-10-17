"""S4C-3 report table (decision 88, instruction S4C-3 item 4): per country the international bunker demand and its CO2 under the three
attributions asean_pool (main) | bunkering_country (former state) | excluded, from the static builds (no solver).

CO2 columns are the fuel carbon content of the bound demand (kerosene x EF_oil, methanol x EF_methanol, technology-data v0.15.0 'CO2 intensity'):
the amount booked if the fuel were fossil (kerosene) or the carbon the methanol carries (booked at synthesis in the producing country under
origin_neutral, decision 64). Where it is booked depends on the attribution (column 'kerosene_co2_account').

    python scripts_project/s4c_3_bunker_report.py --asean-pool <build dir> --bunkering-country <build dir> --excluded <build dir> --output <dir>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

ACCOUNTS = {"InternationalAviationBunker": "aviation", "InternationalShippingBunker": "shipping"}


def load_net(d: Path, scenario="integrated"):
    import pypsa
    logging.disable(logging.WARNING)
    return pypsa.Network(str(d / f"{scenario}_2920_3h_unsolved.nc"))


def annual_by(n):
    w = n.snapshot_weightings.generators
    a = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum()
    return pd.DataFrame(dict(country=n.loads.country, account=n.loads.account, carrier=n.loads.carrier, mwh=a))


def main():
    ap = argparse.ArgumentParser()
    for k in ("asean-pool", "bunkering-country", "excluded", "output"):
        ap.add_argument("--" + k, type=Path, required=True)
    a = ap.parse_args()
    nets = {"asean_pool": load_net(a.asean_pool), "bunkering_country": load_net(a.bunkering_country), "excluded": load_net(a.excluded)}
    led = {k: n.meta["research_bunkers"] for k, n in nets.items()}
    for k, v in led.items():
        if v["mode"] != k:
            raise ValueError(f"build {k} has mode {v['mode']}")
    ef_oil, ef_meoh = led["asean_pool"]["ef_oil_t_per_mwh"], led["asean_pool"]["ef_methanol_t_per_mwh"]
    tabs = {k: annual_by(n) for k, n in nets.items()}
    src = tabs["bunkering_country"]; src = src[src.account.isin(list(ACCOUNTS))]
    countries = sorted(set(nets["asean_pool"].buses.country) - {"ASEAN", ""})
    rows = []
    for c in countries:
        av = float(src[(src.country == c) & (src.account == "InternationalAviationBunker")].mwh.sum())
        sh = float(src[(src.country == c) & (src.account == "InternationalShippingBunker")].mwh.sum())
        r = dict(country=c, aviation_kerosene_twh=av / 1e6, shipping_methanol_twh=sh / 1e6, kerosene_co2_if_fossil_mt=av * ef_oil / 1e6, methanol_carbon_mt=sh * ef_meoh / 1e6)
        for k, t in tabs.items():
            x = t[t.country == c]
            r[f"national_bound_demand_twh_{k}"] = float(x.mwh.sum()) / 1e6
            r[f"national_bunker_demand_twh_{k}"] = float(x[x.account.isin(list(ACCOUNTS))].mwh.sum()) / 1e6
        r["kerosene_co2_account_bunkering_country"] = f"co2 atmosphere {c} (country net zero; offset with the country's own removals allowed)"
        r["kerosene_co2_account_asean_pool"] = "co2 bunkers ASEAN (net zero on its own; no removals can enter -> fossil kerosene 0)"
        r["kerosene_co2_account_excluded"] = "not bound"
        rows.append(r)
    t = pd.DataFrame(rows)
    pooled = tabs["asean_pool"]; pooled = pooled[pooled.country == "ASEAN"]
    tot = dict(country="ASEAN_TOTAL", aviation_kerosene_twh=t.aviation_kerosene_twh.sum(), shipping_methanol_twh=t.shipping_methanol_twh.sum(),
               kerosene_co2_if_fossil_mt=t.kerosene_co2_if_fossil_mt.sum(), methanol_carbon_mt=t.methanol_carbon_mt.sum(),
               asean_pool_loads_twh=float(pooled.mwh.sum()) / 1e6)
    for k in tabs:
        tot[f"national_bound_demand_twh_{k}"] = t[f"national_bound_demand_twh_{k}"].sum()
        tot[f"national_bunker_demand_twh_{k}"] = t[f"national_bunker_demand_twh_{k}"].sum()
    t = pd.concat([t, pd.DataFrame([tot])], ignore_index=True)
    a.output.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.output / "BUNKER_ATTRIBUTION_S4C3_BY_COUNTRY.csv", index=False)
    summary = dict(ef_oil_t_per_mwh=ef_oil, ef_methanol_t_per_mwh=ef_meoh,
                   asean_pool=dict(asean_loads={k: dict(v, annual_twh=v["annual_mwh"] / 1e6) for k, v in led["asean_pool"]["asean_loads"].items()}, account=led["asean_pool"]["account"],
                                   loads_moved=led["asean_pool"]["loads_moved"], links_removed=led["asean_pool"]["links_removed"], buses_removed=led["asean_pool"]["buses_removed"]),
                   excluded=dict(deferred_twh=sum(d["annual_mwh"] for d in led["excluded"]["deferred"]) / 1e6, deferred_rows=len(led["excluded"]["deferred"])),
                   load_totals_twh={k: float(v.mwh.sum()) / 1e6 for k, v in tabs.items()})
    (a.output / "BUNKER_ATTRIBUTION_S4C3_SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str))
    pd.set_option("display.width", 250)
    cols = ["country", "aviation_kerosene_twh", "shipping_methanol_twh", "kerosene_co2_if_fossil_mt", "methanol_carbon_mt"] + [f"national_bound_demand_twh_{k}" for k in tabs]
    print(t[cols].round(3).to_string())
    print(json.dumps({k: v for k, v in summary.items() if k != "asean_pool"}, default=str))
    print(json.dumps(summary["asean_pool"]["asean_loads"], default=str)[:800])


if __name__ == "__main__":
    main()
