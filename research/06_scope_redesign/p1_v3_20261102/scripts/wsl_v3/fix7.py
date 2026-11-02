from pathlib import Path
f=Path("/home/jin/wt_v3_20261102/scripts_project/v3_data.py"); t=f.read_text()
a='    for r in reg.rows:   # registry validation: numeric grade C rows carry a range; +-50 % like research.liquids.ship_cost_scale\n'
b=a+'        r["source_sha256"] = r["source_sha256"] or REVIEW_SHA\n'
assert a in t; t=t.replace(a,b)
a2='TECH = dict('; b2='REVIEW_SHA = "5bc090fe0bcc9808dd973b10ab47209b135b0134ffae9dd10cc355a7ea99de9b"   # V3_REVIEW_DECISIONS_PHASE1.md: rule and assumption rows cite it\nTECH = dict('
assert a2 in t; t=t.replace(a2,b2,1)
f.write_text(t)
