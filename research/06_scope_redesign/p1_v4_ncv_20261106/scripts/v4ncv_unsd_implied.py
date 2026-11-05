"""V4 W11 section 2.1: UNSD's own (country-specific) conversion factors implied by the UN Energy Balances 2019 publication (TJ, NCV) and the
UNdata export quantities used by the model (2025-05-02 export, same files as the upstream), for the 11 ASEAN countries, 2019.

    python scripts/v4ncv_unsd_implied.py --work <work dir>

Method (no new data):
  * export rows of 2019 are mapped to UN Energy Balances flows (v4ncv_common.flow_of); duplicate spellings of the same commodity x flow are
    collapsed when their values agree (a conflict is listed);
  * primary coal is taken at parent level: 'Hard coal' (alias 'Hrad coal') if reported, else anthracite + other bituminous + coking coal;
    'Brown coal' if reported, else lignite + sub-bituminous (the parent equals the sum of its children wherever both exist: checked here);
  * per country x flow x balance column: export quantity (kt / 10^3 m3 / TJ), TJ at UNSD standard NCV, TJ at the upstream factors,
    publication TJ; ratio publication / standard;
  * implied coal NCV per country = publication primary-coal TJ / parent-level coal kt for flows that carry one coal parent only; a country value
    is accepted (VERIFIED) when at least two flows agree within 0.5 %, otherwise it is listed as not derivable (data vintage of the 2019
    publication differs from the 2025 export; S2-0 found the same for the visualisation exports).
Outputs ncv/UNSD_EXPORT_VS_EB2019_BY_FLOW.csv, ncv/UNSD_IMPLIED_COAL_NCV_2019.csv, ncv/UNSD_COAL_PARENT_CHECK.csv,
ncv/UNSD_EXPORT_DUPLICATE_CONFLICTS.csv.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4ncv_common as cm   # noqa: E402

HARD_CHILD = ["Anthracite", "Other bituminous coal", "Coking coal"]
BROWN_CHILD = ["Lignite", "Sub-bituminous coal"]
COAL_PRODUCTS = ["Coke-oven coke", "Coke oven coke", "Coke Oven Coke", "Brown coal briquettes", "Brown Coal Briquettes", "Patent fuel"]
COAL_PRODUCTS_TJ = ["Blast Furnace Gas", "Blast furnace gas", "Coke Oven Gas", "Gasworks Gas"]
GAS = ["Natural gas (including LNG)", "Natural Gas (including LNG)", "Natural gas"]
BIO_KT = ["Charcoal", "Bagasse", "Biodiesel", "Biogasoline", "Bio jet kerosene"]
BIO_TJ = ["Biogases", "Black Liquor", "Animal waste"]
OIL_PRODUCTS = ["Gas Oil/ Diesel Oil", "Motor Gasoline", "Motor gasoline", "Kerosene-type Jet Fuel", "Aviation gasoline", "Gasoline-type jet fuel",
                "Other kerosene", "Fuel oil", "Liquefied petroleum gas (LPG)", "Liquified Petroleum Gas (LPG)", "Naphtha", "Bitumen", "Lubricants",
                "Petroleum coke", "Petroleum Coke", "Paraffin waxes", "Refinery gas", "Refinery Gas", "Ethane"]
ALIAS = {"Hrad coal": "Hard coal", "Coke oven coke": "Coke-oven coke", "Coke Oven Coke": "Coke-oven coke", "Brown Coal Briquettes": "Brown coal briquettes",
         "Liquified Petroleum Gas (LPG)": "Liquefied petroleum gas (LPG)", "Petroleum Coke": "Petroleum coke", "Refinery Gas": "Refinery gas",
         "Natural Gas (including LNG)": "Natural gas (including LNG)", "Natural gas": "Natural gas (including LNG)", "Blast furnace gas": "Blast Furnace Gas",
         "Motor gasoline": "Motor Gasoline"}
FLOWS = ["Primaryproduction", "Imports", "Exports", "Finalenergyconsumption", "Manufacturing,const.,mining", "Ironandsteel", "Chemicalandpetrochemical",
         "Non-ferrousmetals", "Non-metallicminerals", "Transportequipment", "Machinery", "Miningandquarrying", "Foodandtobacco", "Paper,pulpandprinting",
         "Woodandwoodproducts", "Textileandleather", "Construction", "Industriesn.e.s", "Households", "Commerce,publicservices",
         "Agriculture,forestry,fishing", "Otherconsumers", "Road", "Rail", "Domesticaviation", "Domesticnavigation", "Non-energyuse"]


def export_2019() -> tuple[pd.DataFrame, pd.DataFrame]:
    d = cm.unsd_export()
    d = d[d.Year.eq("2019") & d.q.notna()].copy()
    d["flow"] = d.transaction.map(cm.flow_of)
    d = d[d.flow.notna()].copy()
    d["com"] = d.commodity.map(lambda c: ALIAS.get(c, c))
    conflicts = []
    rows = []
    for (cc, com, flow), g in d.groupby(["country", "com", "flow"]):
        vals = sorted(set(np.round(g.q.values, 6)))
        if len(vals) > 1:
            conflicts.append(dict(country=cc, commodity=com, flow=flow, values=";".join(map(str, vals)),
                                  transactions=" | ".join(sorted(set(g.transaction))), units=";".join(sorted(set(g.Unit)))))
        rows.append(dict(country=cc, commodity=com, flow=flow, unit=g.Unit.iloc[0], q=max(vals, key=abs)))
    return pd.DataFrame(rows), pd.DataFrame(conflicts)


def parent_check(E: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (cc, flow), g in E.groupby(["country", "flow"]):
        q = g.set_index("commodity").q
        for parent, kids in (("Hard coal", HARD_CHILD), ("Brown coal", BROWN_CHILD)):
            k = [c for c in kids if c in q.index]
            if parent in q.index and k:
                out.append(dict(country=cc, flow=flow, parent=parent, parent_kt=q[parent], children=";".join(k), children_kt=float(q[k].sum()),
                                diff_kt=q[parent] - float(q[k].sum())))
    return pd.DataFrame(out)


def coal_parents(q: pd.Series) -> dict:
    """{'Hard coal': kt, 'Brown coal': kt, 'Peat': kt} at parent level, plus which children were used when no parent is reported."""
    res = {}
    for parent, kids in (("Hard coal", HARD_CHILD), ("Brown coal", BROWN_CHILD)):
        if parent in q.index:
            res[parent] = float(q[parent])
        elif any(c in q.index for c in kids):
            res[parent] = float(sum(q.get(c, 0.0) for c in kids))
    if "Peat" in q.index:
        res["Peat"] = float(q["Peat"])
    return res


def std_tj(com: str, qty: float, unit: str) -> float:
    if unit.startswith("Terajoules"):
        return qty * (0.90 if com == "Natural gas (including LNG)" else 1.0)
    if com == "Fuelwood":
        return qty * cm.UNSD_STD["Fuelwood (TJ per 10^3 m3)"]
    key = cm.COMMODITY_REF.get(com, (None,))[0]
    if key is None:
        return np.nan
    return qty * cm.UNSD_STD[key]


def by_flow(E: pd.DataFrame, B: pd.DataFrame, conv: dict) -> pd.DataFrame:
    b19 = B[B.year == 2019]
    out = []
    for cc in cm.ISO:
        e = E[E.country == cc]
        b = b19[b19.country == cc]
        lay = b.layout.iloc[0]
        for flow in FLOWS:
            g = e[e.flow == flow]
            q = g.set_index("commodity").q
            unit = g.set_index("commodity").unit
            groups = {}
            cp = coal_parents(q)
            groups["coal_primary"] = [(k, v, "Metric tons,  thousand") for k, v in cp.items()]
            groups["coal_products"] = [(c, q[c], unit[c]) for c in ["Coke-oven coke", "Brown coal briquettes", "Patent fuel", "Blast Furnace Gas"] if c in q.index]
            groups["oil_products"] = [(c, q[c], unit[c]) for c in sorted(set(ALIAS.get(x, x) for x in OIL_PRODUCTS)) if c in q.index]
            groups["natural_gas"] = [(c, q[c], unit[c]) for c in ["Natural gas (including LNG)"] if c in q.index]
            groups["biofuels"] = [(c, q[c], unit[c]) for c in ["Fuelwood"] + BIO_KT + BIO_TJ if c in q.index]
            if lay == "detailed":
                pubcols = {"coal_primary": ["Primary coal and peat"], "coal_products": ["Coal and peat products"], "oil_products": ["Oil products"],
                           "natural_gas": ["Natural gas"], "biofuels": ["Biofuels and waste"]}
            else:
                pubcols = {"coal_all": ["All coal"], "oil_products": ["All oil"], "natural_gas": ["Natural gas"], "biofuels": ["Primary biofuels/waste", "Charcoal"]}
                groups["coal_all"] = groups.pop("coal_primary") + groups.pop("coal_products")
            pflow = flow
            for grp, items in groups.items():
                z = b[(b.flow == pflow) & b.column.isin(pubcols[grp])]
                pub = float(z.value_tj.fillna(0).sum()) if not z.empty else np.nan
                pub_est = bool(z.estimate.any()) if not z.empty else False
                if not items and (np.isnan(pub) or pub == 0):
                    continue
                stdv = float(np.nansum([std_tj(c, v, u) for c, v, u in items])) if items else 0.0
                upv = 0.0
                for c, v, u in items:
                    if u.startswith("Terajoules"):
                        upv += v
                    elif u.startswith("Kilowatt"):
                        upv += v * 3.6
                    else:
                        f = conv.get(c) if c not in ("Hard coal", "Brown coal") else conv[c]
                        upv += v * f * 3600 if f is not None else 0.0
                out.append(dict(country=cc, flow=flow, group=grp, layout=lay, commodities=";".join(f"{c}={v:g}" for c, v, _ in items),
                                tj_unsd_standard=stdv, tj_upstream_factors=upv, tj_publication=pub, publication_estimate=pub_est,
                                ratio_pub_to_standard=(pub / stdv if stdv else np.nan), ratio_pub_to_upstream=(pub / upv if upv else np.nan)))
    return pd.DataFrame(out)


def implied_coal(F: pd.DataFrame, E: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cc in cm.ISO:
        f = F[(F.country == cc) & F.group.isin(["coal_primary", "coal_all"])]
        for _, r in f.iterrows():
            items = [x.split("=") for x in r.commodities.split(";") if x]
            if len(items) != 1 or np.isnan(r.tj_publication) or r.tj_publication == 0:
                continue
            com, kt = items[0][0], float(items[0][1])
            if com not in ("Hard coal", "Brown coal") or kt == 0 or r.group == "coal_all" and r.flow not in ("Manufacturing,const.,mining", "Households"):
                pass
            if com not in ("Hard coal", "Brown coal"):
                continue
            rows.append(dict(country=cc, flow=r.flow, commodity=com, kt=kt, tj_publication=abs(r.tj_publication), gj_per_t=abs(r.tj_publication) / abs(kt),
                             publication_estimate=r.publication_estimate, layout=r.layout))
    D = pd.DataFrame(rows)
    D["source"] = "UN Energy Balances 2019 publication"
    return D


VIS_LABEL = {"Primary production": "Primaryproduction", "Imports": "Imports", "Exports": "Exports", "Final Energy Consumption": "Finalenergyconsumption",
             "Manufacturing  const. and mining": "Manufacturing,const.,mining", "Iron and steel": "Ironandsteel",
             "Chemical and petrochemical": "Chemicalandpetrochemical", "Non-metallic minerals": "Non-metallicminerals",
             "Industries n.e.s.": "Industriesn.e.s", "Households": "Households", "Commerce and public services": "Commerce,publicservices",
             "Other consumers": "Otherconsumers", "Agriculture  forestry and fishing": "Agriculture,forestry,fishing"}


def implied_coal_vis(E: pd.DataFrame) -> pd.DataFrame:
    """Same ratio with the repository's UNSD Energy Balance Visualization exports (BN, KH, LA, TL; later data vintage than the publication)."""
    rows = []
    for cc in ("BN", "KH", "LA", "TL"):
        v = pd.read_csv(cm.REPO / f"research_inputs/registry_v5/sources/UNSD_EB_2019_{cc}.csv", dtype=str)
        tr = v.columns[1]
        for _, r in v.iterrows():
            flow = VIS_LABEL.get(" ".join(str(r[tr]).split(" ")).strip())
            if flow is None:
                continue
            tj = str(r["Primary Coal and Peat"]).strip().lstrip("*")
            if tj in ("---", "", "nan") or float(tj) == 0:
                continue
            q = E[(E.country == cc) & (E.flow == flow)].set_index("commodity").q
            cp = coal_parents(q)
            if len(cp) != 1:
                continue
            com, kt = next(iter(cp.items()))
            if kt == 0:
                continue
            rows.append(dict(country=cc, flow=flow, commodity=com, kt=abs(kt), tj_publication=abs(float(tj)), gj_per_t=abs(float(tj)) / abs(kt),
                             publication_estimate=str(r["Primary Coal and Peat"]).strip().startswith("*"), layout="visualisation",
                             source="UNSD Energy Balance Visualization 2019 export (repository copy)"))
    return pd.DataFrame(rows)


