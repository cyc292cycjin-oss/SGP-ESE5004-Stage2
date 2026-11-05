"""I1-1d / I1-2b: 2050 effect of the 2019 base version and of the growth-anchor construction, in a scratch copy OUTSIDE the repository
(/home/jin/v4i1/chain). Nothing is solved; the repository is not written.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_chain.py

Gate: the unmodified copy (with the anchor-mode patch at its default) reproduces the eight m08b + s3_0 outputs of the repository byte for byte.

Anchor modes (scratch patch of m08b_demand.py after the RAS step, environment I1_ANCHOR_MODE; default 'ras' = repository code path):
  I    reading I: ATS multipliers unchanged (ATS table rows = new base x the repository multiplier_total; s3_0 only);
  IIa  'ras': RAS re-solved on the new seed (country TFEC anchors and ASEAN C.3 sector totals fixed; country x sector anchors move);
  IIb  'frozen': every country x sector anchor fixed at its repository value (the v3 RAS solution); a correction only changes that country's
       own multipliers (anchor absolute unchanged, no cross-country transfer);
  IIc  'independent': country TFEC anchor from AEO8, sector split = own 2019 seed x C.3 ATS sector growth, normalised (the TL rule of m08b for
       all countries; no column constraint, no cross-country transfer); its own unchanged-base run is the reference for its deltas.
D1 base cases (from scripts/i1_base.py, /home/jin/v4i1/d1_base_<S>.csv):
  S0 repository; VNnonind = S0 + VN diesel outside industry (W12 case B); VNall = S0 + all VN diesel (= S1); S1 truncation; S2 + absent
  commodities; S3 + data version; S4 SDMX with SDMX factors (= BASE2019_SDMX); S5 S4 with decision-207 coal NCV (ID 20.29);
  S4c / S5c = S4 / S5 with the industry sub-sector cache rebuilt from the same SDMX rows (shares only).
T_v2 = sum of the v3_industry.CARRIERS columns of INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv (v3_industry.col: biomass
before overflow), i.e. the definition behind the 3,820.05 TWh of S0 / W11 / G0-G4.
Writes tables/I1_CHAIN_*.csv, BASE2019_SDMX/INDUSTRY_CACHE_SDMX_2019.json, evidence/I1_chain.json.
"""
from __future__ import annotations

import copy
import io
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402
from d1_common import fmt  # noqa: E402
import reconstruct_base_accounts as rba  # noqa: E402

