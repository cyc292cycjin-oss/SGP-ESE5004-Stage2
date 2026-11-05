"""V4 S2 section 1: the confirmed corrections quantified together in a scratch copy of the data chain (outside the repository).

    PYTHONHASHSEED=0 python scripts/v4s2_chain.py          (WSL pypsa-earth python)

Steps (decisions 203, 204), each reported as ID T_v2 2050, the 'other' bucket 2050 (TWh and share of T_v2) and the carrier changes:
  1  captive coal option (b), central 75.89 TWh (low 60.63 / mid 96.08 as sensitivities): C leaves the UNSD 'other' coal of 2019, eta*C enters as
     'other' electricity, ATS multiplier unchanged (S1 section 1.8; C and E from s1/ID_CAPTIVE_COAL_2019.csv).
  2  nickel on the 2023 base, nickel only (USGS 2023 Ni content x G^((2050-2023)/28 x 0.5) x Wei 2020 Case 3), the other non-ferrous stay on 2019;
     NIUPPER (26 MWh/t NPI gross) as a sensitivity.
  3  cement correction (ii): kiln fuel on EDGAR clinker (unchanged), grinding electricity on USGS 2019 cement 71.9 Mt (scratch-only patch, see
     v4s2_common.py).
  4  steel: national total unchanged, spatial allocation only (scripts/v4s2_steel.py) - no effect on T_v2 or 'other'.
  5  products of section 2: pulp and paper (2019 energy leaves 'other' by the s3_0 rule for a product without a UNSD row: electricity from
     electricity, fuel spread over the bucket's fuel mix; 2050 = FAOSTAT activity x PyPSA-Eur 2050 ratios, explicit) and ethylene (2019 energy
     use leaves the UNSD chemicals row, same spread rule on that row; 2050 = PyPSA-Eur HVC without naphtha, explicit).
Combined result, sum of single steps against the combined result (non-additivity), sensitivities (captive low / mid, pulp biomass-first, pulp
literal-2024 base, ethylene low / high and 2025 base, NIUPPER). The unmodified copy must reproduce the repository ID row bit for bit first.
Outputs s2/ID_S2_COMBINED.csv, s2/ID_S2_ADDITIVITY.csv, s2/_chain_evidence.json. Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s2_common as cm   # noqa: E402

USGS_CEMENT_2019_T = 71.9e6   # USGS MYB 2023 Indonesia table 1 (S1 _facilities_evidence usgs.cement_kt 2019)
CHEM = "chemical and petrochemical"


class Runner:
    def __init__(self):
        self.v3 = cm.import_v3()
        self.fut = self.v3.future_vectors(); self.ne = self.v3.nickel_unit_energy()
        self.nf_main = self.v3.nonferrous(self.fut, "main", self.ne)[0]["ID"]
        self.nf_2023 = self.v3.nonferrous(self.fut, "nf2023", self.ne)[0]["ID"]
        sc = (self.v3.NI_UPPER_MWH_PER_T_NPI / self.v3.NI_NPI_NI_FRACTION) / (self.ne["electricity_mwh_per_t_ni"] + self.ne["fuel_mwh_per_t_ni"])
        self.niupper_scale = sc
        E = pd.read_csv(cm.WORK / "s1/ID_CAPTIVE_COAL_2019.csv"); tot = E[E.group == "合计"].set_index("level")
        self.captive = {lv: (float(tot.at[lv, "coal_in_industry_twh_model"]) * 1e6, float(tot.at[lv, "gen_in_industry_gwh"]) * 1e3) for lv in ("low", "central", "mid", "high")}
        self.prod = json.loads((cm.WORK / "s2/_products_evidence.json").read_text())["extra"]["chain_inputs"]
        self.ch = cm.Chain(); self.ch.copy()
        cache = json.loads(self.ch.orig["cache"]); d1 = pd.read_csv(cm.REPO / cm.D1_REL, keep_default_na=False)
        d1 = d1[(d1.country == "ID") & (d1.sector == "Industry")].set_index("carrier").base_2019_mwh.astype(float)
        self.e19_0 = float(d1.sum())
        self.chem19 = {}
        for r in cache["records"]:
            if r["country"] == "ID":
                tot_c = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
                self.chem19[r["carrier"]] = float(d1[r["carrier"]]) * float(r[CHEM]) / tot_c
        self.repro = None

    def reproduce(self):
        row, ob, pz = self.ch.run()
        repo_row = pd.read_csv(cm.REPO / "research_inputs/demand_v5" / cm.SUMMARY).set_index("country").loc["ID"]
        dev = max(abs(float(row[self.v3.col(x)]) - float(repo_row[self.v3.col(x)])) for x in self.v3.CARRIERS)
        L = cm.v3_layer(self.v3, row, self.fut, self.nf_main)
        sub = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
        sub = sub[(sub.case == "main") & (sub.country == "ID") & (sub.subsector == "other")].set_index("carrier").mwh_2050
        dev3 = max(abs(L["other"].get(k, 0.0) - float(sub.get(k, 0.0))) for k in L["other"])
        self.ch.patch(); row_p, _, _ = self.ch.run()
        dev_p = max(abs(float(row_p[self.v3.col(x)]) - float(row[self.v3.col(x)])) for x in self.v3.CARRIERS)
        self.repro = dict(max_abs_dev_T_carriers_mwh=dev, max_abs_dev_v3_other_mwh=dev3, max_abs_dev_patched_no_env_mwh=dev_p, T_v2_twh=L["T"] / 1e6, other_twh=L["other_total"] / 1e6)
        if dev > 1e-3 or dev3 > 1e-3 or dev_p > 1e-3:
            raise SystemExit(f"STOP: the unmodified scratch copy does not reproduce the repository ID row ({self.repro})")
        return self.repro

    @staticmethod
    def spread(fuel_mwh, el_mwh, mix):
        """s3_0_industry spread(): fuel over the bucket's fuel mix, electricity separately."""
        ft = sum(mix[f] for f in cm.FUELS)
        out = {f: fuel_mwh * mix[f] / ft for f in cm.FUELS}; out["electricity"] = el_mwh
        return out

    def scenario(self, name, b=None, ni=None, cem=False, steel=False, prod=None, pp_case="main", pp_rule="spread", eth_level="central", eth_base2025=False, extra_moves=None):
        moves = list(extra_moves or [])
        if b:
            C, E = self.captive[b]; moves += [("other", "coal", C), ("other", "electricity", -E)]
        cem_env = {"ID": USGS_CEMENT_2019_T} if cem else None
        extra, pp_moves, eth_moves = {}, {}, {}
        if prod:
            _, ob0, _ = self.ch.run(moves, cem_env)   # bucket after the earlier steps
            mix = {c: float(ob0[f"other_2019_{c}_mwh"]) for c in cm.CARS19}
            el, fu = self.prod["pp_2019_electricity_mwh"], self.prod["pp_2019_fuel_mwh"]
            if pp_rule == "spread":
                pp_moves = self.spread(fu, el, mix)
            elif pp_rule == "biomass_first":   # fuel taken from the bucket's biomass first (the UNSD fuelwood row), rest spread
                tb = min(fu, mix["biomass"]); rest = fu - tb
                m2 = dict(mix); m2["biomass"] = 0.0
                pp_moves = self.spread(rest, el, m2); pp_moves["biomass"] = pp_moves.get("biomass", 0.0) + tb
            moves += [("other", c, v) for c, v in pp_moves.items()]
            eq = self.prod["eth"][eth_level]
            eth_moves = self.spread(eq["d19_mwh"] * (1 - eq["el_share"]), eq["d19_mwh"] * eq["el_share"], self.chem19)
            moves += [(CHEM, c, v) for c, v in eth_moves.items()]
            extra["pulp_paper"] = {k: float(v) for k, v in self.prod["pp_2050"][pp_case].items()}
            extra["ethylene"] = {k: 0.0 for k in cm.OUTC}
            for k, v in (self.prod["eth_base2025_v2050"] if eth_base2025 else eq["v2050"]).items():
                extra["ethylene"][k] += float(v)
        row, ob, pz = self.ch.run(moves, cem_env)
        nf = dict(self.nf_main)
        if ni:
            nk = dict(self.nf_2023["nonferrous_nickel"])
            if ni == "niupper":
                nk = {k: v * self.niupper_scale for k, v in nk.items()}
            nf["nonferrous_nickel"] = nk
        L = cm.v3_layer(self.v3, row, self.fut, nf, extra)
        C_, E_ = self.captive[b] if b else (0.0, 0.0)
        r = dict(scenario=name, captive=b or "", nickel=ni or "", cement_ii=cem, steel_spatial=steel, products=bool(prod), pp_case=pp_case if prod else "",
                 pp_rule=pp_rule if prod else "", eth_level=(("2025 base" if eth_base2025 else eth_level) if prod else ""),
                 industry_2019_twh=(self.e19_0 - C_ + E_) / 1e6, other_2019_v2_twh=float(ob.other_2019_mwh) / 1e6,
                 T_2050_twh=L["T"] / 1e6, other_2050_twh=L["other_total"] / 1e6, other_share=L["other_total"] / L["T"], other_scale=L["scale"],
                 explicit_2050_twh=L["explicit"] / 1e6, cement_2019_twh=float(pz[pz.subsector == "cement"].mwh_2019.astype(float).sum()) / 1e6)
        for k in cm.OUTC:
            r[f"other_2050_{k}_twh"] = L["other"].get(k, 0.0) / 1e6
        for k, v in L["by_sub"].items():
            r[f"sub_2050_{k}_twh"] = v / 1e6
        for c in cm.CARS19:
            r[f"other_2019_{c}_twh"] = float(ob[f"other_2019_{c}_mwh"]) / 1e6
            r[f"pp_move_2019_{c}_twh"] = pp_moves.get(c, 0.0) / 1e6
            r[f"eth_move_2019_{c}_twh"] = eth_moves.get(c, 0.0) / 1e6
        return r


