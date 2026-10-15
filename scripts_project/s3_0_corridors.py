"""S3-0 (decisions 59/62): APG AIMS III 2024 corridors TH-MM (#11) and LA-MM (#17) added to the corridor table, and a cross-check of
the corridor table against the 18 APG priority interconnections (ACE 2024 APG Interconnections Project Profiles, Table 1 p.2).

* #11 Thailand - Myanmar: existing 0, future 365 MW -> candidate corridor (extendable AC line, s_nom 0).
* #17 Lao PDR - Myanmar: existing 30 MW, future 100-600 MW -> 30 MW as 2025 stock (s_nom_min), expansion endogenous.
* Border nodes: the nearest AC node pair of the two countries by great-circle distance (s1_network_nodes_xy.csv); the next candidates are
  listed as justification. Length = great-circle x the median length / great-circle ratio of the 19 existing cross-border AC lines
  (the frozen base's own routing convention), subsea_share 0 (land borders).
* Cross-check: covered (corridor table has the country pair) / table_only / apg_only / internal (single-country APG projects, out of scope).
  Only the two decided additions are made; every other difference is reported.
The lines themselves are created at build time (s2_layers.add_apg_corridor_lines) from the rows written here.

    python scripts_project/s3_0_corridors.py
"""
from __future__ import annotations

import math

import pandas as pd

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, src_sha, write_csv, write_json

SCRIPT = "scripts_project/s3_0_corridors.py"
CORR = ROOT / "research_inputs/corridors/cross_border_corridors.csv"
OUT_DIR = ROOT / "research_inputs/corridors"
APG = "APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv"
XY = "s1_network_nodes_xy.csv"
RAW8_SUMS = SRC_DIR / "SHA256SUMS_raw8.txt"
# corridor-table components -> APG project (by border section; Peninsular MY-TH incl. the HVDC links = #2, Sarawak-W.Kalimantan = #6)
COMPONENT_TO_APG = {"92": "1", "91": "2", "250878579-1_0": "2", "250878579-2_0": "2", "250878579-3_0": "2", "250878579-4_0": "2", "Khlong Ngae \u2013 Gurun": "2", "23": "6",
                    "49": "9", "52": "9", "53": "9", "55": "9", "56": "9", "58": "9", "61": "9", "62": "9", "66": "9", "59": "10", "60": "10", "63": "10", "64": "10",
                    "APG11_TH_MM": "11", "39": "12", "43": "13", "47": "14", "APG17_LA_MM": "17"}
