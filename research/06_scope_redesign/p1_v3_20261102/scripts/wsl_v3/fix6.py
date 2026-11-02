from pathlib import Path
f=Path("/home/jin/wt_v3_20261102/scripts_project/v3_data.py"); t=f.read_text()
a='    reg.write(REG_DIR / "fragments" / "v3.csv")\n'
b='''    for r in reg.rows:   # registry validation: numeric grade C rows carry a range; +-50 % like research.liquids.ship_cost_scale
        try:
            v = float(r["value"])
        except ValueError:
            continue
        if r["tier"] == "C" and r["status"] == "REGISTERED" and r["sensitivity_low"] == "":
            if v == 0.0:
                r["status"] = "REFERENCE_ONLY"
            else:
                r["sensitivity_low"], r["sensitivity_high"] = fmt(0.5 * v), fmt(1.5 * v)
    reg.write(REG_DIR / "fragments" / "v3.csv")
'''
assert a in t; t=t.replace(a,b)
a2="from d1_common import REG_DIR, ROOT, Registry, sha256"; assert a2 in t; t=t.replace(a2,"from d1_common import REG_DIR, ROOT, Registry, fmt, sha256")
f.write_text(t)
