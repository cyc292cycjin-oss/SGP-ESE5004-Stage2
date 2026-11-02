from pathlib import Path
import pandas as pd
f=Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/V3_DATA_INTAKE.md"); t=f.read_text(encoding="utf-8")
for a,b in (("| 合计 | 243 | 471.3 | 279.5 |","| 合计 | 243 | 471.3 | 276.5 |"),
            ("产能字段：水泥 240 / 243 有 `cap`（LA、MM、MY、PH、TH 各缺 1–4）；熟料另一字段。","产能字段：水泥 235 / 243 有值（PH 缺 4，LA、MM、MY、TH 各缺 1）。"),
            ("| 11 国 | 1,906 | 1,174 | 61.6 % | | |","| 11 国 | 1,905 | 1,173 | 61.6 % | | |")):
    assert a in t, a
    t=t.replace(a,b)
f.write_text(t,encoding="utf-8")
p=Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/phase1/ID_NODE_TIMEZONE_PROPOSAL.csv")
d=pd.read_csv(p,index_col=0); d.loc[d.NAME_1=="Papua Barat","tz"]=9.0; d.to_csv(p); print(d.groupby("tz").size().to_dict())
