"""W19a section 5: registry re-count by grade on the W14 package COMMIT, against the W10 baseline (aad8e476).

Definitions as in W10 (work/p1_v4_w10_20261106/C_GRADE_INVENTORY_META.json): in use = status REGISTERED + SENSITIVITY + DATA_PENDING;
families by parameter-name prefix (biomass_, industry_, share_, co2_, wacc_, potential_ / renewable_cap_ / candidate_cap_ /
nuclear_plan_cap_, other). Inputs: DATA_REGISTRY.csv at 26c2e47d and at aad8e476 (git show), the T06 adjustment table at 26c2e47d,
the W10 inventory (mechanism column) and the D2b top 30.

Classes of the 462 rows that were in-use C at aad8e476 (mutually exclusive, first match wins):
  (b) superseded  : the v4 main switch set replaces the main value; the row stays as the v3.1 fallback (rule + replacing row named)
  (c) range only  : main value unchanged, registered range added or corrected
  (d) value fixed : main value determined in the row itself (DATA_PENDING -> value)
  (x) demand side : W10 mechanism demand_I2 / side demand (decision 211: covered by I2; v4 demand tables, not re-judged here)
  (u) unchanged
New rows (a) are counted separately by grade and status.

    python w19a_4_registry_tiers.py <delivery dir> <w14 worktree>
"""
import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109")
WT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/home/jin/wt_v4_w19a")
COMMIT, BASE = "26c2e47d025fdd4e46cb278718d93aeddabbe984", "aad8e476"
USE = {"REGISTERED", "SENSITIVITY", "DATA_PENDING"}
TIERS = ["A", "B", "C", "D", "E"]
W10 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w10_20261106/C_GRADE_INVENTORY.csv")
TOP30 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2b_20261108/RERANK_D2B_TOP30.csv")


def show(rev, path):
    out = subprocess.run(["git", "-C", str(WT), "show", f"{rev}:{path}"], capture_output=True, text=True, check=True).stdout
    return pd.read_csv(StringIO(out), dtype=str, keep_default_na=False)


def family(p):
    for pre, fam in (("biomass_", "biomass"), ("industry_", "industry"), ("share_", "route_share"), ("co2_", "co2"), ("wacc_", "wacc")):
        if p.startswith(pre):
            return fam
    if p.startswith(("potential_", "renewable_cap_", "candidate_cap_", "nuclear_plan_cap_")):
        return "potential"
    return "other"


def counts(reg, label):
    rows = []
    u = reg[reg.status.isin(USE)]
    for scope, df in (("all rows", reg), ("in use", u)):
        rows.append(dict(version=label, scope=scope, key="rows", value=len(df)))
        for t in TIERS + ["(blank)"]:
            n = int((df.tier == ("" if t == "(blank)" else t)).sum())
            if n or t in TIERS[:3]:
                rows.append(dict(version=label, scope=scope, key=f"tier {t}", value=n))
    for (st, t), n in reg.groupby(["status", "tier"]).size().items():
        rows.append(dict(version=label, scope="status x tier", key=f"{st or '(blank)'} / {t or '(blank)'}", value=int(n)))
    cu = u[u.tier == "C"]
    for fam, n in cu.param_id.map(family).value_counts().items():
        rows.append(dict(version=label, scope="in-use C by family (W10 rule)", key=fam, value=int(n)))
    return rows


