"""W19a section 2.1: CO2 account of KH (and of every country, for the flows towards KH) in the v3.1 2920x3h F1 / F2 solutions.

Read only. Source: the W10 / D2a first-order extraction caches of the v3.1 solved networks (cache schema v4-w10-first-order-v1;
meta.json records the solved-network SHA256, checked against the files by w19a_2_verify_nc.py). Per link, per port j:
CO2 into the bus of port j = flow0 x efficiency_j (bus0: -flow0), flow0 = sum_t w_t p0_t (objective weights, 3 h).
Store e_nom upper duals: stores_enom_upper.csv (D2a 4.1, raw linopy sign); global-row duals: meta.json scalars.

    python w19a_1_kh_co2_account.py <d2a cache root> <delivery dir>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107/cache")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109")
RUNS = {"F1": "7508ec72ddce9a9d_v1", "F2": "4cc51892d748805f_v1"}
COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
TRANSPORT = {"CO2 pipeline", "CO2 ship", "CO2 transit ship", "CO2 export extra-ASEAN", "CO2 sequestration"}


def source_class(carrier: str) -> str:
    c = carrier.lower()
    if c == "dac":
        return "DAC"
    if "biomass" in c or "biogas" in c:
        return "BECCS (biogenic capture)"
    if "process emissions" in c or "smr" in c or "industry" in c:
        return "industrial CCS (fossil / process)"
    if "ccgt" in c or "coal" in c or "ocgt" in c:
        return "power CCS (fossil)"
    if c in ("methanolisation", "fischer-tropsch", "sabatier"):
        return "utilisation (CO2 use)"
    return "other"


def load(key: str):
    d = CACHE / key
    b = pd.read_csv(d / "buses.csv", index_col=0)
    k = pd.read_csv(d / "links.csv", index_col=0, low_memory=False)
    s = pd.read_csv(d / "stores.csv", index_col=0)
    eu = pd.read_csv(d / "stores_enom_upper.csv", index_col=0).mu_enom_upper
    meta = json.loads((d / "meta.json").read_text())
    return b, k, s, eu, meta


def port_rows(b: pd.DataFrame, k: pd.DataFrame) -> pd.DataFrame:
    """One row per (link, port) whose bus is a 'co2 stored' or 'co2 sequestered' bus."""
    carr = b.carrier.astype(str)
    ctry = b.country.astype(str)
    rows = []
    for j in range(5):
        bc = f"bus{j}"
        if bc not in k:
            continue
        ec = None if j == 0 else ("efficiency" if j == 1 else f"efficiency{j}")
        bus = k[bc].astype(str)
        m = bus.map(carr).isin(["co2 stored", "co2 sequestered", "co2 sequestered extra-ASEAN"])
        for name, r in k[m].iterrows():
            eff = -1.0 if ec is None else float(r[ec])
            f0, fp = float(r.flow0), float(r.flow0_pos)
            rows.append(dict(link=name, carrier=str(r.carrier), port=j, bus=r[bc], bus_carrier=carr[r[bc]], country=ctry[r[bc]],
                             eff=eff, flow0=f0, flow0_pos=fp, flow0_neg=f0 - fp, co2=f0 * eff, p_nom_opt=float(r.p_nom_opt),
                             other_country=ctry.get(str(r.bus1 if j == 0 else r.bus0), ""), capital_cost=float(r.capital_cost),
                             marginal_cost=float(r.marginal_cost), length=float(r.length) if pd.notna(r.length) else np.nan))
    return pd.DataFrame(rows)


def account(lab: str, key: str):
    b, k, s, eu, meta = load(key)
    pr = port_rows(b, k)
    st = pr[pr.bus_carrier == "co2 stored"]
    out = []

    def add(country, section, item, partner, value, note=""):
        out.append(dict(run=lab, country=country, section=section, item=item, partner=partner, value=value, note=note))

    for c in COUNTRIES:
        x = st[st.country == c]
        cap = x[~x.carrier.isin(TRANSPORT)]
        # capture / use by carrier (non-transport links)
        for car, v in cap.groupby("carrier").co2.sum().items():
            if abs(v) > 1e-3:
                cls = source_class(car)
                add(c, "source" if v > 0 else "use", cls, "", v, car)
        # domestic injection
        seq = x[x.carrier == "CO2 sequestration"].co2.sum()
        add(c, "sink", "domestic injection (CO2 sequestration links)", c, seq)
        # pipelines: per link direction split
        pp = x[x.carrier == "CO2 pipeline"]
        for _, r in pp.iterrows():
            if r.other_country == c:
                continue
            if r.port == 0:       # c is bus0: positive p0 = export to other, negative p0 = import from other
                add(c, "pipeline", "export", r.other_country, -r.flow0_pos, r.link)
                add(c, "pipeline", "import", r.other_country, -r.flow0_neg * 1.0, r.link)
            else:                 # c is bus1: positive p0 = import from other, negative = export to other
                add(c, "pipeline", "import", r.other_country, r.flow0_pos * r.eff, r.link)
                add(c, "pipeline", "export", r.other_country, r.flow0_neg * r.eff, r.link)
        for car in ("CO2 ship", "CO2 transit ship", "CO2 export extra-ASEAN"):
            sh = x[x.carrier == car]
            for _, r in sh.iterrows():
                partner = r.other_country if car != "CO2 export extra-ASEAN" else "extra-ASEAN"
                if abs(r.co2) > 1e-6:
                    add(c, car, "export" if r.co2 < 0 else "import", partner, r.co2, r.link)
        # co2 stored stores (node buffers): net discharge into the bus = -(e_end - e_initial)
        ss = s[(s.carrier.astype(str) == "co2 stored") & (s.country.astype(str) == c)]
        add(c, "buffer", "co2 stored Store net discharge", "", float(-(ss.e_end - ss.e_initial).sum()))
        add(c, "check", "balance residual of co2 stored buses (should be ~0)", "", float(x.co2.sum() - (ss.e_end - ss.e_initial).sum()))
        sq = f"co2 sequestered {c}"
        if sq in s.index:
            add(c, "cap", "co2 sequestered Store e_nom (cap, t/a)", "", float(s.at[sq, "e_nom"]))
            add(c, "cap", "co2 sequestered Store final level e_end (t)", "", float(s.at[sq, "e_end"]))
            add(c, "cap", "utilisation e_end / e_nom", "", float(s.at[sq, "e_end"] / s.at[sq, "e_nom"]) if s.at[sq, "e_nom"] > 0 else np.nan)
            add(c, "dual", "Store e_nom upper dual (EUR/t, raw sign)", "", float(eu.get(sq, 0.0)))
            g = meta["scalars"].get(f"research_co2_storage_cap-{c}", 0.0)
            add(c, "dual", "global row research_co2_storage_cap dual (EUR/t)", "", float(g))
            add(c, "dual", "total cap dual = global row + Store bound (EUR/t)", "", float(g) + float(eu.get(sq, 0.0)))
            add(c, "dual", "co2 sequestered bus price (EUR/t, time-weighted mean)", "", float(b.at[sq, "lam_mean"]))
            add(c, "cost", "co2 sequestered Store capital_cost (EUR/t/a)", "", float(s.at[sq, "capital_cost"]))
        node_b = b[(b.carrier.astype(str) == "co2 stored") & (b.country.astype(str) == c)]
        if len(node_b):
            add(c, "dual", "co2 stored node bus price, min / max over nodes (EUR/t)", "", float(node_b.lam_mean.min()), f"max {node_b.lam_mean.max():.4f}")
        add(c, "dual", "research_country_co2_limit dual (EUR/t)", "", float(meta["scalars"].get(f"research_country_co2_limit-{c}", np.nan)))
    return pd.DataFrame(out), pr, meta


def main():
    frames, ports, metas = [], {}, {}
    for lab, key in RUNS.items():
        a, pr, meta = account(lab, key)
        frames.append(a); ports[lab] = pr; metas[lab] = meta
    long = pd.concat(frames, ignore_index=True)
    long.to_csv(OUT / "cache" / "CO2_ACCOUNT_ALL_LONG.csv", index=False)
    # aggregate by (country, section, item, partner) for the wide table
    agg = long.groupby(["country", "section", "item", "partner", "run"], dropna=False).value.sum().unstack("run").fillna(0.0).reset_index()
    agg.to_csv(OUT / "cache" / "CO2_ACCOUNT_ALL_WIDE.csv", index=False)
    # pipeline / ship transport cost per t for KH exports (annuity + marginal) as a check of the dual reading
    tc = []
    for lab, pr in ports.items():
        x = pr[(pr.country == "KH") & (pr.carrier.isin(["CO2 pipeline", "CO2 ship"])) & (pr.other_country != "KH")]
        for _, r in x.iterrows():
            out_t = r.flow0_pos if r.port == 0 else -r.flow0_neg
            if out_t > 1e3:
                ann = r.capital_cost * r.p_nom_opt
                tc.append(dict(run=lab, link=r.link, carrier=r.carrier, to=r.other_country, export_t=out_t, p_nom_opt_t_per_h=r.p_nom_opt,
                               capital_cost_eur_per_t_h=r.capital_cost, marginal_cost_eur_per_t=r.marginal_cost, length_km=r.length,
                               annuity_eur=ann, annuity_per_t=ann / out_t, total_per_t=ann / out_t + r.marginal_cost))
    pd.DataFrame(tc).to_csv(OUT / "cache" / "KH_EXPORT_ROUTE_COST.csv", index=False)
    json.dump({lab: dict(nc_sha256=m["nc_sha256"], duals_sha256=m["duals_sha256"], objective=m["objective"], objective_constant=m["objective_constant"],
                         snapshots=m["snapshots"], weight_sum=m["weight_sum"]) for lab, m in metas.items()},
              open(OUT / "cache" / "CO2_ACCOUNT_SOURCES.json", "w"), indent=1)
    print(agg[agg.country == "KH"].to_string())
    print(pd.DataFrame(tc).to_string())


if __name__ == "__main__":
    main()
