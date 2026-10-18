"""S4I (item 103) section D: compute estimate for the connected-coalition study under the academic licence (INFERENCE, no solve).

    python scripts_project/s4i_coalition_estimate.py --static <S4I_STATIC_AUDIT.json> --extrapolation <EXTRAPOLATION_S4H4.json> --out <json>

Coalitions: connected subsets (>= 2 members) of the country graph of the integrated network's cross-border corridors (all network
carriers, rule of research.cross_border.coalition), counted in s4i_static_audit.py. Per-run time and memory: the S4H-3 56x3h runs under
profile A extrapolated in EXTRAPOLATION_S4H4.json (barrier n^1.3-n^1.5, pessimistic = 1.5 x iterations; non-solve time linear); a
coalition LP lies between the disconnected and the integrated LP in size (only cross-border corridors differ), so the envelope of
these two runs is used. Licence: <= 2 concurrent WLS sessions, token kept >= 5 min after an environment closes (S4I instruction C).
"""
from pathlib import Path
import argparse, json, math, sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from s4i_static_audit import jsonable, sha

TOKEN_GAP_S = 300.0
CONTENTION = (1.10, 1.20)   # two lanes on one instance: memory-bandwidth contention (CLOUD_RESOURCE_ESTIMATE.md section 17)


def per_run(ex, res):
    """Envelope over the integrated and disconnected runs: (low, high, pessimistic) wall seconds and peak memory (median, upper)."""
    lo, hi, pe, mem_med, mem_up = [], [], [], [], []
    for k in ("integrated", "disconnected"):
        e = ex["runs"][k]["extrapolation"][res]
        ns = float(e.get("non_solve_s", 0.0)) if not isinstance(e.get("non_solve_s"), list) else float(max(e["non_solve_s"]))
        lo.append(float(e["barrier_s"][0]) + ns); hi.append(float(e["barrier_s"][1]) + ns); pe.append(float(e["barrier_s_with_1_5x_iterations"]) + ns)
        for key in ("peak_rss_gib", "peak_gib", "rss_gib"):
            if key in e:
                v = e[key]; mem_med.append(float(v[0] if isinstance(v, list) else v)); mem_up.append(float(v[-1] if isinstance(v, list) else v)); break
    return dict(wall_s_low=min(lo), wall_s_high=max(hi), wall_s_pessimistic=max(pe), peak_gib_median=max(mem_med) if mem_med else None, peak_gib_upper=max(mem_up) if mem_up else None,
                source_keys=sorted(ex["runs"]["integrated"]["extrapolation"][res].keys()))


def totals(n_runs, r):
    out = {}
    for case, t in (("low", r["wall_s_low"]), ("high", r["wall_s_high"]), ("pessimistic", r["wall_s_pessimistic"])):
        serial = n_runs * t
        lane_runs = math.ceil(n_runs / 2)
        two = (lane_runs * t * CONTENTION[0] if case == "low" else lane_runs * t * CONTENTION[1]) + lane_runs * TOKEN_GAP_S
        out[case] = dict(serial_h=serial / 3600, serial_days=serial / 86400, two_lanes_h=two / 3600, two_lanes_days=two / 86400)
    out["memory_gib"] = dict(serial=dict(median=r["peak_gib_median"], upper=r["peak_gib_upper"]),
                             two_lanes=dict(median=2 * r["peak_gib_median"] if r["peak_gib_median"] else None, upper=2 * r["peak_gib_upper"] if r["peak_gib_upper"] else None))
    return out


def main(a):
    S = json.loads(Path(a.static).read_text()); ex = json.loads(Path(a.extrapolation).read_text())
    co = S["sections"]["integrated"]["D_coalitions"]
    n_all = int(co["connected_total_ge2"]); n_new = n_all - 1   # the grand coalition is the integrated run of the first batch
    res = dict(script="scripts_project/s4i_coalition_estimate.py", inputs=dict(static=str(a.static), static_sha256=sha(a.static), extrapolation=str(a.extrapolation), extrapolation_sha256=sha(a.extrapolation)),
               coalitions=dict(connected_ge2=n_all, by_size=co["connected_by_size"], excluding_grand=n_new, corridor_edges=co["edges"]),
               assumptions=dict(token_gap_s=TOKEN_GAP_S, contention=CONTENTION, licence_sessions=2, per_run_envelope="max / min over the integrated and disconnected S4H-3 extrapolations",
                                caps=ex.get("caps"), method=ex.get("method")))
    for resn in ("365x24h", "2920x3h"):
        r = per_run(ex, resn)
        res[resn] = dict(per_run=r, all_383=totals(n_all, r), excluding_grand_382=totals(n_new, r),
                         exceeds_3h_cap=bool(r["wall_s_high"] > 10800), runs_exceeding_cap_if_pessimistic=bool(r["wall_s_pessimistic"] > 10800))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(jsonable(res), indent=1, sort_keys=True))
    print(json.dumps({k: res[k] for k in ("coalitions",)}, default=str)[:400])
    for resn in ("365x24h", "2920x3h"):
        print(resn, json.dumps(res[resn]["per_run"], default=str), json.dumps(res[resn]["all_383"], default=str))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--static", required=True); p.add_argument("--extrapolation", required=True); p.add_argument("--out", required=True)
    sys.exit(main(p.parse_args()))
