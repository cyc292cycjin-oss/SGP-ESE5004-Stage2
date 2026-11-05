"""W12-3: bagasse NCV differs between the demand side (UNSD 7.718 GJ/t, upstream dictionary 0.002144 TWh/kt) and the biomass supply side
(d1_biomass.py LHV_RESIDUE_GJ_T = 15 GJ/t for all crop residues, also used to turn the bagasse price per tonne into EUR/MWh).

A. Replicates the sugarcane_residues potential of research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv exactly with the functions of
   d1_biomass.py (imported read-only, main() not called) and splits it into harvest residues (tops/leaves, x hf x 0.25) and process
   residues (bagasse, x pf x 0.90), both x (1 - feed share).
B. Overestimate of the bagasse part = bagasse mass x (15 - NCV) for NCV = UNSD 7.718 (main), IPCC other primary solid biomass 11.6,
   APEC 2022 country values (PH 17.816, TH 7.53; W11 transcription) as sensitivities; the EUR/MWh price of the store scales by 15 / NCV
   for the bagasse part (same USD per tonne).
C. Demand side: UNSD 2019 bagasse flows (kt) x 7.718 vs x 15 GJ/t.
D. Solved runs: per country the sugarcane store (e_initial, use, exhausted?, shadow value of e_initial = stores_t_mu_energy_balance at the
   first snapshot) and the national solid-biomass pool (potential, use, weighted bus price).
E. Scratch copy: s3_0_industry.py re-run with the bagasse part of potential_main_mwh scaled to 7.718 GJ/t (s3_0_industry.py:133-134 uses
   the solid potential for the decision-36 biomass overflow) -> T_v2 and overflow changes. The unmodified copy must reproduce the
   repository s3_0 outputs byte for byte first.
Writes tables/W12_3_*.csv and evidence/W12_3.json. Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import json
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w12_common as cm  # noqa: E402

CHAIN = Path("/home/jin/v4w07_w12/chain")
DV = "research_inputs/demand_v5"
POT = "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv"
S3_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv", "INDUSTRY_2050_OTHER_BUCKET.csv",
          "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
NCV_SUPPLY = 15.0


def replicate(ev: cm.Evidence) -> pd.DataFrame:
    sys.path.insert(0, str(cm.REPO / "scripts_project"))
    import d1_biomass as B   # noqa: E402  (module constants and helpers only; main() is not called)
    text = B.IRENA_TXT.read_text(encoding="utf-8")
    r3 = B.parse_r3(text)
    factors = r3.groupby("commodity").agg(hf=("hf", lambda s: statistics.mode(s)), pf=("pf", lambda s: statistics.mode(s))).to_dict("index")
    q = B.fao_recent(B.SRC_DIR / B.QCL_CSV)
    prod = q[(q.Element == "Production") & (q.Unit == "t")].copy()
    prod["irena"] = prod.Item.map(B.FAO_TO_IRENA)
    pot = pd.read_csv(cm.REPO / POT, keep_default_na=False)
    rows = []
    for c in cm.ASEAN:
        feed = B.FEED_SHARE_2050.get(c, B.FEED_SHARE_REGIONAL)
        d = prod[(prod.ISO2 == c) & prod.irena.notna() & prod.irena.isin(factors)].copy()
        d["cat"] = d.irena.map(B.CATEGORY_OF).fillna("other_crop_residues")
        dd = d[d.cat == "sugarcane_residues"].copy()
        if dd.empty:
            continue
        dd["hf"] = dd.irena.map(lambda k: factors[k]["hf"]); dd["pf"] = dd.irena.map(lambda k: factors[k]["pf"])
        dd["p2050_t"] = dd.mean_2019_2023.fillna(0.0) * B.GROWTH_2021_2050
        h = float((dd.p2050_t * dd.hf).sum()) * B.HARVEST_MAIN * (1 - feed)
        p = float((dd.p2050_t * dd.pf).sum()) * B.PROCESS * (1 - feed)
        rep = pot[(pot.country == c) & (pot.category == "sugarcane_residues")]
        mass_rep = float(rep.mass_main_t.iloc[0]) if len(rep) else 0.0
        e_rep = float(rep.potential_main_mwh.iloc[0]) if len(rep) else 0.0
        cane19 = float(pd.to_numeric(dd[dd.irena == "Sugar cane"]["Y2019"], errors="coerce").fillna(0.0).sum()) if "Y2019" in dd.columns else None
        pf_cane = float(factors["Sugar cane"]["pf"]) if "Sugar cane" in factors else None
        rows.append(dict(country=c, cane_2019_t_faostat=cane19, pf_sugar_cane=pf_cane, crops=";".join(sorted(set(dd.irena))), hf=";".join(f"{k}:{factors[k]['hf']}" for k in sorted(set(dd.irena))),
                         pf=";".join(f"{k}:{factors[k]['pf']}" for k in sorted(set(dd.irena))), cane_2050_t=float(dd.p2050_t.sum()), feed_share=feed,
                         harvest_mass_t=h, bagasse_mass_t=p, mass_main_t_repl=h + p, mass_main_t_repo=mass_rep,
                         replicates=bool(abs(h + p - mass_rep) <= 1e-6 * max(1.0, mass_rep)), potential_main_mwh_repo=e_rep,
                         harvest_mwh_15=h * NCV_SUPPLY / 3.6, bagasse_mwh_15=p * NCV_SUPPLY / 3.6,
                         cost_eur_per_mwh_15=float(rep.cost_eur2020_per_mwh.iloc[0]) if len(rep) and rep.cost_eur2020_per_mwh.iloc[0] != "" else None))
    R = pd.DataFrame(rows)
    ev.add("replication.all_countries", bool(R.replicates.all()), "bool", "VERIFIED", "A", f"{POT} mass_main_t (sugarcane_residues)",
           "d1_biomass.py parse_r3 + fao_recent + constants, main() not called")
    hits = [ln.strip()[:160] for ln in text.splitlines() if "agasse" in ln][:6]
    return R, hits


def unsd_bagasse(ev: cm.Evidence) -> pd.DataFrame:
    u = cm.load_unsd_2019()
    b = u[u.commodity.str.lower() == "bagasse"]
    t = b.pivot_table(index="ISO", columns="transaction", values="q", aggfunc="sum").fillna(0.0)
    keep = [c for c in t.columns if c in ("production", "final consumption", "final energy consumption", "transformation", "transformation in electricity, chp and heat plants",
                                          "consumption by manufacturing, construction and non-fuel industry", "consumption by food and tobacco", "consumption by industries not elsewhere specified")]
    out = []
    for c, r in t.iterrows():
        rec = dict(country=c, **{f"kt_{k.replace(' ', '_').replace(',', '')}": float(r.get(k, 0.0)) for k in keep})
        prodkt = float(r.get("production", 0.0))
        rec.update(production_twh_7718=prodkt * 7.718 / 3600.0, production_twh_15=prodkt * NCV_SUPPLY / 3600.0)
        out.append(rec)
        ev.add(f"unsd2019.{c}.bagasse_production_kt", prodkt, "kt", "VERIFIED", "A", "UNdata export (pypsa-asean) Bagasse - production 2019")
    return pd.DataFrame(out)


def solved_part(R: pd.DataFrame, ev: cm.Evidence) -> pd.DataFrame:
    rows = []
    over = R.set_index("country")
    for run, (folder, scen, res, ver) in cm.SOLVED.items():
        ds = xr.open_dataset(cm.solved_nc(folder))
        try:
            si = [str(x) for x in ds["stores_i"].values]
            sidx = {s: i for i, s in enumerate(si)}
            bus = dict(zip(si, [str(x) for x in ds["stores_bus"].values]))
            e0 = dict(zip(si, ds["stores_e_initial"].values.astype(float)))
            mc = dict(zip(si, ds["stores_marginal_cost"].values.astype(float)))
            ecols = [str(x) for x in ds["stores_t_e_i"].values]; eidx = {s: i for i, s in enumerate(ecols)}
            E = ds["stores_t_e"].values
            mcols = [str(x) for x in ds["stores_t_mu_energy_balance_i"].values]; midx = {s: i for i, s in enumerate(mcols)}
            MU = ds["stores_t_mu_energy_balance"].values
            w = ds["snapshots_objective"].values.astype(float)
            bi = [str(x) for x in ds["buses_t_marginal_price_i"].values]; bidx = {b: i for i, b in enumerate(bi)}
            MP = ds["buses_t_marginal_price"].values
            for c in cm.ASEAN:
                pool = [s for s in si if bus[s] == f"solid biomass {c}"]
                if not pool:
                    continue
                pot_c = sum(e0[s] for s in pool)
                used_c = sum(e0[s] - (float(E[-1, eidx[s]]) if s in eidx else e0[s]) for s in pool)
                lam = MP[:, bidx[f"solid biomass {c}"]] if f"solid biomass {c}" in bidx else None
                s = f"{c} biomass sugarcane_residues"
                rec = dict(run=run, scenario=scen, resolution=res, model=ver, country=c, pool_potential_mwh=pot_c, pool_used_mwh=used_c,
                           pool_used_share=used_c / pot_c if pot_c else None,
                           pool_price_wmean=float((lam * w).sum() / w.sum()) if lam is not None else None, pool_price_max=float(lam.max()) if lam is not None else None,
                           pool_price_min=float(lam.min()) if lam is not None else None)
                if s in sidx:
                    used = e0[s] - (float(E[-1, eidx[s]]) if s in eidx else e0[s])
                    mu0 = float(MU[0, midx[s]]) if s in midx else None
                    dE1 = float(over.at[c, "overestimate_mwh_R1"]) if c in over.index else 0.0
                    dE2 = over.at[c, "overestimate_mwh_R2"] if c in over.index else None
                    dE2 = float(dE2) if dE2 is not None and dE2 == dE2 else None
                    lamw = rec["pool_price_wmean"]
                    degenerate = bool((mu0 is not None and abs(mu0) > 1000.0) or (lamw is not None and lamw > 1000.0))
                    rec.update(sugar_store_e_initial_mwh=e0[s], sugar_store_used_mwh=used, sugar_store_exhausted=bool(used >= e0[s] * (1 - 1e-4)),
                               sugar_store_marginal_cost=mc[s], sugar_store_mu0=mu0, pool_value_mu0_plus_mc=(abs(mu0) + mc[s]) if mu0 is not None else None,
                               degenerate_dual=degenerate, overestimate_mwh_R1=dE1, overestimate_mwh_R2=dE2,
                               potential_only_lb_R1_eur=(abs(mu0) * dE1 if mu0 is not None else None),
                               potential_and_price_R1_eur=((abs(mu0) + mc[s]) * dE1 if mu0 is not None else None),
                               potential_and_price_R2_eur=((abs(mu0) + mc[s]) * dE2 if (mu0 is not None and dE2 is not None) else None))
                rows.append(rec)
        finally:
            ds.close()
    S = pd.DataFrame(rows)
    cm.write_csv(S.to_dict("records"), cm.TABLES / "W12_3_BIOMASS_POOL_BY_RUN.csv")
    for r in S.itertuples():
        ev.add(f"{r.run}.{r.country}.pool_used_share", r.pool_used_share, "ratio", "VERIFIED", "A", f"{r.run} stores_t_e (solid biomass {r.country})")
        if isinstance(getattr(r, "sugar_store_mu0", None), float) and not np.isnan(r.sugar_store_mu0):
            ev.add(f"{r.run}.{r.country}.sugar_store_mu0", r.sugar_store_mu0, "EUR2020/MWh", "VERIFIED", "A", f"{r.run} stores_t_mu_energy_balance[0]",
                   "degenerate (zero-slack pool)" if r.degenerate_dual else "")
            ev.add(f"{r.run}.{r.country}.potential_and_price_R1_eur", r.potential_and_price_R1_eur, "EUR2020/a", "INFERENCE", "C", "W12_3_BIOMASS_POOL_BY_RUN.csv",
                   "(|mu0| + mc) x R1 overestimate: first order, same USD per tonne, energy cut at the pool value")
            ev.add(f"{r.run}.{r.country}.potential_and_price_R2_eur", r.potential_and_price_R2_eur, "EUR2020/a", "INFERENCE", "C", "W12_3_BIOMASS_POOL_BY_RUN.csv",
                   "(|mu0| + mc) x R2 overestimate")
    pairs = [("S56", "S56_F2", "S56_F1"), ("SCR", "SCR_V2", "SCR_V1"), ("S07", "S07_V2", "S07_V1")]
    b6 = []
    for name, a, b in pairs:
        A = S[(S.run == a) & S.sugar_store_mu0.notna()].set_index("country"); Bq = S[(S.run == b) & S.sugar_store_mu0.notna()].set_index("country")
        for c in A.index:
            for k in ("potential_and_price_R1_eur", "potential_and_price_R2_eur", "potential_only_lb_R1_eur"):
                va, vb = A.at[c, k], Bq.at[c, k]
                b6.append(dict(pair=name, country=c, measure=k, no_new_xb_eur=va, integrated_eur=vb, dB6_first_order_eur=(va - vb) if (va == va and vb == vb) else None,
                               degenerate=bool(A.at[c, "degenerate_dual"] or Bq.at[c, "degenerate_dual"])))
    B6 = pd.DataFrame(b6)
    tot = B6[~B6.degenerate].groupby(["pair", "measure"]).agg(no_new_xb_eur=("no_new_xb_eur", "sum"), integrated_eur=("integrated_eur", "sum"),
                                                              dB6_first_order_eur=("dB6_first_order_eur", "sum")).reset_index().assign(country="ALL_EXCL_DEGENERATE")
    B6 = pd.concat([B6, tot], ignore_index=True)
    cm.write_csv(B6.to_dict("records"), cm.TABLES / "W12_3_B6_FIRST_ORDER.csv")
    for r in tot.itertuples():
        ev.add(f"{r.pair}.{r.measure}.dB6_first_order_excl_degenerate", r.dB6_first_order_eur, "EUR2020", "INFERENCE", "C", "W12_3_B6_FIRST_ORDER.csv",
               f"no_new_xb {r.no_new_xb_eur:.4g} / integrated {r.integrated_eur:.4g} EUR; VN excluded (degenerate pool duals)")
    return S


def chain_part(R: pd.DataFrame, ev: cm.Evidence):
    if CHAIN.exists():
        shutil.rmtree(CHAIN)
    CHAIN.mkdir(parents=True)
    shutil.copytree(cm.REPO / "research_inputs", CHAIN / "research_inputs")
    shutil.copytree(cm.REPO / "scripts_project", CHAIN / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (CHAIN / "scripts_project/retired").mkdir(exist_ok=True)

    def run(script):
        t = time.time()
        r = subprocess.run([sys.executable, script], cwd=CHAIN / "scripts_project", capture_output=True, text=True, env=ENV)
        if r.returncode:
            raise RuntimeError(r.stderr[-3000:])
        return time.time() - t
    t0 = run("s3_0_industry.py")
    rep = [dict(file=f"{DV}/{f}", identical=(cm.REPO / DV / f).read_bytes() == (CHAIN / DV / f).read_bytes()) for f in S3_OUT]
    ok = all(r["identical"] for r in rep)
    ev.add("chain.unmodified_s3_0_reproduces_repo", ok, "bool", "VERIFIED", "A", "scratch /home/jin/v4w07_w12/chain", f"{len(rep)} files; {t0:.1f} s")
    if not ok:
        raise SystemExit("STOP: unmodified scratch copy does not reproduce the repository s3_0 outputs (instruction A1)")
    base = {f: pd.read_csv(CHAIN / DV / f, keep_default_na=False, dtype=str) for f in (S3_OUT[0], S3_OUT[1])}
    pot = pd.read_csv(CHAIN / POT, keep_default_na=False, dtype=str)
    for r in R.itertuples():
        m = (pot.country == r.country) & (pot.category == "sugarcane_residues")
        if m.sum() == 0:
            continue
        new =float(pot.loc[m, "potential_main_mwh"].iloc[0]) - r.bagasse_mwh_15 * (1 - 7.718 / NCV_SUPPLY)
        pot.loc[m, "potential_main_mwh"] = repr(new)
    pot.to_csv(CHAIN / POT, index=False, lineterminator="\n")
    t1 = run("s3_0_industry.py")
    fix = {f: pd.read_csv(CHAIN / DV / f, keep_default_na=False, dtype=str) for f in (S3_OUT[0], S3_OUT[1])}
    S0 = base[S3_OUT[1]].set_index("country"); S1 = fix[S3_OUT[1]].set_index("country")
    pe = [c for c in S0.columns if c.startswith("pe_")]
    A0 = base[S3_OUT[0]].set_index("country"); A1 = fix[S3_OUT[0]].set_index("country")
    ovc = [c for c in A0.columns if "overflow" in c or "solid_biomass_potential" in c]
    out = []
    for c in S0.index:
        rec = dict(country=c, T_v2_v3_mwh=float(pd.to_numeric(S0.loc[c, pe]).sum()), T_v2_ncv7718_mwh=float(pd.to_numeric(S1.loc[c, pe]).sum()))
        rec["T_v2_dv_mwh"] = rec["T_v2_ncv7718_mwh"] - rec["T_v2_v3_mwh"]
        for k in pe:
            dv = float(pd.to_numeric(S1.at[c, k])) - float(pd.to_numeric(S0.at[c, k]))
            if abs(dv) > 1e-3:
                rec[f"d_{k}"] = dv
        for k in ovc:
            rec[f"{k}_v3"] = float(pd.to_numeric(A0.at[c, k], errors="coerce")); rec[f"{k}_ncv7718"] = float(pd.to_numeric(A1.at[c, k], errors="coerce"))
        out.append(rec)
    cols = sorted({k for r in out for k in r}, key=lambda k: (k != "country", k))
    cm.write_csv(out, cm.TABLES / "W12_3_S3_0_OVERFLOW_EFFECT.csv", cols)
    for r in out:
        if abs(r["T_v2_dv_mwh"]) > 1e-3:
            ev.add(f"{r['country']}.T_v2_dv_mwh", r["T_v2_dv_mwh"], "MWh/a", "EXACT", "C", "scratch s3_0 re-run with bagasse at 7.718 GJ/t", f"{t1:.1f} s")
    return out, ovc


def main():
    ev = cm.Evidence("W12_3")
    R, hits = replicate(ev)
    alt = {"unsd_7718": 7.718, "ipcc_11p6": 11.6}
    apec = {"PH": 17.816, "TH": 7.53}
    for k, v in alt.items():
        R[f"bagasse_mwh_{k}"] = R.bagasse_mass_t * v / 3.6
        R[f"overestimate_mwh_{k}"] = R.bagasse_mwh_15 - R[f"bagasse_mwh_{k}"]
    R["bagasse_mwh_apec2022"] = [r.bagasse_mass_t * apec[r.country] / 3.6 if r.country in apec else None for r in R.itertuples()]
    R["overestimate_mwh_apec2022"] = [(r.bagasse_mwh_15 - r.bagasse_mwh_apec2022) if r.bagasse_mwh_apec2022 is not None else None for r in R.itertuples()]
    R["overestimate_share_of_sugarcane_potential_unsd"] = R.overestimate_mwh_unsd_7718 / R.potential_main_mwh_repo
    # cross-check per tonne of cane against UNSD 2019 bagasse production (reading R2): IRENA energy per t cane = pf x 15 GJ/t;
    # UNSD energy per t cane = bagasse kt x 7.718 / FAOSTAT 2019 cane; R2 overestimate = bagasse_mwh_15 x (1 - UNSD / IRENA) when UNSD < IRENA
    U0 = unsd_bagasse(cm.Evidence("tmp")).set_index("country")
    R["unsd_bagasse_2019_kt"] = R.country.map(lambda c: float(U0.at[c, "kt_production"]) if c in U0.index and "kt_production" in U0.columns else 0.0)
    R["unsd_bagasse_t_per_t_cane"] = R.unsd_bagasse_2019_kt * 1e3 / R.cane_2019_t_faostat.replace(0, np.nan)
    R["unsd_gj_per_t_cane"] = R.unsd_bagasse_t_per_t_cane * 7.718
    R["irena_gj_per_t_cane"] = R.pf_sugar_cane * NCV_SUPPLY
    R["implied_ncv_for_irena_mass_gj_t"] = R.unsd_gj_per_t_cane / R.pf_sugar_cane
    R["overestimate_mwh_R2"] = [(r.bagasse_mwh_15 * max(0.0, 1 - r.unsd_gj_per_t_cane / r.irena_gj_per_t_cane)) if (r.unsd_gj_per_t_cane == r.unsd_gj_per_t_cane and r.unsd_gj_per_t_cane > 0) else None
                                for r in R.itertuples()]
    R["overestimate_mwh_R1"] = R.overestimate_mwh_unsd_7718
    R["bagasse_cost_eur_per_mwh_unsd"] = R.cost_eur_per_mwh_15 * NCV_SUPPLY / 7.718
    pot = pd.read_csv(cm.REPO / POT, keep_default_na=False)
    solid = pot[pot.feedstock_group != "biogas"].assign(p=pd.to_numeric(pot.potential_main_mwh, errors="coerce").fillna(0.0)).groupby("country").p.sum()
    R["solid_potential_country_mwh"] = R.country.map(solid)
    R["overestimate_share_of_solid_potential_unsd"] = R.overestimate_mwh_unsd_7718 / R.solid_potential_country_mwh
    cm.write_csv(R.to_dict("records"), cm.TABLES / "W12_3_BAGASSE_SUPPLY_OVERESTIMATE.csv")
    for r in R.itertuples():
        ev.add(f"{r.country}.bagasse_mass_t", r.bagasse_mass_t, "t/a (2050, after feed share)", "EXACT", "C", "replication of d1_biomass.py", "cane x pf x 0.90 x (1 - feed)")
        ev.add(f"{r.country}.bagasse_mwh_15", r.bagasse_mwh_15, "MWh/a", "EXACT", "C", "bagasse mass x 15 GJ/t (d1_biomass.py:47)")
        ev.add(f"{r.country}.overestimate_mwh_unsd", r.overestimate_mwh_unsd_7718, "MWh/a", "EXACT", "C", "bagasse mass x (15 - 7.718) GJ/t")
        ev.add(f"{r.country}.overestimate_share_of_solid_potential", r.overestimate_share_of_solid_potential_unsd, "ratio", "EXACT", "C", "vs national solid-biomass potential_main_mwh")
    U = unsd_bagasse(ev)
    cm.write_csv(U.to_dict("records"), cm.TABLES / "W12_3_UNSD_BAGASSE_2019.csv")
    S = solved_part(R, ev)
    out, ovc = chain_part(R, ev)
    cm.write_json(dict(script="scripts/w12_bagasse.py", irena_text_bagasse_lines=hits,
                       ncv=dict(supply_gj_t=NCV_SUPPLY, unsd_gj_t=7.718, unsd_source="FROZEN_UPSTREAM_CONVERSIONS.json Bagasse 0.002144 TWh/kt", ipcc_other_primary=11.6,
                                apec2022=apec)), cm.EVID / "W12_3_meta.json")
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(R[["country", "replicates", "cane_2050_t", "harvest_mass_t", "bagasse_mass_t", "potential_main_mwh_repo", "bagasse_mwh_15", "overestimate_mwh_unsd_7718",
             "overestimate_share_of_solid_potential_unsd", "cost_eur_per_mwh_15", "bagasse_cost_eur_per_mwh_unsd"]].to_string())
    print(U.to_string())
    print(R[["country", "cane_2019_t_faostat", "pf_sugar_cane", "unsd_bagasse_2019_kt", "unsd_bagasse_t_per_t_cane", "unsd_gj_per_t_cane", "irena_gj_per_t_cane",
             "implied_ncv_for_irena_mass_gj_t", "overestimate_mwh_R1", "overestimate_mwh_R2"]].to_string())
    print(S[S.run.isin(["SCR_V1", "SCR_V2"])][["run", "country", "pool_price_wmean", "sugar_store_mu0", "degenerate_dual", "potential_and_price_R1_eur",
                                               "potential_and_price_R2_eur"]].to_string())
    B6 = pd.read_csv(cm.TABLES / "W12_3_B6_FIRST_ORDER.csv")
    print(B6[B6.country == "ALL_EXCL_DEGENERATE"].to_string())
    print(pd.DataFrame(out).to_string())
    print(hits)
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