def main():
    R = Runner(); ev = cm.Ev("1")
    rep = R.reproduce()
    for k, v in rep.items():
        ev.put(f"reproduction.{k}", v, "MWh" if k.endswith("mwh") else "TWh", "scratch copy /home/jin/v4s2/chain vs repository", "EXACT", "-")
    S = [R.scenario("v3"),
         R.scenario("1 captive b central", b="central"),
         R.scenario("2 nickel 2023", ni="nf2023"),
         R.scenario("3 cement ii", cem=True),
         R.scenario("4 steel spatial", steel=True),
         R.scenario("5 products", prod=True),
         R.scenario("1+2", b="central", ni="nf2023"),
         R.scenario("1+2+3", b="central", ni="nf2023", cem=True),
         R.scenario("1+2+3+4", b="central", ni="nf2023", cem=True, steel=True),
         R.scenario("all (1-5)", b="central", ni="nf2023", cem=True, steel=True, prod=True),
         R.scenario("all, captive low", b="low", ni="nf2023", cem=True, steel=True, prod=True),
         R.scenario("all, captive mid", b="mid", ni="nf2023", cem=True, steel=True, prod=True),
         R.scenario("all, nickel NIUPPER", b="central", ni="niupper", cem=True, steel=True, prod=True),
         R.scenario("all, pulp fuel biomass-first", b="central", ni="nf2023", cem=True, steel=True, prod=True, pp_rule="biomass_first"),
         R.scenario("all, pulp/paper literal 2024 base", b="central", ni="nf2023", cem=True, steel=True, prod=True, pp_case="literal2024"),
         R.scenario("all, ethylene low", b="central", ni="nf2023", cem=True, steel=True, prod=True, eth_level="low"),
         R.scenario("all, ethylene high", b="central", ni="nf2023", cem=True, steel=True, prod=True, eth_level="high"),
         R.scenario("all, ethylene 2025 base incl. LINE", b="central", ni="nf2023", cem=True, steel=True, prod=True, eth_base2025=True)]
    R.ch.restore(); R.ch.unpatch()   # leave the scratch copy unmodified
    D = pd.DataFrame(S)
    base = D.iloc[0]
    for c in [c for c in D.columns if c.endswith("_twh")]:
        D[f"d_{c}"] = D[c] - float(base[c])
    D["d_other_share_pp"] = (D.other_share - float(base.other_share)) * 100
    D.to_csv(cm.WORK / "s2/ID_S2_COMBINED.csv", index=False, float_format="%.6f")
    # ---- additivity: sum of single steps vs combined
    singles = D[D.scenario.str.match(r"^[1-5] ")]; comb = D[D.scenario.eq("all (1-5)")].iloc[0]
    cols = ["T_2050_twh", "other_2050_twh"] + [f"other_2050_{k}_twh" for k in cm.OUTC] + ["other_2019_v2_twh"]
    A = []
    for c in cols:
        s = float(singles[f"d_{c}"].sum()); x = float(comb[f"d_{c}"])
        A.append(dict(quantity=c, sum_of_single_steps_twh=s, combined_twh=x, non_additive_twh=x - s))
    for pair, a_, b_ in (("1x2", "1 captive b central", "2 nickel 2023"), ("1x3", "1 captive b central", "3 cement ii"), ("1x5", "1 captive b central", "5 products")):
        za = D[D.scenario.eq(a_)].iloc[0]; zb = D[D.scenario.eq(b_)].iloc[0]
        nm = {"1x2": "1+2"}.get(pair)
        if nm:
            zc = D[D.scenario.eq(nm)].iloc[0]
            for c in cols:
                A.append(dict(quantity=f"pair {pair}: {c}", sum_of_single_steps_twh=float(za[f"d_{c}"] + zb[f"d_{c}"]), combined_twh=float(zc[f"d_{c}"]),
                              non_additive_twh=float(zc[f"d_{c}"] - za[f"d_{c}"] - zb[f"d_{c}"])))
    AD = pd.DataFrame(A); AD.to_csv(cm.WORK / "s2/ID_S2_ADDITIVITY.csv", index=False, float_format="%.6f")
    for r in D.itertuples():
        for k in ("T_2050_twh", "other_2050_twh", "other_share", "d_T_2050_twh", "d_other_2050_twh", "d_other_share_pp", "other_2019_v2_twh", "industry_2019_twh",
                  "d_other_2050_electricity_twh", "d_other_2050_heat_high_twh", "d_other_2050_heat_medium_b_twh", "d_other_2050_heat_medium_a_twh", "d_other_2050_heat_twh",
                  "d_other_2050_coal_twh", "d_other_2050_oil_twh", "d_other_2050_gas_twh", "d_other_2050_biomass_twh"):
            ev.put(f"scenario.{r.scenario}.{k}", getattr(r, k), "-" if k == "other_share" else ("pp" if k.endswith("pp") else "TWh"), "s2/ID_S2_COMBINED.csv (scratch chain)",
                   "EXACT" if r.scenario == "v3" else "PROPOSED (quantified)", "C")
    for r in AD.itertuples():
        ev.put(f"additivity.{r.quantity}", r.non_additive_twh, "TWh", "s2/ID_S2_ADDITIVITY.csv (combined - sum of single steps)", "EXACT", "C")
    ev.put("cement_ii.delta_cement_2019", float(D[D.scenario.eq("3 cement ii")].cement_2019_twh.iloc[0] - base.cement_2019_twh), "TWh", "scratch chain (S1 analytic -1.52)", "EXACT", "C")
    ev.put("nickel.niupper_scale", R.niupper_scale, "-", "v3_industry NIUPPER: 26 MWh/t NPI gross / (Wei el + fuel per t Ni)", "EXACT", "C")
    ev.put("nickel.2050_nf2023_twh", sum(R.nf_2023["nonferrous_nickel"].values()) / 1e6, "TWh", "v3_industry.nonferrous nf2023 (nickel only)", "EXACT", "C")
    ev.put("nickel.2050_main_twh", sum(R.nf_main["nonferrous_nickel"].values()) / 1e6, "TWh", "v3_industry.nonferrous main", "EXACT", "C")
    ev.put("chem19_total_twh", sum(R.chem19.values()) / 1e6, "TWh", "UNSD chemicals row of ID in the D1 base (cache shares x D1)", "EXACT", "B")
    ev.extra.update(reproduction=rep, patch=dict(old=cm.PATCH_OLD, new=cm.PATCH_NEW), chem19_mwh=R.chem19, captive=R.captive)
    ev.write(cm.WORK / "s2/_chain_evidence.json")
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 40)
    print(json.dumps(rep))
    print(D[["scenario", "industry_2019_twh", "other_2019_v2_twh", "T_2050_twh", "d_T_2050_twh", "other_2050_twh", "d_other_2050_twh", "other_share", "d_other_share_pp"]].round(3).to_string())
    print(D[["scenario"] + [f"d_other_2050_{k}_twh" for k in ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass")]].round(2).to_string())
    print(AD.round(4).to_string())
    print(D[["scenario"] + [c for c in D.columns if c.startswith("pp_move") or c.startswith("eth_move")]].iloc[[5, 9, 13]].round(3).T.to_string())


if __name__ == "__main__":
    main()
