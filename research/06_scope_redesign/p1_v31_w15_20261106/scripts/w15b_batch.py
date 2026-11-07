"""V31 W15 stage B, sections 5.2-5.3 and 6: final acceptance, interim-vs-final file comparison, independent B6 recomputation, Owen
description, reference comparison (read only; no solver).

  python -I w15b_batch.py --final <hpc_results_v31/unpacked/export> --interim <hpc_results_v31/interim_unpacked/export>
         --top <hpc_results_v31> --pkg <hpc_package_v3_1> --out <work/p1_v31_w15_20261106>

Writes evidence/STAGE_B_ACCEPTANCE.json, INTERIM_VS_FINAL.csv, B6_CHECK.json, OWEN_PAIRS.csv, evidence/OWEN_BALANCE.json,
REFERENCE_COMPARISON.csv. Exit code 3 when an independent B6 differs from the batch summary by more than 1e-6 (stop condition).
"""
import argparse, csv, hashlib, json, re, sys
from pathlib import Path

RUNS = ("F1", "F2", "F3", "F4")
PAIRS = {"A": ("F1", "F2"), "B": ("F3", "F4")}
PLAYERS = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER")
# products of the batch regrade (run_batch4.sh regrade_all): C1 regrade, Owen regrade, provisional copy, final V6 label, and their exports
REGRADE_PRODUCTS = {"PRECISION.json", "PRECISION.md", "V6_ACCEPTANCE.json", "V6_ACCEPTANCE_PROVISIONAL.json", "m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json",
                    "c1_regrade.log", "m12_owen_regrade.log"}
SCRUB = [(re.compile(r"/hpctmp/[^/\s\"']+"), "/hpctmp/<user>"), (re.compile(r"/home/svu/[^/\s\"']+"), "/home/svu/<user>"), (re.compile(r"cnode[-0-9]+"), "<node>")]


