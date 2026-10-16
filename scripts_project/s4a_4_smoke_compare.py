"""S4A-4: capacity and generation by country for wind, solar, geothermal, hydro and nuclear (plus the fossil and storage context) of
a solved 56x3h smoke network, compared with the S3B smoke (SMOKE_TEST_ONLY, representative weights; no scientific meaning before the cloud run).

    python scripts_project/s4a_4_smoke_compare.py --new results_project/s4a/smoke/solves/integrated/integrated_SMOKE_TEST_ONLY_solved.nc \
        --old results_project/s3b/smoke/solves/integrated/integrated_SMOKE_TEST_ONLY_solved.nc --gates results_project/s4a/smoke/solves/integrated/V5_GATES.json \
        --output results_project/s4a/smoke/analysis/integrated
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

GROUPS = {   # group -> (component, carriers); electricity output only
    "onwind": ("Generator", ["onwind", "onwind existing"]),
    "offwind": ("Generator", ["offwind-ac", "offwind-dc", "offwind existing"]),
    "solar": ("Generator", ["solar", "solar existing"]),
    "solar rooftop": ("Generator", ["solar rooftop"]),
    "geothermal": ("Generator", ["geothermal", "geothermal existing"]),
    "hydro reservoir": ("StorageUnit", ["hydro", "hydro existing"]),
    "ror": ("Generator", ["ror", "ror existing"]),
    "PHS": ("StorageUnit", ["PHS", "PHS existing"]),
    "nuclear": ("Generator", ["nuclear"]),
    "nuclear SMR": ("Generator", ["nuclear SMR"]),
    "coal": ("Link", ["coal existing", "lignite existing", "coal", "lignite"]),
    "gas CCGT/OCGT": ("Link", ["CCGT existing", "OCGT existing", "CCGT", "OCGT", "CCGT CC"]),
    "oil": ("Link", ["oil existing", "oil"]),
    "battery (discharge)": ("Link", ["battery discharger", "home battery discharger"]),
}


def country_of(n, bus):
    c = n.buses.country.get(bus, "") if "country" in n.buses else ""
    return str(c) if isinstance(c, str) and c else str(bus)[:2]


def tables(n):
    w = n.snapshot_weightings.generators
    rows = []
    for grp, (comp, carriers) in GROUPS.items():
        if comp == "Generator":
            df = n.generators[n.generators.carrier.isin(carriers)]
            if df.empty:
                continue
            cap = df.p_nom_opt.where(df.p_nom_extendable, df.p_nom)
            gen = n.generators_t.p.reindex(columns=df.index, fill_value=0.0).mul(w, axis=0).sum()
            avail = (n.generators_t.p_max_pu.reindex(columns=df.index).fillna(1.0).mul(w, axis=0).sum() * cap) if grp in ("onwind", "offwind", "solar", "solar rooftop", "ror") else None
            buses = df.bus
        elif comp == "StorageUnit":
            df = n.storage_units[n.storage_units.carrier.isin(carriers)]
            if df.empty:
                continue
            cap = df.p_nom_opt.where(df.p_nom_extendable, df.p_nom)
            p = n.storage_units_t.p.reindex(columns=df.index, fill_value=0.0)
            gen = p.clip(lower=0).mul(w, axis=0).sum(); avail = None; buses = df.bus
        else:
            df = n.links[n.links.carrier.isin(carriers)]
            if df.empty:
                continue
            cap = df.p_nom_opt.where(df.p_nom_extendable, df.p_nom) * df.efficiency
            gen = (-n.links_t.p1.reindex(columns=df.index, fill_value=0.0)).mul(w, axis=0).sum(); avail = None; buses = df.bus1
        for name in df.index:
            rows.append(dict(group=grp, country=country_of(n, buses[name]), mw=float(cap[name]), twh=float(gen[name]) / 1e6,
                             avail_twh=(float(avail[name]) / 1e6 if avail is not None else np.nan)))
    t = pd.DataFrame(rows)
    agg = t.groupby(["group", "country"]).agg(gw=("mw", lambda s: s.sum() / 1e3), twh=("twh", "sum"), avail_twh=("avail_twh", "sum")).reset_index()
    agg["curtailment_share"] = np.where(agg.avail_twh > 0, 1 - agg.twh / agg.avail_twh, np.nan)
    agg["cf_realised"] = np.where(agg.gw > 0, agg.twh * 1e3 / (agg.gw * 8760.0), np.nan)
    return agg


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--new", type=Path, required=True); ap.add_argument("--old", type=Path, default=None)
    ap.add_argument("--gates", type=Path, default=None); ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    nn = pypsa.Network(str(a.new)); tn = tables(nn); tn.to_csv(a.output / "CAP_GEN_BY_COUNTRY_S4A.csv", index=False)
    out = dict(new=str(a.new), objective=float(nn.objective) if nn.objective is not None else None, weights_sum=float(nn.snapshot_weightings.generators.sum()))
    tot = tn.groupby("group")[["gw", "twh"]].sum().round(2); out["asean_new"] = tot.to_dict("index")
    if a.old and a.old.exists():
        no = pypsa.Network(str(a.old)); to = tables(no); to.to_csv(a.output / "CAP_GEN_BY_COUNTRY_S3B.csv", index=False)
        m = tn.merge(to, on=["group", "country"], how="outer", suffixes=("_s4a", "_s3b")).fillna(0.0)
        m["d_gw"] = m.gw_s4a - m.gw_s3b; m["d_twh"] = m.twh_s4a - m.twh_s3b
        m.to_csv(a.output / "CAP_GEN_BY_COUNTRY_S4A_VS_S3B.csv", index=False)
        tot_o = to.groupby("group")[["gw", "twh"]].sum().round(2)
        out["asean_old"] = tot_o.to_dict("index"); out["objective_old"] = float(no.objective) if no.objective is not None else None
        pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
        print("== ASEAN totals (GW / TWh): S3B -> S4A"); print(pd.concat([tot_o.add_suffix("_s3b"), tot.add_suffix("_s4a")], axis=1).round(1).to_string())
        for grp in ["onwind", "offwind", "solar", "solar rooftop", "geothermal", "hydro reservoir", "ror", "PHS", "nuclear", "nuclear SMR", "coal", "gas CCGT/OCGT"]:
            d = m[m.group == grp].set_index("country")[["gw_s3b", "gw_s4a", "twh_s3b", "twh_s4a"]].round(1)
            d = d[(d.abs().sum(axis=1)) > 0.05]
            if len(d):
                print("==", grp); print(d.T.to_string())
        # electricity by country (all groups) and VRE realised CF / curtailment
        print("== realised CF / curtailment (S4A)"); print(tn[tn.group.isin(["onwind", "offwind", "solar", "solar rooftop"])].set_index(["group", "country"])[["gw", "twh", "cf_realised", "curtailment_share"]].round(3).to_string())
    if a.gates and a.gates.exists():
        g = json.loads(a.gates.read_text())
        out["gates"] = {k: dict(passed=v.get("passed")) for k, v in g.items() if isinstance(v, dict) and "passed" in v}
        b1 = g.get("B1", {}); out["gates_B1_countries"] = b1.get("countries")
        print("== gates", {k: v["passed"] for k, v in out["gates"].items()})
    (a.output / "S4A_SMOKE_COMPARE.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
