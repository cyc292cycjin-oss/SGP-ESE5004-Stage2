"""S4K-2 static review: the S4I audit (s4i_static_audit.py, s4i_followups.py) re-run on the four S4K networks (365x24h), compared item by item with
the same audit of the S4J networks (supplement 01 (a) re-run), plus the S4K-specific checks (read only, no solve):

  * every A-section value that differs between S4J and S4K, by network -> S4K2_AUDIT_DIFF.csv;
  * component comparison S4K vs S4J network by network (the only expected difference: the per-line lambda column of the AC lines);
  * the proxy acts on the AC lines only: lambda on every line, links (DC, pipelines) unchanged, meta ac_losses = linear_proxy and solver
    transmission_losses = 0, hook research_ac_loss_proxy present;
  * model-build check (no solve, first 56 snapshots) for every network: create_model(transmission_losses from the meta = 0) + research hooks ->
    'Line-loss' exists, no PyPSA tangent rows, the proxy rows and their counts;
  * scenario differences: NZE vs integrated (fuel prices only), disconnected vs integrated (all cross-border components removed).

    python scripts_project/s4k_2_review.py --ref-audit <S4J audit dir> --audit <S4K audit dir> --ref-networks <S4J networks> --networks <S4K networks> --out <dir>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from s4j_5_review import NETS, audit_diff
from s4k_layers import LAMBDA_COL, PROXY_HOOK, line_lambda


def same(a, b) -> dict:
    bad = {}
    for c in ["Bus", "Link", "Store", "Generator", "Load", "StorageUnit", "Line", "Carrier"]:
        x, y = a.df(c).sort_index(), b.df(c).sort_index()
        if set(x.index) != set(y.index):
            bad[c] = "index differs"; continue
        cols = sorted(set(x.columns) | set(y.columns)); x = x.reindex(columns=cols); y = y.reindex(columns=cols)
        d = [k for k in cols if not x[k].equals(y[k])]
        if d:
            bad[c] = d
        for attr, df in a.pnl(c).items():
            if not df.sort_index(axis=1).equals(b.pnl(c)[attr].sort_index(axis=1)):
                bad.setdefault(c + "_t", []).append(attr)
    return bad


def model_check(path: Path) -> dict:
    import pypsa
    from assembly_components import install_research_constraint_hooks
    n = pypsa.Network(str(path)); n.set_snapshots(n.snapshots[:56])
    n.meta.update(solver_allowed=True, artifact_role="S4K2_MODEL_CHECK_UNSOLVED", s2_solve_label="S4K2_MODEL_CHECK")
    tl = int(n.meta["research_transmission_losses"]["ac_transmission_losses"])
    m = n.optimize.create_model(transmission_losses=tl); install_research_constraint_hooks(n)
    rows = {k: int(np.asarray(m.constraints[k].labels.values).ravel().__ge__(0).sum()) for k in m.constraints if "loss" in k}
    return dict(solver_transmission_losses=tl, loss_variables=int(np.asarray(m["Line-loss"].labels.values).ravel().__ge__(0).sum()) if "Line-loss" in m.variables else 0,
                tangent_rows=sum(v for k, v in rows.items() if "tangents" in k), loss_rows=rows, lines=int(len(n.lines)), num_col=int(m.nvars), num_row=int(m.ncons))


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    for k in ("ref_audit", "audit", "ref_networks", "networks", "out"):
        ap.add_argument("--" + k.replace("_", "-"), dest=k, type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    ref = json.loads((a.ref_audit / "static/S4I_STATIC_AUDIT.json").read_text()); new = json.loads((a.audit / "static/S4I_STATIC_AUDIT.json").read_text())
    D = audit_diff(ref, new).rename(columns={"s4i": "s4j", "s4j": "s4k"}); D.to_csv(a.out / "S4K2_AUDIT_DIFF.csv", index=False)
    nets = {k: pypsa.Network(str(a.networks / f)) for k, f in NETS.items()}
    refs = {k: pypsa.Network(str(a.ref_networks / f)) for k, f in NETS.items()}
    res = dict(audit_diff_rows=int(len(D)), audit_diff_by_section=D.groupby(["network", "section"]).size().reset_index().rename(columns={0: "rows"}).to_dict(orient="records"))
    res["components_vs_s4j"] = {k: same(nets[k], refs[k]) for k in NETS}
    pr = {}
    for k, n in nets.items():
        m = n.meta.get("research_ac_losses", {}); t = n.meta.get("research_transmission_losses", {})
        pr[k] = dict(mode=m.get("mode"), alpha=m.get("alpha"), solver_transmission_losses=t.get("ac_transmission_losses"), hook=PROXY_HOOK in n.meta.get("required_constraint_hooks", []),
                     lambda_on_all_lines=bool(LAMBDA_COL in n.lines and n.lines[LAMBDA_COL].notna().all() and (n.lines[LAMBDA_COL] > 0).all()),
                     lambda_matches_formula=bool(LAMBDA_COL in n.lines and np.allclose(n.lines[LAMBDA_COL], line_lambda(n, float(m.get("alpha", 0.5))).ac_loss_lambda, rtol=0, atol=1e-15)),
                     lambda_elsewhere=[c for c in ("Link", "Generator", "Store", "StorageUnit") if LAMBDA_COL in n.df(c)],
                     links_unchanged=("Link" not in res["components_vs_s4j"][k] and "Link_t" not in res["components_vs_s4j"][k]),
                     lambda_min=float(n.lines[LAMBDA_COL].min()) if LAMBDA_COL in n.lines else None, lambda_max=float(n.lines[LAMBDA_COL].max()) if LAMBDA_COL in n.lines else None)
    res["proxy"] = pr
    res["model_check"] = {k: model_check(a.networks / f) for k, f in NETS.items()}
    res["cross_border_components"] = {k: dict(lines=int((n.lines.border_class == "cross_border").sum()), links=int((n.links.border_class == "cross_border").sum())) for k, n in nets.items()}
    i, z = nets["integrated"], nets["integrated_nze"]; diff = {}
    for c in ["Generator", "Link", "Store", "StorageUnit", "Line", "Load", "Bus"]:
        x, y = i.df(c), z.df(c)
        if set(x.index) != set(y.index):
            diff[c] = "index differs"; continue
        cols = [col for col in sorted(set(x.columns) & set(y.columns)) if not x[col].equals(y[col])]
        if cols:
            diff[c] = {col: int((x[col] != y[col]).sum()) for col in cols}
    res["integrated_vs_nze_static"] = diff
    (a.out / "S4K2_REVIEW.json").write_text(json.dumps(res, indent=1, default=str))
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90); pd.set_option("display.max_rows", 400)
    print(D.to_string())
    print(json.dumps({k: res[k] for k in ("components_vs_s4j", "proxy", "model_check", "cross_border_components", "integrated_vs_nze_static")}, indent=1, default=str))


if __name__ == "__main__":
    main()
