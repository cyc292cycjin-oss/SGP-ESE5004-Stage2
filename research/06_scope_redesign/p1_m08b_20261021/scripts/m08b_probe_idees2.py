"""M08b probe: JRC-IDEES-2021 EU27 OIS final energy 2019 by process row (read-only)."""
import pandas as pd

X = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research_inputs/registry_v5/sources/jrc_idees_2021/EU27/JRC-IDEES-2021_Industry_EU27.xlsx"
for sheet in ["OIS_fec", "OIS_ued"]:
    d = pd.read_excel(X, sheet, header=None)
    hdr = list(d.iloc[0])
    yc = next(j for j, v in enumerate(hdr) if str(v).startswith("2019"))
    print("=====", sheet, "col", yc, d.shape)
    for i in range(1, len(d)):
        v = d.iat[i, 0]
        if isinstance(v, str) and v.strip():
            if v.startswith("Market shares") or v.startswith("Ratio of useful"):
                break
            print(i, repr(v)[:80], d.iat[i, yc])
