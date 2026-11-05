"""G2-1 (quantification): the sub-sector split of the VN 2019 industry base and its effect on dispersed / other (B-G2 item 1).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_split.py

The v3 rule takes T_v2(VN) from the UNSD run and the decomposition from a run with the APEC 2022 matrix. The split only changes the
decomposition (T_v2 is the same in every variant, EXACT). Variants of the decomposition matrix:
  apec2022 (v3), apec2022_yearadj (steel / cement / ammonia rows scaled to 2019 activity), hybrid (UNSD explicit rows kept: steel coke, chemical
  coal and gas, non-metallic gas, the LPG rows; bagasse to food; the UNSD n.e.s. amount spread by APEC 2022 over the rows UNSD does not report),
  hybrid_yearadj, unsd_only (the decomposition of the UNSD run itself = v2).
Writes tables/VN_SPLIT_VARIANTS.csv, tables/VN_SPLIT_DISPERSED_ROWS.csv, evidence/_split_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402
import v4w07g2_unsd as un   # noqa: E402

OTHER_ROWS = ("other", "construction", "mining and quarrying")


def matrices(cache_ratio: dict | None = None) -> dict:
    """Decomposition matrices; the UNSD matrix after an optional NCV cell ratio (the hybrid follows the NCV of the UNSD cells)."""
    cache = json.loads((cm.REPO / cm.CACHE_REL).read_text())
    subs = [k for k in cache["records"][0] if k not in ("country", "carrier")]
    U = pd.DataFrame({r["carrier"]: {k: float(r[k]) for k in subs} for r in cache["records"] if r["country"] == cm.CC})
    for (car, sub), f in (cache_ratio or {}).items():
        U.at[sub, car] *= f
    A = pd.read_csv(cm.REPO / cm.APEC_REL).set_index("cache_subsector")
    A = A[[cm.APEC_COL[c] for c in cm.CARS19]].rename(columns={v: k for k, v in cm.APEC_COL.items()}).reindex(subs).fillna(0.0).astype(float)
    Ay = A.copy()
    for sub, (q19, q22, _) in un.ACT_2019_2022.items():
        Ay.loc[sub] = Ay.loc[sub] * q19 / q22
    rows = pd.read_csv(cm.WORK / "tables/VN_UNSD_2019_ROWS.csv")
    bag = float(rows[(rows.commodity == "Bagasse") & (rows.sdmx_transaction == "121")].twh_v3_factor.iloc[0]) * 1e6
    out = {"apec2022": A, "apec2022_yearadj": Ay, "hybrid": un.hybrid(U, A, bag), "hybrid_yearadj": un.hybrid(U, Ay, bag), "unsd_only": U}
    return {k: v.rename(columns={c: cm.APEC_COL[c] for c in cm.CARS19}) for k, v in out.items()}


def dispersed_rows(pz: pd.DataFrame) -> dict:
    z = pz[pz.carrier.eq("all (see mapping shares)") & ~pz.subsector.isin(OTHER_ROWS)]
    return (z.groupby("subsector").mwh_2050.sum() / 1e6).to_dict()


def main():
    v3 = cm.import_v3(); fut = v3.future_vectors()
    ch = cm.Chain(); ch.copy()
    ev = cm.Ev("split"); rows, drows = [], []
    for name, M in matrices().items():
        res = ch.run(apec_override=M)
        lay = cm.v3_layer(v3, res, fut)
        d = dispersed_rows(res["pz_apec"])
        st19 = res["pz_apec"][(res["pz_apec"].subsector == "iron and steel")].mwh_2019.sum() / 1e6
        cem19 = res["pz_apec"][(res["pz_apec"].subsector == "cement")].mwh_2019.sum() / 1e6
        gaps = res["gaps_apec"]
        r = dict(variant=name, T_v2_twh=lay["T"] / 1e6, steel_twh=lay["by_sub"]["steel"] / 1e6, cement_twh=lay["by_sub"]["cement"] / 1e6,
                 ammonia_twh=lay["by_sub"]["ammonia"] / 1e6, dispersed_twh=lay["by_sub"]["dispersed"] / 1e6, other_twh=lay["other_total"] / 1e6,
                 other_share=lay["other_total"] / lay["T"], other_scale=lay["scale"], T_decomposition_run_twh=lay["T_apec_run"] / 1e6,
                 steel_2019_deducted_twh=st19, cement_2019_deducted_twh=cem19, other_2019_twh=float(res["ob_apec"].other_2019_mwh) / 1e6,
                 gap_items="; ".join(f"{g.item[:60]} {g.carrier} {g.mwh / 1e6:.2f}" for g in gaps.itertuples()), **cm.band_row(lay))
        rows.append(r)
        for k, x in d.items():
            drows.append(dict(variant=name, unsd_row=k, dispersed_2050_twh=x))
        for k in ("T_v2_twh", "dispersed_twh", "other_twh", "other_share", "steel_2019_deducted_twh", "other_scale"):
            ev.put(f"{name}.{k}", r[k], "share" if "share" in k or "scale" in k else "TWh", f"scratch chain, decomposition matrix {name} (v3 rule otherwise)", "EXACT", "C")
    V = pd.DataFrame(rows); D = pd.DataFrame(drows).pivot(index="unsd_row", columns="variant", values="dispersed_2050_twh").fillna(0.0)
    V.to_csv(cm.WORK / "tables/VN_SPLIT_VARIANTS.csv", index=False, float_format="%.6f")
    D.to_csv(cm.WORK / "tables/VN_SPLIT_DISPERSED_ROWS.csv", float_format="%.6f")
    ev.write(cm.WORK / "evidence/_split_evidence.json")
    pd.set_option("display.width", 250)
    print(V.drop(columns=["gap_items"]).round(3).to_string()); print(D.round(2).to_string())
    for r in V.itertuples():
        print(r.variant, r.gap_items)


if __name__ == "__main__":
    main()
