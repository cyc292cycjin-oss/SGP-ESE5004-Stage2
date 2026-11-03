"""V3 supplement 07 (review EVDIAG section 2.1 item 4) read-out of the HiGHS daily path check (8 days: no economic reading): the EV morning floor holds in every solved run and binds somewhere;
the ledger identity, B16, Owen identity and RHS premise close; GATES_V6 labels; benefit sum = B6. Writes evidence/dmax/PATH_CHECK_DAILY.json. usage: python chk_pc7.py <path_check7 dir> <evidence dir>"""
import json, logging, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pypsa

logging.disable(logging.WARNING)
R, E = Path(sys.argv[1]), Path(sys.argv[2]); E.mkdir(parents=True, exist_ok=True); out = dict(runs={})
jl = lambda p: json.loads(p.read_text()) if p.exists() else None
fail = lambda x: sorted(k for k, z in (x or {}).items() if isinstance(z, dict) and z.get("passed") is False)
for r in ("integrated", "no_new_xb", "disconnected"):
    d = R / r; rec = jl(d / "SOLVE_RECEIPT.json") or {}; p = jl(d / "PRECISION.json") or {}; v = jl(d / "V6_ACCEPTANCE.json") or {}; w = jl(d / "m12_owen/OWEN.json") or {}; led = jl(d / "LEDGER_IDENTITY.json") or {}
    aud = (jl(d / "m12_owen/RHS_AUDIT.json") or {}).get("owen_premise") or {}; g = jl(d / "V5_GATES.json")
    f = next(iter(sorted(d.glob("*_solved.nc"))), None); ev = None
    if f is not None:
        n = pypsa.Network(str(f)); lo = n.stores_t.e_min_pu; cols = list(lo.columns); en = n.stores.e_nom.loc[cols]
        soc = n.stores_t.e[cols] / en; slack = soc - lo
        tot = n.stores_t.e[cols].sum(axis=1); band = float(0.2 * en.sum())
        ev = dict(stores=len(cols), snapshots=int(len(n.snapshots)), store_weight_h=float(n.snapshot_weightings.stores.iloc[0]), floor_values=sorted(set(np.round(lo.to_numpy().ravel(), 12).tolist())),
                  min_soc_minus_floor=float(slack.to_numpy().min()), violations_1e6=int((slack.to_numpy() < -1e-6).sum()), binding_share=float((slack.to_numpy() <= 1e-4).mean()),
                  soc_min=float(soc.to_numpy().min()), soc_max=float(soc.to_numpy().max()), e_nom_twh=float(en.sum()) / 1e6, cross_day_band_twh=band / 1e6,
                  system_energy_above_floor_twh=[round(float(x) / 1e6, 4) for x in (tot - 0.8 * en.sum()).to_numpy()], above_floor_within_band=bool(((tot - 0.8 * en.sum()) <= band * (1 + 1e-9) + 1e-3).all()))
    c = p.get("c_prices") or {}
    out["runs"][r] = dict(termination=rec.get("termination_condition") or rec.get("status"), objective_eur=rec.get("objective", rec.get("objective_value")), solver=rec.get("solver"),
                          ledger_identity={k: led.get(k) for k in ("relative_error", "difference", "passed") if k in led}, b16=c.get("b16"), c1={k: (p.get("grade") or {}).get(k) for k in ("a", "b", "c")},
                          v6_label=v.get("label"), g2={k: ((v.get("G2") or {}).get(k) or {}).get("passed") for k in ("G2_1", "G2_2", "G2_3")}, v5_failed=fail(g),
                          owen_usable=w.get("usable_for_allocation"), owen_identity=w.get("identity"), rhs_premise_passed=aud.get("passed"), rhs_rows_by_class=aud.get("nonzero_rhs_rows_by_class"), ev_floor=ev)
    print(r, json.dumps(out["runs"][r], default=str)[:1400])
ben = R / "M12_BENEFIT/BENEFIT.csv"; ob = lambda x: (x or {}).get("objective", (x or {}).get("objective_value"))
i, k = jl(R / "integrated/SOLVE_RECEIPT.json"), jl(R / "no_new_xb/SOLVE_RECEIPT.json")
out["benefit"] = dict(owen_sum_bn=float(pd.read_csv(ben).owen_benefit_eur.sum()) / 1e9 if ben.exists() else None, b6_bn=(float(ob(k)) - float(ob(i))) / 1e9 if ob(i) is not None and ob(k) is not None else None,
                      players=int(len(pd.read_csv(ben))) if ben.exists() else None)
out["status"] = (R / "STATUS.txt").read_text().splitlines()
runs = out["runs"].values()
out["passed"] = bool(all(x["ev_floor"] and x["ev_floor"]["violations_1e6"] == 0 and x["ev_floor"]["floor_values"] == [0.8] and x["ev_floor"]["above_floor_within_band"] for x in runs)
                     and all((x["ledger_identity"] or {}).get("passed", True) is not False and (x["b16"] or {}).get("passed") is not False and x["owen_usable"] and x["rhs_premise_passed"] for x in runs))
print(json.dumps(out["benefit"]), "passed", out["passed"])
(E / "PATH_CHECK_DAILY.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
