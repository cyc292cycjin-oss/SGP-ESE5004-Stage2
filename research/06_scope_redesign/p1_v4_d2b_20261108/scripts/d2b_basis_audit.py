"""V4 D2b section 2.4: BIOMASS_BASIS_AUDIT.csv (category x country: old = D2a main v4_adjusted_t04, new = D2b main v4_adjusted_t05, basis verdict, sources,
grade, low / high of the category range applied to the old value) and tables/BIOMASS_T05_CHANGE_BY_COUNTRY_CATEGORY.csv (TWh). Reads the repository tables
(no recomputation of the potential). Nothing is solved.

    python scripts/d2b_basis_audit.py <repo>
"""
import sys
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
R = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/jin/wt_v4_d2b")
B = R / "research_inputs/biomass_v5"


def pot(f):
    t = pd.read_csv(B / f, keep_default_na=False)
    t["p"] = pd.to_numeric(t.potential_main_mwh, errors="coerce").fillna(0.0)
    t = t[~t.status.isin(["DATA_PENDING", "ZERO_BY_DECISION"])]   # the rows the build reads (Fable F-14)
    return t.set_index(["country", "category"])


def main():
    old, new, v3 = pot("BIOMASS_POTENTIAL_2050_V4_T04.csv"), pot("BIOMASS_POTENTIAL_2050_V4_T05.csv"), pot("BIOMASS_POTENTIAL_2050.csv")
    basis = pd.read_csv(B / "BIOMASS_BASIS_T05.csv", keep_default_na=False).set_index("category")
    rows = []
    for (c, k) in sorted(set(old.index) | set(new.index)):
        o = float(old.p.get((c, k), 0.0)); n = float(new.p.get((c, k), 0.0))
        b = basis.loc[k] if k in basis.index else None
        fl = float(b.factor_low) if b is not None else None; fh = float(b.factor_high) if b is not None else None; fm = float(b.factor_mid) if b is not None else None
        applied = (b is not None and str(b.applied) == "True")
        # range on the new value: applied rows -> factor_low / factor_mid and factor_high / factor_mid of the new value; kept rows -> factor_low / factor_high x the kept value
        if b is None:
            lo = hi = None
        elif applied:
            lo, hi = n * fl / fm, n * fh / fm
        else:
            lo, hi = n * fl, n * fh
        rows.append(dict(category=k, country=c, group=str(new.feedstock_group.get((c, k), old.feedstock_group.get((c, k), ""))) if (c, k) in new.index or (c, k) in old.index else "",
                         old_t04_twh=o / 1e6, new_t05_twh=n / 1e6, change_twh=(n - o) / 1e6, v3_twh=float(v3.p.get((c, k), 0.0)) / 1e6,
                         basis_verdict=(b.verdict if b is not None else "not assessed"), applied=applied, factor_mid=fm, factor_low=fl, factor_high=fh,
                         range_low_twh=(lo / 1e6 if lo is not None else None), range_high_twh=(hi / 1e6 if hi is not None else None),
                         mass_basis=(b.mass_basis if b is not None else ""), heat_basis=(b.heat_basis_table if b is not None else ""),
                         sources=(b.sources if b is not None else ""), grade=(b.grade if b is not None else ""), origin=(b.origin if b is not None else ""),
                         rule=(b.rule if b is not None else "")))
    A = pd.DataFrame(rows)
    A.to_csv(W / "BIOMASS_BASIS_AUDIT.csv", index=False, float_format="%.6f", lineterminator="\n")
    piv = A.pivot_table(index="category", columns="country", values="change_twh", aggfunc="sum").fillna(0.0)
    piv["ASEAN11"] = piv.sum(axis=1); piv.loc["TOTAL"] = piv.sum(axis=0)
    (W / "tables").mkdir(exist_ok=True)
    piv.to_csv(W / "tables/BIOMASS_T05_CHANGE_BY_COUNTRY_CATEGORY.csv", float_format="%.6f", lineterminator="\n")
    tot = A.groupby("category")[["old_t04_twh", "new_t05_twh", "change_twh", "range_low_twh", "range_high_twh"]].sum(min_count=1)
    tot["verdict"] = [basis.verdict.get(k, "") for k in tot.index]
    pd.set_option("display.width", 250)
    print(tot.round(2).to_string())
    print("solid total old / new:", round(A[A.group != "biogas"].old_t04_twh.sum(), 3), round(A[A.group != "biogas"].new_t05_twh.sum(), 3))
    print(piv.round(3).loc[["oil_palm_trunk", "TOTAL"]].to_string())


if __name__ == "__main__":
    main()