def scrub(s: str) -> str:
    for p, r in SCRUB:
        s = p.sub(r, s)
    return s


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jl(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def ledger_total(d: Path) -> float:
    with (d / "COUNTRY_COST_LEDGER.csv").open(encoding="utf-8") as f:
        return sum(float(r["total"]) for r in csv.DictReader(f))


def owen(d: Path) -> dict:
    with (d / "m12_owen" / "OWEN.csv").open(encoding="utf-8") as f:
        return {r["player"]: r for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    for k in ("final", "interim", "top", "pkg", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    FIN, INT, TOP, PKG, OUT = map(Path, (a.final, a.interim, a.top, a.pkg, a.out))
    (OUT / "evidence").mkdir(exist_ok=True)
    summ = jl(FIN / "batch" / "BATCH4_SUMMARY.json")
    # ------------------------------------------------------------------ 5.2 acceptance
    status = (FIN / "batch" / "STATUS.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    commits = sorted({m.group(1) for l in status for m in [re.search(r"START:[^:]+:[^:]+:\d\dZ:commit=([0-9a-f]{40})", l)] if m} |
                     {m.group(1) for l in status for m in [re.search(r":commit=([0-9a-f]{40}):repo_commit=", l)] if m})
    repo_commits = sorted({m.group(1) for l in status for m in [re.search(r"repo_commit=([0-9a-f]{40})", l)] if m})
    acc = dict(package_commit=(PKG / "COMMIT").read_text().strip(), status_commits=commits, status_repo_commits=repo_commits,
               status_lines=dict(regrade=[scrub(l) for l in status if l.startswith(("REGRADE_", "BATCH_REFERENCE", "M12_BENEFIT", "SUMMARY", "PACK_", "DONE"))],
                                 stop=[scrub(l) for l in status if re.match(r"(STOP|HALT|UNUSABLE|POSTPROC_ERROR|KILLED)", l)]),
               runs={})
    for r in RUNS:
        d = FIN / r
        A = jl(d / "V6_ACCEPTANCE.json"); AP = jl(d / "V6_ACCEPTANCE_PROVISIONAL.json"); P = jl(d / "PRECISION.json"); V = jl(d / "VIOLATIONS.json")
        OR = jl(d / "m12_owen" / "OWEN_REGRADE_BATCH_REFERENCE.json"); S = jl(d / "SOLVE_RECEIPT.json")
        acc["runs"][r] = dict(
            termination=S["termination_condition"], gurobi=S["split"]["gurobi_status_name"], objective=S["objective"], objective_lp=S["objective_lp"],
            label_final=A["label"], label_provisional=AP["label"] if AP else None, G1_final=dict(a=A["G1"]["a"], b=A["G1"]["b"], c=A["G1"]["c"]),
            G1_reference=scrub(str(A["G1"]["reference"]))[:120], G2=all(A["G2"][k]["passed"] for k in ("G2_1", "G2_2", "G2_3")),
            c1=dict(grade=P["grade"]["grade"], a=P["acceptance"]["a"], b=P["acceptance"]["b"], c=P["acceptance"]["c"], reference=scrub(str(P["reference"]["source"]))[:120],
                    regrades=len(P.get("regrades", []) or P.get("grade_history", []) or [])),
            owen_regrade=({k: (scrub(v) if isinstance(v, str) else v) for k, v in OR.items() if not isinstance(v, (dict, list))} if OR else None),
            violations=dict(rows_over_budget=V["totals"]["rows_over_budget"], row_max_ratio=V["totals"]["row_max_ratio_to_budget"], first_order_cost_eur=V["totals"]["first_order_cost_eur"]),
            gates_failing=sorted(k for k, v in S["gates"].items() if v is False))
        # NetCDF files of the full pack: solved network = A4 read-back SHA256 (V5_GATES), duals = export manifest entry
        G = jl(d / "V5_GATES.json"); EX = jl(d / "EXPORTS.json") or {}
        nc = sorted(d.glob("*_solved.nc"))
        acc["runs"][r]["netcdf"] = dict(solved=nc[0].name if nc else None, solved_sha256=sha(nc[0]) if nc else None, a4_sha256=G["A4"].get("sha256"),
                                        duals_sha256=sha(d / "DUALS_BY_CONSTRAINT.nc"), exports_duals_sha256=(EX.get("DUALS_BY_CONSTRAINT.nc") or {}).get("sha256"))
        n_ = acc["runs"][r]["netcdf"]
        n_["solved_equals_a4"] = n_["solved_sha256"] == n_["a4_sha256"]; n_["duals_equal_manifest"] = n_["duals_sha256"] == n_["exports_duals_sha256"]
    acc["all_accepted"] = all(v["label_final"].startswith("ACCEPTED") for v in acc["runs"].values())
    br = jl(FIN / "batch" / "BATCH_REFERENCE.json")
    acc["batch_reference"] = {k: ((scrub(v) if isinstance(v, str) else v) if not isinstance(v, (dict, list)) else (list(v.keys())[:20] if isinstance(v, dict) else len(v)))
                              for k, v in (br or {}).items()}
    # top-level downloaded copies vs the pack copies
    acc["downloaded_vs_pack"] = {f: dict(downloaded=sha(TOP / f) if (TOP / f).exists() else None, pack=sha(FIN / "batch" / f) if (FIN / "batch" / f).exists() else None)
                                 for f in ("BATCH4_SUMMARY.json", "BATCH4_SUMMARY.md", "STATUS.txt")}
    for f, v in acc["downloaded_vs_pack"].items():
        v["equal"] = v["downloaded"] == v["pack"]
        if not v["equal"] and (TOP / f).exists() and (FIN / "batch" / f).exists():
            dl, pk = (TOP / f).read_bytes(), (FIN / "batch" / f).read_bytes()
            v["pack_is_prefix_of_download"] = dl.startswith(pk)
            v["lines_after_pack"] = [scrub(l)[:60] for l in dl[len(pk):].decode("utf-8", "replace").splitlines()] if dl.startswith(pk) else None
    (OUT / "evidence" / "STAGE_B_ACCEPTANCE.json").write_text(json.dumps(acc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    # ------------------------------------------------------------------ 5.3 interim vs final
    rows = []
    for r in RUNS:
        fi, ii = FIN / r, INT / r
        fset = {str(p.relative_to(fi)).replace("\\", "/") for p in fi.rglob("*") if p.is_file()}
        iset = {str(p.relative_to(ii)).replace("\\", "/") for p in ii.rglob("*") if p.is_file()} if ii.exists() else set()
        for f in sorted(fset | iset):
            s_f = sha(fi / f) if f in fset else None; s_i = sha(ii / f) if f in iset else None
            if not iset:
                st = "no_interim"
            elif s_f and s_i:
                st = "same" if s_f == s_i else "differs"
            else:
                st = "only_final" if s_f else "only_interim"
            exp = ("regrade product" if f in REGRADE_PRODUCTS else ("NetCDF (full pack only; interim excluded *.nc)" if f.endswith(".nc") else "should be identical"))
            note = ""
            if f == "EXPORTS.json" and st == "differs":
                ei, ef = jl(ii / f), jl(fi / f)
                def flat(d, pre=""):
                    o = {}
                    for k, v in (d.items() if isinstance(d, dict) else enumerate(d)):
                        o.update(flat(v, f"{pre}/{k}") if isinstance(v, (dict, list)) else {f"{pre}/{k}": v})
                    return o
                fi_, ff_ = flat(ei), flat(ef)
                changed = sorted({k.rsplit("/", 1)[0] for k in set(fi_) | set(ff_) if fi_.get(k) != ff_.get(k)})
                entries = {c for c in changed}
                only_regrade = all(any(p in c for p in ("PRECISION.json", "PRECISION.md", "V6_ACCEPTANCE", "OWEN_REGRADE")) or
                                   any(p in str(ff_.get(c + "/path", "")) + str(fi_.get(c + "/path", "")) for p in ("PRECISION", "V6_ACCEPTANCE", "OWEN_REGRADE"))
                                   for c in entries)
                exp = "export manifest: entries of the regraded files" if only_regrade else "export manifest: OTHER entries changed"
                note = "; ".join(changed)[:300]
            rows.append(dict(run=r, file=f, status=st, expected=exp, sha256_interim=s_i or "", sha256_final=s_f or "", note=note,
                             unexpected=(st in ("differs", "only_interim", "only_final") and exp in ("should be identical", "export manifest: OTHER entries changed"))))
    with (OUT / "INTERIM_VS_FINAL.csv").open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    # ------------------------------------------------------------------ 6.1 B6
    Z = {r: jl(FIN / r / "SOLVE_RECEIPT.json")["objective"] for r in RUNS}
    Lt = {r: ledger_total(FIN / r) for r in RUNS}
    b6 = {}
    sb = dict(A=summ["B6_pairs"]["A"], B=summ["B6_pairs"]["B"])
    if "difference" not in sb["A"]:
        sb["A"] = summ["B6"]
    stop = False
    for p, (ri, rd) in PAIRS.items():
        by_obj = Z[rd] - Z[ri]; by_led = Lt[rd] - Lt[ri]; bs = sb[p]["difference"] if sb[p] else None
        rel_obj = abs(by_obj - bs) / abs(bs) if bs else None; rel_led = abs(by_led - bs) / abs(bs) if bs else None
        b6[p] = dict(pair=f"{rd} - {ri}", Z_integrated=Z[ri], Z_no_new_xb=Z[rd], b6_by_objective=by_obj, ledger_integrated=Lt[ri], ledger_no_new_xb=Lt[rd],
                     b6_by_ledger=by_led, b6_batch_summary=bs, rel_diff_objective_vs_summary=rel_obj, rel_diff_ledger_vs_summary=rel_led,
                     ledger_vs_objective=dict(integrated=Lt[ri] - Z[ri], no_new_xb=Lt[rd] - Z[rd]), within_1e6=(rel_obj is not None and rel_obj <= 1e-6 and rel_led <= 1e-6),
                     summary_gate=dict(passed=sb[p]["passed"], usable=sb[p].get("usable")) if sb[p] else None)
        stop |= not b6[p]["within_1e6"]
    b6["delta_B_minus_A"] = b6["B"]["b6_by_objective"] - b6["A"]["b6_by_objective"]
    b6["summary_delta_bn"] = summ["pair_comparison"]["delta_b6_bn"]
    b6["summary_pair_b6_bn"] = summ["pair_comparison"]["b6_bn"]
    b6["summary_A_equals_B6"] = summ["B6"]["difference"] == sb["A"].get("difference")
    b6["stop"] = stop
    (OUT / "B6_CHECK.json").write_text(json.dumps(b6, indent=1) + "\n", encoding="utf-8", newline="\n")
    # ------------------------------------------------------------------ 6.2 Owen
    orows, bal = [], {}
    ow = {r: owen(FIN / r) for r in RUNS}
    ben = {}
    for p, sub in (("A", "M12_BENEFIT"), ("B", "M12_BENEFIT_B")):
        f = FIN / "batch" / sub / "BENEFIT.csv"
        with f.open(encoding="utf-8") as fh:
            ben[p] = {r.get("player") or r.get("participant") or r.get("country"): r for r in csv.DictReader(fh)}
    for r in RUNS:
        alloc = {k: float(v["owen_dual_alpha_0.5_eur"]) for k, v in ow[r].items()}
        tot = sum(alloc.values())
        bal[r] = dict(sum_allocation=tot, objective=Z[r], rel_error=abs(tot - Z[r]) / abs(Z[r]), within_1e6=abs(tot - Z[r]) / abs(Z[r]) <= 1e-6,
                      players=sorted(alloc), alpha_spread_max_eur=max(abs(float(v["owen_dual_alpha_0_eur"]) - float(v["owen_dual_alpha_1_eur"])) for v in ow[r].values()))
    for pl in sorted(set(ow["F1"]) | set(ow["F2"])):
        row = dict(player=pl)
        for p, (ri, rd) in PAIRS.items():
            ai, ad = float(ow[ri][pl]["owen_dual_alpha_0.5_eur"]), float(ow[rd][pl]["owen_dual_alpha_0.5_eur"])
            row[f"alloc_{ri}_eur"] = ai; row[f"alloc_{rd}_eur"] = ad; row[f"benefit_{p}_eur"] = ad - ai
            bb = ben[p].get(pl)
            row[f"benefit_{p}_batch_eur"] = float(bb["owen_benefit_eur"]) if bb else ""
            row[f"benefit_{p}_minus_batch_eur"] = (ad - ai - float(bb["owen_benefit_eur"])) if bb else ""
            row[f"benefit_{p}_alpha_range_eur"] = f'{float(bb["owen_benefit_min_eur"]):.6g}..{float(bb["owen_benefit_max_eur"]):.6g}' if bb else ""
            row[f"market_form_benefit_{p}_eur"] = float(bb["market_form_benefit_eur"]) if bb else ""
            row[f"sign_{p}"] = "+" if ad - ai > 0 else ("-" if ad - ai < 0 else "0")
        row["sign_same"] = row["sign_A"] == row["sign_B"]
        orows.append(row)
    with (OUT / "OWEN_PAIRS.csv").open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(orows[0]), lineterminator="\n"); w.writeheader(); w.writerows(orows)
    sumben = {p: sum(r[f"benefit_{p}_eur"] for r in orows) for p in PAIRS}
    (OUT / "evidence" / "OWEN_BALANCE.json").write_text(json.dumps(dict(
        budget_balance=bal, benefit_sum_vs_b6={p: dict(sum_benefit=sumben[p], b6=b6[p]["b6_by_objective"], rel=abs(sumben[p] - b6[p]["b6_by_objective"]) / abs(b6[p]["b6_by_objective"]))
                                               for p in PAIRS},
        benefit_file_columns={p: list(next(iter(ben[p].values())).keys()) for p in PAIRS}), indent=1) + "\n", encoding="utf-8", newline="\n")
    # ------------------------------------------------------------------ 6.3 reference values
    ref = jl(PKG / "REFERENCE_VALUES.json")["references"]
    rr = []
    for k, v in ref.items():
        zi, zd = v["integrated"]["objective_eur"], v["disconnected"]["objective_eur"]
        for p, (ri, rd) in PAIRS.items():
            rr.append(dict(reference=k, label=v["label"], resolution=v["resolution"], shipping=v["shipping"], pair=p, ref_b6_bn=v["b6_bn"],
                           b6_bn=b6[p]["b6_by_objective"] / 1e9, b6_minus_ref_bn=b6[p]["b6_by_objective"] / 1e9 - v["b6_bn"],
                           Z_int_minus_ref_bn=(Z[ri] - zi) / 1e9, Z_dis_minus_ref_bn=(Z[rd] - zd) / 1e9,
                           **{f"owen_benefit_{pl}_minus_ref_bn": ((float(ow[rd][pl]["owen_dual_alpha_0.5_eur"]) - float(ow[ri][pl]["owen_dual_alpha_0.5_eur"]))
                                                                 - (v["disconnected"]["owen_alpha_main_eur"][pl] - v["integrated"]["owen_alpha_main_eur"][pl])) / 1e9
                              for pl in PLAYERS if pl in v["integrated"]["owen_alpha_main_eur"] and pl in ow[ri]}))
    with (OUT / "REFERENCE_COMPARISON.csv").open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rr[0]), lineterminator="\n"); w.writeheader(); w.writerows(rr)
    print("all_accepted", acc["all_accepted"], "commits", commits, repo_commits)
    print({r: (v["label_provisional"], v["label_final"], v["c1"]["reference"][:30], v["violations"]["rows_over_budget"], v["gates_failing"]) for r, v in acc["runs"].items()})
    print("netcdf", {r: (v["netcdf"]["solved_equals_a4"], v["netcdf"]["duals_equal_manifest"], v["netcdf"]["solved_sha256"][:16]) for r, v in acc["runs"].items()})
    print("status prefix", {f: v.get("pack_is_prefix_of_download") for f, v in acc["downloaded_vs_pack"].items() if not v["equal"]})
    print("downloaded_vs_pack", {f: v["equal"] for f, v in acc["downloaded_vs_pack"].items()})
    print("interim_vs_final", {s: sum(1 for x in rows if x["status"] == s) for s in ("same", "differs", "only_final", "only_interim", "no_interim")},
          "unexpected", [(x["run"], x["file"], x["status"]) for x in rows if x["unexpected"]][:20])
    print("differs/only_final (expected)", sorted({(x["file"], x["status"]) for x in rows if x["status"] in ("differs", "only_final") and not x["unexpected"]}))
    for p in PAIRS:
        print("B6", p, {k: b6[p][k] for k in ("b6_by_objective", "b6_by_ledger", "b6_batch_summary", "rel_diff_objective_vs_summary", "rel_diff_ledger_vs_summary", "within_1e6")})
    print("budget", {r: (v["rel_error"], v["within_1e6"]) for r, v in bal.items()}, "benefit sums", {p: sumben[p] / 1e9 for p in PAIRS})
    print("signs", [(r["player"], r["sign_A"], r["sign_B"]) for r in orows])
    sys.exit(3 if stop else 0)


if __name__ == "__main__":
    main()
