"""DFX F5.3: demand review of the v2 networks (adapted from work/p1_dmd_20261026/scripts/dmd_d1_demand.py and dmd_d3_benchmark.py; the originals
are untouched). Read-only on the repository and the networks; no solve.

  tables   export the v1 demand tables (git blob of the rules commit 834a0f19 = the ec80668f tables) to results_project/dfx_v3/tables_v1
  d1 --tag v1|v2   every exogenous load of the four networks of the tag (builds_v1 / builds_v2) classified country x sector x subsector x carrier
                   (industry reconstructed by product with the s3_0_industry.py algorithm incl. the DFX F2 production-rule row) -> DEMAND_BY_COUNTRY_SECTOR_CARRIER_<tag>.csv
  diff     v2 - v1 per row -> DEMAND_DIFF_V2_V1.csv (+ summaries by sector / country / carrier)
  bridge   AEO8 ATS 2050 TFEC -> v2 loads, step by step, closure <= 1e-3 TWh -> evidence/DFX_BRIDGE_V2.json, DFX_BRIDGE_V2.csv
  percap   per-country per-capita fixed electricity and fixed-electricity / ATS ratios of v2 (pre-solve; the solved R1 columns of DMD are not available for v2) -> DFX_ELECTRICITY_PER_CAPITA_V2.csv

Usage (WSL pypsa-earth python): python dfx_demand_review.py tables|d1 --tag v2|diff|bridge|percap
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
RES = MAIN / "results_project/dfx_v3"
WT = Path("/home/jin/wt_dfx_v3_20261026")
OUT = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026")
RULES_COMMIT = "834a0f19"
C11 = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
OTHER_BUCKET = {"other", "construction", "mining and quarrying"}
TABLE_TO_LOAD = {"electricity": "industry electricity", "heat": "industry heat", "hydrogen": "industry hydrogen", "ammonia": "industry ammonia",
                 "methanol": "industry methanol", "gas": "gas final energy", "biomass": "biomass final energy", "oil": "oil final energy", "coal": "coal final energy"}
PRODUCT = {"HVC": "HVC", "Ammonia": "ammonia", "Methanol": "methanol", "Chlorine": "chlorine", "Other chemicals": "other chemicals", "Pharmaceutical products etc.": "other chemicals"}
TABLES = ["DEMAND_ANCHOR_AEO8_ATS.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv", "INDUSTRY_SUBSECTOR_MAPPING_UNSD_PYPSA_EUR.csv",
          "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv", "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "INDUSTRY_OUTPUT_2050_M08B.csv",
          "INDUSTRY_2050_OTHER_BUCKET.csv"]
HVC = ["NonEnergy:Naphtha", "NonEnergy:Ethane", "NonEnergy:Liquefied petroleum gas (LPG)", "NonEnergy:Natural gas liquids"]
LAND = ["RoadResidualFuel", "TransportNEC", "TransportEmbeddedFuelParent"]
TWH_PER_MTOE = 11.63
num = lambda s: float(str(s).replace(",", ""))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tables_dir(tag: str) -> Path:
    return (RES / "tables_v1") if tag == "v1" else (WT / "research_inputs/demand_v5")


def export_v1_tables():
    d = RES / "tables_v1"; d.mkdir(parents=True, exist_ok=True)
    for f in TABLES:
        txt = subprocess.run(["git", "show", f"{RULES_COMMIT}:research_inputs/demand_v5/{f}"], cwd=WT, check=True, capture_output=True, text=True).stdout
        (d / f).write_text(txt, encoding="utf-8")
    print("v1 tables exported:", d, len(TABLES))


def load_table(n) -> pd.DataFrame:
    w = n.snapshot_weightings
    assert np.allclose(w.generators, w.objective) and abs(w.generators.sum() - 8760.0) < 1e-6
    e = n.get_switchable_as_dense("Load", "p_set").mul(w.generators, axis=0).sum()
    L = n.loads[["bus", "carrier", "sector", "account", "country"]].copy()
    L["mwh"] = e.reindex(L.index).fillna(0.0)
    L["bus_carrier"] = n.buses.carrier.reindex(L.bus).values
    L["time_varying"] = L.index.isin(n.loads_t.p_set.columns)
    for c in ("sector", "account", "country"):
        L[c] = L[c].fillna("").astype(str)
    return L


def industry_split(c: str, tab: pd.DataFrame, mp: dict, uh: pd.Series) -> list:
    """Same algorithm as DMD D1 (s3_0_industry.py useful_heat_bands) plus the DFX F2 production-rule ammonia row."""
    rows = []
    t = tab[tab.country == c]
    for sub in ("iron and steel", "cement"):
        for r in t[(t.subsector == sub) & (t.carrier != "all (see mapping shares)")].itertuples():
            if r.mwh_2050 != 0:
                rows.append(dict(subsector=sub, table_carrier=r.carrier, mwh=float(r.mwh_2050), method=r.method, tier=r.tier))
    for r in t[t.carrier == "all (see mapping shares)"].itertuples():
        if r.subsector in OTHER_BUCKET:
            continue
        p = re.search(r"via (.+)$", r.method).group(1)
        fs = mp[(r.subsector, p)]
        prod = PRODUCT.get(p, r.subsector)
        for car, sh in fs.items():
            if sh != 0 and r.mwh_2050 != 0:
                rows.append(dict(subsector=prod, table_carrier=car, mwh=float(r.mwh_2050) * sh, method=f"{r.subsector} energy fallback via {p} x future share {sh:.6g}", tier=r.tier))
    for r in t[t.subsector == "ammonia (production rule)"].itertuples():   # DFX F2
        rows.append(dict(subsector="ammonia", table_carrier="ammonia", mwh=float(r.mwh_2050), method=r.method, tier=r.tier))
    ob = "other bucket (other / construction / mining)"
    for col, car in (("other_heat_low_mwh", "heat"), ("other_heat_medium_a_mwh", "heat_medium_a"), ("other_heat_medium_b_mwh", "heat_medium_b"),
                     ("other_heat_high_mwh", "heat_high"), ("other_electricity_2050_mwh", "electricity"), ("other_mechanical_oil_mwh", "oil"),
                     ("other_mechanical_coal_mwh", "coal"), ("other_mechanical_gas_mwh", "gas"), ("other_mechanical_biomass_mwh", "biomass")):
        v = float(uh.get(col, 0.0))
        if v != 0:
            rows.append(dict(subsector=ob, table_carrier=car, mwh=v, method=f"OTHER_USEFUL_HEAT_BANDS {col}", tier="C"))
    return rows


def d1(tag: str):
    import pypsa
    nets_dir = RES / f"builds_{tag}"; DEM = tables_dir(tag)
    NETS = {("integrated", "2920x3h"): nets_dir / "integrated/integrated_2920_3h_unsolved.nc", ("integrated", "365x24h"): nets_dir / "integrated/integrated_365_24h_unsolved.nc",
            ("disconnected", "2920x3h"): nets_dir / "disconnected/disconnected_2920_3h_unsolved.nc", ("disconnected", "365x24h"): nets_dir / "disconnected/disconnected_365_24h_unsolved.nc"}
    checks = dict(tag=tag, networks={}); tabs = {}
    for (scen, res), p in NETS.items():
        checks["networks"][f"{scen}_{res}"] = dict(path=str(p), sha256=sha256(p), bytes=p.stat().st_size)
        n = pypsa.Network(str(p)); tabs[(scen, res)] = load_table(n)
        if (scen, res) == ("integrated", "2920x3h"):
            meta_bunkers = n.meta["research_bunkers"]; checks["ledger_parameters"] = n.meta["s2_demand_ledger"]["parameters"]; checks["research_config_sha256"] = n.meta.get("research_config_sha256")
    base = tabs[("integrated", "2920x3h")]
    cons = {}
    for key, a_key, other in [("2920_vs_365_integrated", ("integrated", "2920x3h"), ("integrated", "365x24h")), ("integrated_vs_disconnected_2920", ("integrated", "2920x3h"), ("disconnected", "2920x3h")),
                              ("integrated_vs_disconnected_365", ("integrated", "365x24h"), ("disconnected", "365x24h"))]:
        a = tabs[a_key].mwh; b = tabs[other].mwh; idx = a.index.union(b.index); d = (a.reindex(idx) - b.reindex(idx)).abs()
        cons[key] = dict(loads_a=int(len(a)), loads_b=int(len(b)), only_in_a=int(len(a.index.difference(b.index))), only_in_b=int(len(b.index.difference(a.index))),
                         max_abs_diff_mwh=float(d.max()), max_rel_diff=float((d / a.reindex(idx).abs().clip(lower=1.0)).max()), total_a_twh=float(a.sum() / 1e6), total_b_twh=float(b.sum() / 1e6))
    checks["consistency"] = cons
    an = pd.read_csv(DEM / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    tab = pd.read_csv(DEM / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
    mpt = pd.read_csv(DEM / "INDUSTRY_SUBSECTOR_MAPPING_UNSD_PYPSA_EUR.csv")
    mp = {(r.unsd_subsector, r.pypsa_eur_sector): json.loads(r.future_shares) for r in mpt.itertuples()}
    uhs = pd.read_csv(DEM / "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
    dt = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False); dt["v"] = pd.to_numeric(dt.value_2050_mwh, errors="coerce").fillna(0.0)
    checks["input_sha256"] = {f: sha256(DEM / f) for f in TABLES if (DEM / f).exists()}
    par = checks["ledger_parameters"]
    g = {k: v.groupby(["country", "account", "carrier"]).mwh.sum() for k, v in tabs.items()}

    def val(country, account, carrier):
        return {f"twh_{scen}_{res}": float(s.get((country, account, carrier), 0.0)) / 1e6 for (scen, res), s in g.items()}

    rows = []

    def add(country, sector, subsector, carrier, energy_form, account, values, derivation, source_twh=None, source_note=""):
        rows.append(dict(country=country, sector=sector, subsector=subsector, carrier=carrier, energy_form=energy_form, network_account=account, **values,
                         source_final_energy_twh=source_twh, source_note=source_note, derivation=derivation))

    for c in C11:
        a = an.loc[c]; d = dt[dt.country == c]
        tot = val(c, "Astar", "electricity"); bl = float(a.base_load_anchor_mwh)
        for sec, sub, col in (("Residential", "", "residential_elec_anchor_mwh"), ("Commercial", "", "commercial_elec_anchor_mwh"), ("AgricultureOthers", "", "agri_other_elec_anchor_mwh"),
                              ("Transport", "rail / existing electric road (2019 transport electricity)", "transport_elec_anchor_mwh")):
            sh = float(a[col]) / bl if bl > 0 else 0.0
            add(c, sec, sub, "electricity", "final electricity (Astar hourly shape; incl. cooling and appliances)", "Astar", {k: v * sh for k, v in tot.items()}, f"Astar base load x {col} / base_load_anchor_mwh")
        for sec, acc in (("Residential", "ResidentialFuel"), ("Commercial", "CommercialFuel")):
            for car in ("oil final energy", "coal final energy", "gas final energy"):
                v = val(c, acc, car)
                if any(x != 0 for x in v.values()):
                    add(c, sec, "", car, "final energy", acc, v, f"{acc} rows of the anchor table")
            acc_cc = f"{sec}Fuel biomass -> clean cooking (decision 23)"; v = val(c, acc_cc, "clean cooking useful")
            if any(x != 0 for x in v.values()):
                eta = par["cookstove_basic"].get(c, par["cookstove_basic_default"])
                add(c, sec, "cooking", "clean cooking useful", "useful energy", acc_cc, v, f"{sec} biomass fuel row x basic cookstove efficiency {eta}", source_twh=v["twh_integrated_2920x3h"] / eta, source_note="biomass final energy before conversion")
        for car in ("oil final energy", "coal final energy", "gas final energy", "biomass final energy"):   # gas: SG agriculture anchor is positive in v2 (not in the DMD D1 list)
            v = val(c, "AgricultureFinalEnergy", car)
            if any(x != 0 for x in v.values()):
                add(c, "AgricultureOthers", "", car, "final energy", "AgricultureFinalEnergy", v, "agriculture-and-others fuel rows")
        v = val(c, "AgricultureMachineryElectric", "agriculture machinery electric")
        if any(x != 0 for x in v.values()):
            add(c, "AgricultureOthers", "agricultural machinery", "agriculture machinery electric", "final electricity", "AgricultureMachineryElectric", v,
                f"agriculture oil x electric share {par['agriculture_electric_share']} / efficiency gain {par['agriculture_efficiency_gain']:.4f}", source_twh=v["twh_integrated_2920x3h"] * par["agriculture_efficiency_gain"], source_note="oil equivalent of the electrified half")
        for acc, car in (("AgricultureBiomassOverflowUsefulHeat", "industry heat"),):
            v = val(c, acc, car)
            if any(x != 0 for x in v.values()):
                add(c, "AgricultureOthers", "biomass overflow -> useful heat", car, "useful heat", acc, v, "agriculture biomass above the solid-biomass potential x 0.90")
        land = d[(d.sector == "Transport") & d.account.isin(LAND) & (d.carrier != "electricity")]
        v = val(c, "LandTransportEV", "land transport EV")
        add(c, "Transport", "road (land transport, EV)", "land transport EV", "electricity at the EV battery (grid draw = / 0.9)", "LandTransportEV", v,
            f"non-electric land-transport fuel rows x EV share {par['ev_share']} x oil_to_electricity {par['oil_to_electricity']:.6f}", source_twh=float(land.v.sum()) / 1e6, source_note="oil-equivalent land-transport fuel anchor")
        for car in ("oil final energy", "biomass final energy"):
            v = val(c, "RailNonElectric", car)
            if any(x != 0 for x in v.values()):
                add(c, "Transport", "rail (non-electric)", car, "final energy", "RailNonElectric", v, "rail non-electric fuel rows")
        v = val(c, "DomesticAviationFuel", "oil final energy"); add(c, "Transport", "domestic aviation", "oil final energy", "final energy", "DomesticAviationFuel", v, "domestic aviation fuel rows")
        v = val(c, "DomesticShippingFuel", "shipping methanol"); ds = float(d[d.account == "DomesticShippingFuel"].v.sum()) / 1e6
        add(c, "Transport", "domestic shipping", "shipping methanol", "final energy (methanol, oil-equivalent x 0.4/0.46)", "DomesticShippingFuel", v, "domestic navigation oil rows x 0.40 / 0.46", source_twh=ds, source_note="oil-equivalent")
        rec = pd.DataFrame(industry_split(c, tab, mp, uhs.loc[c]))
        net_ind = {}
        for car_load, acc in (("industry electricity", "IndustryElectricityRoutes"), ("industry heat", "IndustryLowTemperatureHeat"), ("industry heat medium A", "IndustryHeatMediumA"),
                              ("industry heat medium B", "IndustryHeatMediumB"), ("industry heat high", "IndustryHeatHigh"), ("industry hydrogen", "IndustryHydrogenDRI"), ("industry ammonia", "IndustryAmmonia"),
                              ("industry methanol", "IndustryMethanol"), ("gas final energy", "IndustryFinalEnergy"), ("biomass final energy", "IndustryFinalEnergy"), ("oil final energy", "IndustryFinalEnergy"), ("coal final energy", "IndustryFinalEnergy")):
            net_ind[car_load] = (acc, val(c, acc, car_load))
        band_load = {"heat_medium_a": "industry heat medium A", "heat_medium_b": "industry heat medium B", "heat_high": "industry heat high"}
        if len(rec):
            rec["load_carrier"] = rec.table_carrier.map(lambda x: band_load.get(x, TABLE_TO_LOAD.get(x))); sums = rec.groupby("load_carrier").mwh.sum()
        else:
            sums = pd.Series(dtype=float)
        h2 = float(sums.get("industry hydrogen", 0.0)); ind_check = {}
        for car_load, (acc, v) in net_ind.items():
            net = v["twh_integrated_2920x3h"] * 1e6; r_ = float(sums.get(car_load, 0.0))
            if car_load == "industry hydrogen":
                r_ = max(r_, 0.0)
            ind_check[car_load] = dict(network_mwh=net, reconstructed_mwh=r_, diff_mwh=net - r_)
        checks.setdefault("industry_reconstruction", {})[c] = ind_check
        for (sub, car_load), grp in (rec.groupby(["subsector", "load_carrier"]) if len(rec) else []):
            mwh = float(grp.mwh.sum())
            if car_load == "industry hydrogen" and h2 < 0:
                mwh = mwh * 0.0 if sub == "chlorine" else mwh
            net_v = net_ind[car_load][1]; share = mwh / (net_v["twh_integrated_2920x3h"] * 1e6) if net_v["twh_integrated_2920x3h"] > 0 else 0.0
            form = {"industry heat": "useful heat < 150 C", "industry heat medium A": "useful heat 150-200 C", "industry heat medium B": "useful heat 200-400 C", "industry heat high": "useful heat > 400 C",
                    "industry ammonia": "product (NH3, regional bus)", "industry methanol": "product (MeOH, regional bus)", "industry hydrogen": "H2 (DRI steel / chemicals)", "industry electricity": "final electricity (process routes)"}.get(car_load, "final energy")
            meth = "; ".join(sorted(set(grp.method)))[:300]; src_twh = None; src_note = ""
            if sub.startswith("other bucket") and car_load.startswith("industry heat"):
                src_twh = mwh / 0.9 / 1e6; src_note = "other-bucket fuel before x 0.90"
            add(c, "Industry", sub, car_load, form, net_ind[car_load][0], {k: x * share for k, x in net_v.items()}, f"network load x share of the reconstructed {sub} part: {meth}", source_twh=src_twh, source_note=src_note)
        v = val(c, "IndustryBiomassOverflowUsefulHeat", "industry heat medium A"); v2 = val(c, "IndustryBiomassOverflowUsefulHeat", "industry heat medium B"); v3 = val(c, "IndustryBiomassOverflowUsefulHeat", "industry heat high")
        for car, vv in (("industry heat medium A", v), ("industry heat medium B", v2), ("industry heat high", v3)):
            if any(x != 0 for x in vv.values()):
                add(c, "Industry", "biomass overflow -> useful heat", car, "useful heat", "IndustryBiomassOverflowUsefulHeat", vv, "industry biomass above the solid-biomass potential x 0.90 in its source band")
        for car in ("oil feedstock", "gas feedstock", "coal feedstock"):
            k = car.split()[0]; v = val(c, f"NonEnergy:{k}", car); ne = float(d[(d.sector == "NonEnergyUse") & (d.carrier == k)].v.sum()) / 1e6
            if any(x != 0 for x in v.values()) or ne:
                add(c, "NonEnergyUse", "feedstock", car, "feedstock (non-energy)", f"NonEnergy:{k}", v, "NEU rows x industry multiplier" + (f" x HVC primary fraction {par['hvc_primary_fraction']} ({'HVC feedstock accounts only' if par.get('hvc_primary_scope') not in (None, 'none') and tag == 'v2' else 'every NEU oil row'})" if k == "oil" else ""),
                    source_twh=ne, source_note="NEU rows before the HVC primary-fraction scaling" if k == "oil" else "")
        bc = meta_bunkers["by_country"].get(c, {})
        for key, sub, car in (("aviation_oil_mwh", "international aviation (origin, memo)", "oil final energy"), ("shipping_shipping_methanol_mwh", "international shipping (origin, memo)", "shipping methanol")):
            mv = float(bc.get(key, 0.0)) / 1e6
            add(c, "InternationalBunkers", sub, car, "memo: origin of the ASEAN pool load", "memo", {f"twh_{s}_{r}": mv for (s, r) in NETS}, "meta research_bunkers.by_country")
    for acc, car, sub in (("InternationalAviationBunker", "oil final energy", "international aviation (ASEAN pool)"), ("InternationalShippingBunker", "shipping methanol", "international shipping (ASEAN pool)")):
        add("ASEAN", "InternationalBunkers", sub, car, "final energy; non-fossil only", acc, val("ASEAN", acc, car), "regional pool load")
    out = pd.DataFrame(rows); tcols = [f"twh_{s}_{r}" for (s, r) in NETS]
    out["max_rel_diff_4_networks"] = (out[tcols].max(axis=1) - out[tcols].min(axis=1)) / out[tcols].abs().max(axis=1).clip(lower=1e-12)
    out.insert(4, "twh", out["twh_integrated_2920x3h"])
    out.to_csv(OUT / f"DEMAND_BY_COUNTRY_SECTOR_CARRIER_{tag}.csv", index=False, float_format="%.9f")   # 1e-9 TWh: the bridge closure (<= 1e-3 TWh) must not be eaten by row rounding
    real = out[out.network_account != "memo"]
    checks["totals_twh"] = dict(all_loads=float(real.twh.sum()), eleven_countries=float(real[real.country != "ASEAN"].twh.sum()), asean_pool=float(real[real.country == "ASEAN"].twh.sum()),
                                network_all_loads=float(base.mwh.sum() / 1e6), network_eleven=float(base[base.country.isin(C11)].mwh.sum() / 1e6),
                                by_sector=real.groupby("sector").twh.sum().round(3).to_dict(), by_country=real.groupby("country").twh.sum().round(3).to_dict())
    ic = checks["industry_reconstruction"]; checks["industry_reconstruction_max_abs_diff_mwh"] = max(abs(v["diff_mwh"]) for cc in ic.values() for v in cc.values())
    checks["coverage_diff_twh"] = checks["totals_twh"]["all_loads"] - checks["totals_twh"]["network_all_loads"]
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / f"DFX_D1_CHECKS_{tag}.json").write_text(json.dumps(checks, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: checks[k] for k in ("consistency", "totals_twh", "industry_reconstruction_max_abs_diff_mwh", "coverage_diff_twh")}, indent=1, default=float))


def diff():
    key = ["country", "sector", "subsector", "carrier", "network_account"]
    a = pd.read_csv(OUT / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v1.csv", keep_default_na=False); b = pd.read_csv(OUT / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv", keep_default_na=False)
    a = a[a.network_account != "memo"].groupby(key, as_index=False).twh.sum().rename(columns={"twh": "twh_v1"})
    b = b[b.network_account != "memo"].groupby(key, as_index=False).twh.sum().rename(columns={"twh": "twh_v2"})
    m = a.merge(b, on=key, how="outer").fillna(0.0); m["diff_twh"] = m.twh_v2 - m.twh_v1
    m = m.sort_values(key); m.to_csv(OUT / "DEMAND_DIFF_V2_V1.csv", index=False, float_format="%.9f")
    s = {}
    for k in ("sector", "country", "carrier"):
        g = m.groupby(k)[["twh_v1", "twh_v2", "diff_twh"]].sum(); s[k] = g.round(3).to_dict("index")
    s["total"] = dict(twh_v1=float(m.twh_v1.sum()), twh_v2=float(m.twh_v2.sum()), diff_twh=float(m.diff_twh.sum()))
    (OUT / "evidence" / "DFX_DEMAND_DIFF_SUMMARY.json").write_text(json.dumps(s, indent=1, default=float), encoding="utf-8")
    pd.set_option("display.width", 220)
    print(pd.DataFrame(s["sector"]).T.round(3).to_string()); print(pd.DataFrame(s["country"]).T.round(3).to_string()); print(s["total"])


def bridge():
    """AEO8 ATS 2050 TFEC -> v2 loads (closure <= 1e-3 TWh). Adapted from DMD D3 for the DFX rules (RAS split, NEU outside, ammonia rule, HVC scope)."""
    DEM = tables_dir("v2"); SRC = WT / "research_inputs/registry_v5/sources"
    d1 = pd.read_csv(OUT / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv", keep_default_na=False); real = d1[d1.network_account != "memo"]; r11 = real[real.country.isin(C11)]
    an = pd.read_csv(DEM / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    dt = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False); dt["v"] = pd.to_numeric(dt.value_2050_mwh, errors="coerce").fillna(0.0) / 1e6; dt["b"] = pd.to_numeric(dt.base_2019_mwh, errors="coerce").fillna(0.0) / 1e6
    ind = pd.read_csv(DEM / "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"); ob = pd.read_csv(DEM / "INDUSTRY_2050_OTHER_BUCKET.csv").query("mode == 'aeo8_ats_anchor'").set_index("country")
    uh = pd.read_csv(DEM / "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
    par = json.loads((OUT / "evidence/DFX_D1_CHECKS_v2.json").read_text())["ledger_parameters"]
    tot = pd.read_csv(SRC / "AEO8_2050_ASEAN_TOTALS.csv", dtype=str)
    ev = json.loads((DEM / "DEMAND_ANCHOR_M08B_EVIDENCE.json").read_text()); ras = ev["ras"]
    br = []

    def B(item, twh, basis, group, tier="VERIFIED"):
        br.append(dict(step=len(br), item=item, twh=float(twh), group=group, basis=basis, grade=tier))

    def t(table, item, scen, year="2050"):
        x = tot[(tot.table.str.startswith(table)) & (tot["item"] == item) & (tot.scenario == scen) & (tot.year == year)]
        return num(x.value_as_printed.iloc[0]) if len(x) else None
    s0 = t("C.3", "Total", "ATS") * TWH_PER_MTOE; a10 = float(an.drop(index="TL").ats_tfec_2050_mwh.sum()) / 1e6
    B("AEO8 ATS 2050 TFEC as printed (C.3 total 746.2 Mtoe x 11.63; 10 AMS; excludes non-energy use and international transport)", s0, "AEO8 C.3 PDF p.184", "start", "A")
    B(f"rounding: sum of C.8 per capita x D.1 population (10 AMS) - printed total = (k - 1) x C.3 total, k = {ras['k_scale']:.9f} (DFX F1 column scaling)", a10 - s0, "DEMAND_ANCHOR_AEO8_ATS.csv; RAS k", "baseline")
    B("TL added (mean KH/LA/MM per capita x UN WPP 2024)", float(an.at["TL", "ats_tfec_2050_mwh"]) / 1e6, "demand_anchor_tl_rule (C)", "baseline", "C")
    B("NEU outside the TFEC envelope (DFX F1.2): the 11-country energy-use anchors = sum of the RAS sector anchors (no NEU carved out)", 0.0, "demand_neu_outside_tfec", "definition", "A")
    sec_anchor = {s: float(an[f"ras_sector_anchor_{s}_mwh"].sum()) / 1e6 for s in ("Industry", "Transport", "Residential", "Commercial", "AgricultureOthers")}
    land = dt[(dt.sector == "Transport") & dt.account.isin(LAND) & (dt.carrier != "electricity")]; e_land = float(land.v.sum()); ev_ = float(r11[r11.subsector == "road (land transport, EV)"].twh.sum())
    B(f"road: RAS land-transport fuel anchor {e_land:.1f} TWh oil-eq -> EV at the battery x {par['oil_to_electricity']:.4f}", ev_ - e_land, "registry share_transport_*_efficiency (C)", "transport electrification efficiency", "C")
    dship = float(dt[dt.account == "DomesticShippingFuel"].v.sum()); ship_m = float(r11[r11.subsector == "domestic shipping"].twh.sum())
    B(f"domestic shipping {dship:.1f} TWh oil-eq -> methanol x 0.40/0.46", ship_m - dship, "shipping_methanol_conversion (B)", "transport fuel switch", "C")
    neg = sum(-float(an.at[c, f"{k}_fuel_anchor_raw_mwh"]) / 1e6 for c in C11 for k in ("residential", "commercial", "agriculture") if an.at[c, f"{k}_fuel_zeroed"] == "negative")
    pos0 = sum(float(an.at[c, f"{k}_fuel_anchor_raw_mwh"]) / 1e6 for c in C11 for k in ("residential", "commercial", "agriculture") if an.at[c, f"{k}_fuel_zeroed"] == "no_2019_fuel_rows")
    B("negative residential / commercial / agriculture fuel anchors set to 0 (8 cells): sector = electricity anchor, above ATS", neg, "demand_sector_fuel_anchor_zeroed (C)", "anchoring artefact", "C")
    B("TL commercial positive fuel anchor without 2019 carrier structure set to 0", -pos0, "demand_sector_fuel_anchor_zeroed (C)", "anchoring artefact", "C")
    bio_bld = float(dt[dt.sector.isin(["Residential", "Commercial"]) & (dt.carrier == "biomass")].v.sum()); cc = float(r11[r11.carrier == "clean cooking useful"].twh.sum())
    B(f"clean cooking: residential / commercial biomass {bio_bld:.1f} TWh -> useful cooking energy x 0.08 (TH 0.16)", cc - bio_bld, "cookstove_efficiency_* (registered, DFX F4)", "useful-energy accounting (buildings)", "C")
    ag_oil = float(dt[(dt.sector == "AgricultureOthers") & (dt.carrier.isin(["oil", "unclassified_fuel"]))].v.sum())
    ag_model = float(r11[(r11.sector == "AgricultureOthers") & r11.carrier.isin(["agriculture machinery electric", "oil final energy"])].twh.sum())
    B(f"agriculture: oil {ag_oil:.1f} TWh, half electrified at efficiency 0.3/0.7", ag_model - ag_oil, "share_agriculture_machinery_* (C)", "agriculture machinery electrification", "C")
    ag_bio = float(dt[(dt.sector == "AgricultureOthers") & (dt.carrier == "biomass")].v.sum()); ag_bio_model = float(r11[(r11.sector == "AgricultureOthers") & r11.carrier.isin(["biomass final energy", "industry heat"])].twh.sum())
    B(f"agriculture biomass {ag_bio:.1f} TWh: overflow above the solid-biomass potential -> useful heat x 0.90", ag_bio_model - ag_bio, "biomass_overflow_rule (C)", "agriculture biomass overflow", "C")
    mult = an.industry_multiplier; ind19 = an.tfec_2019_Industry_mwh / 1e6; e_ind_anchor = float((ind19 * mult).sum()); m_c = mult.to_dict()
    st = ind[ind.subsector == "iron and steel"]; ce = ind[ind.subsector == "cement"]
    steel_19m = float(sum(r.mwh_2019 * m_c[r.country] for r in st.itertuples())) / 1e6; steel_50 = float(st.mwh_2050.sum()) / 1e6
    cem_19m = float(sum(r.mwh_2019 * m_c[r.country] for r in ce.itertuples())) / 1e6; cem_50 = float(ce.mwh_2050.sum()) / 1e6
    det = ind[(ind.carrier == "all (see mapping shares)") & ~ind.subsector.isin(["other", "construction", "mining and quarrying"])]
    det_19m = float(sum(r.mwh_2019 * m_c[r.country] for r in det.itertuples())) / 1e6; det_50 = float(det.mwh_2050.sum()) / 1e6
    nh3_dropped = float(uh.pe_ammonia_eu27_share_dropped_mwh.sum()) / 1e6; nh3_rule = float(ind[ind.subsector == "ammonia (production rule)"].mwh_2050.sum()) / 1e6
    ob19 = float(sum(ob.at[c, "other_2019_mwh"] * m_c[c] for c in ob.index if c in m_c)) / 1e6
    ob_fuel = float(uh.other_heat_fuel_2050_mwh.sum()) / 1e6; ob_heat = float((uh.other_heat_low_mwh + uh.other_heat_medium_a_mwh + uh.other_heat_medium_b_mwh + uh.other_heat_high_mwh).sum()) / 1e6
    B(f"steel: physical output rule instead of 2019 energy x multiplier ({steel_19m:.1f} -> {steel_50:.1f})", steel_50 - steel_19m, "industry_output_rule_2050 (C)", "industry: physical output rule", "C")
    B(f"cement: physical output rule instead of 2019 energy x multiplier ({cem_19m:.1f} -> {cem_50:.1f})", cem_50 - cem_19m, "industry_output_rule_2050 (C)", "industry: physical output rule", "C")
    B(f"route sub-sectors (chemicals excl. the ammonia share, food, paper, ...): 2050/2019 specific-energy efficiency factors ({det_19m:.1f} -> {det_50 + nh3_dropped:.1f})", det_50 + nh3_dropped - det_19m,
      "industry_efficiency_factor_* (B), industry_subsector_mapping (C)", "industry: PyPSA-Eur efficiency factors", "B")
    B(f"ammonia (DFX F2): EU27 chemicals-weight ammonia share dropped ({nh3_dropped:.1f}) and replaced by USGS 2019 production x growth x 5.166 MWh/t ({nh3_rule:.1f})", nh3_rule - nh3_dropped,
      "industry_ammonia_output_rule (C)", "industry: ammonia production rule", "C")
    B(f"other bucket: heat-use fuels {ob_fuel:.1f} TWh -> useful heat x 0.90 (mechanical oil and electricity kept)", ob_heat - ob_fuel, "industry_useful_heat_efficiency (C)", "industry: useful-heat accounting", "C")
    ind_model = float(r11[(r11.sector == "Industry") & (r11.subsector != "biomass overflow -> useful heat")].twh.sum())
    ov_ind = float(r11[(r11.sector == "Industry") & (r11.subsector == "biomass overflow -> useful heat")].twh.sum())
    bio_ind_before = float(uh.pe_biomass_before_overflow_mwh.sum()) / 1e6; bio_ind_after = float(r11[(r11.sector == "Industry") & (r11.carrier == "biomass final energy")].twh.sum())
    resid = ind_model - (e_ind_anchor + (steel_50 - steel_19m) + (cem_50 - cem_19m) + (det_50 + nh3_dropped - det_19m) + (nh3_rule - nh3_dropped) + (ob_heat - ob_fuel)) + (bio_ind_before - bio_ind_after)
    B(f"industry biomass overflow: fixed biomass {bio_ind_before:.1f} -> {bio_ind_after:.1f} TWh, overflow -> useful heat x 0.90 ({ov_ind:.1f})", ov_ind - (bio_ind_before - bio_ind_after), "biomass_overflow_rule (C)", "industry biomass overflow", "C")
    B(f"industry residual (2019 sub-sector split vs UNSD industry total; H2 by-product floor)", resid, "computed residual", "industry: residual")
    sub_energy = sum(b["twh"] for b in br)
    neu = float(r11[r11.sector == "NonEnergyUse"].twh.sum()); neu_tab = float(dt[dt.sector == "NonEnergyUse"].v.sum())
    neu_gas_ded = float(an.ammonia_feedstock_gas_deduction_mwh.sum()) / 1e6
    B(f"subtotal: model energy-use loads excl. NEU ({sub_energy:.1f}); + NEU added as non-energy demand (2019 NEU x multiplier {neu_tab + neu_gas_ded:.1f}, minus ammonia feedstock gas {neu_gas_ded:.1f}, DFX F2.4)", neu_tab,
      "NEU rows of the anchor table", "non-energy use: added")
    neu_oil = float(dt[(dt.sector == "NonEnergyUse") & (dt.carrier == "oil")].v.sum()); neu_oil_hvc = float(dt[(dt.sector == "NonEnergyUse") & (dt.carrier == "oil") & dt.account.isin(HVC)].v.sum())
    B(f"NEU oil: HVC feedstock accounts {neu_oil_hvc:.1f} TWh x HVC primary fraction 0.4 (DFX F3: naphtha / ethane / LPG / NGL only; non-HVC products {neu_oil - neu_oil_hvc:.1f} TWh x 1.0)", -(1 - par["hvc_primary_fraction"]) * neu_oil_hvc,
      "share_HVC_primary_fraction_2050 (C), hvc_primary_fraction_scope", "non-energy use: recycling assumption", "C")
    model11 = float(r11.twh.sum()); run = sum(b["twh"] for b in br)
    B("= model 11-country loads (network v2, 2920x3h = 365x24h)", 0.0, "closure", "end")
    closure = dict(start_twh=s0, end_computed_twh=run, model_loads_twh=model11, residual_twh=run - model11, closed=abs(run - model11) <= 1e-3)
    sector_check = {s: dict(anchor=sec_anchor[s], model=float(r11[r11.sector == s].twh.sum())) for s in sec_anchor}
    res = dict(bridge=br, closure=closure, energy_use_subtotal_excl_neu_twh=sub_energy, sector_anchor_twh=sec_anchor, sector_check=sector_check,
               inputs=dict(e_land=e_land, ev=ev_, dship=dship, ship_methanol=ship_m, bio_buildings=bio_bld, clean_cooking=cc, ag_oil=ag_oil, neu_oil=neu_oil, neu_oil_hvc=neu_oil_hvc, industry_energy_anchor=e_ind_anchor,
                           steel=(steel_19m, steel_50), cement=(cem_19m, cem_50), fallback=(det_19m, det_50), ammonia=(nh3_dropped, nh3_rule), other_bucket=(ob_fuel, ob_heat), ind_model=ind_model, neu=neu, neu_gas_deducted=neu_gas_ded))
    (OUT / "evidence/DFX_BRIDGE_V2.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    pd.DataFrame(br).to_csv(OUT / "DFX_BRIDGE_V2.csv", index=False, float_format="%.6f")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 150)
    print(pd.DataFrame(br)[["item", "twh", "grade"]].round(2).to_string()); print(json.dumps(closure, indent=1)); print(json.dumps(sector_check, indent=1))


def percap():
    DEM = tables_dir("v2"); SRC = WT / "research_inputs/registry_v5/sources"
    d1 = pd.read_csv(OUT / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv", keep_default_na=False); r11 = d1[(d1.network_account != "memo") & d1.country.isin(C11)]
    d0 = pd.read_csv(OUT / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v1.csv", keep_default_na=False); r10 = d0[(d0.network_account != "memo") & d0.country.isin(C11)]
    an = pd.read_csv(DEM / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country"); byc = pd.read_csv(SRC / "AEO8_2050_BY_COUNTRY.csv", dtype=str)
    names = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao PDR": "LA", "Malaysia": "MY", "Myanmar": "MM", "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Vietnam": "VN"}
    hist = {names[r.country]: num(r.value_as_printed) for r in byc.itertuples() if r.country in names and r.indicator.startswith("Electricity consumption per capita") and r.year == "2022"}
    rows = []
    for c in C11:
        a = an.loc[c]; p = float(a.population_2050_million); ats_el = float(a.ats_elec_2050_mwh) / 1e6; ats_tf = float(a.ats_tfec_2050_mwh) / 1e6
        fx = lambda r: float(r[r.carrier.isin(["electricity", "industry electricity", "agriculture machinery electric", "land transport EV"])].twh.sum())
        rc, r0 = r11[r11.country == c], r10[r10.country == c]
        rows.append(dict(country=c, population_2050_million=p, aeo8_2022_kwh_per_cap=hist.get(c), ats_2050_kwh_per_cap=ats_el * 1e3 / p, model_fixed_v1_kwh_per_cap=fx(r0) * 1e3 / p, model_fixed_v2_kwh_per_cap=fx(rc) * 1e3 / p,
                         ats_electricity_twh=ats_el, model_fixed_v1_twh=fx(r0), model_fixed_v2_twh=fx(rc), ratio_fixed_v1_to_ats=fx(r0) / ats_el, ratio_fixed_v2_to_ats=fx(rc) / ats_el,
                         base_load_twh=float(rc[rc.carrier == "electricity"].twh.sum()), industry_electricity_twh=float(rc[rc.carrier == "industry electricity"].twh.sum()), ev_battery_twh=float(rc[rc.carrier == "land transport EV"].twh.sum()),
                         loads_excl_neu_v2_twh=float(rc[rc.sector != "NonEnergyUse"].twh.sum()), ats_tfec_twh=ats_tf, ratio_loads_excl_neu_to_ats_tfec=float(rc[rc.sector != "NonEnergyUse"].twh.sum()) / ats_tf))
    el = pd.DataFrame(rows); el.to_csv(OUT / "DFX_ELECTRICITY_PER_CAPITA_V2.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 250); print(el[["country", "aeo8_2022_kwh_per_cap", "ats_2050_kwh_per_cap", "model_fixed_v1_kwh_per_cap", "model_fixed_v2_kwh_per_cap", "ratio_fixed_v1_to_ats", "ratio_fixed_v2_to_ats", "ratio_loads_excl_neu_to_ats_tfec"]].round(3).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["tables", "d1", "diff", "bridge", "percap"]); ap.add_argument("--tag", default="v2")
    a = ap.parse_args()
    {"tables": export_v1_tables, "d1": lambda: d1(a.tag), "diff": diff, "bridge": bridge, "percap": percap}[a.cmd]()
