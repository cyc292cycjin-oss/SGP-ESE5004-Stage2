"""Fable W08 review, section 2 quantification: decision 211 item 2 read literally (remove the 2019 paper-row fuelwood 41.59 TWh from the
2010-2017 mean 74.88 TWh -> (b) item 33.29 TWh) against the W08 reading (paper share of the mean -> 17.67 TWh). Runs the repository chain
(v4_industry.run_case) in the temporary copy; nothing in the repository is written. usage: in the copy root, python <this> <work dir> <OUT.json>"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "scripts_project"))
import v4_industry as V  # noqa: E402
from v4_common import V4_MAIN  # noqa: E402

work, OUT = Path(sys.argv[1]), Path(sys.argv[2])
I = V.Inputs(); ch = V.Chain(work)
out = {}
for mode in ("ras", "iid"):
    s = dict(V4_MAIN, anchor_mode=mode)
    case = V.final_case(I, s)
    base = V.pack(ch.run(case), "w08")
    lit = dict(case)
    adds = []
    for a in case["ats_add"]:
        if a[0] == "ID" and a[1] == "biomass":
            adds.append(("ID", "biomass", I.fw["mean_mwh"] - I.fw["paper_sdmx_mwh"], a[3]))   # literal: mean minus the 2019 paper-row quantity
        else:
            adds.append(a)
    lit["ats_add"] = adds
    rl = V.pack(ch.run(lit), "literal")
    out[mode] = dict(fw=I.fw, w08_add_mwh=[a[2] for a in case["ats_add"] if a[0] == "ID"], literal_add_mwh=[a[2] for a in adds if a[0] == "ID"],
                     ID=dict(T_w08=base["countries"]["ID"]["T"], T_literal=rl["countries"]["ID"]["T"], other_w08=base["countries"]["ID"]["other"], other_literal=rl["countries"]["ID"]["other"],
                             T_car_diff={k: rl["countries"]["ID"]["T_car"][k] - base["countries"]["ID"]["T_car"][k] for k in base["countries"]["ID"]["T_car"]}),
                     asean=dict(T_w08=sum(v["T"] for v in base["countries"].values()), T_literal=sum(v["T"] for v in rl["countries"].values())))
    o = out[mode]
    print(mode, "ID T w08", round(o["ID"]["T_w08"] / 1e6, 4), "literal", round(o["ID"]["T_literal"] / 1e6, 4), "diff", round((o["ID"]["T_literal"] - o["ID"]["T_w08"]) / 1e6, 4),
          "| other diff", round((o["ID"]["other_literal"] - o["ID"]["other_w08"]) / 1e6, 4), "| add w08", [round(x / 1e6, 3) for x in o["w08_add_mwh"]], "literal", [round(x / 1e6, 3) for x in o["literal_add_mwh"]])
json.dump(out, open(OUT, "w"), indent=1, default=float)
