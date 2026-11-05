"""V4 W07 G1 step 9 (Malaysia): combined quantification in the scratch copy of the data chain, under the v3 coal NCV and the decision-207 NCV.

    PYTHONHASHSEED=0 python scripts/v4g1_chain.py        (WSL pypsa-earth python; after v4g1_base / products / captive_ncv)

Steps (cumulative, growth mode I 'ATS industry multiplier unchanged'; every step reports MY T_v2 2050, the 'other' bucket 2050 and its carriers):
  0  v3 (reproduction).
  1  coal NCV: 'v3' scheme 25.8012 GJ/t (no change) | '207' scheme 26.394 GJ/t (UNSD SDMX): the UNSD NMM hard coal row (1,232.691 kt) is
     re-converted at UNSD row level (W11 section 4.2 item 5); it feeds the cement deduction.
  2  captive option (b): not triggered for MY (C = 0, E = 0).
  3  cement correction (ii): grinding electricity on USGS 2019 cement 16,102 kt (scratch-only patch of s3_0, env V4S2_CEM_EL_T19_MY).
  4  steel and primary aluminium: v3 rules kept (no change; aluminium 1,080 kt and kiln fuel are sensitivities).
  5  ammonia: the 2019 process fuel and electricity of the plants whose fuel is recorded in UNSD industry gas (Peninsular + Sabah, central) leave
     'other' (gas, electricity): the v3 ammonia product load already covers ammonia, so the fuel in 'other' is a duplicate.
  6  methanol (Labuan, energy use only): 2019 fuel + electricity leave 'other' (gas, electricity); 2050 explicit = activity x growth x the same
     energy-use intensity (no PyPSA-Eur energy-only methanol column; product rule 5.528 MWh/t as sensitivity).
  7  HVC (Titan, Kerteh crackers; PC Aromatics Kerteh): JRC-IDEES today energy use 3.269 MWh/t HVC leaves 'other' (fuel from gas, electricity);
     2050 = PyPSA-Eur HVC without naphtha (6.103 MWh/t).
  8  pulp and paper (FAOSTAT; closed-loop rule): 2019 energy leaves 'other' (electricity from electricity, fuel spread over the bucket's fuel mix);
     2050 = PyPSA-Eur ratios without the biomass rows (biomass reported as closed-loop, outside T_v2).
  9  lime (ETSAP 2018 x BAT): same spread rule; 2050 = BAT unchanged (gas, electricity).
 10  glass (no MY data) and biomass (closed-loop, no MY industrial biomass): no change.
Each new explicit sub-sector enters T_v2 with its 2050 vector; 'other' = T_v2 - explicit (D163-6 a). Additivity: single steps against the
combined result. Sensitivities on the combined 207 case: chemicals low / high, chemical fuel spread instead of gas, HVC electricity-only deduction,
methanol product rule, pulp and paper biomass counted, aluminium 1,080 kt, kiln fuel fully in the NMM coal row, W11 inferred NCV 28.544, R4 (PIC
2025, Sarawak Petchem 2023). Outputs tables/MY_CHAIN_SCENARIOS.csv, MY_OTHER_SHARE_STEPS.csv, MY_CHAIN_ADDITIVITY.csv, MY_SUBSECTORS_V4.csv,
tables/_chain_evidence.json. The scratch copy is restored afterwards; nothing is solved; the repository is not written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g1_common as cm   # noqa: E402

OUT = cm.G1 / "tables"
NMM = "non-metallic minerals"
HEAT_COLS = {"electricity": "elec", "heat": "heat_lt150", "heat_medium_a": "heat_150_200", "heat_medium_b": "heat_200_400", "heat_high": "heat_gt400",
             "oil": "oil", "gas": "gas", "coal": "coal", "biomass": "biomass", "hydrogen": "H2"}


class Runner:
    def __init__(self):
        self.v3 = cm.import_v3(); self.fut = self.v3.future_vectors(); self.ne = self.v3.nickel_unit_energy()
        self.nf_main = self.v3.nonferrous(self.fut, "main", self.ne)[0][cm.CC]
        self.nf_2023 = self.v3.nonferrous(self.fut, "nf2023", self.ne)[0][cm.CC]
        P = json.loads((OUT / "_products_evidence.json").read_text())["extra"]
        self.ci = P["chain_inputs"]
        cn = json.loads((OUT / "_captive_ncv_evidence.json").read_text())["extra"]
        self.d_coal = {"v3": 0.0, "207": cn["coal_delta_2019_mwh"], "w11": cn["coal_delta_2019_mwh_w11_inferred"]}
        # Sabah: NEB 2019 industry gas by region minus the central energy use of the Sabah chemical plants (methanol Labuan, ammonia Sipitang)
        neb = json.loads((OUT / "_base_evidence.json").read_text())["extra"]["neb_checks"]
        ce = pd.read_csv(OUT / "MY_CHEM_ENERGY.csv")
        sab = float(ce[(ce.region == "Sabah") & (ce.level == "central")].deduct_gas_2019_mwh.sum())
        self.sabah_resid = float(neb["industry_gas_twh_Sabah"]) * 1e6 - sab
        self.sabah_chem_gas = sab
        self.ch = cm.Chain(); self.ch.copy(); self.ch.patch()
        d1 = pd.read_csv(cm.REPO / cm.D1_REL, keep_default_na=False)
        self.e19_0 = float(d1[(d1.country == cm.CC) & (d1.sector == "Industry")].base_2019_mwh.astype(float).sum())

    def reproduce(self):
        row, ob, pz = self.ch.run()
        repo_row = pd.read_csv(cm.REPO / "research_inputs/demand_v5" / cm.SUMMARY).set_index("country").loc[cm.CC]
        dev = max(abs(float(row[self.v3.col(x)]) - float(repo_row[self.v3.col(x)])) for x in self.v3.CARRIERS)
        if dev > 1e-3:
            raise SystemExit(f"STOP: patched scratch copy without the environment variable does not reproduce the MY row ({dev} MWh)")
        return dev

    @staticmethod
    def spread(fuel, el, mix):
        ft = sum(mix[f] for f in cm.FUELS)
        out = {f: fuel * mix[f] / ft for f in cm.FUELS}; out["electricity"] = el
        return out

    def scenario(self, name, ncv="v3", cem=False, nh3=None, meoh=None, hvc=None, pp=False, lime=False, chem_rule="gas", hvc_el_only=False,
                 meoh_rule="energy_use", pp_bio=False, al="v3", kiln_in_nmm=False, r4=False, sabah_to_neu=False):
        moves = []
        if sabah_to_neu:   # sensitivity: the Sabah industry gas not explained by the explicit plants is chemical feedstock / energy-sector gas (to NEU, out of T_v2)
            moves.append(("other", "gas", self.sabah_resid))
        if self.d_coal[ncv]:
            moves.append((NMM, "coal", -self.d_coal[ncv]))
        if kiln_in_nmm:
            moves.append((NMM, "coal", -self.ci["cement_kiln_fuel_from_other_2019_mwh"]))
        cem_env = {cm.CC: self.ci["cement_usgs_2019_t"]} if cem else None
        chem_moves = {"gas": 0.0, "electricity": 0.0}
        for prod, lv in (("ammonia", nh3), ("methanol", meoh), ("olefins", hvc), ("aromatics", hvc)):
            if lv:
                m = self.ci["chem_moves_2019"][lv].get(prod, {})
                g = 0.0 if (prod in ("olefins", "aromatics") and hvc_el_only) else m.get("gas", 0.0)
                chem_moves["gas"] += g; chem_moves["electricity"] += m.get("electricity", 0.0)
        extra = {}
        if chem_rule == "gas":
            moves += [("other", c, v) for c, v in chem_moves.items() if v]
        pp_moves, lime_moves = {}, {}
        if chem_rule == "spread" or pp or lime:
            _, ob0, _ = self.ch.run(moves, cem_env)
            mix = {c: float(ob0[f"other_2019_{c}_mwh"]) for c in cm.CARS19}
            if chem_rule == "spread" and sum(chem_moves.values()):
                cm_ = self.spread(chem_moves["gas"], chem_moves["electricity"], mix); moves += [("other", c, v) for c, v in cm_.items() if v]
                mix = {c: mix[c] - cm_.get(c, 0.0) for c in mix}
            if pp:
                pp_moves = self.spread(self.ci["pp_2019"]["fuel"], self.ci["pp_2019"]["electricity"], mix); moves += [("other", c, v) for c, v in pp_moves.items() if v]
                mix = {c: mix[c] - pp_moves.get(c, 0.0) for c in mix}
            if lime:
                lime_moves = self.spread(self.ci["lime_2019"]["fuel"], self.ci["lime_2019"]["electricity"], mix); moves += [("other", c, v) for c, v in lime_moves.items() if v]
        row, ob, pz = self.ch.run(moves, cem_env)
        if meoh:
            extra["methanol"] = dict(self.ci["chem_2050"][meoh]["methanol" if meoh_rule == "energy_use" else "methanol_product_rule"])
        if hvc:
            extra["hvc"] = dict(self.ci["chem_2050"][hvc]["hvc"])
        if pp:
            extra["pulp_paper"] = dict(self.ci["pp_2050"]["biomass_as_purchased" if pp_bio else "main"])
        if lime:
            extra["lime"] = dict(self.ci["lime_2050"])
        if r4:
            extra["r4_pic_2025"] = dict(self.ci["chem_2050_r4"]["pic_2025"]); extra["r4_sarawak_petchem_2023"] = dict(self.ci["chem_2050_r4"]["sarawak_petchem_2023"])
        nf = dict(self.nf_main)
        if al == "capacity":
            nf["nonferrous_aluminium_primary"] = dict(self.nf_2023["nonferrous_aluminium_primary"])
        L = cm.v3_layer(self.v3, row, self.fut, nf, extra)
        moved19 = {c: 0.0 for c in cm.CARS19}
        for s_, c, v in moves:
            if s_ == "other":
                moved19[c] += v
        r = dict(scenario=name, ncv=ncv, cement_ii=cem, ammonia=nh3 or "", methanol=meoh or "", hvc=hvc or "", pulp_paper=pp, lime=lime, chem_rule=chem_rule,
                 hvc_el_only=hvc_el_only, methanol_rule=meoh_rule if meoh else "", pp_biomass_counted=pp_bio, aluminium=al, kiln_in_nmm=kiln_in_nmm, r4=r4,
                 industry_2019_twh=(self.e19_0 + sum(-v for s_, c, v in moves if s_ == NMM)) / 1e6,   # statistical 2019 industry total (NCV / kiln-coal edits only)
                 d1_base_after_moves_twh=(self.e19_0 - sum(v for s_, c, v in moves)) / 1e6,          # chain base after the explicit products left 'other'
                 other_2019_v2_twh=float(ob.other_2019_mwh) / 1e6,
                 T_2050_twh=L["T"] / 1e6, other_2050_twh=L["other_total"] / 1e6, other_share=L["other_total"] / L["T"], other_scale=L["scale"], explicit_2050_twh=L["explicit"] / 1e6,
                 cement_2019_twh=float(pz[pz.subsector == "cement"].mwh_2019.astype(float).sum()) / 1e6, steel_2019_twh=float(pz[pz.subsector == "iron and steel"].mwh_2019.astype(float).sum()) / 1e6)
        for k in cm.OUTC:
            r[f"other_2050_{k}_twh"] = L["other"].get(k, 0.0) / 1e6
        for k, v in L["by_sub"].items():
            r[f"sub_2050_{k}_twh"] = v / 1e6
        for c in cm.CARS19:
            r[f"other_2019_{c}_twh"] = float(ob[f"other_2019_{c}_mwh"]) / 1e6
            r[f"moved_from_other_2019_{c}_twh"] = moved19[c] / 1e6
        r["_explicit_carriers"] = L["explicit_carriers"]
        return r


def main():
    R = Runner(); ev = cm.Ev("chain")
    dev = R.reproduce(); ev.put("reproduction.patched_no_env_max_abs_dev_mwh", dev, "MWh", "scratch chain with the cement patch, no environment variable, vs repository", "EXACT", "-")
    steps = [("0 v3", {}), ("1 coal NCV", {}), ("2 captive (b): not triggered", {}), ("3 cement (ii)", dict(cem=True)), ("4 steel, aluminium: v3 rules kept", {}),
             ("5 ammonia fuel duplicate removed", dict(nh3="central")), ("6 methanol explicit", dict(meoh="central")), ("7 HVC explicit", dict(hvc="central")),
             ("8 pulp and paper (closed-loop)", dict(pp=True)), ("9 lime", dict(lime=True)), ("10 glass (no data), biomass (closed-loop)", {})]
    S, cum = [], {}
    for ncv in ("v3", "207"):
        cum = {}
        for i, (nm, kw) in enumerate(steps):
            cum.update(kw)
            S.append(R.scenario(f"{nm}", ncv=("v3" if i == 0 else ncv), **cum) | {"sequence": ncv, "step": i})
    # single steps (207 scheme, each on top of '1 coal NCV') and additivity
    singles = [R.scenario(f"single {k}", ncv="207", **kw) | {"sequence": "single", "step": -1} for k, kw in
               (("cement (ii)", dict(cem=True)), ("ammonia", dict(nh3="central")), ("methanol", dict(meoh="central")), ("HVC", dict(hvc="central")),
                ("pulp and paper", dict(pp=True)), ("lime", dict(lime=True)))]
    ALL = dict(cem=True, nh3="central", meoh="central", hvc="central", pp=True, lime=True)
    sens = [R.scenario(f"sens {k}", ncv=n, **(ALL | kw)) | {"sequence": "sensitivity", "step": -1} for k, n, kw in
            (("chemicals low", "207", dict(nh3="low", meoh="low", hvc="low")), ("chemicals high", "207", dict(nh3="high", meoh="high", hvc="high")),
             ("chemical fuel spread over the bucket mix", "207", dict(chem_rule="spread")), ("HVC: electricity-only deduction (cracker fuel self-produced)", "207", dict(hvc_el_only=True)),
             ("methanol product rule 5.528 MWh/t", "207", dict(meoh_rule="product")), ("pulp and paper biomass counted as purchased heat", "207", dict(pp_bio=True)),
             ("aluminium at capacity 1,080 kt", "207", dict(al="capacity")), ("kiln fuel fully in the NMM coal row (+5.72 TWh coal 2019)", "207", dict(kiln_in_nmm=True)),
             ("NCV W11 inferred 28.544", "w11", {}), ("R4: PIC 2025 and Sarawak Petchem 2023", "207", dict(r4=True)), ("no cement (ii)", "207", dict(cem=False)),
             ("Sabah unexplained industry gas to NEU", "207", dict(sabah_to_neu=True)))]
    ev.put("sabah.industry_gas_minus_chem_central_2019", R.sabah_resid / 1e6, "TWh", "NEB 2019 table 7 Sabah share x UNSD industry gas, minus the central gas energy use of the Labuan methanol and Sipitang ammonia plants", "INFERENCE", "C")
    ev.put("sabah.chem_gas_central_2019", R.sabah_chem_gas / 1e6, "TWh", "tables/MY_CHEM_ENERGY.csv (Sabah, central)", "PROPOSED (quantified)", "C")
    R.ch.restore(); R.ch.unpatch()
    D = pd.DataFrame(S + singles + sens)
    expl = D.pop("_explicit_carriers")
    base = D.iloc[0]
    for c in [c for c in D.columns if c.endswith("_twh")]:
        D[f"d_{c}"] = D[c] - float(base[c])
    D["d_other_share_pp"] = (D.other_share - float(base.other_share)) * 100
    D.to_csv(OUT / "MY_CHAIN_SCENARIOS.csv", index=False, float_format="%.6f")
    # ---- A6 steps table
    rows = []
    for seq in ("v3", "207"):
        z = D[D.sequence == seq].sort_values("step")
        prev = None
        for r in z.itertuples():
            d = dict(country=cm.CC, step=r.scenario, ncv_scheme=seq, T_v2_2050_TWh=r.T_2050_twh, other_2050_TWh=r.other_2050_twh, other_share=r.other_share,
                     delta_TWh=(r.other_2050_twh - prev) if prev is not None else 0.0, delta_T_v2_TWh=(r.T_2050_twh - prevT) if prev is not None else 0.0)
            for k, col in HEAT_COLS.items():
                d[col] = getattr(r, f"other_2050_{k}_twh")
            d["grade"] = "EXACT (chain run); C" if r.step == 0 else "PROPOSED (quantified); C"
            rows.append(d); prev = r.other_2050_twh; prevT = r.T_2050_twh
    ST = pd.DataFrame(rows); ST.to_csv(OUT / "MY_OTHER_SHARE_STEPS.csv", index=False, float_format="%.6f")
    # ---- additivity (207 scheme): single steps (each on top of the NCV step) vs combined
    ncv_row = D[(D.sequence == "207") & (D.step == 1)].iloc[0]; comb = D[(D.sequence == "207") & (D.step == 10)].iloc[0]
    sg = D[D.sequence == "single"]
    cols = ["T_2050_twh", "other_2050_twh"] + [f"other_2050_{k}_twh" for k in cm.OUTC] + ["other_2019_v2_twh"]
    A = [dict(quantity=c, sum_of_single_steps_twh=float((sg[c] - float(ncv_row[c])).sum()), combined_twh=float(comb[c] - float(ncv_row[c])),
              non_additive_twh=float(comb[c] - float(ncv_row[c])) - float((sg[c] - float(ncv_row[c])).sum())) for c in cols]
    AD = pd.DataFrame(A); AD.to_csv(OUT / "MY_CHAIN_ADDITIVITY.csv", index=False, float_format="%.6f")
    # ---- evidence
    for r in D.itertuples():
        for k in ("T_2050_twh", "other_2050_twh", "other_share", "d_T_2050_twh", "d_other_2050_twh", "d_other_share_pp", "other_2019_v2_twh", "industry_2019_twh",
                  "d_other_2050_electricity_twh", "d_other_2050_heat_high_twh", "d_other_2050_heat_medium_b_twh", "d_other_2050_heat_medium_a_twh", "d_other_2050_heat_twh", "d_other_2050_oil_twh"):
            ev.put(f"{r.sequence}.{r.scenario}.{k}", getattr(r, k), "-" if k == "other_share" else ("pp" if k.endswith("pp") else "TWh"), "tables/MY_CHAIN_SCENARIOS.csv (scratch chain)",
                   "EXACT" if (r.sequence == "v3" and r.step == 0) else "PROPOSED (quantified)", "C")
    for r in AD.itertuples():
        ev.put(f"additivity.{r.quantity}", r.non_additive_twh, "TWh", "combined - sum of single steps (207 scheme, relative to the NCV step)", "EXACT", "C")
    # ---- A6 sub-sector table for the main combined case (207 scheme, central)
    ex = expl[(D.sequence == "207") & (D.step == 10)].iloc[0]
    P = json.loads((OUT / "_products_evidence.json").read_text())
    pv = {x["key"]: x["value"] for x in P["numbers"]}
    pz = comb  # scenario row
    meta = {
        "steel": ("DRI + EAF (30 % H2-DRI) / scrap EAF (PyPSA-Eur 2050)", "worldsteel 2024 (2050 base); worldsteel 2019 (2019 deduction)", 2024, 9014.144, 14641.43, "JRC-IDEES today (2019) / PyPSA-Eur 2050",
                  f"{comb.steel_2019_twh:.2f} TWh: UNSD iron-and-steel row (blast furnace gas 4.39) + excess from 'other'", "B"),
        "cement": ("Cement (PyPSA-Eur 2050)", "USGS 2023 (2050 base); EDGAR 2.A.1 / 0.52 / 0.656 (2019 deduction)", 2023, 23191.0, 38377.86, "PyPSA-Eur Cement 0.8655 MWh/t",
                   f"{comb.cement_2019_twh:.2f} TWh: UNSD NMM coal first, rest from 'other' (correction ii applied)", "B/C"),
        "ammonia": ("Ammonia product load 5.166 MWh_NH3/t (v3, DFX F2)", "USGS MYB 2022 Nitrogen T12 2019", 2019, 1457.14, 2598.20, "PyPSA-Eur Ammonia",
                    f"{pv['products.chem.ammonia.central.deduct_gas_2019_mwh'] + pv['products.chem.ammonia.central.deduct_el_2019_mwh']:.2f} TWh fuel + electricity of the Peninsular and Sabah plants (duplicate in 'other' removed)", "B/C"),
        "nonferrous_aluminium_primary": ("Aluminium - primary production (PyPSA-Eur 2050)", "USGS 2017-18 Asia-Pacific estimate (2018 used for 2019)", 2018, 750.0, None, "PyPSA-Eur 2050 ratio",
                                         "none (v3 conservation at 2050)", "C"),
        "methanol": ("energy use only (2019 intensity held)", "GEM 2026-11 capacity 2019 x 0.85", 2019, pv["products.chem.methanol.central.activity_2019_t"] / 1e3, None,
                     "PyPSA-Eur today 10.25 MWh CH4/t minus ETSAP feedstock 5.47; electricity 0.167", f"{pv['products.chem.methanol.central.deduct_gas_2019_mwh'] + pv['products.chem.methanol.central.deduct_el_2019_mwh']:.2f} TWh from 'other' (gas, electricity)", "C"),
        "hvc": ("HVC without naphtha (PyPSA-Eur 2050, 6.103 MWh/t)", "ETSAP 2018 olefins 1,949 kt x HVC/olefins (GEM); aromatics GEM capacity x 0.85", 2018,
                (pv["products.chem.olefins.central.activity_2019_t"] + pv["products.chem.aromatics.central.activity_2019_t"]) / 1e3, None, "JRC-IDEES today 3.269 MWh/t HVC (energy use)",
                f"{sum(pv[f'products.chem.{p}.central.deduct_{c}_2019_mwh'] for p in ('olefins', 'aromatics') for c in ('gas', 'el')):.2f} TWh from 'other' (gas, electricity)", "C"),
        "pulp_paper": ("Pulp / Paper production (PyPSA-Eur 2050) without biomass rows", "FAOSTAT FO (last year with new information; case materials 2024 E)", 2024, None, None,
                       "JRC-IDEES today (pulp 3.567, paper 2.581 MWh/t)", f"{(R.ci['pp_2019']['electricity'] + R.ci['pp_2019']['fuel']) / 1e6:.2f} TWh from 'other' (spread)", "C"),
        "lime": ("ETSAP BAT (no PyPSA-Eur lime sector)", "ETSAP v2.1.0 production 2018", 2018, 1447.0, 2628.70, "ETSAP BAT 1.242 MWh/t",
                 f"{(R.ci['lime_2019']['fuel'] + R.ci['lime_2019']['electricity']) / 1e6:.2f} TWh from 'other' (spread)", "C"),
        "dispersed": ("UNSD sub-sector rows x EU27 weights", "UNSD 2019", 2019, None, None, "-", "MY has no UNSD sub-sector row with energy except NMM coal (used by cement)", "B")}
    sub = []
    for k, v in ex.items():
        mt = meta.get(k, ("", "", None, None, None, "", "", "C"))
        cars = {c: v.get(c, 0.0) / 1e6 for c in cm.OUTC}
        sub.append(dict(country=cm.CC, subsector=k, route=mt[0], activity_source=mt[1], base_year=mt[2], activity_base_kt=mt[3], activity_2050_kt=mt[4], sec_source=mt[5],
                        energy_2019_deducted=mt[6], deducted_from_row="other" if k in ("methanol", "hvc", "pulp_paper", "lime", "ammonia") else ("UNSD row + other" if k in ("steel", "cement") else "-"),
                        energy_2050_TWh=sum(cars.values()), **{f"{c}_TWh": x for c, x in cars.items()},
                        closed_loop_biomass_TWh=(R.ci["pp_closed_loop_biomass_2050_mwh"] / 1e6 if k == "pulp_paper" else 0.0), grade=mt[7]))
    oth = {c: comb[f"other_2050_{c}_twh"] for c in cm.OUTC}
    sub.append(dict(country=cm.CC, subsector="other", route="useful heat bands + electricity + diesel engines (v3 'other' rule)", activity_source="residual: T_v2 - explicit (D163-6 a)",
                    base_year=2019, sec_source="JRC-IDEES OIS process shares x 0.90", energy_2019_deducted="-", deducted_from_row="-", energy_2050_TWh=comb.other_2050_twh,
                    **{f"{c}_TWh": x for c, x in oth.items()}, closed_loop_biomass_TWh=0.0, grade="C"))
    SB = pd.DataFrame(sub); SB.to_csv(OUT / "MY_SUBSECTORS_V4.csv", index=False, float_format="%.6f")
    ev.extra.update(steps=ST.to_dict("records"))
    ev.write(OUT / "_chain_evidence.json")
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 60)
    print(D[["sequence", "scenario", "industry_2019_twh", "other_2019_v2_twh", "T_2050_twh", "d_T_2050_twh", "other_2050_twh", "d_other_2050_twh", "other_share"]].round(3).to_string())
    print(ST[["step", "ncv_scheme", "T_v2_2050_TWh", "other_2050_TWh", "other_share", "delta_TWh"]].round(3).to_string())
    print(AD.round(4).to_string()); print(SB[["subsector", "energy_2050_TWh", "electricity_TWh", "gas_TWh", "biomass_TWh", "hydrogen_TWh", "closed_loop_biomass_TWh"]].round(3).to_string())


if __name__ == "__main__":
    main()
