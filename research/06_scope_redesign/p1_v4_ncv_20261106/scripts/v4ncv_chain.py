"""V4 W11 section 3: the repository data chain re-run in a scratch copy OUTSIDE the repository for the NCV schemes.

    PYTHONHASHSEED=0 python scripts/v4ncv_chain.py --work <work dir> --repo /home/jin/wt_v4_ncv --chain /home/jin/v4ncv/chain

Copy research_inputs + scripts_project of the worktree once (as S1 v4s1_captive_options.py); for every case the edited inputs are restored
from the original bytes first. Two growth readings:
  (I)  'multiplier unchanged' (S1 convention, decision 204 item 1): the 2019 deltas (ncv/NCV_BASE_DELTAS_2019.csv) are added to
       base_2019_mwh of the ATS anchor table; value_2050_mwh = base x multiplier_total for the changed rows; industry_cache.json cells are
       multiplied by the NCV ratios (ncv/NCV_CACHE_RATIOS_2019.csv); s3_0_industry.py is run.
  (II) 'AEO8 anchor absolute': the same deltas are added to base_2019_mwh of the D1 ratio table (the RAS seeds and carrier shares),
       m08b_demand.py is run (re-solves the RAS: sector totals stay at the AEO8 ATS anchors), then s3_0_industry.py.
Before any case, the unmodified copy must reproduce the repository byte for byte: (I) the s3_0 outputs; (II) the m08b ATS table and the s3_0
outputs. The v3 decomposition (v3_industry.decompose + non-ferrous + D163-6 conservation, as S1) gives the 'other' bucket per country.
Side case 'x_cache_dedup' (v3 factors): the coal cells of the KH / LA / TH cache replaced by de-duplicated values (upstream parent + child double count).
Outputs ncv/NCV_IMPACT_COUNTRY.csv, ncv/NCV_IMPACT_SECTOR.csv, ncv/NCV_IMPACT_OTHER_CARRIER.csv, ncv/_chain_evidence.json.
Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4ncv_common as cm   # noqa: E402

SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
CACHE = "research_inputs/assembly_v1/sources/industry_cache.json"
ATS = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
D1 = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
S3_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY, "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
M08B_OUT = ["DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "DEMAND_ANCHOR_AEO8_ATS.csv", "INDUSTRY_OUTPUT_2050_M08B.csv", "INDUSTRY_OUTPUT_BASE_M08B.csv"]
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}


def copy_chain(repo: Path, chain: Path) -> None:
    if chain.exists():
        shutil.rmtree(chain)
    chain.mkdir(parents=True)
    shutil.copytree(repo / "research_inputs", chain / "research_inputs")
    shutil.copytree(repo / "scripts_project", chain / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (chain / "scripts_project/retired").mkdir(exist_ok=True)


def run(chain: Path, script: str) -> float:
    t = time.time()
    r = subprocess.run([sys.executable, script], cwd=chain / "scripts_project", capture_output=True, text=True, env=ENV)
    if r.returncode:
        raise RuntimeError(f"{script}: {r.stderr[-3000:]}")
    return time.time() - t


def restore(chain: Path, orig: dict) -> None:
    for rel, b in orig.items():
        (chain / rel).write_bytes(b)


def apply_table(path: Path, deltas: pd.DataFrame, scheme: str, rescale_2050: bool) -> list:
    d = pd.read_csv(path, keep_default_na=False, dtype=str)
    log = []
    for r in deltas.itertuples():
        dv = float(getattr(r, f"{scheme}_delta_mwh"))
        if dv == 0.0:
            continue
        m = (d.country == r.country) & (d.account == r.account)
        if isinstance(r.carrier, str):
            m &= d.carrier == r.carrier
        if m.sum() != 1:
            if r.account.startswith("International"):
                continue   # bunkers: UNSD constants outside the sector anchors and outside T_v2; reported in the base-delta table only
            raise ValueError(f"{path.name}: {r.country} {r.account} {r.carrier}: {m.sum()} rows")
        b0 = float(d.loc[m, "base_2019_mwh"].iloc[0]); b = b0 + dv
        d.loc[m, "base_2019_mwh"] = repr(b)
        if rescale_2050:
            d.loc[m, "value_2050_mwh"] = repr(b * float(d.loc[m, "multiplier_total"].iloc[0]))
        log.append(dict(country=r.country, account=r.account, carrier=r.carrier, base_v3=b0, base_new=b, delta=dv))
    d.to_csv(path, index=False)
    return log


def apply_cache(path: Path, ratios: pd.DataFrame, scheme: str, dedup: bool = False) -> None:
    cache = json.loads(path.read_text())
    if dedup:
        z = ratios[(ratios.scheme == "b") & (ratios.carrier == "coal") & ratios.country.isin(["KH", "LA", "TH"])]
        for rec in cache["records"]:
            if rec["country"] in ("KH", "LA", "TH") and rec["carrier"] == "coal":
                for k in list(rec):
                    if k in ("country", "carrier"):
                        continue
                    v = z[(z.country == rec["country"]) & (z.subsector == k)].v3_mwh
                    rec[k] = repr(float(v.iloc[0]) if len(v) else 0.0)
    else:
        z = ratios[ratios.scheme == scheme].set_index(["country", "carrier", "subsector"]).ratio
        for rec in cache["records"]:
            for k in list(rec):
                if k in ("country", "carrier"):
                    continue
                f = z.get((rec["country"], rec["carrier"], k))
                if f is not None and f != 1.0:
                    rec[k] = repr(float(rec[k]) * float(f))
    path.write_text(json.dumps(cache))


def vn_row(chain: Path) -> pd.Series:
    """v3_industry.run_vn_chain on the current copy: VN cache shares replaced by the APEC 2022 matrix, s3_0 re-run, VN row returned;
    the cache bytes are restored afterwards (the v3 rule: VN total from the main run, VN decomposition from this row)."""
    cp = chain / CACHE
    keep = cp.read_bytes()
    cache = json.loads(keep)
    apec = pd.read_csv(chain / "research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv").set_index("cache_subsector")
    carmap = dict(coal="coal_pj", oil="oil_pj", gas="gas_pj", biomass="biomass_pj", electricity="electricity_pj")
    for r in cache["records"]:
        if r["country"] == "VN":
            k = carmap[r["carrier"]]
            for s in r:
                if s not in ("country", "carrier"):
                    r[s] = float(apec.at[s, k]) if s in apec.index else 0.0
    cp.write_text(json.dumps(cache))
    run(chain, "s3_0_industry.py")
    row = pd.read_csv(chain / "research_inputs/demand_v5" / SUMMARY).set_index("country").loc["VN"].copy()
    cp.write_bytes(keep)
    return row


def collect(chain: Path, v3, fut, nf, s: pd.DataFrame | None = None) -> dict:
    """v3 decomposition per country (v3_industry.main): T from the main run, VN parts from vn_row(), other scaled to T - explicit."""
    if s is None:
        s = pd.read_csv(chain / "research_inputs/demand_v5" / SUMMARY).set_index("country")
    gaps = pd.read_csv(chain / "research_inputs/demand_v5/INDUSTRY_2050_GAPS.csv")
    gaps = gaps[gaps["mode"] == "aeo8_ats_anchor"].copy()
    vn = vn_row(chain)
    out = {"_gaps": gaps}
    for c in s.index:
        row = s.loc[c]
        T = float(sum(row[v3.col(x)] for x in v3.CARRIERS))
        parts = v3.decompose(vn if c == "VN" else row, fut); parts.update(nf.get(c, {}))
        expl = sum(sum(v.values()) for k, v in parts.items() if k != "other")
        so = sum(parts["other"].values()); f = (T - expl) / so if so else 0.0
        other = {k: v * f for k, v in parts["other"].items()}
        out[c] = dict(T=T, other=other, explicit=expl, scale=f)
    return out


def sectors(chain: Path) -> pd.DataFrame:
    d = pd.read_csv(chain / ATS, keep_default_na=False)
    d["base_2019_mwh"] = pd.to_numeric(d.base_2019_mwh, errors="coerce").fillna(0.0)
    d["value_2050_mwh"] = pd.to_numeric(d.value_2050_mwh, errors="coerce").fillna(0.0)
    return d.groupby(["country", "sector"])[["base_2019_mwh", "value_2050_mwh"]].sum()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); ap.add_argument("--repo", type=Path, default=cm.REPO)
    ap.add_argument("--chain", type=Path, default=Path("/home/jin/v4ncv/chain")); a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import v3_industry as v3   # noqa: E402  (ROOT = repository worktree; explicit sub-sectors do not depend on the NCV)
    fut = v3.future_vectors(); ne = v3.nickel_unit_energy(); nf = v3.nonferrous(fut, "main", ne)[0]
    deltas = pd.read_csv(a.work / "ncv/NCV_BASE_DELTAS_2019.csv")
    ratios = pd.read_csv(a.work / "ncv/NCV_CACHE_RATIOS_2019.csv")
    t0 = time.time()
    copy_chain(a.repo, a.chain)
    orig = {rel: (a.repo / rel).read_bytes() for rel in (CACHE, ATS, D1)}
    ev = dict(timing_s={}, reproduction={}, cases={})
    dd = a.chain / "research_inputs/demand_v5"
    rd = a.repo / "research_inputs/demand_v5"
    # ---- reproduction (I): s3_0 on the unmodified copy -------------------------------------------------------------------------------
    ev["timing_s"]["s3_0_unmodified"] = run(a.chain, "s3_0_industry.py")
    same = {f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in S3_OUT}
    base = collect(a.chain, v3, fut, nf)
    sub = pd.read_csv(rd.parent / "industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
    sub = sub[(sub.case == "main") & (sub.subsector == "other")]
    devs = {c: max(abs(base[c]["other"].get(k, 0.0) - float(g.set_index("carrier").mwh_2050.get(k, 0.0))) for k in set(base[c]["other"]) | set(g.carrier))
            for c, g in sub.groupby("country")}
    dev_other = max(devs.values())
    ev["reproduction"]["I"] = dict(byte_identical=same, max_abs_dev_v3_other_mwh=dev_other, dev_by_country=devs)
    if not all(same.values()) or dev_other > 1e-3:
        raise SystemExit(f"STOP: unmodified copy does not reproduce the repository (I): {same}, v3 other dev {dev_other}, by country {devs}")
    sec0 = sectors(a.chain)
    # ---- reproduction (II): m08b then s3_0 on the unmodified copy --------------------------------------------------------------------
    ev["timing_s"]["m08b_unmodified"] = run(a.chain, "m08b_demand.py")
    same2 = {f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in M08B_OUT}
    ev["timing_s"]["s3_0_after_m08b"] = run(a.chain, "s3_0_industry.py")
    same2.update({f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in S3_OUT})
    ev["reproduction"]["II"] = dict(byte_identical=same2)
    if not all(same2.values()):
        raise SystemExit(f"STOP: unmodified copy does not reproduce the repository (II): {same2}")
    rows_c, rows_s, rows_o, rows_g = [], [], [], []
    NONIND = ["Residential", "Commercial", "AgricultureOthers", "Transport"]

    def record(case, mode, res, sec):
        g = res.pop("_gaps")
        rows_g.extend(dict(case=case, mode=mode, **{("s3_mode" if k == "mode" else k): v for k, v in r.items()}) for r in g.to_dict("records"))
        for c in sorted(res):
            T0, O0 = base[c]["T"], sum(base[c]["other"].values())
            T1, O1 = res[c]["T"], sum(res[c]["other"].values())
            n0 = float(sum(sec0.loc[(c, s_), "value_2050_mwh"] for s_ in NONIND if (c, s_) in sec0.index))
            n1 = float(sum(sec.loc[(c, s_), "value_2050_mwh"] for s_ in NONIND if (c, s_) in sec.index))
            rows_c.append(dict(case=case, mode=mode, country=c, T_v2_2050_twh=T1 / 1e6, delta_T_twh=(T1 - T0) / 1e6, delta_T_pct=((T1 / T0 - 1) * 100 if T0 else 0.0),
                               other_2050_twh=O1 / 1e6, delta_other_twh=(O1 - O0) / 1e6, delta_other_pct=((O1 / O0 - 1) * 100 if O0 else 0.0),
                               other_share_pct=(O1 / T1 * 100 if T1 else 0.0), other_share_v3_pct=(O0 / T0 * 100 if T0 else 0.0),
                               explicit_2050_twh=res[c]["explicit"] / 1e6, nonindustry_2050_twh=n1 / 1e6, delta_nonindustry_twh=(n1 - n0) / 1e6,
                               total_final_2050_twh=(T1 + n1) / 1e6, delta_total_twh=(T1 + n1 - T0 - n0) / 1e6,
                               delta_total_pct=(((T1 + n1) / (T0 + n0) - 1) * 100 if (T0 + n0) else 0.0)))
            for k in OUTC:
                rows_o.append(dict(case=case, mode=mode, country=c, carrier=k, other_2050_twh=res[c]["other"].get(k, 0.0) / 1e6,
                                   delta_twh=(res[c]["other"].get(k, 0.0) - base[c]["other"].get(k, 0.0)) / 1e6))
        for (c, s), r in sec.iterrows():
            r0 = sec0.loc[(c, s)]
            rows_s.append(dict(case=case, mode=mode, country=c, sector=s, base_2019_twh=r.base_2019_mwh / 1e6, delta_2019_twh=(r.base_2019_mwh - r0.base_2019_mwh) / 1e6,
                               value_2050_twh=r.value_2050_mwh / 1e6, delta_2050_twh=(r.value_2050_mwh - r0.value_2050_mwh) / 1e6))

    record("a", "v3", dict(base), sec0)
    base.pop("_gaps", None)
    for s in ("b", "c", "d"):
        # (I)
        restore(a.chain, orig)
        log = apply_table(a.chain / ATS, deltas, s, rescale_2050=True)
        apply_cache(a.chain / CACHE, ratios, s)
        ev["timing_s"][f"{s}_I"] = run(a.chain, "s3_0_industry.py")
        record(s, "I", collect(a.chain, v3, fut, nf), sectors(a.chain))
        ev["cases"][f"{s}_I"] = dict(rows_changed=len(log))
        # (II)
        restore(a.chain, orig)
        log2 = apply_table(a.chain / D1, deltas, s, rescale_2050=False)
        apply_cache(a.chain / CACHE, ratios, s)
        ev["timing_s"][f"{s}_II_m08b"] = run(a.chain, "m08b_demand.py")
        ev["timing_s"][f"{s}_II_s3"] = run(a.chain, "s3_0_industry.py")
        record(s, "II", collect(a.chain, v3, fut, nf), sectors(a.chain))
        ev["cases"][f"{s}_II"] = dict(rows_changed=len(log2))
    # side case: cache de-duplication only (v3 factors), mode I
    restore(a.chain, orig)
    apply_cache(a.chain / CACHE, ratios, "b", dedup=True)
    ev["timing_s"]["x_cache_dedup"] = run(a.chain, "s3_0_industry.py")
    record("x_cache_dedup", "I", collect(a.chain, v3, fut, nf), sectors(a.chain))
    restore(a.chain, orig)   # leave the copy unmodified (outputs of the last run remain; inputs are original)
    ev["timing_s"]["total"] = time.time() - t0
    out = a.work / "ncv"
    pd.DataFrame(rows_c).to_csv(out / "NCV_IMPACT_COUNTRY.csv", index=False, float_format="%.6f")
    pd.DataFrame(rows_s).to_csv(out / "NCV_IMPACT_SECTOR.csv", index=False, float_format="%.6f")
    pd.DataFrame(rows_o).to_csv(out / "NCV_IMPACT_OTHER_CARRIER.csv", index=False, float_format="%.6f")
    pd.DataFrame(rows_g).to_csv(out / "NCV_IMPACT_S3_GAPS.csv", index=False, float_format="%.6f")
    (out / "_chain_evidence.json").write_text(json.dumps(ev, indent=1, default=float) + "\n")
    C = pd.DataFrame(rows_c)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print(json.dumps(ev["reproduction"], default=float))
    print(json.dumps(ev["timing_s"], default=float))
    print(C[C.case != "a"].round(2).to_string())


if __name__ == "__main__":
    main()
