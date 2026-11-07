"""V31 W15 supplement 01 (decision 218): the bunker player's Owen benefit and costs attributed to the bunkering countries, beside the
independent-account result (post-processing only; no solver, no network change).

  python -I w15c_bunker_attribution.py --final <unpacked/export> --out <work/p1_v31_w15_20261106>

Keys: (a) energy share s_c of the bunker loads (aviation international oil + international shipping methanol) by the country of the load's
location node, read from each solved network (loads_t_p x weight); (b) cost share k_c = the bunker player's fuel purchase expenditure at
the nodes of country c in the integrated run (ledger subjects 'bunker_oil final energy' + 'bunker_methanol final energy', the settlement at
the node dual), cross-checked against sum_t marginal_price(bunker bus) x load x weight from the solved network.
Writes BUNKER_ATTRIBUTION.csv and evidence/BUNKER_ATTRIBUTION.json.
"""
import argparse, csv, json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
PAIRS = {"A": ("F1", "F2"), "B": ("F3", "F4")}


def nc_of(d: Path) -> Path:
    return sorted(d.glob("*_solved.nc"))[0]


def bunker_loads(d: Path) -> pd.DataFrame:
    """Annual energy and nodal-price expenditure of every bunker load of one solved network."""
    ds = xr.open_dataset(nc_of(d))
    names = lambda dim: [str(x) for x in ds[dim].values]
    li = names("loads_i")
    lbus = pd.Series(ds["loads_bus"].values.astype(str), index=li); lcar = pd.Series(ds["loads_carrier"].values.astype(str), index=li)
    bi = names("buses_i")
    bcountry = pd.Series(ds["buses_country"].values.astype(str), index=bi)
    bloc = pd.Series(ds["buses_location"].values.astype(str), index=bi) if "buses_location" in ds else pd.Series("", index=bi)
    meta = json.loads(ds.attrs["meta"]) if "meta" in ds.attrs else {}
    rb = meta.get("research_bunkers", {}); asean = rb.get("asean_loads", {})
    sel = [l for l in li if l in asean]
    w = ds["snapshots_objective"].values.astype(float); wl = ds["snapshots_generators"].values.astype(float) if "snapshots_generators" in ds else w
    lp = pd.DataFrame(ds["loads_t_p"].values.astype(float), columns=names("loads_t_p_i"))
    mp = pd.DataFrame(ds["buses_t_marginal_price"].values.astype(float), columns=names("buses_t_marginal_price_i"))
    rows = []
    for l in sel:
        bus = lbus[l]; node = bloc.get(bus, "") or bus.split(" ")[0] + " " + bus.split(" ")[1]
        cc = bcountry.get(node, "")
        p = lp[l].to_numpy() if l in lp.columns else np.zeros(len(w))
        lam = mp[bus].to_numpy() if bus in mp.columns else np.full(len(w), np.nan)
        rows.append(dict(load=l, bus=bus, node=node, country=cc, account=asean[l].get("account"), carrier=lcar[l], sector=asean[l].get("sector"),
                         annual_mwh=float((p * wl).sum()), annual_mwh_meta=float(asean[l].get("annual_mwh", np.nan)),
                         expenditure_eur=float(np.nansum(lam * p * w)), price_missing=bool(np.isnan(lam).all())))
    ds.close()
    df = pd.DataFrame(rows)
    df["kind"] = np.where(df.account.str.contains("Aviation"), "aviation", "shipping")
    return df


def ledger(d: Path) -> pd.DataFrame:
    return pd.read_csv(d / "COUNTRY_COST_LEDGER.csv").set_index("entity")


