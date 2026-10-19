"""Test double for scripts_project/s4o_c1_precision.py (S4O-4 script tests only): same sub-commands and files as the real module, with the grade
given by FAKE_C1_ABC (three digits a b c, default 111) and the reference source taken from --reference (L23 when absent)."""
import json, os, sys

a = sys.argv[1:]; cmd = a[0]
arg = lambda k: a[a.index(k) + 1] if k in a else None


def grade(abc, cond, src):
    ok = [c == "1" for c in abc]
    g = "layer1_plus_nodal_price_settlement" if all(ok) else ("layer1_total_cost_screening" if ok[0] and ok[1] else "not_layer1")
    return dict(grade=dict(grade=g, a=ok[0], b=ok[1], c=ok[2]), acceptance=dict(optimal=cond == "optimal", accepted=bool(cond == "optimal" and all(ok))), reference=dict(source=src))


def write(sd, res):
    json.dump(res, open(os.path.join(sd, "PRECISION.json"), "w")); open(os.path.join(sd, "PRECISION.md"), "w").write("fake precision\n")
    p = os.path.join(sd, "EXPORTS.json"); ex = json.load(open(p)) if os.path.exists(p) else {}
    ex.update({"PRECISION.json": dict(bytes=1, sha256="fake"), "PRECISION.md": dict(bytes=1, sha256="fake")}); json.dump(ex, open(p, "w"))


if cmd == "run":
    sd = arg("--solve-dir"); cond = json.load(open(os.path.join(sd, "SOLVE_RECEIPT.json"))).get("termination_condition")
    src = json.load(open(arg("--reference")))["source"] if arg("--reference") else "L23 365x24h (fake)"
    write(sd, dict(grade(os.environ.get("FAKE_C1_ABC", "111"), cond, src), termination=cond, args=a, licence_env=("GRB_LICENSE_FILE" in os.environ)))
elif cmd == "reference":
    json.dump(dict(source="this batch (fake)", differences_bn={}), open(arg("--out"), "w"))
elif cmd == "regrade":
    sd = arg("--solve-dir"); r = json.load(open(os.path.join(sd, "PRECISION.json"))); r["reference"] = json.load(open(arg("--reference"))); r["regraded"] = True; write(sd, r)
print(json.dumps(dict(fake=cmd)))
