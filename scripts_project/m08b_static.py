"""M08b section 3 (decisions 126, 129-134): static checks of the rebuilt networks and the comparison with the networks before the corrections (no solve).

    python scripts_project/m08b_static.py --new <builds dir> --old <S4M-3 builds dir> --out <evidence dir>

Static gates on both 2920x3h networks: B5 single switch, B8 demand conservation, B11 completeness and supply routes, B13 one-way imports, B16 identical
import prices, G2 structure (G2.1 file SHA256 = build receipt + read-back, G2.2 config-subset hash = current config; G2.3 needs a solve). M08b checks:
demand = ATS anchor by country (base load, transport, industry multiplier; ledger), no negative load, temperature-band map = s2_layers.HEAT_BAND_TECH
(no electric / hydrogen input in the high band, heat pumps low only), no fixed methane overflow demand, fixed solid biomass <= national pool, LNG
terminals uncapped (8,020.43 EUR/MW/a), VN storage cap 106.07 Mt/a, ground PV cap = previous x 5.1/4.6, offshore rule pypsa_eur_v2025_07 active;
the 365x24h networks are the exact daily means (annual load energy equal). Writes M08B_STATIC_CHECKS.json, BUILD_INPUT_CHANGES_M08B.json / .csv,
M08B_NETWORK_FILES.csv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from phase4_static import config   # noqa: E402
from s2_layers import HEAT_BAND_BUS, HEAT_BAND_TECH   # noqa: E402
from v5.gates_v6 import config_subset_sha256   # noqa: E402
from v5.v5_gates import (gate_b5_single_switch, gate_b8_demand_consistency, gate_b11_completeness, gate_b11_supply_routes,   # noqa: E402
                         gate_b13_imports_one_way, gate_b16_import_prices_identical)

logging.getLogger("pypsa").setLevel(logging.ERROR)
COUNTRIES = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]
SCEN = ["integrated", "disconnected"]
FIXED_EL = ["electricity", "industry electricity", "agriculture machinery electric", "land transport EV"]   # S4R fixed electricity load definition
PV_SCALE = 5.1 / 4.6


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def loads(n) -> pd.DataFrame:
    w = n.snapshot_weightings.generators
    e = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum()
    L = n.loads.copy(); L["mwh"] = e.reindex(L.index).fillna(0.0)
    if "country" not in L:
        L["country"] = ""
    L["country"] = L.country.fillna("").astype(str)
    L["account"] = L["account"].fillna("").astype(str) if "account" in L else ""
    return L


def storage_caps(n) -> dict:
    st = n.stores[n.stores.carrier == "co2 sequestered"]
    out = {c: 0.0 for c in COUNTRIES}
    for name, z in st.iterrows():
        out[str(z.country)] = float(z.e_nom_max) if np.isfinite(z.e_nom_max) else float("inf")
    return out


def by_country(n) -> pd.DataFrame:
    L = loads(n); g = n.generators.copy()
    g["country"] = n.buses.country.reindex(g.bus).values   # renewable candidates carry no country column; their bus does
    rows = []
    for c in COUNTRIES:
        lc = L[L.country == c]
        rows.append(dict(country=c, final_demand_twh=float(lc.mwh.sum()) / 1e6,
                         base_electricity_twh=float(lc[lc.account == "Astar"].mwh.sum()) / 1e6,
                         fixed_electricity_twh=float(lc[lc.carrier.isin(FIXED_EL)].mwh.sum()) / 1e6,
                         industry_electricity_twh=float(lc[lc.carrier == "industry electricity"].mwh.sum()) / 1e6,
                         industry_heat_low_twh=float(lc[lc.carrier == "industry heat"].mwh.sum()) / 1e6,
                         industry_heat_medium_twh=float(lc[lc.carrier == "industry heat medium"].mwh.sum()) / 1e6,
                         industry_heat_high_twh=float(lc[lc.carrier == "industry heat high"].mwh.sum()) / 1e6,
                         land_transport_ev_twh=float(lc[lc.carrier == "land transport EV"].mwh.sum()) / 1e6,
                         fixed_gas_twh=float(lc[lc.carrier == "gas final energy"].mwh.sum()) / 1e6,
                         fixed_biomass_twh=float(lc[lc.carrier == "biomass final energy"].mwh.sum()) / 1e6,
                         pv_cap_gw=float(g[(g.carrier == "solar") & (g.country == c)].p_nom_max.sum()) / 1e3,
                         pv_rooftop_cap_gw=float(g[(g.carrier == "solar rooftop") & (g.country == c)].p_nom_max.sum()) / 1e3,
                         storage_cap_mt=storage_caps(n)[c] / 1e6))
    return pd.DataFrame(rows).set_index("country")


def m08b_checks(n, cfg, repo: Path, n_old) -> dict:
    out = {}
    L = loads(n); led = n.meta.get("s2_demand_ledger", {}); R = cfg["research"]
    an = pd.read_csv(repo / R["demand"]["anchor_table"]).set_index("country")
    rows = []
    for c in COUNTRIES:
        bl = float(L[(L.country == c) & (L.account == "Astar")].mwh.sum())
        rows.append(dict(country=c, base_load_mwh=bl, anchor_mwh=float(an.at[c, "base_load_anchor_mwh"]), rel=abs(bl / an.at[c, "base_load_anchor_mwh"] - 1)))
    chk = led.get("anchors", {}).get("checks", [])
    out["demand_equals_anchor"] = dict(passed=bool(max(r["rel"] for r in rows) <= 1e-6 and len(chk) == 11 and all(abs(r["transport_table_mwh"] / r["transport_anchor_mwh"] - 1) <= 1e-6 for r in chk)),
                                       base_load=rows, ledger_checks=chk, max_rel=max(r["rel"] for r in rows))
    pset = n.get_switchable_as_dense("Load", "p_set")
    out["no_negative_loads"] = dict(passed=bool((pset.values >= -1e-9).all()), min_p_set=float(pset.values.min()))
    lk = n.links; band = {}
    for b, (bus_carrier, _) in HEAT_BAND_BUS.items():
        buses = set(n.buses.index[n.buses.carrier == bus_carrier])
        feed = lk[lk.bus1.isin(buses)]
        want = {car for _, car, _ in HEAT_BAND_TECH[b]}
        in_car = sorted(set(n.buses.carrier.reindex(feed.bus0).fillna("?")))
        band[b] = dict(buses=len(buses), link_carriers=sorted(set(feed.carrier)), expected=sorted(want), input_bus_carriers=in_car,
                       per_node_links=(int(len(feed) / len(buses)) if len(buses) else 0))
    ok = all(set(band[b]["link_carriers"]) == set(band[b]["expected"]) for b in band) and not ({"AC", "H2"} & set(band["high"]["input_bus_carriers"]))
    ok &= [b for b in band if "industry heat pump" in band[b]["link_carriers"]] == ["low"]
    out["temperature_band_map"] = dict(passed=bool(ok), bands=band)
    ovg = L[L.account.isin(["IndustryBiomassOverflowToGas", "AgricultureBiomassOverflowToGas"])]
    ovh = L[L.account.isin(["IndustryBiomassOverflowUsefulHeat", "AgricultureBiomassOverflowUsefulHeat"])]
    out["no_fixed_methane_overflow"] = dict(passed=bool(len(ovg) == 0), methane_overflow_loads=int(len(ovg)), useful_heat_overflow_loads=int(len(ovh)),
                                            useful_heat_overflow_twh={str(k): float(v) / 1e6 for k, v in ovh.groupby("country").mwh.sum().items()})
    st = n.stores; pool = st[(st.bus.str.startswith("solid biomass")) & (st.get("research_role", pd.Series(index=st.index, dtype=str)) == "FINITE_RESOURCE")]
    bio = {}
    for c in COUNTRIES:
        fixed = float(L[(L.country == c) & (L.carrier == "biomass final energy")].mwh.sum()); cap = float(pool[pool.bus == f"solid biomass {c}"].e_nom.sum())
        bio[c] = dict(fixed_mwh=fixed, pool_mwh=cap, within=bool(fixed <= cap + 1e-6))
    out["fixed_biomass_within_pool"] = dict(passed=all(v["within"] for v in bio.values()), by_country=bio)
    g = n.generators; lng = g[g.carrier == "LNG import"]
    out["lng_uncapped"] = dict(passed=bool(len(lng) > 0 and np.isinf(lng.p_nom_max).all() and lng.p_nom_extendable.all() and np.allclose(lng.capital_cost, 8020.43, atol=1e-6)),
                               terminals=int(len(lng)), capital_cost=sorted(set(lng.capital_cost.round(4))))
    caps = storage_caps(n); meta_caps = (n.meta.get("research_co2_storage") or {}).get("caps_t_per_year", {})
    out["vn_storage_cap"] = dict(passed=bool(abs(caps["VN"] / 1e6 - 106.07) < 0.01 and abs(float(meta_caps.get("VN", 0)) - caps["VN"]) < 1e-3),
                                 store_e_nom_max_mt=caps["VN"] / 1e6, meta_cap_mt=float(meta_caps.get("VN", 0)) / 1e6)
    pv_new = g[g.carrier == "solar"].p_nom_max; pv_old = n_old.generators[n_old.generators.carrier == "solar"].p_nom_max
    common = pv_new.index.intersection(pv_old.index); pos = common[pv_old[common] > 0]
    ratio = pv_new[pos] / pv_old[pos]
    out["pv_cap_scale"] = dict(passed=bool(len(pos) > 0 and np.allclose(ratio, PV_SCALE, rtol=1e-6) and len(pv_new) == len(pv_old)), generators=int(len(pv_new)), compared=int(len(pos)),
                               ratio_min=float(ratio.min()), ratio_max=float(ratio.max()), expected=PV_SCALE, total_new_gw=float(pv_new.sum()) / 1e3, total_old_gw=float(pv_old.sum()) / 1e3)
    off = {car: dict(count=int((g.carrier == car).sum()), p_nom_max_gw=float(g[g.carrier == car].p_nom_max.sum()) / 1e3) for car in ["offwind-ac", "offwind-dc", "offwind-float"]}
    out["offshore_rule"] = dict(passed=bool(R["renewable"].get("offshore_rules") == "pypsa_eur_v2025_07" and off["offwind-float"]["count"] > 0), config=R["renewable"].get("offshore_rules"), by_carrier=off)
    out["passed"] = all(v["passed"] for v in out.values() if isinstance(v, dict) and "passed" in v)
    return out


def g2(n, path: Path, receipt: dict, cfg) -> dict:
    file_sha = sha(path); rec_sha = ((receipt.get("network") or {}).get("sha256")) if receipt else None
    with tempfile.TemporaryDirectory() as td:   # read-back: export the loaded network and compare the component tables
        p2 = Path(td) / "rb.nc"; n.export_to_netcdf(p2); m = pypsa.Network(p2)
        same = all(n.df(c).shape == m.df(c).shape for c in ["Bus", "Generator", "Link", "Line", "Load", "Store", "StorageUnit"]) and n.meta.get("research_config_sha256") == m.meta.get("research_config_sha256")
    sub = n.meta.get("research_config_subset_sha256"); cur = config_subset_sha256(cfg["research"])
    return dict(G2_1=dict(passed=bool(rec_sha is not None and file_sha == rec_sha and same), file_sha256=file_sha, receipt_sha256=rec_sha, readback_component_shapes_equal=bool(same)),
                G2_2=dict(passed=bool(sub == cur), network_subset_sha256=sub, current_config_subset_sha256=cur),
                G2_3=dict(passed=None, note="needs a solve (export completeness); not applicable to an unsolved network"))


def daily_equal(n3: pypsa.Network, n24: pypsa.Network) -> dict:
    a = loads(n3).mwh; b = loads(n24).mwh.reindex(a.index)
    return dict(passed=bool(np.allclose(a.values, b.values, rtol=1e-9, atol=1e-3)), loads=int(len(a)), max_abs_mwh=float((a - b).abs().max()),
                snapshots=dict(h3=int(len(n3.snapshots)), h24=int(len(n24.snapshots))))


def main():
    p = argparse.ArgumentParser(); p.add_argument("--repo", type=Path, default=HERE.parent); p.add_argument("--new", type=Path, required=True)
    p.add_argument("--old", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(); repo = a.repo.resolve(); a.out.mkdir(parents=True, exist_ok=True)
    cfgs = {s: config(repo, s) for s in SCEN}
    nets, olds, res, files, comp = {}, {}, {}, [], []
    for s in SCEN:
        f3 = a.new / s / f"{s}_2920_3h_unsolved.nc"; f24 = a.new / s / f"{s}_365_24h_unsolved.nc"
        receipt = json.loads((a.new / s / f"{s}_BUILD_RECEIPT.json").read_text()) if (a.new / s / f"{s}_BUILD_RECEIPT.json").exists() else {}
        n = pypsa.Network(f3); n24 = pypsa.Network(f24); o = pypsa.Network(a.old / s / f"{s}_2920_3h_unsolved.nc")
        nets[s], olds[s] = n, o
        res[s] = dict(B8=gate_b8_demand_consistency(n), B11_completeness=gate_b11_completeness(n, cfgs[s]), B11_supply_routes=gate_b11_supply_routes(n, cfgs[s]),
                      B13=gate_b13_imports_one_way(n), G2=g2(n, f3, receipt, cfgs[s]), daily_mean_365x24h=daily_equal(n, n24), M08b=m08b_checks(n, cfgs[s], repo, o))
        for f in (f3, f24):
            files.append(dict(scenario=s, file=f.name, bytes=f.stat().st_size, mib=round(f.stat().st_size / 2**20, 2), sha256=sha(f), resolution="2920x3h" if "2920" in f.name else "365x24h",
                              snapshots=len(n.snapshots) if "2920" in f.name else len(n24.snapshots)))
        new_t, old_t = by_country(n), by_country(o)
        for c in COUNTRIES:
            row = dict(scenario=s, country=c)
            for k in new_t.columns:
                row[f"{k}_old"] = float(old_t.at[c, k]); row[f"{k}_new"] = float(new_t.at[c, k])
            comp.append(row)
    res["B5"] = gate_b5_single_switch(cfgs["integrated"], cfgs["disconnected"])
    res["B16"] = gate_b16_import_prices_identical(nets["integrated"], nets["disconnected"])
    # industry physical output (tables): ratio-table main (pre-M08b networks) vs the ATS-anchor rule
    old_i = pd.read_csv(repo / "research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv").set_index("country")
    new_i = pd.read_csv(repo / "research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
    for r in comp:
        c = r["country"]
        r.update(cement_mt_old=float(old_i.at[c, "cement_2050_t"]) / 1e6, cement_mt_new=float(new_i.at[c, "cement_2050_t"]) / 1e6,
                 steel_mt_old=float(old_i.at[c, "crude_steel_2050_t"]) / 1e6, steel_mt_new=float(new_i.at[c, "crude_steel_2050_t"]) / 1e6)
    cdf = pd.DataFrame(comp)
    cdf.to_csv(a.out / "BUILD_INPUT_CHANGES_M08B.csv", index=False, float_format="%.6f")
    pd.DataFrame(files).to_csv(a.out / "M08B_NETWORK_FILES.csv", index=False)
    summary = {s: {k: (v.get("passed") if isinstance(v, dict) else v) for k, v in res[s].items() if k not in ("G2", "M08b")} | {f"G2.{k[3:]}": v["passed"] for k, v in res[s]["G2"].items()}
               | {f"M08b.{k}": v["passed"] for k, v in res[s]["M08b"].items() if isinstance(v, dict)} for s in SCEN}
    summary["B5"] = res["B5"]["passed"]; summary["B16"] = res["B16"]["passed"]
    old_meta = {s: dict(network=str(a.old / s / f"{s}_2920_3h_unsolved.nc"), sha256=sha(a.old / s / f"{s}_2920_3h_unsolved.nc"),
                        research_config_sha256=olds[s].meta.get("research_config_sha256")) for s in SCEN}
    (a.out / "M08B_STATIC_CHECKS.json").write_text(json.dumps(dict(script="scripts_project/m08b_static.py", summary=summary, results=res), indent=1, default=str, sort_keys=True))
    tot = cdf.groupby("scenario").sum(numeric_only=True)
    (a.out / "BUILD_INPUT_CHANGES_M08B.json").write_text(json.dumps(dict(script="scripts_project/m08b_static.py", before=old_meta, after={s: dict(network=str(a.new / s)) for s in SCEN},
                                                                         definitions=dict(final_demand_twh="all loads of the country (energy carriers incl. useful heat, feedstock, H2, ammonia / methanol; bunkers in the regional pool excluded)",
                                                                                          base_electricity_twh="Astar loads (base / non-industry electricity)", fixed_electricity_twh="base + industry electricity + agriculture machinery electric + land transport EV (S4R definition)",
                                                                                          pv_cap_gw="sum of p_nom_max of the ground-mounted solar candidates", storage_cap_mt="annual national CO2 storage cap (co2 sequestered Store e_nom_max)",
                                                                                          cement_and_steel_mt="2050 physical output (old: ratio-table main INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv; new: ATS anchor + output rule)"),
                                                                         totals_11_countries=tot.to_dict(orient="index"), by_country=comp, files=files), indent=1, default=str))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
