"""M10R B2.3 regression comparator (read only): compare two post-processing folders file by file.
  * CSV / text files: byte equality (SHA256);
  * JSON files: deep comparison of every number / string after dropping volatile keys (paths, timestamps, seconds, code hashes);
    every numeric leaf is compared bit for bit (==); the maximum relative difference over leaves that differ is reported.
Usage: python compare_dirs.py <dir A> <dir B> <out.json> [--label X]   -> prints a one-line verdict; exit 0 when every compared file is equal."""
import hashlib
import json
import math
import sys
from pathlib import Path

VOLATILE = {"solve_dir", "into", "path", "written_utc", "seconds", "timestamp", "utc", "created_utc", "elapsed_s", "code", "script_sha256", "s4d_ledger_sha256",
            "s4d_ledger_redo_sha256", "solved_network", "file", "files", "out", "network", "costs_table", "output", "export", "registered_sha256_source", "repo",
            "layers_sha256", "allocation", "tag", "label", "duals", "source", "note", "definition", "solve_seconds", "finished_epoch", "time", "generated",
            "existing_cross_border_fom_ledger", "fom_ledger",   # the two diagnostic keys ADDED by the M10R fix (counts of meta rows; no number of the results)
            "build_seconds", "peak_rss_gib", "peak_rss_gib_after_build", "threshold_source"}   # timing / memory of the run and a folder path string
COMPARE = ("COUNTRY_COST_LEDGER.csv", "COUNTRY_COST_LEDGER_USD2020.csv", "COUNTRY_COST_LEDGER_DETAIL.csv", "NODAL_PRICES.csv", "LEDGER_IDENTITY.json", "V5_GATES.json",
           "PRECISION.json", "ALLOCATION.json", "ALLOCATION.csv", "ALLOCATION_LINES.csv", "V6_ACCEPTANCE.json", "m12_owen/OWEN.json", "m12_owen/OWEN.csv",
           "m12_owen/RHS_AUDIT.json", "m12_owen/RHS_BY_FAMILY_OWNER.csv", "m12_owen/RHS_FAMILIES.csv", "m12_owen/RHS_FAMILY_SUMMARY.csv", "STOP_CLASS.json")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k not in VOLATILE}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o


def walk(a, b, path, diffs, stats):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                diffs.append((path + "/" + str(k), "missing in " + ("B" if k not in b else "A"))); continue
            walk(a[k], b[k], path + "/" + str(k), diffs, stats)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append((path, f"list length {len(a)} vs {len(b)}")); return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", diffs, stats)
    elif isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
        stats["numbers"] += 1
        if (isinstance(a, float) and math.isnan(a)) and (isinstance(b, float) and math.isnan(b)):
            return
        if a != b:
            rel = abs(a - b) / max(1.0, abs(a), abs(b)); stats["max_rel"] = max(stats["max_rel"], rel); diffs.append((path, f"{a!r} vs {b!r} (rel {rel:.3e})"))
    elif a != b:
        diffs.append((path, f"{str(a)[:60]!r} vs {str(b)[:60]!r}"))


def main():
    A, B, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else ""
    rows = {}; all_ok = True
    for f in COMPARE:
        pa, pb = A / f, B / f
        if not pa.exists() and not pb.exists():
            continue
        if not pa.exists() or not pb.exists():
            rows[f] = dict(status="missing_in_" + ("A" if not pa.exists() else "B")); all_ok = False; continue
        if f.endswith(".json"):
            try:
                a, b = strip(json.loads(pa.read_text())), strip(json.loads(pb.read_text()))
            except ValueError as e:
                rows[f] = dict(status="unreadable", error=str(e)[:100]); all_ok = False; continue
            diffs, stats = [], dict(numbers=0, max_rel=0.0)
            walk(a, b, "", diffs, stats)
            rows[f] = dict(status=("equal" if not diffs else "DIFFERENT"), numbers_compared=stats["numbers"], bytes_equal=(sha(pa) == sha(pb)),
                           max_relative_difference=stats["max_rel"], differences=len(diffs), examples=[f"{p}: {d}" for p, d in diffs[:12]])
            all_ok &= not diffs
        else:
            eq = sha(pa) == sha(pb)
            rows[f] = dict(status=("equal" if eq else "DIFFERENT"), bytes_equal=eq, bytes=(pa.stat().st_size, pb.stat().st_size))
            all_ok &= eq
    res = dict(label=label, A=str(A), B=str(B), all_equal=all_ok, files=rows)
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(dict(label=label, all_equal=all_ok, files={k: v["status"] for k, v in rows.items()})))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
