"""V31 W15 stage A, section 3.2 support: the shipping cost basis (S-A vs S-B) at the SAME 3-hour resolution, from the two local 56x3h smokes
whose networks differ only in the 270 shipping links (RUN_PLAN_V3.md section 24.1): supplement 05 smoke (S-B, 1bddacb7 / b262f6aa) and the
V3 HPC package smoke (S-A, 8b5fd663 / e2837e4a = the first 56 snapshots of the F1 / F2 networks). Both use the pre-v3.1 bunker row.

  python -I w15a_ship_basis_56.py --sb <results_project/v3/smoke_s5> --sa <results_project/v3hpc/smoke_hpc> --decomp-summary <evidence/RESOLUTION_SUMMARY.json> --out <dir>

Writes evidence/SHIP_BASIS_56.csv: ASEAN capacity per carrier, S-A minus S-B at 56x3h, next to F minus s07 (2920x3h minus 365 daily slices).
"""
import argparse, json
from pathlib import Path

import pandas as pd

KEYS = ["solar", "solar rooftop", "onwind", "offwind-dc", "battery", "battery discharger", "home battery", "H2 Electrolysis", "H2 pipeline", "hydro", "geothermal",
        "SMR CC", "SMR", "co2 sequestered", "gas production", "LNG import", "gas pipeline", "DC", "methanolisation", "methanol store", "ammonia store",
        "methanol ship", "ammonia ship", "oil non-fossil ship", "BtL"]


def cap(d: Path) -> dict:
    C = json.loads((d / "CAPACITY_BY_TECH_COUNTRY.json").read_text(encoding="utf-8")); out = {}
    for comp, recs in C.items():
        k = "e_nom_opt" if comp == "Store" else "p_nom_opt"
        for r in recs:
            out[r["carrier"]] = out.get(r["carrier"], 0.0) + float(r[k])
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("sb", "sa", "decomp_summary", "out"):
        ap.add_argument("--" + k.replace("_", "-"), required=True)
    a = ap.parse_args()
    S = json.loads(Path(a.decomp_summary).read_text(encoding="utf-8"))["capacity_asean"]
    rows = []
    for sc, pair in (("integrated", "F1−V1"), ("no_new_xb", "F2−V2")):
        sb, sa = cap(Path(a.sb) / sc), cap(Path(a.sa) / sc)
        for c in KEYS:
            u = [k.split("|")[2] for k in S if k.startswith(f"{pair}|{c}|")]
            fv = S.get(f"{pair}|{c}|{u[0]}") if u else None
            rows.append(dict(scenario=sc, carrier=c, unit=(u[0] if u else ""), smoke56_SB=sb.get(c, 0.0), smoke56_SA=sa.get(c, 0.0), smoke56_SA_minus_SB=sa.get(c, 0.0) - sb.get(c, 0.0),
                             F=(fv[0] if fv else ""), s07=(fv[1] if fv else ""), F_minus_s07=(fv[0] - fv[1] if fv else ""),
                             ratio_ship_to_resolution_delta=((sa.get(c, 0.0) - sb.get(c, 0.0)) / (fv[0] - fv[1]) if fv and fv[0] != fv[1] else "")))
    df = pd.DataFrame(rows)
    df.to_csv(Path(a.out) / "evidence" / "SHIP_BASIS_56.csv", index=False, lineterminator="\n")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(df.assign(**{c: df[c].map(lambda x: f"{x:.4g}" if isinstance(x, float) else x) for c in df.columns if c not in ("scenario", "carrier", "unit")}).to_string(index=False))


if __name__ == "__main__":
    main()
