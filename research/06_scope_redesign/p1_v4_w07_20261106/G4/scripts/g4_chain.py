"""G4 combined quantification (V4 W07 B-G4; S2 method template step 9) in a scratch copy of the data chain OUTSIDE the repository.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python -I scripts/g4_chain.py        (WSL)

The unmodified copy must first reproduce the repository: the four s3_0 outputs byte for byte, the v3 'other' bucket of MM, KH, LA, BN, TL to
< 1e-3 MWh, and the patched copy without the environment variable identical (A1: otherwise stop). Then cumulative steps, each run for both
coal NCV schemes ('v3' = frozen dictionary, '207' = decision 207 main values), growth reading I (ATS multiplier unchanged):
  1 ncv       coal NCV at the UNSD row level (MM 23.26, KH 19.853, LA 25.121 / 9.63 GJ/t; BN and TL have no industry coal);
  2 captive   option (b), MM central (= low, cross-checks in evidence/MM_CAPTIVE_COAL_2019.csv): C leaves the UNSD non-metallic minerals coal,
              E = generation enters as 'other' electricity; C in tonnes, converted with the NCV of the scheme (W11 section 4.3);
  3 cement    correction (ii) for MM, KH, LA (grinding electricity on USGS 2019 cement, kiln fuel on EDGAR clinker unchanged);
              BN (iii): no clinker kiln (GEM: one grinding plant), EDGAR 2.A.1 set to 0 in the copy, grinding electricity on USGS 2019 cement,
              2050 cement = electricity part of the PyPSA-Eur cement ratio only;
  4 products  MM paper (+ non-wood pulp) and MM refined copper, LA pulp and LA refined copper: 2019 energy (JRC-IDEES today x PyPSA-Eur
              structure) leaves the same-name dispersed row first, then 'other' (s3_0 spread rule); closed-loop rule (decision 206 item 3):
              pulp / paper count electricity and heat only, the biomass part is listed separately; 2050 = activity x PyPSA-Eur 2050 ratio.
Sensitivities on the full main case (scheme 207), single steps and additivity. Outputs <CC>_OTHER_SHARE_STEPS.csv, evidence/G4_SCENARIOS.csv,
evidence/G4_ADDITIVITY.csv, evidence/_chain_evidence.json. Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import filecmp
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g4_common as cm   # noqa: E402

CI = json.loads((cm.G4 / "evidence/_chain_inputs.json").read_text())
EV = cm.Ev("chain")
PROD_ROWS = {"MM_paper": ("MM", "paper pulp and print"), "MM_pulp": ("MM", "paper pulp and print"), "MM_copper": ("MM", "non-ferrous metals"),
             "LA_pulp": ("LA", None), "LA_copper": ("LA", None), "LA_paper_R4": ("LA", None)}
MAIN_PRODUCTS = ["MM_paper", "MM_pulp", "MM_copper", "LA_pulp", "LA_copper"]


def ncv_edit(scheme: str) -> dict:
    if scheme == "v3":
        return {}
    if scheme == "sens":
        src = {"MM": CI["ncv"]["sens_ipcc"]["MM"], "KH": CI["ncv"]["sens_child"]["KH"], "LA": CI["ncv"]["sens_child"]["LA"]}
    else:
        src = CI["ncv"][scheme]
    return {iso: {"ats": e["ats"], "cache": {tuple(k.split("|")): v for k, v in e["cache"].items()}} for iso, e in src.items()}


class Runner:
    def __init__(self):
        self.v3 = cm.import_v3(); self.fut = self.v3.future_vectors()
        self.ch = cm.Chain(); self.ch.copy(); self.ch.patch()
        self.cache0 = json.loads(self.ch.orig[cm.CACHE_REL])
        self.repro = None; self.n_runs = 0

    def reproduce(self):
        self.ch.restore()
        (self.ch.chain / cm.S30_REL).write_bytes(self.ch.orig[cm.S30_REL])   # unpatched first
        s, ob, pz, gp = self._run_unpatched()
        dd, rd = self.ch.chain / "research_inputs/demand_v5", cm.REPO / "research_inputs/demand_v5"
        same = {f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in cm.S3_OUT}
        sub = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
        sub = sub[(sub.case == "main") & (sub.subsector == "other")]
        dev = {}
        for c in cm.C5:
            L = self.layer(s, c, {}, None)
            ref = sub[sub.country == c].set_index("carrier").mwh_2050
            dev[c] = max([abs(L["other"].get(k, 0.0) - float(ref.get(k, 0.0))) for k in set(L["other"]) | set(ref.index)] + [0.0])
        self.ch.patch()
        s2, _, _, _ = self.ch.run()
        dev_p = max(abs(float(s2.at[c, self.v3.col(x)]) - float(s.at[c, self.v3.col(x)])) for c in cm.C5 for x in self.v3.CARRIERS)
        self.repro = dict(byte_identical=same, max_abs_dev_v3_other_mwh=dev, max_abs_dev_patched_no_env_mwh=dev_p)
        if not all(same.values()) or max(dev.values()) > 1e-3 or dev_p > 1e-3:
            raise SystemExit(f"STOP (A1): the unmodified scratch copy does not reproduce the repository: {self.repro}")
        return self.repro

    def _run_unpatched(self):
        self.ch.patched = False
        out = cm.Chain.run(self.ch)
        return out

    # ---------------------------------------------------------------- v3 conservation layer ----------------------------------------------
    def layer(self, s, c, extra: dict, cement_iii_t50: float | None):
        row = s.loc[c]
        T_chain = float(sum(row[self.v3.col(x)] for x in self.v3.CARRIERS))
        if T_chain <= 0:
            z = {k: 0.0 for k in cm.OUTC}
            return dict(T=0.0, other=z, other_total=0.0, explicit=0.0, by_sub={}, scale=0.0, parts={})
        parts = self.v3.decompose(row, self.fut)
        T = T_chain
        if cement_iii_t50 is not None:   # BN (iii): grinding only -> electricity part of the PyPSA-Eur cement ratio
            full = sum(parts["cement"].values())
            parts["cement"] = {k: (self.fut["Cement"].get("electricity", 0.0) * cement_iii_t50 if k == "electricity" else 0.0) for k in parts["cement"]}
            T += sum(parts["cement"].values()) - full
        for k, v in extra.items():
            parts[k] = {oc: float(v.get(oc, 0.0)) for oc in cm.OUTC}
            T += sum(parts[k].values())
        expl = sum(sum(v.values()) for k, v in parts.items() if k != "other")
        so = sum(parts["other"].values()); f = (T - expl) / so if so > 0 else 0.0
        if f < 0:
            raise ValueError(f"{c}: explicit sub-sectors exceed T (D163-4)")
        other = {k: parts["other"].get(k, 0.0) * f for k in cm.OUTC}
        return dict(T=T, other=other, other_total=sum(other.values()), explicit=expl, scale=f,
                    by_sub={k: sum(v.values()) for k, v in parts.items() if k != "other"}, parts=parts)

    # ---------------------------------------------------------------- scenario ------------------------------------------------------------
    def scenario(self, name, scheme="v3", captive=None, cement=False, bn_cement="iii", products=(), biomass=(), note=""):
        ncv = ncv_edit(scheme); moves = {c: [] for c in cm.C4}
        if captive:
            cap = CI["captive_MM"][{"central": "low"}.get(captive, captive)]
            C = cap["C_mwh_v3"] if scheme == "v3" else cap["C_kt"] * (23.26 if scheme != "sens" else 18.9) / 3.6 * 1e3
            moves["MM"] += [("non-metallic minerals", "coal", C), ("other", "electricity", -cap["E_mwh"])]
        for b in biomass:
            z = CI["biomass_sens"][b]; moves[z["iso"]].append((z["sub"], z["carrier"], z["d_mwh"]))
        cem_t19, ez = None, None
        if cement:
            cem_t19 = {c: CI["cement_usgs_2019_t"][c] for c in ("MM", "KH", "LA", "BN")}
            if bn_cement == "iii":
                ez = ["BN"]
        extra = {c: {} for c in cm.C5}; prod_moves = {}
        if products:
            s0, ob0, pz0, _ = self.ch.run(ncv=ncv, moves=moves, cem_t19=cem_t19, edgar_zero=ez); self.n_runs += 1
            d1 = pd.read_csv(self.ch.chain / cm.ATS_REL, keep_default_na=False)
            used = {}   # (iso, row, carrier) -> MWh already taken by earlier products of this scenario
            for p in products:
                d = CI["products"][p]; iso, row = PROD_ROWS[p]
                el, fu = d["e2019_purchased_el"], d["e2019_purchased_fuel"]
                mv = []
                if row:   # same-name dispersed row first (its own carrier mix), excess to 'other'
                    rec = {r["carrier"]: r for r in self.cache0["records"] if r["country"] == iso}
                    avail = {}
                    for car in cm.FUELS:
                        if car in rec and row in rec[car]:
                            e19 = float(d1[(d1.country == iso) & (d1.sector == "Industry") & (d1.carrier == car)].base_2019_mwh.iloc[0])
                            tot = sum(float(v) for k, v in rec[car].items() if k not in ("country", "carrier"))
                            avail[car] = max(0.0, e19 * float(rec[car][row]) / tot - used.get((iso, row, car), 0.0))
                    at = sum(avail.values()); take = min(fu, at) * (1 - 1e-9)
                    for car, a in avail.items():
                        if take > 0 and at > 0:
                            mv.append((row, car, take * a / at)); used[(iso, row, car)] = used.get((iso, row, car), 0.0) + take * a / at
                    fu -= take
                mix = {k: float(ob0.at[iso, f"other_2019_{k}_mwh"]) for k in cm.FUELS}; mt = sum(mix.values())
                if fu > 0 and mt > 0:
                    for car in cm.FUELS:
                        if mix[car] > 0:
                            mv.append(("other", car, fu * mix[car] / mt))
                    fu = 0.0
                if el > 0:
                    mv.append(("other", "electricity", el))
                prod_moves[p] = dict(moves=mv, fuel_not_found_mwh=fu)
                moves[iso] += mv
                extra[iso][p] = d["v2050_counted"]
        s, ob, pz, gp = self.ch.run(ncv=ncv, moves=moves, cem_t19=cem_t19, edgar_zero=ez); self.n_runs += 1
        rule = cm.rule()
        out = []
        self.last_pz = pz[pz.country.isin(cm.C5)].copy(); self.last_gaps = gp[gp.country.isin(cm.C5)].copy(); self.last_parts = {}
        for c in cm.C5:
            iii = float(rule.at[c, "cement_2050_mt"]) * 1e6 if (cement and bn_cement == "iii" and c == "BN") else None
            L = self.layer(s, c, extra[c], iii)
            self.last_parts[c] = {k: dict(v) for k, v in L["parts"].items()}
            if "other" in self.last_parts[c]:
                self.last_parts[c]["other"] = dict(L["other"])
            r = dict(scenario=name, ncv_scheme=scheme, country=c, captive=captive or "", cement=("(iii)" if (cement and c == "BN" and bn_cement == "iii") else ("(ii)" if cement else "")),
                     products="+".join(p for p in products if p.startswith(c)), biomass="+".join(b for b in biomass if b.startswith(c)), note=note,
                     T_v2_2050_TWh=L["T"] / 1e6, other_2050_TWh=L["other_total"] / 1e6, other_share=(L["other_total"] / L["T"] if L["T"] > 0 else 0.0),
                     explicit_2050_TWh=L["explicit"] / 1e6, other_scale=L["scale"],
                     industry_2019_TWh=float(pd.read_csv(self.ch.chain / cm.ATS_REL).query("country == @c and sector == 'Industry'").base_2019_mwh.sum()) / 1e6,
                     other_2019_v2_TWh=float(ob.at[c, "other_2019_mwh"]) / 1e6 if c in ob.index else 0.0,
                     cement_2019_TWh=float(pz[(pz.country == c) & (pz.subsector == "cement")].mwh_2019.astype(float).sum()) / 1e6 if "mwh_2019" in pz.columns else float("nan"),
                     gaps_TWh=float(gp[gp.country == c].query("carrier != 'hydrogen'").mwh.sum()) / 1e6,
                     products_fuel_not_found_TWh=sum(v["fuel_not_found_mwh"] for k, v in prod_moves.items() if k.startswith(c)) / 1e6)
            for k in cm.OUTC:
                r[f"other_{cm.OUT_LABEL[k]}_TWh"] = L["other"].get(k, 0.0) / 1e6
            for k, v in L["by_sub"].items():
                r[f"sub_{k}_TWh"] = v / 1e6
            for car in cm.CARS19:
                r[f"other_2019_{car}_TWh"] = float(ob.at[c, f"other_2019_{car}_mwh"]) / 1e6 if c in ob.index else 0.0
            out.append(r)
        self.last_prod_moves = prod_moves
        return out


STEPS = [("0 v3", {}), ("1 ncv", {"ncv": True}), ("2 captive (b) central", {"ncv": True, "captive": "central"}),
         ("3 cement (ii) / BN (iii)", {"ncv": True, "captive": "central", "cement": True}),
         ("4 products (closed loop)", {"ncv": True, "captive": "central", "cement": True, "products": MAIN_PRODUCTS})]


def kw(scheme, k):
    return dict(scheme=(scheme if k.get("ncv") else "v3"), captive=k.get("captive"), cement=k.get("cement", False), products=k.get("products", ()))


def main():
    t0 = time.time(); R = Runner()
    rep = R.reproduce()
    for k, v in rep.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                EV.put(f"reproduction.{k}.{kk}", float(vv) if not isinstance(vv, bool) else str(vv), "MWh" if "mwh" in k else "-", "scratch copy /home/jin/v4w07_g4/chain vs worktree", "EXACT", "-")
        else:
            EV.put(f"reproduction.{k}", v, "MWh", "scratch copy vs worktree", "EXACT", "-")
    rows = []
    for scheme in ("v3", "207"):
        for name, k in STEPS:
            rr = R.scenario(name, **kw(scheme, k))
            for r in rr:
                r["ncv_scheme"] = scheme   # path label: step 0 of the 207 path is the v3 starting point
            rows += rr
            if scheme == "207" and name.startswith("4 ") or name.startswith("0 ") and scheme == "v3":
                tag = "main" if name.startswith("4 ") else "v3"
                pr = [dict(case=tag, country=c, subsector=sub, carrier=k, mwh_2050=v) for c, P in R.last_parts.items() for sub, d in P.items() for k, v in d.items() if abs(v) > 0]
                pd.DataFrame(pr).to_csv(cm.G4 / f"evidence/G4_PARTS_2050_{tag.upper()}.csv", index=False, float_format="%.6f")
                R.last_pz.to_csv(cm.G4 / f"evidence/G4_S3_SUBSECTORS_{tag.upper()}.csv", index=False, float_format="%.6f")
                R.last_gaps.to_csv(cm.G4 / f"evidence/G4_S3_GAPS_{tag.upper()}.csv", index=False, float_format="%.6f")
    prod_moves_main = R.last_prod_moves
    full = dict(scheme="207", captive="central", cement=True, products=MAIN_PRODUCTS)
    sens = [("S ncv sensitivity (MM 18.9; KH, LA children)", dict(full, scheme="sens")),
            ("S captive (a) none", dict(full, captive=None)), ("S captive mid", dict(full, captive="mid")), ("S captive high", dict(full, captive="high")),
            ("S BN cement (ii) instead of (iii)", dict(full, bn_cement="ii")),
            ("S products without copper", dict(full, products=["MM_paper", "MM_pulp", "LA_pulp"])),
            ("S LA paper R4 (2023 base) added", dict(full, products=MAIN_PRODUCTS + ["LA_paper_R4"])),
            ("S bagasse closed loop (MM, LA)", dict(full, biomass=("MM_bagasse_closed_loop", "LA_bagasse_closed_loop"))),
            ("S MM bagasse SDMX vintage (850 kt)", dict(full, biomass=("MM_bagasse_sdmx_vintage",))),
            ("S MM other vegetal residues 5150 added (9.42 TWh)", dict(full, biomass=("MM_ovr_5150_added",))),
            ("S MM fuelwood at SDMX 2022 level", dict(full, biomass=("MM_fuelwood_2022_sdmx_level",))),
            ("S KH fuelwood 2020-2022 mean", dict(full, biomass=("KH_fuelwood_2020_2022_mean",)))]
    for name, k in sens:
        rows += R.scenario(name, **k)
    singles = [("A ncv alone", dict(scheme="207")), ("A captive alone (v3 NCV)", dict(captive="central")), ("A cement alone", dict(cement=True)),
               ("A products alone", dict(products=MAIN_PRODUCTS))]
    for name, k in singles:
        rows += R.scenario(name, **k)
    D = pd.DataFrame(rows)
    D.to_csv(cm.G4 / "evidence/G4_SCENARIOS.csv", index=False, float_format="%.9g")
    # additivity (scheme 207 combined vs sum of single steps)
    base = D[(D.scenario == "0 v3") & (D.ncv_scheme == "v3")].set_index("country")
    comb = D[(D.scenario == "4 products (closed loop)") & (D.ncv_scheme == "207")].set_index("country")
    ad = []
    for c in cm.C5:
        sm = {q: sum(float(D[(D.scenario == n) & (D.country == c)][q].iloc[0]) - float(base.at[c, q]) for n, _ in singles) for q in ("T_v2_2050_TWh", "other_2050_TWh")}
        for q in ("T_v2_2050_TWh", "other_2050_TWh"):
            ad.append(dict(country=c, quantity=q, sum_of_single_steps=sm[q], combined=float(comb.at[c, q]) - float(base.at[c, q]),
                           difference=float(comb.at[c, q]) - float(base.at[c, q]) - sm[q]))
    A = pd.DataFrame(ad); A.to_csv(cm.G4 / "evidence/G4_ADDITIVITY.csv", index=False, float_format="%.9g")
    # <CC>_OTHER_SHARE_STEPS.csv (A6)
    grade = {"0 v3": "EXACT (repository)", "1 ncv": "EXACT chain; NCV B", "2 captive (b) central": "EXACT chain; C estimate C (INFERENCE)",
             "3 cement (ii) / BN (iii)": "EXACT chain; USGS 2019 C (estimate flags)", "4 products (closed loop)": "EXACT chain; activity B-C, unit energy C"}
    for c in cm.C5:
        z = D[D.country == c].copy()
        z = z[~z.scenario.str.startswith("A ")]
        prev = {}
        out = []
        for r in z.itertuples():
            key = r.ncv_scheme if not r.scenario.startswith("S ") else "S"
            if r.scenario.startswith("S "):
                ref = D[(D.country == c) & (D.scenario == "4 products (closed loop)") & (D.ncv_scheme == "207")].iloc[0]
                dlt = r.T_v2_2050_TWh - float(ref.T_v2_2050_TWh); dlo = r.other_2050_TWh - float(ref.other_2050_TWh)
            else:
                p = prev.get(key); dlt = r.T_v2_2050_TWh - (p.T_v2_2050_TWh if p is not None else r.T_v2_2050_TWh); dlo = r.other_2050_TWh - (p.other_2050_TWh if p is not None else r.other_2050_TWh)
                prev[key] = r
            out.append(dict(step=r.scenario, ncv_scheme=r.ncv_scheme, T_v2_2050_TWh=r.T_v2_2050_TWh, other_2050_TWh=r.other_2050_TWh, other_share=r.other_share,
                            delta_TWh=dlo, delta_T_v2_TWh=dlt, elec=r.other_elec_TWh, heat_lt150=r.other_heat_lt150_TWh, heat_150_200=r.other_heat_150_200_TWh,
                            heat_200_400=r.other_heat_200_400_TWh, heat_gt400=r.other_heat_gt400_TWh, oil=r.other_oil_TWh, gas=r.other_gas_TWh, coal=r.other_coal_TWh,
                            biomass=r.other_biomass_TWh, H2=r.other_H2_TWh, grade=grade.get(r.scenario, "EXACT chain; option PROPOSED (sensitivity)"),
                            delta_basis=("against the full main case (scheme 207)" if r.scenario.startswith("S ") else "against the previous step of the same scheme")))
        pd.DataFrame(out).to_csv(cm.G4 / f"{c}_OTHER_SHARE_STEPS.csv", index=False, float_format="%.6f")
    for r in D.itertuples():
        for q in ("T_v2_2050_TWh", "other_2050_TWh", "other_share", "industry_2019_TWh", "other_2019_v2_TWh", "gaps_TWh"):
            EV.put(f"{r.scenario}.{r.ncv_scheme}.{r.country}.{q}", getattr(r, q), "TWh" if q.endswith("TWh") else "-", "g4_chain.py scratch run (s3_0 + v3 layer)",
                   "EXACT", "-" if r.scenario.startswith("0") else "C")
    for r in A.itertuples():
        EV.put(f"additivity.{r.country}.{r.quantity}.difference", r.difference, "TWh", "combined minus sum of single steps", "EXACT", "-")
    EV.extra["product_moves_main_2019_mwh"] = prod_moves_main
    EV.extra["runs"] = R.n_runs; EV.extra["seconds"] = time.time() - t0
    EV.write(cm.G4 / "evidence/_chain_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    show = D[["scenario", "ncv_scheme", "country", "T_v2_2050_TWh", "other_2050_TWh", "other_share", "industry_2019_TWh", "other_2019_v2_TWh", "gaps_TWh"]]
    print(json.dumps(rep, indent=0, default=str)[:800])
    print(show[show.country != "TL"].round(4).to_string(index=False))
    print(A.round(5).to_string(index=False))
    print("runs", R.n_runs, "seconds", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
