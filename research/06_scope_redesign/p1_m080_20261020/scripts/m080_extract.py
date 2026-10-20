"""M08-0 (item 130) read-only extraction: what the screening runs actually used, for the registry backfill.

Inputs (read only, nothing is built, solved or written outside the output directory):
  * the S4O cloud-package unsolved networks (365 x 24 h, integrated and disconnected; build commit 126110ff), the same
    networks the S4O / S4N screening runs and the S4P extraction used;
  * their build receipt and active cost table, the renewable profile files named in the network meta, the author paper
    network the electric base inherits p_nom_max / p_max_pu / base-load shapes from, and the author-chain data files
    (Copernicus LC100, natura, GEBCO, EEZ, GEGIS demand), the GEM LNG workbook and the shipping-density zip.
Outputs: <out>/evidence/M080_EXTRACT.json, M080_VRE_CAPS_BY_COUNTRY.csv, M080_LNG_CAPS_BY_NODE.csv,
         M080_EXISTING_FLEET_COST_BASIS.csv

    /home/jin/miniforge3/envs/pypsa-earth/bin/python -I m080_extract.py --out /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m080_20261020
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work")
PKG = WORK / "p1_step4o_20261019/cloud_package_dist"
NET = {"integrated": PKG / "networks/integrated_365_24h_unsolved.nc", "disconnected": PKG / "networks/disconnected_365_24h_unsolved.nc"}
RECEIPT = PKG / "networks/integrated_BUILD_RECEIPT.json"
COSTS = PKG / "networks/integrated_costs_active_research.csv"
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")   # main checkout (git-ignored inputs live here)
WT = Path("/home/jin/wt_m080_20261020")                                          # M08-0 worktree (git objects)
BUILD_COMMIT = "126110ff"
RENEW = MAIN / "research_inputs/renewable_v5"
AUTHOR_NET = Path("/mnt/d/ResearchWorkspaces/ASEAN/research/00_source_provenance/cache/results-asean-paper-v1/baseline-aims-3H/"
                  "elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export.nc")
PA = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean")                   # local author chain checkout (data bundle copies)
DATA_FILES = {
    "copernicus_lc100": PA / "data/copernicus/PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif",
    "natura": PA / "data/natura/natura.tiff",
    "natura_metadata": PA / "data/natura/metadata.json",
    "gebco": PA / "data/gebco/GEBCO_2025_sub_ice.nc",
    "eez": PA / "data/eez/eez_v11.gpkg",
    "gegis_asia": PA / "data/ssp2-2.6/2030/era5_2013/Asia.nc",
    "gem_lng_xlsx": WORK / "p2_data_intake/raw/GEM-GGIT-LNG-Teminals-2025-09.xlsx",
    "gem_lng_s4r_download_zip": WORK / "p1_s4r_downloads_20261020/F2_lng/gem-download (1).zip",
    "shipdensity_zip": WORK / "p2_data_intake/raw12/shipdensity_global.zip",
    "lng_terminal_table": MAIN / "research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv",
    "electric_base": MAIN / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc",
    "v0_13_2_costs_2050": Path("/mnt/d/ResearchWorkspaces/ASEAN/research/00_source_provenance/official/technology-data/outputs/costs_2050.csv"),
    "author_costs_2030": PA / "resources/baseline-aims-3H-tutorial/costs_2030.csv",
}
COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
VRE = ["solar", "solar rooftop", "onwind", "offwind-ac", "offwind-dc"]
MWH_PER_MTPA = 1e6 * 48.0 / 3.6


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def meta_of(path: Path) -> dict:
    ds = xr.open_dataset(path, engine="netcdf4")
    m = json.loads(ds.attrs.get("meta", "{}"))
    ds.close()
    return m


def git_show(rev_path: str) -> str:
    return subprocess.check_output(["git", "-C", str(WT), "show", rev_path], text=True)


def vre_caps(nets):
    rows = []
    for label, n in nets.items():
        g = n.generators.copy()
        g["country"] = n.buses.country.reindex(g.bus).values   # generator country attribute is empty for the inherited VRE candidates
        for car in VRE:
            sel = g[g.carrier == car]
            for c in COUNTRIES:
                s = sel[sel.country == c]
                rows.append(dict(network=label, carrier=car, country=c, generators=int(len(s)), nodes=int(s.bus.nunique()),
                                 p_nom_max_mw=float(s.p_nom_max.replace(np.inf, np.nan).sum()) if len(s) else 0.0,
                                 inf_generators=int(np.isinf(s.p_nom_max).sum()), p_nom_mw=float(s.p_nom.sum()),
                                 extendable=int(s.p_nom_extendable.sum())))
    return pd.DataFrame(rows)


def lng_caps(nets, meta):
    rows = []
    led = meta["research_gas_network"]["lng"]
    for label, n in nets.items():
        g = n.generators[n.generators.carrier == "LNG import"]
        for name, r in g.iterrows():
            node = name.replace(" LNG import", "")
            t = led["terminals"].get(node, {})
            rows.append(dict(network=label, generator=name, node=node, country=r.country, p_nom_mw=float(r.p_nom), p_nom_max_mw=float(r.p_nom_max),
                             cap_twh_per_a=float(r.p_nom_max) * 8760 / 1e6, capital_cost_eur_per_mw_a=float(r.capital_cost),
                             existing_mw=t.get("existing_mw"), proposed_mw=t.get("proposed_mw"),
                             rule=("2.5 x existing" if (t.get("existing_mw") or 0) > 0 else "proposed capacity (no existing)"),
                             terminals=t.get("terminals", "")))
    return pd.DataFrame(rows), {k: v for k, v in led.items() if k != "terminals"}, {k: v for k, v in led["terminals"].items() if v.get("p_nom_max_mw", 0) == 0}


def existing_fleet_basis(n, costs15: pd.DataFrame, v13: pd.DataFrame, author30: pd.DataFrame):
    """Existing conventional components (carrier '<tech> existing', asset_role existing_survivor) vs the new-build candidates of the
    same technology: efficiency in the screening network against the active layer (v0.15.0), v0.13.2 2050 and the author costs_2030."""
    out = []
    techs = {"CCGT": "CCGT", "OCGT": "OCGT", "coal": "coal", "oil": "oil", "lignite": "lignite", "nuclear": "nuclear", "ror": "ror"}

    def val(tab, t, p):
        try:
            return float(tab.loc[(t, p), "value"])
        except Exception:
            return np.nan

    def effs(s):
        return ";".join(f"{v:.6g}" for v in sorted(set(np.round(s.efficiency.astype(float), 6)))) if len(s) else ""
    for comp, df in (("Generator", n.generators), ("Link", n.links)):
        role = df["research_role"].fillna("") if "research_role" in df else pd.Series("", index=df.index)
        for car, t in techs.items():
            ex = df[df.carrier == f"{car} existing"]
            nb = df[(df.carrier == car) & df.p_nom_extendable.astype(bool)]
            if not len(ex) and not len(nb):
                continue
            for origin, sub in (("electric_base (author chain)", ex[role.reindex(ex.index) != "EXISTING_FLEET_S4A"]), ("GEM additions S4A-2", ex[role.reindex(ex.index) == "EXISTING_FLEET_S4A"])):
                if not len(sub):
                    continue
                out.append(dict(component=comp, technology=t, existing_origin=origin, existing_n=int(len(sub)), existing_p_nom_mw=float(sub.p_nom.sum()),
                                existing_eff_values=effs(sub), new_build_n=int(len(nb)), new_build_eff_values=effs(nb),
                                v0_15_0_eff_2050=float(costs15.at[t, "efficiency"]) if t in costs15.index else np.nan,
                                v0_13_2_eff_2050=val(v13, t, "efficiency"), author_costs_2030_eff=val(author30, t, "efficiency")))
    return pd.DataFrame(out)


def electric_base_cost_basis():
    """Price basis of the electric-base cost layer (assembly V1): rows by prior transformation (technology-data v0.13.2 rebased / AEO8 append)."""
    p = MAIN / "results_project/assembly_v1/final_assets/model_cost_layer.json"
    d = json.loads(p.read_text())
    df = pd.DataFrame(d["rows"])
    return dict(file=str(p), sha256=sha256(p), rows=int(len(df)), by_prior_transformation=df.PriorTransformation.value_counts().to_dict(),
                source_inputs=sorted(d.get("source_inputs", {}).keys()))


def profile_check():
    res = {}
    for c in ("c1", "c3"):
        cm = xr.open_dataset(RENEW / f"profiles_calibrated_modern_{c}_3h.nc")
        pe = xr.open_dataset(RENEW / f"profiles_pypsa_eur_{c}_3h.nc")
        fk = xr.open_dataset(RENEW / f"profiles_fork_{c}_3h.nc")
        for v in ("offwind_ac", "offwind_dc", "solar", "onwind"):
            a = cm[v].values
            r = {}
            for name, other in (("pypsa_eur", pe), ("fork", fk)):
                b = other[v].values
                r[name] = dict(identical=bool(a.shape == b.shape and np.array_equal(np.nan_to_num(a, nan=-9), np.nan_to_num(b, nan=-9))),
                               max_abs_diff=float(np.nanmax(np.abs(a - b))) if a.shape == b.shape else None, mean_other=float(np.nanmean(b)))
            res[f"{c}:{v}"] = dict(mean_calibrated_modern=float(np.nanmean(a)), **r)
        res[f"{c}:attrs"] = {k: str(v) for k, v in cm.attrs.items()}
    src = git_show(f"{BUILD_COMMIT}:scripts_project/s4a_profiles.py")
    variants = [ln.strip() for ln in src.splitlines() if re.search(r'"offwind-(ac|dc)": dict\(method="wind"', ln)]
    return res, variants


def astar_check():
    g = xr.open_dataset(DATA_FILES["gegis_asia"])["Electricity demand"]
    gattrs = {k: str(v) for k, v in g.attrs.items()}
    a = xr.open_dataset(AUTHOR_NET)
    loads_i = pd.Index(a["loads_i"].values.astype(str))
    bus = pd.Series(a["loads_bus"].values.astype(str), index=loads_i)
    carrier = pd.Series(a["loads_carrier"].values.astype(str), index=loads_i)
    buses_i = pd.Index(a["buses_i"].values.astype(str))
    cty = pd.Series(a["buses_country"].values.astype(str), index=buses_i)
    bcar = pd.Series(a["buses_carrier"].values.astype(str), index=buses_i)
    geo = buses_i[bcar.isin(["AC", "DC"])]
    base = loads_i[loads_i.isin(geo) & (carrier == "AC")]
    cols = pd.Index(a["loads_t_p_set_i"].values.astype(str))
    p = pd.DataFrame(a["loads_t_p_set"].values, columns=cols)[[c for c in base if c in cols]]
    nat = p.T.groupby(cty.reindex(bus.reindex(p.columns).values).values).sum().T
    sub = {"LA": "KH", "TL": "ID"}
    out = {}
    for c in COUNTRIES:
        src = sub.get(c, c)
        s = g.sel(region_code=src).values.astype(float)
        s3 = s.reshape(-1, 3).mean(axis=1)
        x = nat[c].values if c in nat.columns else np.zeros(len(s3))
        ratio = x / np.where(s3 > 0, s3, np.nan)
        out[c] = dict(gegis_region=src, base_loads=int((cty.reindex(bus.reindex(p.columns).values).values == c).sum()),
                      corr=float(np.corrcoef(x, s3)[0, 1]) if np.std(x) > 0 and np.std(s3) > 0 else None,
                      scale_cv=float(np.nanstd(ratio) / np.nanmean(ratio)) if np.isfinite(ratio).any() else None,
                      author_base_twh=float(x.sum() * 3 / 1e6), gegis_twh=float(s.sum() / 1e6),
                      gegis_own_twh=float(g.sel(region_code=c).values.sum() / 1e6))
    a.close()
    return gattrs, out


def gem_about():
    import openpyxl
    wb = openpyxl.load_workbook(DATA_FILES["gem_lng_xlsx"], read_only=True, data_only=True)
    lines = []
    for row in wb["About GGIT LNG"].iter_rows(max_row=40, values_only=True):
        for v in row:
            if isinstance(v, str) and re.search(r"release|creation date|Copyright", v, re.I):
                lines.append(v.strip()[:300])
    props = dict(created=str(wb.properties.created), modified=str(wb.properties.modified))
    wb.close()
    import zipfile
    z = zipfile.ZipFile(DATA_FILES["gem_lng_s4r_download_zip"])
    members = {i.filename: hashlib.sha256(z.read(i.filename)).hexdigest() for i in z.infolist() if "LNG-Te" in i.filename and i.filename.endswith(".xlsx")}
    return lines[:8], props, members


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--skip-big-hashes", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    ev = a.out / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    import pypsa
    hashes = {k: dict(path=str(p), sha256=sha256(p), bytes=p.stat().st_size) for k, p in NET.items()}
    for k, p in DATA_FILES.items():
        if a.skip_big_hashes and p.stat().st_size > 2e8:
            hashes[k] = dict(path=str(p), sha256="skipped", bytes=p.stat().st_size)
            continue
        hashes[k] = dict(path=str(p), sha256=sha256(p), bytes=p.stat().st_size)
    hashes["natura"]["md5"] = md5(DATA_FILES["natura"])
    hashes["author_net"] = dict(path=str(AUTHOR_NET), sha256=sha256(AUTHOR_NET), bytes=AUTHOR_NET.stat().st_size)
    for f in ("profiles_calibrated_modern_c1_3h.nc", "profiles_calibrated_modern_c3_3h.nc", "profiles_pypsa_eur_c3_3h.nc", "profiles_fork_c3_3h.nc", "S4A_PROFILE_CLASSES_c3.csv"):
        hashes[f] = dict(path=str(RENEW / f), sha256=sha256(RENEW / f), bytes=(RENEW / f).stat().st_size)
    for f in (RECEIPT, COSTS):
        hashes[f.name] = dict(path=str(f), sha256=sha256(f), bytes=f.stat().st_size)
    nat_meta = json.loads(DATA_FILES["natura_metadata"].read_text())
    nat_file = next((x for x in nat_meta["datasetVersion"]["files"] if x["dataFile"]["filename"].endswith(".tif")), None)

    nets = {k: pypsa.Network(str(p)) for k, p in NET.items()}
    meta = nets["integrated"].meta
    vre = vre_caps(nets)
    vre.to_csv(ev / "M080_VRE_CAPS_BY_COUNTRY.csv", index=False, float_format="%.6f")
    piv = vre[vre.network == "integrated"].pivot(index="country", columns="carrier", values="p_nom_max_mw")
    same_vre = bool(np.allclose(vre[vre.network == "integrated"].p_nom_max_mw.values, vre[vre.network == "disconnected"].p_nom_max_mw.values, rtol=0, atol=1e-9))
    lng, lng_rule, lng_zero = lng_caps(nets, meta)
    lng.to_csv(ev / "M080_LNG_CAPS_BY_NODE.csv", index=False, float_format="%.6f")
    li = lng[lng.network == "integrated"]
    lng_country = {c: dict(p_nom_mw=float(li[li.country == c].p_nom_mw.sum()), p_nom_max_mw=float(li[li.country == c].p_nom_max_mw.sum()),
                           cap_mwh_per_a=float(li[li.country == c].p_nom_max_mw.sum() * 8760), cap_twh_per_a=float(li[li.country == c].cap_twh_per_a.sum()),
                           nodes=int((li.country == c).sum()), rules=sorted(set(li[li.country == c].rule))) for c in COUNTRIES}
    ld = lng[lng.network == "disconnected"].set_index("generator").p_nom_max_mw
    same_lng = bool(np.allclose(li.set_index("generator").p_nom_max_mw.reindex(ld.index).values, ld.values))
    costs = pd.read_csv(COSTS, index_col=0)
    geo_cols = ["investment", "FOM", "VOM", "lifetime", "efficiency", "CO2 intensity", "fixed", "marginal_cost", "discount rate"]
    geo = {k: float(costs.at["geothermal", k]) for k in geo_cols}
    smr = {k: float(costs.at["nuclear SMR", k]) for k in geo_cols}
    nuc = {k: float(costs.at["nuclear", k]) for k in geo_cols}
    car = nets["integrated"].carriers
    geo_carrier_co2 = float(car.at["geothermal", "co2_emissions"]) if "geothermal" in car.index else None
    ng = nets["integrated"].generators
    geo_gens = ng[ng.carrier == "geothermal"]
    receipt = json.loads(RECEIPT.read_text())
    geo_existing = [dict(generator=x["generator"], p_nom_mw=x["p_nom_mw"], fom_eur_per_mw_a=x["fom_eur_per_mw_a"], vom_eur_per_mwh=x["vom_eur_per_mwh"],
                         co2=x.get("co2_simplification")) for x in receipt["geothermal"]["added"]]
    v13 = pd.read_csv(DATA_FILES["v0_13_2_costs_2050"]).set_index(["technology", "parameter"])
    a30 = pd.read_csv(DATA_FILES["author_costs_2030"]).set_index(["technology", "parameter"])
    fleet = existing_fleet_basis(nets["integrated"], costs, v13, a30)
    fleet.to_csv(ev / "M080_EXISTING_FLEET_COST_BASIS.csv", index=False, float_format="%.6g")
    eb_cost = electric_base_cost_basis()
    eb_cost["existing_annual_fixed_om_eur_in_network"] = float(nets["integrated"].meta.get("existing_annual_fixed_om_eur", np.nan))
    eb_cost["existing_cost_boundary"] = nets["integrated"].meta.get("existing_cost_boundary")
    prof, variants = profile_check()
    gattrs, astar = astar_check()
    gem_lines, gem_props, gem_zip = gem_about()
    amet = meta_of(AUTHOR_NET)
    rules = {t: {k: v for k, v in amet["renewable"][t].items() if k != "cutout"} for t in ("solar", "onwind", "offwind-ac", "offwind-dc")}
    bundles = {k: dict(urls=v.get("urls"), output=v.get("output")) for k, v in amet["databundles"].items() if k in ("bundle_data_earth", "bundle_natura_earth")}
    ren_meta = {k: v for k, v in meta["research_renewable"].items() if k not in ("added", "replaced")}
    rooftop_src = sorted({v.get("source") for v in meta["research_renewable"]["replaced"].values() if v.get("tech") == "solar rooftop"})
    cfg_ren = {k: meta["research_config"]["renewable"].get(k) for k in ("profile_variant", "resource_classes", "profile_dir", "clip_p_max_pu")} if "renewable" in meta.get("research_config", {}) else None
    out = dict(schema="m080-extract-v1", generated_utc=pd.Timestamp.utcnow().isoformat(timespec="seconds"), python=sys.version.split()[0], pypsa=pypsa.__version__,
               build_commit=BUILD_COMMIT, solver_runs=0, network_builds=0, files=hashes,
               natura_dataverse_file=dict(filename=nat_file["dataFile"]["filename"], md5=nat_file["dataFile"].get("md5"), filesize=nat_file["dataFile"].get("filesize"),
                                          version=f'{nat_meta["datasetVersion"]["versionNumber"]}.{nat_meta["datasetVersion"]["versionMinorNumber"]}',
                                          release=nat_meta["datasetVersion"].get("releaseTime"), license=nat_meta["datasetVersion"].get("license", {}).get("name"),
                                          doi=nat_meta.get("persistentUrl")) if nat_file else None,
               networks=dict(snapshots=int(len(nets["integrated"].snapshots)), weight_sum=float(nets["integrated"].snapshot_weightings.generators.sum()),
                             meta_role=meta.get("artifact_role"), research_config_sha256=meta.get("research_config_sha256"), electric_base_sha256=meta.get("electric_base_sha256"),
                             receipt_inputs={k: v.get("sha256") for k, v in receipt["inputs"].items() if isinstance(v, dict) and "sha256" in v}),
               vre_caps_mw=piv.to_dict(), vre_identical_integrated_disconnected=same_vre,
               vre_inf=int(vre.inf_generators.sum()), research_renewable_meta=ren_meta, research_config_renewable=cfg_ren, rooftop_profile_source=rooftop_src,
               author_renewable_rules=rules, author_natura_cfg=amet.get("natura"), author_build_natura_raster=amet.get("enable", {}).get("build_natura_raster"),
               author_git_commit=amet.get("git_commit"), author_version=amet.get("version"), author_databundles=bundles,
               author_rooftop_cfg=amet.get("sector", {}).get("solar_rooftop"), author_load_options=amet.get("load_options"),
               author_costs_cfg={k: amet.get("costs", {}).get(k) for k in ("technology_data_version", "year", "append_cost_data")},
               lng_rule=lng_rule, lng_skipped_nodes=lng_zero, lng_caps_by_country=lng_country, lng_identical_integrated_disconnected=same_lng,
               geothermal_new_costs=geo, geothermal_carrier_co2_emissions=geo_carrier_co2, geothermal_generators=dict(n=int(len(geo_gens)), extendable=int(geo_gens.p_nom_extendable.sum()),
                                                                                                                   p_nom_mw=float(geo_gens.p_nom.sum())),
               geothermal_existing_receipt=geo_existing, existing_fleet_efficiency=fleet.to_dict(orient="records"), electric_base_cost_layer=eb_cost, smr_costs=smr, nuclear_costs=nuc, cost_layer_ledger_layers=sorted(set(map(str, receipt["cost_layer"]["rows"].values())))[:12],
               profiles=prof, s4a_profiles_offwind_variants=variants, gegis_attrs=gattrs, astar_vs_gegis=astar,
               gem_about=gem_lines, gem_properties=gem_props, gem_s4r_download_members=gem_zip, seconds=round(time.time() - t0, 1))
    (ev / "M080_EXTRACT.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(dict(seconds=out["seconds"], vre_identical=same_vre, lng_identical=same_lng, lng_twh={c: round(v["cap_twh_per_a"], 2) for c, v in lng_country.items()},
                          geothermal_investment=geo["investment"]), indent=1))
    print(piv.round(1).to_string())


if __name__ == "__main__":
    main()