def main():
    new = show(COMMIT, "research_inputs/registry_v5/DATA_REGISTRY.csv").set_index("param_id", drop=False)
    old = show(BASE, "research_inputs/registry_v5/DATA_REGISTRY.csv").set_index("param_id", drop=False)
    adj = show(COMMIT, "research_inputs/biomass_v5/BIOMASS_POTENTIAL_ADJ_V4_T06.csv")
    inv = pd.read_csv(W10, dtype=str, keep_default_na=False).set_index("param_id")
    tiers = counts(old, f"{BASE} (W10 baseline)") + counts(new, "26c2e47d (W14 package COMMIT)")
    # (a) new rows
    added = new.loc[sorted(set(new.index) - set(old.index))]
    removed = sorted(set(old.index) - set(new.index))
    for (t, st), n in added.groupby(["tier", "status"]).size().items():
        tiers.append(dict(version="(a) v4 new rows", scope="tier / status", key=f"{t} / {st}", value=int(n)))
    for t, n in added.tier.value_counts().items():
        tiers.append(dict(version="(a) v4 new rows", scope="tier", key=t, value=int(n)))
    au = added[added.status.isin(USE)]
    for t, n in au.tier.value_counts().items():
        tiers.append(dict(version="(a) v4 new rows", scope="in use, tier", key=t, value=int(n)))
    # tier / status changes on common rows
    common = sorted(set(new.index) & set(old.index))
    tier_chg = [p for p in common if old.at[p, "tier"] != new.at[p, "tier"]]
    stat_chg = [p for p in common if old.at[p, "status"] != new.at[p, "status"]]
    # classification of the old in-use C rows
    oc = old[(old.tier == "C") & old.status.isin(USE)]
    adj["key"] = "biomass_potential_" + adj.country + "_" + adj.category
    adj = adj.set_index("key")
    proxy_targets = [s.strip().rstrip(".") for s in new.at["biomass_missing_cost_proxy", "description"].split("applies to ")[1].split(". Grade")[0].split(",")]
    explicit = {
        "fuel_price_lng_regasification_adder": ("v4_lng_regas_adder_asean_tariffs", "research.demand.v4.lng_regas_adder = asean_tariffs (v3.1 fallback m08a = 1.26)"),
        "share_MWh_MeOH_per_tCO2": ("ammonia_methanol_MWh_MeOH_per_tCO2_stoichiometric", "research.demand.v4.meoh_per_tco2 = stoichiometric 4.0248 (v3.1 fallback pypsa_eur 4.0321)"),
    }
    cls = []
    for p, r in oc.iterrows():
        n = new.loc[p]
        changed = [c for c in old.columns if old.at[p, c] != n[c]]
        rec = dict(param_id=p, family_201=family(p), old_value=r.value, new_value=n.value, unit=r.unit, old_status=r.status, new_status=n.status,
                   old_range=f"{r.sensitivity_low} .. {r.sensitivity_high}", new_range=f"{n.sensitivity_low} .. {n.sensitivity_high}",
                   changed_columns=";".join(changed), w10_mechanism=inv.at[p, "mechanism"] if p in inv.index else "", replaced_by="", replaced_by_tier="", switch="")
        if p in explicit:
            rb, sw = explicit[p]
            rec.update(cls="b", replaced_by=rb, replaced_by_tier=new.at[rb, "tier"], switch=sw)
        elif p in proxy_targets:
            rec.update(cls="b", replaced_by="biomass_missing_cost_proxy", replaced_by_tier=new.at["biomass_missing_cost_proxy", "tier"],
                       switch="research.biomass.missing_cost_rule = proxy (v4 main; v3.1 = zero: empty cost enters at 0 EUR/MWh)")
        elif p in adj.index and p.startswith("biomass_potential_"):
            a = adj.loc[p]
            f3, f4, f5 = (float(a[c] or 0) for c in ("F3_bagasse_R2_TWh", "F4_self_use_TWh", "F5_basis_TWh"))
            if abs(f3) + abs(f4) + abs(f5) > 1e-9:
                drv = []
                cat = p.split("_", 3)[3]
                if f3: drv.append("v4_w12_bagasse_supply_overestimate (F3 bagasse R2)")
                if f4: drv.append(f"v4_palm_mill_{'pks' if 'pks' in cat else 'fibre'}_self_use_{a.country} (F4 in-mill self use)" if "pks" in cat or "fibre" in cat else "v4_biomass_potential_adjustment_t06 (F4)")
                if f5:
                    drv.append({"oil_palm_trunk": "v4_oil_palm_trunk_energy_per_reported_t_t06 + v4_oil_palm_trunk_dry_mass_per_palm (F5 T06 trunk basis)",
                                "oil_palm_efb": "v4_palm_residue_energy_per_wet_t_efb (F5 T04 basis)",
                                "oil_palm_fibre": "v4_palm_residue_energy_per_wet_t_fibre (F5 T04 basis)"}.get(cat, "v4_biomass_basis_table_t06 (F5 basis)"))
                tiers_drv = sorted({new.at[x.split(" ")[0], "tier"] for x in drv if x.split(" ")[0] in new.index})
                rec.update(cls="b", replaced_by="v4_biomass_potential_2050_t06; " + "; ".join(drv), replaced_by_tier="C (table); drivers " + "/".join(tiers_drv),
                           switch=f"research.demand.v4.biomass_potential = v4_adjusted_t06: {float(a.potential_v3_TWh):.4f} -> {float(a.potential_adjusted_TWh):.4f} TWh "
                                  f"(F3 {f3:+.4f}, F4 {f4:+.4f}, F5 {f5:+.4f})")
        appended = n.description[len(r.description):] if n.description.startswith(r.description) else n.description
        linked = [q for q in added.index if q in appended]
        linked_sens = [q for q in linked if added.at[q, "status"] == "SENSITIVITY"]
        if "cls" not in rec:
            if r.value != n.value or (r.status != n.status and n.status == "REGISTERED"):
                rec["cls"] = "d"
            elif r.sensitivity_low != n.sensitivity_low or r.sensitivity_high != n.sensitivity_high:
                rec["cls"] = "c"
            elif linked_sens:
                rec.update(cls="c", replaced_by="range registered in " + "; ".join(linked_sens), replaced_by_tier="/".join(added.at[q, "tier"] for q in linked_sens),
                           switch="main value unchanged; the appended description names the new SENSITIVITY row")
            elif (p in inv.index and (inv.at[p, "mechanism"] == "demand_I2" or inv.at[p, "side"] == "demand")):
                rec["cls"] = "x"
            else:
                rec["cls"] = "u"
        cls.append(rec)
    cdf = pd.DataFrame(cls)
    names = {"b": "(b) superseded by a v4 switch value, kept as fallback", "c": "(c) range added / corrected, main value unchanged",
             "d": "(d) main value determined in the row (DATA_PENDING -> value)", "x": "(x) demand side (decision 211: I2; not re-judged)", "u": "(u) unchanged"}
    for k, v in cdf.cls.value_counts().items():
        tiers.append(dict(version="462 in-use C rows of aad8e476", scope="class", key=names[k], value=int(v)))
    for (k, fam), v in cdf.groupby(["cls", "family_201"]).size().items():
        tiers.append(dict(version="462 in-use C rows of aad8e476", scope=f"class x family: {names[k][:3]}", key=fam, value=int(v)))
    # status / tier of the 462 rows at the COMMIT
    still = cdf[(cdf.new_status.isin(USE))]
    tiers.append(dict(version="462 in-use C rows of aad8e476", scope="still in-use C at 26c2e47d", key="rows", value=int(len(still))))
    tiers.append(dict(version="462 in-use C rows of aad8e476", scope="still in-use C at 26c2e47d", key="of which class b (fallback, value not the v4 main)", value=int((still.cls == "b").sum())))
    # effective C count in use for the v4 main set = in-use C at COMMIT minus fallback rows (b) plus nothing else (the replacing rows are counted as new rows)
    nu = new[new.status.isin(USE)]
    eff = int((nu.tier == "C").sum()) - int((still.cls == "b").sum())
    tiers.append(dict(version="26c2e47d (W14 package COMMIT)", scope="in use, v4 main reading", key="C rows in use minus fallback rows (b)", value=eff))
    tdf = pd.DataFrame(tiers)
    tdf.to_csv(D / "REGISTRY_TIERS.csv", index=False)
    cdf.to_csv(D / "evidence" / "REGISTRY_C462_CLASSES.csv", index=False)
    added[["param_id", "tier", "status", "value", "unit", "decision_ref", "description"]].assign(description=lambda x: x.description.str.slice(0, 300)).to_csv(
        D / "evidence" / "REGISTRY_NEW_ROWS.csv", index=False)
    meta = dict(commit=COMMIT, base=BASE, rows_new=len(new), rows_old=len(old), added=len(added), removed=removed, tier_changes=tier_chg, status_changes=stat_chg,
                in_use_old=int(old.status.isin(USE).sum()), in_use_new=int(new.status.isin(USE).sum()),
                c_in_use_old=int(((old.tier == "C") & old.status.isin(USE)).sum()), c_in_use_new=int(((new.tier == "C") & new.status.isin(USE)).sum()),
                classes={names[k]: int(v) for k, v in cdf.cls.value_counts().items()}, effective_c_in_use_v4_main=eff, proxy_targets=proxy_targets)
    (D / "evidence" / "REGISTRY_TIERS_META.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps(meta, indent=1)[:3000])
    pd.set_option("display.width", 250)
    print(tdf.to_string()[:6000])
    print(cdf[cdf.cls.isin(["b", "c", "d"])][["param_id", "cls", "replaced_by", "replaced_by_tier", "switch"]].to_string(max_colwidth=90))


if __name__ == "__main__":
    main()
