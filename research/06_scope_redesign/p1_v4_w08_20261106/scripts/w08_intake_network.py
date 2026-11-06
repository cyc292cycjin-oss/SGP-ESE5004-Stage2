"""W08 checklist sections 8 and 7 (node shares): copy the W12 / W07 session tables the repository code needs into research_inputs (byte copies;
the node-share files are concatenated with their source file). Read only on the W07 side.

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_intake_network.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd

W07 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106")
R = Path("/home/jin/wt_v4_w08/research_inputs")
COPIES = [(W07 / "W12/tables/W12_3_BAGASSE_SUPPLY_OVERESTIMATE.csv", R / "biomass_v5/W12_BAGASSE_SUPPLY_OVERESTIMATE.csv"),
          (W07 / "W12/tables/W12_3_UNSD_BAGASSE_2019.csv", R / "biomass_v5/W12_UNSD_BAGASSE_2019.csv"),
          (W07 / "W12/tables/W12_1_UNSD_GAS_2019.csv", R / "gas_v5/W12_UNSD_GAS_2019.csv")]
SESSION_FILES = {"ID": "G0/ID_NODE_SHARES.csv", "MY": "G1/MY_NODE_SHARES.csv", "VN": "G2/VN_NODE_SHARES.csv", "TH": "G3/TH_NODE_SHARES.csv",
                 "PH": "G3/PH_NODE_SHARES.csv", "SG": "G3/SG_NODE_SHARES.csv", "MM": "G4/MM_NODE_SHARES.csv", "KH": "G4/KH_NODE_SHARES.csv",
                 "LA": "G4/LA_NODE_SHARES.csv", "BN": "G4/BN_NODE_SHARES.csv"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    rec = {}
    for a, b in COPIES:
        shutil.copyfile(a, b); rec[b.name] = dict(source=str(a).replace("/mnt/d/ResearchWorkspaces/ASEAN/", ""), sha256=sha(b))
    rows = []
    for c, f in SESSION_FILES.items():
        t = pd.read_csv(W07 / f, dtype=str, keep_default_na=False)
        for x in t.to_dict("records"):
            rows.append(dict(country=c, subsector=x["subsector"], node=x["node"], share_v4=x["share_v4"], note=x.get("note", ""), source=f"work/p1_v4_w07_20261106/{f}"))
    p = R / "industry_v4/NODE_SHARES_SESSIONS_V4.csv"
    pd.DataFrame(rows).to_csv(p, index=False, lineterminator="\n"); rec[p.name] = dict(source="W07 G0-G4 <CC>_NODE_SHARES.csv (share_v4 as written)", sha256=sha(p), rows=len(rows))
    (R / "industry_v4/INTAKE_NETWORK_W08.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
