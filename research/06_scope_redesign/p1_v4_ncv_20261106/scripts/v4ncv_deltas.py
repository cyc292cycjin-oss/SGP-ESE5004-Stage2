"""V4 W11 section 3 (inputs to the scratch-copy runs): 2019 base changes per scheme, row by row.

    python scripts/v4ncv_deltas.py --work <work dir>

* D1 base (what T_v2 and every sector's 2019 base use): BASE_RECONSTRUCTION.json selected rows and non-energy references are recomputed with
  the scheme factor (ncv/NCV_FACTOR_SCHEMES.csv; v3 factor where the scheme gives none). A coal parent row ('Hard coal' / 'Brown coal') whose
  scheme value is given per rank (TH (c), TH/KH/LA (d)) is converted through its child rows of the same country and flow (lignite,
  sub-bituminous, other bituminous, anthracite); the children must add up to the parent (checked), otherwise the parent factor is used and the
  row is flagged. Delta = scheme MWh - v3 MWh, so an unchanged factor gives exactly 0. The v3 MWh is recomputed and must equal the file.
* industry_cache.json gives only the within-carrier sub-sector shares in s3_0_industry.py; it carries the upstream coal double count (parent +
  children, KH / LA / TH). To change only the NCV, each cache cell (country x carrier x sub-sector) is multiplied by
  E_scheme / E_v3 of the de-duplicated export rows of that sub-sector flow (ratio 1 where the flow has no rows).
Outputs ncv/NCV_BASE_ROWS_2019.csv, ncv/NCV_BASE_DELTAS_2019.csv (country x account x carrier x scheme), ncv/NCV_CACHE_RATIOS_2019.csv,
ncv/_deltas_evidence.json. Nothing in the repository is written.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4ncv_common as cm   # noqa: E402
import v4ncv_unsd_implied as ui   # noqa: E402

SCHEMES = ("b", "c", "d")
CHILDREN = {"Hard coal": ["Anthracite", "Other bituminous coal", "Coking coal"], "Brown coal": ["Lignite", "Sub-bituminous coal"]}
CACHE_FLOW = {"iron and steel": "Ironandsteel", "chemical and petrochemical": "Chemicalandpetrochemical", "non-ferrous metals": "Non-ferrousmetals",
              "non-metallic minerals": "Non-metallicminerals", "transport equipment": "Transportequipment", "machinery": "Machinery",
              "mining and quarrying": "Miningandquarrying", "food and tobacco": "Foodandtobacco", "paper pulp and print": "Paper,pulpandprinting",
              "wood and wood products": "Woodandwoodproducts", "textile and leather": "Textileandleather", "construction": "Construction",
              "other": "Industriesn.e.s"}


class Factors:
    def __init__(self, work: Path, conv: dict):
        X = pd.read_csv(work / "ncv/NCV_FACTOR_SCHEMES.csv")
        self.over = {(r.country, r.commodity, r.scheme): float(r.gj_per_unit) for r in X.itertuples() if r.scheme != "a"}
        self.conv = conv

    def v3_mwh_per_unit(self, com: str) -> float:
        return self.conv[com] * 1e6

    def mwh_per_unit(self, scheme: str, cc: str, com: str) -> float:
        key = "Hard coal" if com == "Hrad coal" else com
        if scheme != "a" and (cc, key, scheme) in self.over:
            return self.over[(cc, key, scheme)] * 1000.0 / 3.6
        return self.v3_mwh_per_unit(com)

    def has_child_values(self, scheme: str, cc: str, parent: str) -> bool:
        return any((cc, ch, scheme) in self.over for ch in CHILDREN[parent])

    def has_parent_value(self, scheme: str, cc: str, parent: str) -> bool:
        return (cc, parent, scheme) in self.over


def energy(F: Factors, scheme: str, cc: str, com: str, qty: float, flow: str | None, E: pd.DataFrame) -> tuple[float, str]:
    """MWh of one raw row under a scheme, and the method used."""
    parent = "Hard coal" if com in ("Hard coal", "Hrad coal") else ("Brown coal" if com == "Brown coal" else None)
    if parent and scheme != "a" and not F.has_parent_value(scheme, cc, parent) and F.has_child_values(scheme, cc, parent):
        ch = E[(E.country == cc) & (E.flow == flow) & E.commodity.isin(CHILDREN[parent])]
        if len(ch) and abs(ch.q.sum() - qty) <= 1e-6 * max(1.0, abs(qty)):
            return float(sum(r.q * F.mwh_per_unit(scheme, cc, r.commodity) for r in ch.itertuples())), "children:" + ";".join(f"{r.commodity}={r.q:g}" for r in ch.itertuples())
        return qty * F.mwh_per_unit(scheme, cc, com), "parent (children missing or not adding up)"
    return qty * F.mwh_per_unit(scheme, cc, com), "commodity"


def base_rows(F: Factors, E: pd.DataFrame) -> pd.DataFrame:
    b = json.loads((cm.SRC / "BASE_RECONSTRUCTION.json").read_text())
    rows = []
    for r in b["selected_rows"]:
        unit, com = r["RawUnit"], r["Commodity"]
        if unit not in ("Metric tons,  thousand", "Cubic metres, thousand"):
            continue   # TJ / GWh rows carry no NCV choice (gas x0.9 is the UNSD rule; electricity has none)
        if com not in F.conv:
            raise KeyError(com)
        q = float(r["RawValue"])
        v3_file = float(r["MWh"])
        v3 = float(Decimal(r["RawValue"]) * Decimal(str(F.conv[com])) * Decimal(1000000))
        qty_note = "raw quantity"
        if abs(v3 - v3_file) > 1e-6:
            # biofuel blend rows (final_closure_inputs.py): the file MWh is (parent - blended bio mass) x petroleum NCV
            q = v3_file / F.v3_mwh_per_unit(com)
            qty_note = f"blend-adjusted quantity {q:.6f} (raw {r['RawValue']})"
        flow = cm.flow_of(r["Transaction"])
        rec = dict(country=r["Country"], account=r["Account"], carrier=r["Carrier"], commodity=com, transaction=r["Transaction"], flow=flow, raw_value=q,
                   raw_unit=unit, quantity_note=qty_note, v3_mwh=v3_file, row_id=r["RowID"], kind="final energy")
        for s in SCHEMES:
            e, how = energy(F, s, r["Country"], com, q, flow, E)
            rec[f"{s}_mwh"] = e; rec[f"{s}_method"] = how
        rows.append(rec)
    for r in b["nonenergy_reference"]:
        com = r["Commodity"]
        if com not in F.conv:
            continue
        mwh = float(r["MWh"])
        q = mwh / F.v3_mwh_per_unit(com)
        rec = dict(country=r["Country"], account="NonEnergy:" + com, carrier=None, commodity=com, transaction="non-energy use", flow="Non-energyuse",
                   raw_value=q, raw_unit="derived from MWh", v3_mwh=mwh, row_id=r["RawRow"], kind="non-energy reference")
        for s in SCHEMES:
            e, how = energy(F, s, r["Country"], com, q, "Non-energyuse", E)
            rec[f"{s}_mwh"] = e; rec[f"{s}_method"] = how
        rows.append(rec)
    D = pd.DataFrame(rows)
    for s in SCHEMES:
        D[f"{s}_delta_mwh"] = D[f"{s}_mwh"] - D.v3_mwh
    return D


def cache_ratios(F: Factors, E: pd.DataFrame) -> pd.DataFrame:
    _, lists = cm.upstream_dicts()
    car = {c: k for k, v in (("coal", lists["coal_fuels"]), ("oil", lists["oil_fuels"]), ("biomass", lists["biomass_fuels"])) for c in v}
    out = []
    for cc in cm.ISO:
        for col, flow in CACHE_FLOW.items():
            e = E[(E.country == cc) & (E.flow == flow)]
            q = e.set_index("commodity").q
            # de-duplicate coal: parents if reported, else children
            keep = []
            for c_ in q.index:
                if c_ in CHILDREN["Hard coal"] and "Hard coal" in q.index:
                    continue
                if c_ in CHILDREN["Brown coal"] and "Brown coal" in q.index:
                    continue
                keep.append(c_)
            for carrier in ("coal", "oil", "biomass"):
                items = [(c_, float(q[c_])) for c_ in keep if car.get(c_) == carrier and c_ in F.conv]
                if not items:
                    continue
                v3 = sum(qq * F.v3_mwh_per_unit(c_) for c_, qq in items)
                for s in SCHEMES:
                    sc = sum(energy(F, s, cc, c_, qq, flow, E)[0] for c_, qq in items)
                    out.append(dict(country=cc, carrier=carrier, subsector=col, flow=flow, scheme=s, v3_mwh=v3, scheme_mwh=sc,
                                    ratio=(sc / v3 if v3 else 1.0), commodities=";".join(f"{c_}={qq:g}" for c_, qq in items)))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); a = ap.parse_args()
    conv, _ = cm.upstream_dicts()
    F = Factors(a.work, conv)
    E, _ = ui.export_2019()
    D = base_rows(F, E)
    agg = D.groupby(["country", "account", "carrier", "kind"], dropna=False)[["v3_mwh"] + [f"{s}_delta_mwh" for s in SCHEMES]].sum().reset_index()
    C = cache_ratios(F, E)
    out = a.work / "ncv"
    D.to_csv(out / "NCV_BASE_ROWS_2019.csv", index=False, float_format="%.12g")
    agg.to_csv(out / "NCV_BASE_DELTAS_2019.csv", index=False, float_format="%.12g")
    C.to_csv(out / "NCV_CACHE_RATIOS_2019.csv", index=False, float_format="%.12g")
    flagged = D[D[[f"{s}_method" for s in SCHEMES]].apply(lambda r: r.str.startswith("parent (").any(), axis=1)]
    ev = dict(rows=len(D), rows_with_change={s: int((D[f"{s}_delta_mwh"].abs() > 1e-9).sum()) for s in SCHEMES},
              flagged_children_mismatch=flagged[["country", "account", "commodity", "transaction"]].to_dict("records"),
              delta_total_twh={s: float(D[f"{s}_delta_mwh"].sum() / 1e6) for s in SCHEMES})
    (out / "_deltas_evidence.json").write_text(json.dumps(ev, indent=1, default=float) + "\n")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(json.dumps(ev, indent=0, default=float)[:1500])
    nz = agg[(agg[[f"{s}_delta_mwh" for s in SCHEMES]].abs() > 1e-6).any(axis=1)].copy()
    for c in ["v3_mwh"] + [f"{s}_delta_mwh" for s in SCHEMES]:
        nz[c] = nz[c] / 1e6
    print(nz.round(3).to_string())
    cc = C[(C.ratio - 1).abs() > 1e-9].pivot_table(index=["country", "carrier", "subsector"], columns="scheme", values="ratio")
    print(cc.round(4).to_string())


if __name__ == "__main__":
    main()
