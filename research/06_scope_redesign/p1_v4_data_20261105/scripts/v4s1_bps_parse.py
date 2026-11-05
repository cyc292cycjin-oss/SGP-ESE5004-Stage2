"""V4 S1 section 4.1 (step 3): BPS IBS 2019 tables 5.1 (electricity generated / purchased / sold by industrial code) and 6a.1 (fuel and
lubricant quantities by industrial code) from the glyph tokens of v4s1_bps_glyphs.py; reconciliation against the printed totals.

    python scripts/v4s1_bps_parse.py --work <work dir>          (WSL pypsa-earth python)

Reading rules (printed note of every table page): bold = total large and medium industry (IBS), italic = large industry, '*' = not
published, '-' = zero. In the token layout every record is one line that starts with the industrial code (the IBS total) and, when
present, a following line without a code (large industry; '* ...' when not published). Values are taken from the IBS-total line.
Columns: numbers are right-aligned, so each value token goes to the column whose right edge (cluster of token right edges on that
page) is nearest; a page whose clusters do not match the expected column count stops the run.

Check (written to s1/ID_BPS_PARSE_CHECK.csv): every printed 3-digit row against the sum of its printed 4-digit rows, every 2-digit
row against its 3-digit rows, the printed Total against the 2-digit rows, for IBS totals and large industry separately. A child
marked '*' makes the sum a lower bound (flag). |difference| > 0.5 % is listed with the reason found.
Outputs: s1/ID_BPS_IBS_2019_RAW.csv (every code row, both lines, raw tokens and flags) and the check table; the 2-digit energy table is
built by v4s1_bps_energy.py.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

TABLES = {
    "5.1": dict(pages=[(p, "left") for p in range(109, 121)],
                cols={"left": ["el_generated_kwh", "el_purchased_kwh", "el_purchased_value_krp", "el_sold_kwh", "el_sold_value_krp"]}),
    "6a.1": dict(pages=[(p, "left" if p % 2 else "right") for p in range(123, 149)],
                 cols={"left": ["gasoline_l", "diesel_l", "coal_kg", "coal_briquette_kg"],
                       "right": ["gas_pgn_m3", "gas_nonpgn_m3", "lpg_l", "lubricant_l"]}),
}
NUM = re.compile(r"^\d+$")
CODE = re.compile(r"^(\d{2,4}|Total)$")


def page_records(tok: pd.DataFrame, side: str, cols: list, page: int):
    hdr = tok[tok.text == "(1)"]
    if hdr.empty:
        raise ValueError(f"p{page}: header '(1)' not found")
    hy, hx = float(hdr.line_y.iloc[0]), float((hdr.x0.iloc[0] + hdr.x1.iloc[0]) / 2)
    foot = tok[tok.text.str.startswith("Catatan")]
    fy = float(foot.line_y.iloc[0]) if len(foot) else -1.0
    d = tok[(tok.line_y < hy - 1) & (tok.line_y > fy + 1)].copy()
    d["xc"] = (d.x0 + d.x1) / 2
    is_code = d.text.str.match(CODE) & ((d.xc - hx).abs() < 30)
    vals = d[~is_code & d.text.str.match(r"^(\d+|-|\*)$")]
    other = d[~is_code & ~d.text.str.match(r"^(\d+|-|\*)$")]
    if len(other):
        raise ValueError(f"p{page}: unexpected tokens in the data area {other.text.tolist()[:10]}")
    # column right edges: clusters of value-token right edges
    xs = np.sort(vals.x1.values)
    edges, cur = [], [xs[0]]
    for x in xs[1:]:
        if x - cur[-1] > 8.0:
            edges.append(float(np.median(cur))); cur = [x]
        else:
            cur.append(x)
    edges.append(float(np.median(cur)))
    if len(edges) != len(cols):
        raise ValueError(f"p{page} {side}: {len(edges)} column clusters {edges} for {len(cols)} columns")
    recs, last = [], None
    for y, g in d.groupby("line_y", sort=False):
        pass
    for y in sorted(d.line_y.unique(), reverse=True):
        g = d[d.line_y == y]
        code = g[is_code.loc[g.index]]
        row = {c: None for c in cols}
        for _, t in g[~is_code.loc[g.index]].iterrows():
            k = int(np.argmin([abs(t.x1 - e) for e in edges]))
            if abs(t.x1 - edges[k]) > 6.0:
                raise ValueError(f"p{page}: token {t.text} at {t.x1} not near a column edge {edges}")
            if row[cols[k]] is not None:
                raise ValueError(f"p{page}: two tokens in column {cols[k]} on line {y}")
            row[cols[k]] = t.text
        if len(code):
            last = dict(page=page, side=side, line_y=y, code=code.text.iloc[0], total=row, large=None)
            recs.append(last)
        else:
            if last is None or last["large"] is not None:
                raise ValueError(f"p{page}: line {y} without a code and no open record")
            last["large"] = row
    return recs, edges


def value(tok):
    if tok is None:
        return np.nan, "blank"
    if tok == "-":
        return 0.0, "dash"
    if tok == "*":
        return np.nan, "star"
    return float(tok), ""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    T = a.work / "extracted/12_bps_indonesia/bps_tokens"; out = a.work / "s1"; out.mkdir(exist_ok=True)
    raw, checks, meta = [], [], {}
    for tab, spec in TABLES.items():
        recs = {"left": [], "right": []}
        for p, side in spec["pages"]:
            tok = pd.read_csv(T / f"p{p:03d}.csv", dtype={"text": str})
            r, edges = page_records(tok, side, spec["cols"][side], p)
            recs[side] += r
            meta[f"{tab}:p{p}"] = dict(side=side, edges=[round(e, 2) for e in edges], records=len(r))
        L = recs["left"]
        if spec["cols"].get("right"):
            R = recs["right"]
            if [x["code"] for x in L] != [x["code"] for x in R]:
                raise ValueError(f"{tab}: left and right pages list different codes")
            for x, y in zip(L, R):
                x["total"].update(y["total"])
                if (x["large"] is None) != (y["large"] is None):
                    raise ValueError(f"{tab} {x['code']}: large-industry line on one page only")
                if x["large"] is not None:
                    x["large"].update(y["large"])
                x["page"] = f"{x['page']}/{y['page']}"
        seen = {}
        for x in L:
            if x["code"] in seen:
                raise ValueError(f"{tab}: code {x['code']} listed twice (pages {seen[x['code']]} and {x['page']})")
            seen[x["code"]] = x["page"]
            for kind in ("total", "large"):
                row = x[kind]
                rec = dict(table=tab, code=x["code"], level=(0 if x["code"] == "Total" else len(x["code"])), line=kind, page=x["page"],
                           large_line_present=x["large"] is not None)
                if row is None:
                    rec.update({c: np.nan for side in spec["cols"].values() for c in side}); rec["flags"] = "no large-industry line"
                else:
                    fl = []
                    for side in spec["cols"].values():
                        for c in side:
                            v, f = value(row.get(c)); rec[c] = v; rec[f"{c}_raw"] = row.get(c)
                            if f in ("star", "blank"):
                                fl.append(f"{c}:{f}")
                    rec["flags"] = ";".join(fl)
                raw.append(rec)
        # ---- reconciliation against printed totals ---------------------------------------------------------------------------
        df = pd.DataFrame([r for r in raw if r["table"] == tab])
        cols = [c for side in spec["cols"].values() for c in side]
        for kind in ("total", "large"):
            z = df[df.line == kind].set_index("code")
            for parent in z.index:
                lev = z.at[parent, "level"]
                if lev == 4:
                    continue
                kids = [c for c in z.index if (z.at[c, "level"] == (2 if lev == 0 else lev + 1)) and (lev == 0 or c.startswith(parent))]
                if not kids:
                    continue
                for c in cols:
                    pv = z.at[parent, c]
                    kv = z.loc[kids, c]
                    star = int(kv.isna().sum())
                    s = float(kv.sum(skipna=True))
                    if np.isnan(pv):
                        continue
                    diff = s - pv
                    rel = diff / pv if pv else (0.0 if s == 0 else np.inf)
                    checks.append(dict(table=tab, line=kind, parent=parent, parent_level=int(lev), children=len(kids), column=c, printed=pv,
                                       sum_children=s, children_not_published=star, diff=diff, rel_diff=rel,
                                       status=("OK" if abs(rel) <= 0.005 else ("LOWER_BOUND_STAR" if star and diff < 0 else "DIFF_GT_0.5PCT"))))
    R = pd.DataFrame(raw)
    R.to_csv(out / "ID_BPS_IBS_2019_RAW.csv", index=False)
    C = pd.DataFrame(checks)
    C.to_csv(out / "ID_BPS_PARSE_CHECK.csv", index=False, float_format="%.6g")
    s = C.groupby(["table", "line", "status"]).size().unstack(fill_value=0)
    print(s.to_string())
    bad = C[C.status == "DIFF_GT_0.5PCT"]
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(bad[["table", "line", "parent", "column", "printed", "sum_children", "rel_diff", "children_not_published"]].to_string())
    (out / "_bps_parse_meta.json").write_text(pd.Series(meta).to_json(indent=1))


if __name__ == "__main__":
    main()