def owen(d: Path) -> dict:
    with (d / "m12_owen" / "OWEN.csv").open(encoding="utf-8") as f:
        return {r["player"]: float(r["owen_dual_alpha_0.5_eur"]) for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    F, OUT = Path(a.final), Path(a.out)
    loads = {r: bunker_loads(F / r) for r in ("F1", "F2", "F3", "F4")}
    led = {r: ledger(F / r) for r in loads}
    ow = {r: owen(F / r) for r in loads}
    ev = dict(keys={}, checks={}, pairs={})
    # ---------------------------------------------------------------- keys
    keys = {}
    for r, df in loads.items():
        e = df.groupby("country").annual_mwh.sum().reindex(COUNTRIES, fill_value=0.0)
        ek = df.groupby(["country", "kind"]).annual_mwh.sum().unstack(fill_value=0.0).reindex(COUNTRIES, fill_value=0.0)
        L = led[r]
        cost = -(L.reindex(list(COUNTRIES))[["bunker_oil final energy", "bunker_methanol final energy"]].fillna(0.0).sum(axis=1))
        ck = -(L.reindex(list(COUNTRIES))[["bunker_oil final energy", "bunker_methanol final energy"]].fillna(0.0))
        exp_nc = df.groupby("country").expenditure_eur.sum().reindex(COUNTRIES, fill_value=0.0)
        bun = L.loc["ASEAN_BUNKER"]
        keys[r] = dict(energy=e / e.sum(), cost=cost / cost.sum())
        ev["keys"][r] = dict(
            loads=int(len(df)), aviation_loads=int((df.kind == "aviation").sum()), shipping_loads=int((df.kind == "shipping").sum()),
            loads_with_energy=int((df.annual_mwh > 1).sum()), unresolved_country=sorted(df.loc[~df.country.isin(COUNTRIES), "load"].tolist())[:10],
            energy_total_twh=float(e.sum()) / 1e6, energy_by_country_twh={c: float(v) / 1e6 for c, v in e.items()},
            energy_by_country_kind_twh={c: {k: float(v) / 1e6 for k, v in ek.loc[c].items()} for c in COUNTRIES},
            energy_vs_meta_max_rel=float((df.annual_mwh - df.annual_mwh_meta).abs().max() / max(df.annual_mwh_meta.abs().max(), 1.0)),
            ledger_bunker_purchase_by_country_bn={c: float(v) / 1e9 for c, v in cost.items()},
            ledger_bunker_purchase_by_country_kind_bn={c: {"aviation_oil": float(ck.at[c, "bunker_oil final energy"]) / 1e9, "shipping_methanol": float(ck.at[c, "bunker_methanol final energy"]) / 1e9} for c in COUNTRIES},
            ledger_bunker_entity_bn=dict(oil=float(bun.get("bunker_oil final energy", 0.0)) / 1e9, methanol=float(bun.get("bunker_methanol final energy", 0.0)) / 1e9,
                                         total=float(bun["total"]) / 1e9),
            ledger_country_sum_vs_entity_rel=float(abs(cost.sum() - (bun.get("bunker_oil final energy", 0.0) + bun.get("bunker_methanol final energy", 0.0))) / cost.sum()),
            nodal_price_expenditure_by_country_bn={c: float(v) / 1e9 for c, v in exp_nc.items()},
            nodal_price_vs_ledger_max_abs_eur=float((exp_nc - cost).abs().max()), nodal_price_vs_ledger_rel=float((exp_nc - cost).abs().sum() / cost.sum()))
    ev["checks"]["energy_key_F1_vs_F2_max_abs_diff"] = float((keys["F1"]["energy"] - keys["F2"]["energy"]).abs().max())
    ev["checks"]["energy_key_F1_vs_F3_max_abs_diff"] = float((keys["F1"]["energy"] - keys["F3"]["energy"]).abs().max())
    ev["checks"]["cost_key_F1_vs_F2_max_abs_diff"] = float((keys["F1"]["cost"] - keys["F2"]["cost"]).abs().max())
    # ---------------------------------------------------------------- attribution
    rows = []
    for p, (ri, rd) in PAIRS.items():
        ben = {c: ow[rd].get(c, 0.0) - ow[ri].get(c, 0.0) for c in COUNTRIES}
        bb = ow[rd]["BUNKER"] - ow[ri]["BUNKER"]
        b6_obj = float(json.loads((F / rd / "SOLVE_RECEIPT.json").read_text())["objective"] - json.loads((F / ri / "SOLVE_RECEIPT.json").read_text())["objective"])
        sum_before = sum(ben.values()) + bb + (ow[rd].get("SHARED", 0.0) - ow[ri].get("SHARED", 0.0))
        ev["pairs"][p] = dict(runs=f"{rd} - {ri}", bunker_benefit_eur=bb, bunker_integrated_cost_eur=ow[ri]["BUNKER"], bunker_no_new_xb_cost_eur=ow[rd]["BUNKER"],
                              b6_objective_eur=b6_obj, owen_benefit_sum_before_eur=sum_before,
                              owen_sum_vs_b6_objective_rel=abs(sum_before - b6_obj) / b6_obj, keys={})
        base_rank = pd.Series(ben).rank(ascending=False, method="first")
        for kname in ("energy", "cost"):
            kk = keys[ri][kname]   # keys from the integrated run of the pair (energy key identical in both runs)
            att = {c: ben[c] + kk[c] * bb for c in COUNTRIES}
            sum_after = sum(att.values()) + (ow[rd].get("SHARED", 0.0) - ow[ri].get("SHARED", 0.0))
            rank = pd.Series(att).rank(ascending=False, method="first")
            tot_b, tot_a = sum(ben.values()) + bb, sum(att.values())
            for c in COUNTRIES:
                rows.append(dict(pair=p, runs=f"{rd}-{ri}", key=kname, country=c, key_share=kk[c],
                                 benefit_independent_eur=ben[c], bunker_benefit_attributed_eur=kk[c] * bb, benefit_attributed_eur=att[c],
                                 share_of_total_independent=ben[c] / tot_b, share_of_total_attributed=att[c] / tot_a,
                                 rank_independent=int(base_rank[c]), rank_attributed=int(rank[c]),
                                 cost_integrated_independent_eur=ow[ri][c], cost_integrated_attributed_eur=ow[ri][c] + kk[c] * ow[ri]["BUNKER"],
                                 cost_no_new_xb_independent_eur=ow[rd][c], cost_no_new_xb_attributed_eur=ow[rd][c] + kk[c] * ow[rd]["BUNKER"]))
            chg = {c: att[c] - ben[c] for c in COUNTRIES}
            ev["pairs"][p]["keys"][kname] = dict(sum_after_eur=sum_after, attribution_conservation_rel=abs(sum_after - sum_before) / abs(sum_before),
                                                 sum_after_vs_b6_objective_rel=abs(sum_after - b6_obj) / b6_obj,
                                                 largest_increase=max(chg, key=chg.get), largest_increase_eur=max(chg.values()),
                                                 rank_changes={c: (int(base_rank[c]), int(rank[c])) for c in COUNTRIES if int(base_rank[c]) != int(rank[c])},
                                                 cost_sum_check_rel=abs(sum(ow[ri][c] + kk[c] * ow[ri]["BUNKER"] for c in COUNTRIES) - sum(ow[ri][c] for c in COUNTRIES) - ow[ri]["BUNKER"]) / ow[ri]["BUNKER"])
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "BUNKER_ATTRIBUTION.csv", index=False, lineterminator="\n")
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "BUNKER_ATTRIBUTION.json").write_text(json.dumps(ev, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in loads:
        k = ev["keys"][r]
        print(r, "loads", k["loads"], k["aviation_loads"], k["shipping_loads"], "energy TWh %.3f" % k["energy_total_twh"], "meta rel %.2e" % k["energy_vs_meta_max_rel"],
              "ledger vs entity %.2e" % k["ledger_country_sum_vs_entity_rel"], "nodal vs ledger rel %.2e" % k["nodal_price_vs_ledger_rel"], "unresolved", k["unresolved_country"])
    print("checks", ev["checks"])
    for p, v in ev["pairs"].items():
        print(p, "bunker benefit %.4f bn" % (v["bunker_benefit_eur"] / 1e9), "sum vs B6 %.2e" % v["owen_sum_vs_b6_objective_rel"],
              {k: (x["attribution_conservation_rel"], x["largest_increase"], round(x["largest_increase_eur"] / 1e9, 4), x["rank_changes"]) for k, x in v["keys"].items()})
    print(df[df.pair == "A"].pivot_table(index="country", columns="key", values=["key_share", "benefit_attributed_eur"]).round(4).to_string())


if __name__ == "__main__":
    main()