CHAIN = cm.SCRATCH / "chain"
DV = "research_inputs/demand_v5"
D1 = f"{DV}/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
ATS = f"{DV}/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
ANCH = f"{DV}/DEMAND_ANCHOR_AEO8_ATS.csv"
CACHE = "research_inputs/assembly_v1/sources/industry_cache.json"
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
OUTS = ["DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "DEMAND_ANCHOR_AEO8_ATS.csv", "INDUSTRY_OUTPUT_2050_M08B.csv", "INDUSTRY_OUTPUT_BASE_M08B.csv",
        "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY, "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
TCARS = ("coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat", "ammonia", "methanol", "heat_medium_a", "heat_medium_b", "heat_high")   # v3_industry.CARRIERS
SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
KEY = ["country", "sector", "carrier", "account"]
PATCH_ANCHOR = '    tfa["TL"] = {s: A_tfec["TL"] * w_tl[s] / w_tl_sum for s in SECTORS}\n'
PATCH_BLOCK = PATCH_ANCHOR + '''    # ---- I1 scratch-only patch (anchor construction variants; default 'ras' leaves the repository code path unchanged) ----
    import os as _i1os
    _i1m = _i1os.environ.get("I1_ANCHOR_MODE", "ras")
    if _i1os.environ.get("I1_DUMP_ANCHORS"):
        json.dump(dict(tfa={c: {s: tfa[c][s] for s in SECTORS} for c in ASEAN}, t19={c: {s: t19[c][s] for s in SECTORS} for c in ASEAN}),
                  open(_i1os.environ["I1_DUMP_ANCHORS"], "w"))
    if _i1m == "frozen":
        _i1f = json.load(open(_i1os.environ["I1_FROZEN_ANCHORS"]))["tfa"]
        tfa = {c: {s: float(_i1f[c][s]) for s in SECTORS} for c in ASEAN}
    elif _i1m == "fixedcol":
        # RAS solution X = diag(r) seed diag(s): keep the v3 column factors s (taken from ID, all five seeds positive; the row factor cancels
        # in the normalisation), country totals from AEO8, sector split from the country's own (corrected) seed; no column constraint
        _i1d = json.load(open(_i1os.environ["I1_FROZEN_ANCHORS"]))
        _i1s = {s: _i1d["tfa"]["ID"][s] / _i1d["t19"]["ID"][s] for s in SECTORS}
        for c in ASEAN10:
            _i1w = {s: t19[c][s] * _i1s[s] for s in SECTORS}; _i1ws = sum(_i1w.values())
            tfa[c] = {s: A_tfec[c] * _i1w[s] / _i1ws for s in SECTORS}
    elif _i1m == "independent":
        for c in ASEAN10:
            _i1w = {s: t19[c][s] * g_tfec[s] for s in SECTORS}; _i1ws = sum(_i1w.values())
            tfa[c] = {s: A_tfec[c] * _i1w[s] / _i1ws for s in SECTORS}
'''
ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
EV_FACTOR = 0.30215          # oil_to_electricity x ev_share 1 (v3.1 HPC networks, W12 REPORT section 3.2, VERIFIED there)
G0_SEED_II = {"coal": -60.883450, "biomass": -90.788326}   # G0 main path (207 NCV) ID industry 2019 seed changes of the NCV and fuelwood steps (ID_OTHER_SHARE_STEPS.csv industry_2019_twh)
SUBTX = {"1211": "iron and steel", "1213": "chemical and petrochemical", "1214A": "non-ferrous metals", "1214B": "non-metallic minerals",
         "1214C": "transport equipment", "1214D": "machinery", "1214E": "mining and quarrying", "1214F": "food and tobacco", "1214G": "paper pulp and print",
         "1214H": "wood and wood products", "1214I": "construction", "1214J": "textile and leather", "1214O": "other"}


def run(script: str, extra: dict | None = None) -> float:
    t = time.time()
    r = subprocess.run([sys.executable, script], cwd=CHAIN / "scripts_project", capture_output=True, text=True, env={**ENV, **(extra or {})})
    if r.returncode:
        raise RuntimeError(f"{script}: {r.stderr[-3000:]}")
    return time.time() - t


def setup(ev: cm.Evidence):
    if CHAIN.exists():
        shutil.rmtree(CHAIN)
    CHAIN.mkdir(parents=True)
    shutil.copytree(cm.REPO / "research_inputs", CHAIN / "research_inputs")
    shutil.copytree(cm.REPO / "scripts_project", CHAIN / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (CHAIN / "scripts_project/retired").mkdir(exist_ok=True)
    m = CHAIN / "scripts_project/m08b_demand.py"
    src = m.read_text()
    if src.count(PATCH_ANCHOR) != 1:
        raise SystemExit("STOP: anchor patch point not unique in m08b_demand.py")
    m.write_text(src.replace(PATCH_ANCHOR, PATCH_BLOCK))
    dump = cm.SCRATCH / "anchors_v3_ras.json"
    run("m08b_demand.py", {"I1_DUMP_ANCHORS": str(dump)}); run("s3_0_industry.py")
    same = {f: (cm.REPO / DV / f).read_bytes() == (CHAIN / DV / f).read_bytes() for f in OUTS}
    ok = all(same.values())
    ev.add("gate.unmodified_copy_reproduces_repository", ok, "bool", "VERIFIED", "A", "scratch /home/jin/v4i1/chain (m08b patched, default 'ras')",
           "; ".join(f"{k}: {v}" for k, v in same.items()))
    if not ok:
        raise SystemExit("STOP: unmodified scratch copy does not reproduce the repository outputs " + str(same))
    return dump


def snapshot() -> dict:
    s = pd.read_csv(CHAIN / DV / SUMMARY).set_index("country")
    T = {c: float(sum(s.at[c, ("pe_biomass_before_overflow_mwh" if k == "biomass" else f"pe_{k}_mwh")] for k in TCARS)) / 1e6 for c in s.index}
    pe = [x for x in s.columns if x.startswith("pe_")]
    T_allpe = {c: float(s.loc[c, pe].sum()) / 1e6 for c in s.index}   # W12 snapshot metric (all pe_ columns: heat sub-bands and biomass before / after overflow both counted)
    a = pd.read_csv(CHAIN / ATS, keep_default_na=False, dtype=str)
    a["v"] = pd.to_numeric(a.value_2050_mwh, errors="coerce").fillna(0.0)
    # land transport fuel as loaded into the EV / FCEV / ICE split (s2_layers.py:25 LAND_TRANSPORT_ACCOUNTS, parent row included as in the
    # network); EV electricity = land fuel x ev_share 1 x oil_to_electricity 0.30215 (v3.1 network parameters, W12 section 3.2)
    land = {c: float(a[(a.country == c) & (a.sector == "Transport") & a.account.isin(["RoadResidualFuel", "TransportNEC", "TransportEmbeddedFuelParent"])
                       & (a.carrier != "electricity")].v.sum()) / 1e6 for c in cm.ASEAN}
    resf = {c: float(a[(a.country == c) & (a.sector == "Residential") & (a.carrier != "electricity")].v.sum()) / 1e6 for c in cm.ASEAN}
    a = a[a.account != "TransportEmbeddedFuelParent"]   # parent and RailNonElectric child carry the same rail fuel (W12 F2): count once
    sec = {c: {sc: float(a[(a.country == c) & (a.sector == sc)].v.sum()) / 1e6 for sc in SECTORS + ["NonEnergyUse"]} for c in cm.ASEAN}
    an = pd.read_csv(CHAIN / ANCH).set_index("country")
    return dict(T=T, T_allpe=T_allpe, sec=sec, land=land, ev=({c: land[c] * EV_FACTOR for c in land}), resf=resf, ind_anchor={c: float(an.at[c, "industry_anchor_mwh"]) / 1e6 for c in cm.ASEAN},
                ind_mult={c: float(an.at[c, "industry_multiplier"]) for c in cm.ASEAN}, tfec={c: float(an.at[c, "ats_tfec_2050_mwh"]) / 1e6 for c in cm.ASEAN})


def base_map(step: str) -> pd.Series:
    d = pd.read_csv(cm.SCRATCH / f"d1_base_{step}.csv")
    return d.groupby(KEY).base_2019_mwh.sum()


def template(tab: pd.DataFrame, c: str, sec: str, car: str) -> pd.Series:
    for cond in ((tab.country == c) & (tab.sector == sec) & ((tab.carrier == "electricity") == (car == "electricity")),
                 (tab.country == c) & (tab.sector == sec), (tab.sector == sec)):
        t = tab[cond]
        if len(t):
            return t.iloc[0].copy()
    raise KeyError((c, sec, car))


def write_table(orig: bytes, case: pd.Series, s0: pd.Series, path: Path, kind: str) -> list:
    """kind 'd1': base strings via d1_common.fmt (the D1 writer), value_2050 = base x multiplier_total (not read by m08b except blank test);
    kind 'ats_I': reading I - base and value_2050 = base x repository multiplier_total, repr floats (the m08b writer)."""
    tab = pd.read_csv(io.BytesIO(orig), keep_default_na=False, dtype=str)
    f = fmt if kind == "d1" else (lambda v: repr(float(v)))
    log = []
    idx = {tuple(r): i for i, r in zip(tab.index, tab[KEY].values)}
    for k in sorted(set(case.index) | set(s0.index)):
        new = float(case.get(k, 0.0)); old = float(s0.get(k, 0.0))
        if new == old:
            continue
        if k in idx:
            i = idx[k]
            tab.at[i, "base_2019_mwh"] = f(new)
            mult = tab.at[i, "multiplier_total"]
            if tab.at[i, "value_2050_mwh"] != "":
                tab.at[i, "value_2050_mwh"] = f(new * float(mult)) if mult not in ("", None) else f(new)
            log.append(dict(key="|".join(k), action="changed", old=old, new=new))
        else:
            t = template(tab, k[0], k[1], k[2])
            t["country"], t["sector"], t["carrier"], t["account"] = k
            t["base_2019_mwh"] = f(new)
            mult = t["multiplier_total"]
            t["value_2050_mwh"] = f(new * float(mult)) if mult not in ("", None) else f(new)
            for col in ("base_status", "status"):
                if col in t:
                    t[col] = "I1_SCRATCH_NEW_ROW"
            for col in ("in_existing_electricity_load",):
                if col in t:
                    t[col] = "False" if k[2] != "electricity" else t[col]
            if "existing_electricity_load_2050_mwh" in t and k[2] != "electricity":
                t["existing_electricity_load_2050_mwh"] = ""
            tab = pd.concat([tab, t.to_frame().T], ignore_index=True)
            idx[k] = tab.index[-1]
            log.append(dict(key="|".join(k), action="new row", old=old, new=new))
    tab.to_csv(path, index=False, lineterminator="\n")
    return log


CACHE_SKIPPED: list = []


def sdmx_cache(exclude: tuple = ()) -> dict:
    """Industry sub-sector table (MWh, shares used only) from the SDMX capsule with the S4 conversion; coal parent replaces children per
    transaction; 'other' = industry n.e.s. (1214O) + the positive residual of 121 minus its reported children. exclude: commodity codes left
    out (the 'x' cases: 5150 other vegetal residues kept outside T_v2 under the closed-loop rule)."""
    import i1_base as ib
    conv = ib.ext_conversion(json.loads((cm.SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text()))
    cap = [r for r in json.loads((cm.SCRATCH / "SDMX_2019_CAPSULE.json").read_text())["records"] if r["CommodityCode"] not in exclude]
    R = ib.Recon(dict(records=cap), conv, "sdmx")
    cars = ("biomass", "coal", "electricity", "gas", "oil")
    E = {c: {car: {s: 0.0 for s in sorted(set(SUBTX.values()))} for car in cars} for c in cm.ASEAN}
    tot = {c: {car: 0.0 for car in cars} for c in cm.ASEAN}
    for c in cm.ASEAN:
        for t in list(SUBTX) + ["121"]:
            rs = [r for r in R.rows if r["Country"] == c and r.get("TransactionCode") == t]
            el = [r for r in rs if R.fuels.get(rba.commodity(r["Commodity"])) == "electricity"]
            fu = [r for r in rs if R.fuels.get(rba.commodity(r["Commodity"])) in ("oil", "gas", "coal", "biomass")]
            fu, _ = R.select_coal_hierarchy(fu)
            vals = {car: 0.0 for car in cars}
            for r in el:
                vals["electricity"] += float(r["Quantity"]) * 1000.0
            for r in fu:
                try:
                    vals[R.fuels[rba.commodity(r["Commodity"])]] += float(R.convert(r)[0])
                except ValueError as exc:
                    CACHE_SKIPPED.append(dict(country=c, transaction=t, commodity=r["Commodity"], unit=r["Unit"], error=str(exc)))
            for car in cars:
                if t == "121":
                    tot[c][car] = vals[car]
                else:
                    E[c][car][SUBTX[t]] += vals[car]
        for car in cars:
            res = tot[c][car] - sum(E[c][car].values())
            if res > 1e-6:
                E[c][car]["other"] += res
    recs = [dict(country=c, carrier=car, **{s: repr(v) for s, v in E[c][car].items()}) for c in cm.ASEAN for car in cars]
    return dict(source="I1 rebuild from UNSD SDMX 2019 (W12 responses), S4 conversion", source_sha256="", source_year=2019,
                meaning="MWh by industry sub-sector (shares only in s3_0); other = 1214O + positive residual of 121", numeric_acceptance="I1_SCRATCH", records=recs)


def main():
    ev = cm.Evidence("I1_chain")
    dump = setup(ev)
    orig_d1 = (cm.REPO / D1).read_bytes(); orig_ats = (cm.REPO / ATS).read_bytes(); orig_cache = (cm.REPO / CACHE).read_bytes()
    # writing the unchanged tables back must give identical bytes (writer check)
    s0 = base_map("S0")
    write_table(orig_d1, s0, s0, cm.SCRATCH / "d1_check.csv", "d1"); write_table(orig_ats, s0, s0, cm.SCRATCH / "ats_check.csv", "ats_I")
    wc = (cm.SCRATCH / "d1_check.csv").read_bytes() == orig_d1 and (cm.SCRATCH / "ats_check.csv").read_bytes() == orig_ats
    ev.add("gate.table_writer_identity", wc, "bool", "VERIFIED", "A", "pandas re-write of the unchanged D1 / ATS tables", "byte-identical")
    if not wc:
        raise SystemExit("STOP: table writer changes the unchanged tables")
    cache_s = sdmx_cache()
    cache_x = sdmx_cache(("5150",))
    cm.write_json(cache_s, cm.BASE_OUT / "INDUSTRY_CACHE_SDMX_2019.json")
    cm.write_json(cache_x, cm.BASE_OUT / "INDUSTRY_CACHE_SDMX_2019_WITHOUT_5150.json")
    cm.write_csv(CACHE_SKIPPED, cm.TABLES / "I1_CACHE_SDMX_SKIPPED_ROWS.csv", ["country", "transaction", "commodity", "unit", "error"])
    cases = {"S0": base_map("S0")}
    s1 = base_map("S1")
    vn_nonind = s0.copy()
    for k, v in s1.items():
        if k[0] == "VN" and k[1] not in ("Industry",):
            vn_nonind[k] = v
    cases["VNnonind"] = vn_nonind; cases["VNall"] = s1
    for s in ("S1", "S2", "S3", "S4", "S5"):
        cases[s] = base_map(s)
    cases["S4c"] = cases["S4"]; cases["S5c"] = cases["S5"]
    # 'x' cases: industry 'Other Vegetal Material and Residues' (5150) kept outside T_v2 (closed-loop reading of decision 208 item 1)
    P = pd.read_csv(cm.BASE_OUT / "BASE2019_SDMX_COMMODITY_BY_STEP.csv")
    v5150 = P[(P.account == "IndustryFinalEnergy") & (P.commodity == "other vegetal material and residues")].set_index("country")
    for s in ("S4", "S5"):
        b = cases[s].copy()
        for c, r in v5150.iterrows():
            k = (c, "Industry", "biomass", "IndustryFinalEnergy")
            b[k] = b[k] - float(r[s])
        cases[s + "x"] = b; cases[s + "xc"] = b
        ev.add(f"case.{s}x.industry_5150_removed_twh", {c: float(r[s]) / 1e6 for c, r in v5150.iterrows()}, "TWh (2019)", "EXACT", "A",
               "BASE2019_SDMX_COMMODITY_BY_STEP.csv", "IndustryFinalEnergy biomass minus SDMX 5150")
    # section 4: ID and MM household motor gasoline moved to RoadResidualFuel (S0 base; same amounts in the S5x base)
    hg = P[(P.account == "ResidentialFuel") & (P.commodity == "motor gasoline") & P.country.isin(["ID", "MM"])].set_index("country")
    for nm, s in (("GASmove", "S0"), ("S5xGASmove", "S5x")):
        b = cases[s].copy()
        src_step = "S0" if s == "S0" else "S5"
        for c, r in hg.iterrows():
            q = float(r[src_step])
            b[(c, "Residential", "oil", "ResidentialFuel")] = b[(c, "Residential", "oil", "ResidentialFuel")] - q
            b[(c, "Transport", "oil", "RoadResidualFuel")] = b[(c, "Transport", "oil", "RoadResidualFuel")] + q
        cases[nm] = b
        ev.add(f"case.{nm}.household_gasoline_moved_twh", {c: float(r[src_step]) / 1e6 for c, r in hg.iterrows()}, "TWh (2019)", "EXACT", "A",
               "BASE2019_SDMX_COMMODITY_BY_STEP.csv", f"ResidentialFuel motor gasoline -> RoadResidualFuel ({src_step} values)")
    # section 2.4: the G0 ID seed corrections of classes (ii) / (iii) (NCV, fuelwood) - industry 2019 base only (structural steps do not move the seed)
    b = cases["S0"].copy()
    b[("ID", "Industry", "coal", "IndustryFinalEnergy")] += G0_SEED_II["coal"] * 1e6
    b[("ID", "Industry", "biomass", "IndustryFinalEnergy")] += G0_SEED_II["biomass"] * 1e6
    cases["G0seedII"] = b
    modes = {"I": None, "IIa": "ras", "IIb": "frozen", "IIc": "independent", "IId": "fixedcol"}
    res, logs, rows = {}, [], []
    t0 = time.time()
    for mode, am in modes.items():
        for case, base in cases.items():
            (CHAIN / D1).write_bytes(orig_d1); (CHAIN / ATS).write_bytes(orig_ats); (CHAIN / CACHE).write_bytes(orig_cache)
            if case.endswith("xc"):
                cm.write_json(cache_x, CHAIN / CACHE)
            elif case.endswith("c"):
                cm.write_json(cache_s, CHAIN / CACHE)
            if mode == "I":
                if case != "S0":
                    logs += [dict(case=case, mode=mode, **x) for x in write_table(orig_ats, base, s0, CHAIN / ATS, "ats_I")]
                run("s3_0_industry.py")
            else:
                if case != "S0":
                    logs += [dict(case=case, mode=mode, **x) for x in write_table(orig_d1, base, s0, CHAIN / D1, "d1")]
                run("m08b_demand.py", {"I1_ANCHOR_MODE": am, "I1_FROZEN_ANCHORS": str(dump)}); run("s3_0_industry.py")
            res[(mode, case)] = snapshot()
            print(f"{mode:4s} {case:9s} done {time.time() - t0:7.1f} s", flush=True)
    (CHAIN / D1).write_bytes(orig_d1); (CHAIN / ATS).write_bytes(orig_ats); (CHAIN / CACHE).write_bytes(orig_cache)
    ref = {m_: res[(m_, "S0")] for m_ in modes}
    v3 = res[("IIa", "S0")]
    for (mode, case), r in res.items():
        for c in cm.ASEAN + ["ASEAN11"]:
            g = (lambda d: sum(d.values())) if c == "ASEAN11" else (lambda d, c=c: d[c])
            rec = dict(mode=mode, case=case, country=c, T_v2_twh=g(r["T"]), dT_v2_vs_mode_S0_twh=g(r["T"]) - g(ref[mode]["T"]), dT_v2_vs_v3_twh=g(r["T"]) - g(v3["T"]),
                       T_allpe_w12_metric_twh=g(r["T_allpe"]), dT_allpe_vs_mode_S0_twh=g(r["T_allpe"]) - g(ref[mode]["T_allpe"]),
                       industry_anchor_twh=g(r["ind_anchor"]), d_industry_anchor_vs_v3_twh=g(r["ind_anchor"]) - g(v3["ind_anchor"]))
            if c != "ASEAN11":
                rec["industry_multiplier"] = r["ind_mult"][c]
            for kk in ("land", "ev", "resf"):
                rec[f"{kk}_2050_twh"] = g(r[kk]); rec[f"d_{kk}_vs_mode_S0_twh"] = g(r[kk]) - g(ref[mode][kk])
            for sc in SECTORS + ["NonEnergyUse"]:
                vv = sum(r["sec"][x][sc] for x in cm.ASEAN) if c == "ASEAN11" else r["sec"][c][sc]
                vr = sum(ref[mode]["sec"][x][sc] for x in cm.ASEAN) if c == "ASEAN11" else ref[mode]["sec"][c][sc]
                rec[f"{sc}_2050_twh"] = vv; rec[f"d_{sc}_vs_mode_S0_twh"] = vv - vr
            rows.append(rec)
    R = pd.DataFrame(rows)
    cm.write_csv(R.to_dict("records"), cm.TABLES / "I1_CHAIN_RESULTS.csv")
    cm.write_csv(logs, cm.TABLES / "I1_CHAIN_TABLE_EDITS.csv")
    for r in R[(R.country.isin(["ID", "VN", "TH", "MY", "PH", "SG", "MM", "KH", "LA", "BN", "ASEAN11"]))].itertuples():
        if r.case == "S0" and r.mode != "IIc":
            continue
        ev.add(f"{r.mode}.{r.case}.{r.country}", dict(T_v2=r.T_v2_twh, dT_vs_mode_S0=r.dT_v2_vs_mode_S0_twh, dT_vs_v3=r.dT_v2_vs_v3_twh, industry_anchor=r.industry_anchor_twh,
                                                       d_transport=r.d_Transport_vs_mode_S0_twh, d_residential=r.d_Residential_vs_mode_S0_twh),
               "TWh (2050)", "EXACT", "C", "scratch chain m08b + s3_0 (tables/I1_CHAIN_RESULTS.csv)", f"anchor mode {r.mode}, base case {r.case}")
    p = ev.write()
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 600)
    piv = R.pivot_table(index=["case", "country"], columns="mode", values="dT_v2_vs_mode_S0_twh").round(2)
    print(piv.to_string())
    print(R[R.case == "S0"].pivot_table(index="country", columns="mode", values="T_v2_twh").round(2).to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
