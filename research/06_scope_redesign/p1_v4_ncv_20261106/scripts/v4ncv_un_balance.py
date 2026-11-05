"""V4 W11 section 2.1: the UN Energy Balances 2019 (UNSD publication, TJ on an NCV basis with UNSD's country-specific factors for solids and
liquids) parsed for the 11 ASEAN countries, 2018 and 2019, from the page text in extracted/un_eb2019/ (v4ncv_pdf_text.py).

    python scripts/v4ncv_un_balance.py --work <work dir>

Output ncv/UN_EB2019_ASEAN11_TJ.csv (country, year, flow, column, value_tj, estimate flag '*', pdf page, layout) and
ncv/UN_EB2019_VS_REPO_VISUALISATION.csv: the 2019 values of BN, KH, LA, TL compared with the repository copies of the UNSD Energy Balance
Visualization exports (research_inputs/registry_v5/sources/UNSD_EB_2019_<cc>.csv), which are a later data vintage (S2-0).
Detailed layout = 11 columns; simplified layout (small countries) = 8 columns with both years on one page.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4ncv_common as cm   # noqa: E402

DETAILED = ["Primary coal and peat", "Coal and peat products", "Primary oil", "Oil products", "Natural gas", "Biofuels and waste", "Nuclear",
            "Electricity", "Heat", "Total energy", "of which renewables"]
SIMPLE = ["All coal", "All oil", "Natural gas", "Primary biofuels/waste", "Charcoal", "Electricity", "Total energy", "of which renewables"]
HEAD = {"BN": "BruneiDarussalam", "KH": "Cambodia", "ID": "Indonesia", "LA": "LaoPeople'sDem.Rep.", "MY": "Malaysia", "MM": "Myanmar",
        "PH": "Philippines", "SG": "Singapore", "TH": "Thailand", "TL": "Timor-Leste", "VN": "VietNam"}
TOK = re.compile(r"^\*?-?\d+$|^\.\.$")


def parse_pages(work: Path) -> pd.DataFrame:
    d = work / "extracted/un_eb2019"
    rows = []
    pages = sorted(d.glob("p[0-9][0-9][0-9].txt"))
    for p in pages:
        txt = p.read_text(encoding="utf-8")
        lines = [ln.rstrip() for ln in txt.splitlines()]
        head = next((ln.strip() for ln in lines if ln.strip()), "")
        cc = next((k for k, v in HEAD.items() if head == v), None)
        if cc is None:
            continue
        layout = "simplified" if "AllCoal" in txt else "detailed"
        cols = SIMPLE if layout == "simplified" else DETAILED
        year = None
        for ln in lines:
            s = ln.strip()
            if re.fullmatch(r"20(18|19)", s):
                year = int(s)
                continue
            parts = s.split()
            if len(parts) < 2 or year is None:
                continue
            label, vals = parts[0], parts[1:]
            if not all(TOK.match(v) for v in vals):
                continue
            if len(vals) != len(cols):
                raise ValueError(f"{p.name} {cc} {year} {label}: {len(vals)} values for {len(cols)} columns")
            for c, v in zip(cols, vals):
                est = v.startswith("*")
                num = None if v == ".." else float(v.lstrip("*"))
                rows.append(dict(country=cc, year=year, flow=label, column=c, value_tj=num, estimate=est, pdf_page=int(p.stem[1:]), layout=layout))
    return pd.DataFrame(rows)


VIS_FLOW = {"Primary production": "Primaryproduction", "Imports": "Imports", "Exports": "Exports", "Final consumption": "Finalconsumption",
            "Final Energy Consumption": "Finalenergyconsumption", "Manufacturing  const. and mining": "Manufacturing,const.,mining",
            "Households": "Households", "Electricity Plants": "Electricityplants", "Non-metallic minerals": "Non-metallicminerals",
            "Commerce and public services": "Commerce,publicservices"}
VIS_COLS = {"All coal": ["Primary Coal and Peat", "Coal and Peat Products"], "All oil": ["Primary Oil", "Oil Products"], "Natural gas": ["Natural Gas"],
            "Biofuels (all)": ["Biofuels and Waste"], "Electricity": ["Electricity"]}


def num(v):
    v = str(v).strip().lstrip("*")
    return 0.0 if v in ("---", "", "nan") else float(v)


def compare_vis(B: pd.DataFrame) -> pd.DataFrame:
    out = []
    for cc in ("BN", "KH", "LA", "TL"):
        v = pd.read_csv(cm.REPO / f"research_inputs/registry_v5/sources/UNSD_EB_2019_{cc}.csv", dtype=str)
        v.columns = [c.strip() for c in v.columns]
        tr = v.columns[1]
        b = B[(B.country == cc) & (B.year == 2019)]
        lay = b.layout.iloc[0]
        for vf, bf in VIS_FLOW.items():
            vr = v[v[tr].str.strip() == vf]
            if vr.empty:
                continue
            for agg, vcols in VIS_COLS.items():
                vis = sum(num(vr[c].iloc[0]) for c in vcols)
                if lay == "simplified":
                    bcols = {"All coal": ["All coal"], "All oil": ["All oil"], "Natural gas": ["Natural gas"],
                             "Biofuels (all)": ["Primary biofuels/waste", "Charcoal"], "Electricity": ["Electricity"]}[agg]
                else:
                    bcols = {"All coal": ["Primary coal and peat", "Coal and peat products"], "All oil": ["Primary oil", "Oil products"],
                             "Natural gas": ["Natural gas"], "Biofuels (all)": ["Biofuels and waste"], "Electricity": ["Electricity"]}[agg]
                z = b[(b.flow == bf) & b.column.isin(bcols)]
                if z.empty:
                    continue
                pub = float(z.value_tj.fillna(0).sum())
                out.append(dict(country=cc, flow=bf, group=agg, publication_tj=pub, visualisation_tj=vis, diff_tj=vis - pub,
                                same=abs(vis - pub) <= 1.0))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); a = ap.parse_args()
    B = parse_pages(a.work)
    got = B.groupby(["country", "year"]).size().unstack()
    print(got)
    missing = [(c, y) for c in cm.ISO for y in (2018, 2019) if c not in got.index or pd.isna(got.loc[c].get(y))]
    if missing:
        raise ValueError(f"pages not parsed: {missing}")
    (a.work / "ncv").mkdir(exist_ok=True)
    B.to_csv(a.work / "ncv/UN_EB2019_ASEAN11_TJ.csv", index=False)
    # internal check: the components of manufacturing add up to the printed manufacturing row (detailed layout)
    chk = []
    sub = ["Ironandsteel", "Chemicalandpetrochemical", "Non-ferrousmetals", "Non-metallicminerals", "Transportequipment", "Machinery",
           "Miningandquarrying", "Foodandtobacco", "Paper,pulpandprinting", "Woodandwoodproducts", "Textileandleather", "Construction",
           "Industriesn.e.s"]
    for (cc, y, col), g in B[B.layout == "detailed"].groupby(["country", "year", "column"]):
        m = g[g.flow == "Manufacturing,const.,mining"].value_tj.fillna(0).sum()
        s = g[g.flow.isin(sub)].value_tj.fillna(0).sum()
        chk.append(dict(country=cc, year=y, column=col, manufacturing_tj=m, sum_subsectors_tj=s, diff_tj=m - s))
    C = pd.DataFrame(chk)
    C.to_csv(a.work / "ncv/UN_EB2019_INTERNAL_CHECK.csv", index=False)
    print("internal check: max |manufacturing - sum of sub-sectors| TJ =", C.diff_tj.abs().max(), "rows > 2 TJ:", int((C.diff_tj.abs() > 2).sum()))
    V = compare_vis(B)
    V.to_csv(a.work / "ncv/UN_EB2019_VS_REPO_VISUALISATION.csv", index=False)
    print(V.groupby("country").same.agg(["sum", "size"]))
    print(V[~V.same].to_string())


if __name__ == "__main__":
    main()
