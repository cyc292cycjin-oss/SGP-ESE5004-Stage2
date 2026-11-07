"""V4 D2a section 7.2: inputs of the (D31, P31) approximation (INFERENCE) for scripts/attribution.py -> evidence/ATTRIB_INPUTS.json.
  v3.1 objectives: W08 R0 (the v3.1 package integrated network 8b5fd663 solved on the W08 code; the v3.1 package smoke of the same network differs by 809 EUR)
                   and the v3.1 package smoke no_new_xb (results_project/v3hpc/smoke_hpc/no_new_xb, network e2837e4a); 56 snapshots, same profile.
  other v4 changes on the v3.1 network (not solved; per-run estimates):
    proxy cost of the trunk pools (D1 section 3): the trunk pools are fully used at zero cost in v3.1 as in W08 / D1 -> dV = proxy x dispatch, the D1 realised
      values +1,449,347,508.86 (F1) / +1,449,345,260.81 (F2) carried over (the D1 per-store table gives the country split);
    PHS reclassification and the TH inflow re-sharing: the D2a lower-bound terms of SMOKE56_D2A.md section 1 (phs + inflow + new-reservoir completion),
      taken as the estimate (loose; sign-indefinite for the new reservoir);
    methanol coefficient: the first-order term of the same registration.
  per player: Owen benefit of the v3.1 smoke pair (v3hpc/smoke_hpc/M12_BENEFIT) and the integrated ledger totals, plus the proxy cost by trunk country.
No solver.
"""
import json
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
RP = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
D1 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107")


def receipt(p):
    r = json.loads((p / "SOLVE_RECEIPT.json").read_text()); return float(r["objective"]), (r.get("input_network") or {}).get("sha256")


def ledger_total(p):
    L = pd.read_csv(p / "COUNTRY_COST_LEDGER.csv").set_index("entity"); col = [c for c in L.columns if c.startswith("total")]; col = col[0] if col else L.columns[-1]
    return {str(k): float(v) for k, v in L[col].items()}


def main():
    f1, sha1 = receipt(RP / "v4w08/smoke56/v31_F1"); f2, sha2 = receipt(RP / "v3hpc/smoke_hpc/no_new_xb")
    f1b, _ = receipt(RP / "v3hpc/smoke_hpc/integrated")
    pre = json.loads((W / "evidence/D2A_BOUNDS_PRE.json").read_text())
    d1s = json.loads((D1 / "evidence/D1_smoke56.json").read_text()) if (D1 / "evidence/D1_smoke56.json").exists() else {}
    d1b = pd.read_csv(D1 / "tables/D1_BOUNDS_PRE.csv")
    proxy_by_run = {}
    for rid, run in (("R1_v4d1_F1", "F1"), ("R2_v4d1_F2", "F2")):
        z = d1b[d1b.run == rid]; proxy_by_run[run] = {str(r.store.split()[0]): float(r.dV_upper_eur) for r in z.itertuples()}
    realised = {"F1": 1449347508.86, "F2": 1449345260.81}   # D1 SMOKE56_D1.md section 2.2 (dV = proxy x dispatch of the W08 solution, which stayed optimal)
    other = {}
    for run, rid in (("F1", "R1_v4d2a_F1"), ("F2", "R2_v4d2a_F2")):
        t = pre[rid]["terms"]
        other[run] = {"trunk_proxy_cost_D1": realised[run],
                      "phs_reclass_lower_bound_terms_D2a": t["phs_rhs_lower_bound_eur"] + t["th_inflow_rhs_lower_bound_eur"] + t["new_reservoir_completion_eur"],
                      "methanol_coefficient_first_order_D2a": t["coefficient_first_order_eur"]}
    notes = {"trunk_proxy_cost_D1": "D1 section 7: realised dV of the proxy cost on the W08 solution (trunk pools fully used; the same holds for the v3.1 smoke, zero-cost pools), scaled 1:1 (INFERENCE)",
             "phs_reclass_lower_bound_terms_D2a": "D2a SMOKE56_D2A.md section 1: PHS capacity value + TH inflow re-sharing + new-reservoir completion (lower-bound terms at the D1 duals, used as the estimate; sign of the new reservoir indefinite)",
             "methanol_coefficient_first_order_D2a": "D2a SMOKE56_D2A.md section 1: first order at the D1 solution (no bound)"}
    # per player
    ben = RP / "v3hpc/smoke_hpc/M12_BENEFIT/BENEFIT.csv"
    owen = {str(k): float(v) for k, v in pd.read_csv(ben).set_index("player").owen_benefit_eur.items()} if ben.exists() else {}
    led = ledger_total(RP / "v3hpc/smoke_hpc/integrated")
    per_player = {"owen": {}, "ledger_F1": {}}
    for pl in ("MY", "ID", "SG", "BUNKER"):
        k = pl if pl in owen else ("ASEAN_BUNKER" if pl == "BUNKER" else pl)
        per_player["owen"][pl] = owen.get(k, float("nan"))   # the Owen benefit of B6 is a difference F2 - F1: the other-change terms are run differences and cancel to first order
        kl = pl if pl in led else ("ASEAN_BUNKER" if pl == "BUNKER" else pl)
        per_player["ledger_F1"][pl] = led.get(kl, float("nan")) + proxy_by_run["F1"].get(pl, 0.0)
    out = dict(v31_objective_eur={"F1": f1, "F2": f2}, v31_networks={"F1": sha1, "F2": sha2},
               v31_source=f"F1 W08 R0 (v3.1 package integrated network solved on the W08 code; the v3.1 package smoke gives {f1b:,.2f}, +{f1b - f1:.2f} EUR); F2 v3.1 package local smoke results_project/v3hpc/smoke_hpc/no_new_xb",
               other_v4_changes_on_v31_eur=other, other_v4_changes_notes=notes, v31_by_player=per_player, proxy_by_country_F1=proxy_by_run["F1"], proxy_by_country_F2=proxy_by_run["F2"],
               v31_owen_all=owen, v31_ledger_F1_all=led, grade="INFERENCE (approximation; the (D31, P31) corner is not solved)")
    (W / "evidence/ATTRIB_INPUTS.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({k: out[k] for k in ("v31_objective_eur", "other_v4_changes_on_v31_eur", "v31_by_player")}, indent=1, default=float))


if __name__ == "__main__":
    main()