ADDITIONS = [
    dict(apg_no="11", component="APG11_TH_MM", country_a="MM", country_b="TH", capacity_2025_mw=0.0, planned_mw=365.0,
         status="APG_AIMS3_2024_CANDIDATE (decision 62): existing 0, future 365 MW -> extendable AC line, s_nom 0"),
    dict(apg_no="17", component="APG17_LA_MM", country_a="LA", country_b="MM", capacity_2025_mw=30.0, planned_mw=600.0,
         status="APG_AIMS3_2024_EXISTING_30MW (decision 62): 30 MW as 2025 stock (s_nom_min), future 100-600 MW endogenous"),
]


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, [a.y, a.x, b.y, b.x])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def main():
    xy = pd.read_csv(SRC_DIR / XY).set_index("Bus"); xy_sha = src_sha(XY)
    apg = pd.read_csv(SRC_DIR / APG, dtype=str, keep_default_na=False); apg_sha = src_sha(APG)
    raw8 = {l.split()[1].split("/")[-1]: l.split()[0] for l in RAW8_SUMS.read_text().splitlines() if l.strip()}
    pdf_sha = next((v for k, v in raw8.items() if "APG" in k), "")
    corr = pd.read_csv(CORR, float_precision="round_trip", keep_default_na=False)
    base = corr[corr.status == "EXISTING_2025"]
    ratios = [float(r.length_km) / hav(xy.loc[r["from"]], xy.loc[r["to"]]) for _, r in base.iterrows() if r.component_type == "Line"]
    lf = float(pd.Series(ratios).median())
    # ---- nearest border nodes and corridor rows ---------------------------------------------------------------
    choices, new_rows = {}, []
    for a in ADDITIONS:
        A = xy[xy.country == a["country_a"]]; B = xy[xy.country == a["country_b"]]
        pairs = sorted(((hav(A.loc[i], B.loc[j]), i, j) for i in A.index for j in B.index))
        d, i, j = pairs[0]
        choices[a["component"]] = dict(from_node=i, to_node=j, great_circle_km=d, length_km=d * lf, length_factor=lf,
                                       alternatives=[dict(from_node=i2, to_node=j2, great_circle_km=d2) for d2, i2, j2 in pairs[1:4]])
        row = {"from": i, "to": j, "carrier": "AC", "length_km": d * lf, "subsea_share": 0.0,
               "source": (f"ACE 2024 APG Interconnections Project Profiles (raw8 PDF SHA256 {pdf_sha}) -> extraction {APG} apg_no {a['apg_no']} (Table 1 p.2): "
                          f"existing {a['capacity_2025_mw']:.0f} MW, future {a['planned_mw']:.0f} MW; nodes = nearest AC node pair by great-circle distance ({d:.0f} km; next "
                          f"{pairs[1][1]}-{pairs[1][2]} {pairs[1][0]:.0f} km); length = great-circle x {lf:.4f} (median length/great-circle of the 19 existing cross-border AC lines); "
                          f"subsea_share 0 (land border); capital cost and electrical parameters per km from the frozen base at build time (s2_layers.add_apg_corridor_lines)"),
               "component_type": "Line", "component": a["component"], "country_from": a["country_a"], "country_to": a["country_b"], "capacity_2025_mw": a["capacity_2025_mw"],
               "nominal_mw_in_base": a["capacity_2025_mw"], "nominal_minus_lower_bound_mw": 0.0, "status": a["status"]}
        new_rows.append(row)
    corr = corr[~corr.component.isin([a["component"] for a in ADDITIONS])]
    out = pd.concat([corr, pd.DataFrame(new_rows)], ignore_index=True)
    out.to_csv(CORR, index=False, lineterminator="\n")
    # ---- cross-check corridor table vs APG --------------------------------------------------------------------
    def pair(a, b):
        return tuple(sorted([a, b]))
    tbl = out.groupby(out.apply(lambda r: pair(r.country_from, r.country_to), axis=1))
    tbl_pairs = {k: g for k, g in tbl}
    rows, seen = [], set()
    for _, r in apg.iterrows():
        pr = pair(r.country_a, r.country_b); seen.add(pr)
        g_pair = tbl_pairs.get(pr)
        comps = [c for c, k in COMPONENT_TO_APG.items() if k == r.apg_no]
        g = out[out.component.astype(str).isin(comps)] if comps else None
        if r.country_a == r.country_b:
            cls = "internal_single_country (out of scope: domestic transmission is endogenous)"
        elif g is not None and len(g):
            cls = "covered_added_s3_0 (decision 62)" if any(c in [a["component"] for a in ADDITIONS] for c in g.component) else "covered"
        elif g_pair is not None:
            cls = f"apg_only_same_country_pair (table rows {';'.join(map(str, g_pair.component))} belong to another APG project; no addition decided)"
        else:
            cls = "apg_only (not in the corridor table; no addition decided)"
        cap_tbl = float(pd.to_numeric(g.capacity_2025_mw, errors="coerce").sum()) if (g is not None and len(g)) else None
        ex = num(r.existing_MW)
        diff = ""
        if cap_tbl is not None and ex is not None and abs(ex - cap_tbl) > 0.05 * max(ex, cap_tbl, 1.0):
            diff = f"APG existing {ex:.0f} MW vs corridor-table 2025 capacity {cap_tbl:.1f} MW"
        elif cap_tbl is not None and ex is None and cap_tbl > 0:
            diff = f"APG existing not stated vs corridor-table 2025 capacity {cap_tbl:.1f} MW"
        rows.append(dict(apg_no=r.apg_no, connection=r.connection, country_pair=f"{pr[0]}-{pr[1]}", apg_existing_mw=r.existing_MW, apg_ongoing_to_2024_mw=r.ongoing_to_2024_MW, apg_future_mw=r.future_MW,
                         apg_total_mw=r.total_MW, aims3_2040_projection_mw=r.aims3_2040_projection_MW, apg_note=r.note, classification=cls,
                         corridor_components=";".join(map(str, g.component)) if g is not None else "", corridor_capacity_2025_mw=cap_tbl if cap_tbl is not None else "", difference=diff,
                         source_locator=r.source_locator))
    for pr, g in tbl_pairs.items():
        g = g[~g.component.astype(str).isin(COMPONENT_TO_APG)]
        if len(g):
            rows.append(dict(apg_no="", connection="", country_pair=f"{pr[0]}-{pr[1]}", apg_existing_mw="", apg_ongoing_to_2024_mw="", apg_future_mw="", apg_total_mw="", aims3_2040_projection_mw="", apg_note="",
                             classification="table_only (existing in the frozen base, not an APG priority project)", corridor_components=";".join(map(str, g.component)),
                             corridor_capacity_2025_mw=float(pd.to_numeric(g.capacity_2025_mw, errors="coerce").sum()), difference="", source_locator=""))
    cols = ["apg_no", "connection", "country_pair", "apg_existing_mw", "apg_ongoing_to_2024_mw", "apg_future_mw", "apg_total_mw", "aims3_2040_projection_mw", "apg_note", "classification",
            "corridor_components", "corridor_capacity_2025_mw", "difference", "source_locator"]
    write_csv(rows, OUT_DIR / "CORRIDOR_APG_CROSSCHECK_2024.csv", cols)
    counts = pd.Series([r["classification"].split(" ")[0] for r in rows]).value_counts().to_dict()
    # ---- registry -----------------------------------------------------------------------------------------------
    reg = Registry(SCRIPT)
    src = "ACE 2024 APG Interconnections Project Profiles, Table 1 p.2 (raw8) -> " + APG
    for a in ADDITIONS:
        ch = choices[a["component"]]
        reg.add(f"corridor_{a['component'].lower()}_capacity_2025", f"APG #{a['apg_no']} {a['country_a']}-{a['country_b']} existing capacity (2025 stock, s_nom_min)", a["capacity_2025_mw"], "MW", "B", src, f"apg_no {a['apg_no']}", f"pdf:{pdf_sha}|csv:{apg_sha}",
                decision_ref="59,62", status="REGISTERED" if a["capacity_2025_mw"] > 0 else "SOURCE_ZERO")
        reg.add(f"corridor_{a['component'].lower()}_planned", f"APG #{a['apg_no']} {a['country_a']}-{a['country_b']} planned/future capacity (upper reference for the endogenous expansion; not a bound)", a["planned_mw"], "MW", "B", src,
                f"apg_no {a['apg_no']}", f"pdf:{pdf_sha}|csv:{apg_sha}", decision_ref="59,62", status="REFERENCE_ONLY")
        reg.add(f"corridor_{a['component'].lower()}_nodes", f"{ch['from_node']} - {ch['to_node']}: nearest AC node pair by great-circle distance {ch['great_circle_km']:.0f} km (next: " +
                "; ".join(f"{x['from_node']}-{x['to_node']} {x['great_circle_km']:.0f} km" for x in ch["alternatives"]) + f"); length {ch['length_km']:.1f} km = great-circle x {lf:.4f}",
                round(ch["length_km"], 3), "km", "C", "derived (s1_network_nodes_xy.csv)", "s3_0_corridors.py", xy_sha, decision_ref="62", sensitivity_low=round(ch["great_circle_km"], 3), sensitivity_high=round(ch["great_circle_km"] * 1.5, 3))
    reg.add("corridor_length_factor_frozen_base", "Median length / great-circle distance of the 19 existing cross-border AC lines in the frozen electric base (routing convention applied to the added corridors)", round(lf, 6), "ratio", "B",
            "derived (cross_border_corridors.csv x s1_network_nodes_xy.csv)", "s3_0_corridors.py", xy_sha, decision_ref="62")
    reg.add("corridor_apg_crosscheck_2024", "Corridor table (26 rows) vs APG AIMS III 2024 priority interconnections: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + " (file CORRIDOR_APG_CROSSCHECK_2024.csv)",
            len(rows), "rows", "B", src, "Table 1 p.2", f"pdf:{pdf_sha}|csv:{apg_sha}", decision_ref="59,62", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "corridors_apg.csv")
    write_json(dict(script=SCRIPT, sources=dict(apg_csv=apg_sha, apg_pdf=pdf_sha, nodes_xy=xy_sha), length_factor=lf, length_ratios_existing=ratios, choices=choices, additions=new_rows,
                    crosscheck_counts=counts, corridor_table_sha256=sha256(CORR)), OUT_DIR / "CORRIDOR_APG_EVIDENCE.json")
    print(pd.DataFrame(rows)[["apg_no", "country_pair", "apg_existing_mw", "classification", "corridor_components", "corridor_capacity_2025_mw", "difference"]].to_string())
    print("length factor", round(lf, 4), "choices", {k: (v["from_node"], v["to_node"], round(v["length_km"], 1)) for k, v in choices.items()})


if __name__ == "__main__":
    main()