def summarise(D: pd.DataFrame) -> pd.DataFrame:
    """A country value is VERIFIED only if >= 2 flows with DIFFERENT quantities (> 0.5 % apart) give the same NCV within 0.5 %."""
    summ = []
    for (cc, com, src), g in D.groupby(["country", "commodity", "source"]):
        best = None
        for _, r in g.iterrows():
            agree = g[np.abs(g.gj_per_t / r.gj_per_t - 1) <= 0.005]
            kts = sorted(agree.kt.values)
            distinct = 1 + sum(1 for a_, b_ in zip(kts, kts[1:]) if b_ / a_ - 1 > 0.005)
            if best is None or distinct > best[0]:
                best = (distinct, agree)
        distinct, agree = best
        ok = distinct >= 2
        summ.append(dict(country=cc, commodity=com, source=src, flows=len(g), flows_agreeing=len(agree), distinct_quantities_agreeing=distinct,
                         implied_gj_per_t=(float((agree.tj_publication.sum()) / agree.kt.sum()) if ok else np.nan),
                         min=float(g.gj_per_t.min()), max=float(g.gj_per_t.max()),
                         status=("VERIFIED (>= 2 flows with different quantities agree within 0.5 %)" if ok else "NOT_DERIVABLE (no two independent flows agree: data vintage)"),
                         agreeing_flows=";".join(agree.flow)))
    return pd.DataFrame(summ)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); a = ap.parse_args()
    conv, _ = cm.upstream_dicts()
    E, C = export_2019()
    B = pd.read_csv(a.work / "ncv/UN_EB2019_ASEAN11_TJ.csv")
    P = parent_check(E)
    F = by_flow(E, B, conv)
    D = pd.concat([implied_coal(F, E), implied_coal_vis(E)], ignore_index=True)
    S = summarise(D)
    out = a.work / "ncv"
    E.to_csv(out / "UNSD_EXPORT_2019_BY_FLOW_COMMODITY.csv", index=False, float_format="%.12g")
    C.to_csv(out / "UNSD_EXPORT_DUPLICATE_CONFLICTS.csv", index=False)
    P.to_csv(out / "UNSD_COAL_PARENT_CHECK.csv", index=False, float_format="%.12g")
    F.to_csv(out / "UNSD_EXPORT_VS_EB2019_BY_FLOW.csv", index=False, float_format="%.12g")
    D.to_csv(out / "UNSD_IMPLIED_COAL_NCV_2019_BY_FLOW.csv", index=False, float_format="%.12g")
    S.to_csv(out / "UNSD_IMPLIED_COAL_NCV_2019.csv", index=False, float_format="%.12g")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 80)
    print("duplicate conflicts:", len(C)); print(C.to_string()[:3000])
    print("parent check: max |parent - children| kt =", P.diff_kt.abs().max(), "rows", len(P))
    print(S.to_string())
    print(D.to_string())


if __name__ == "__main__":
    main()
