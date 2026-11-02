"""Supplement 02: archive the small results of the two smoke runs (no logs, no LP or solution arrays)."""
import shutil
from pathlib import Path
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke_s2")
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke_s2"); P = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/path_check3")
for s in ("integrated", "no_new_xb"):
    (E / s).mkdir(exist_ok=True)
    for f in ("SOLVE_RECEIPT.json", "V5_GATES.json", "V6_ACCEPTANCE.json", "PRECISION.json", "LEDGER_IDENTITY.json", "STOP_CLASS.json", "COUNTRY_COST_LEDGER.csv", "ALLOCATION.csv"):
        if (R / s / f).exists():
            shutil.copy2(R / s / f, E / s / f)
for f in ("STATUS.txt", "BATCH_REFERENCE.json", "ID_LEDGER_DECOMPOSITION.csv", "VN_BIOMASS_BALANCE.json", "LA_EXPORT_UTILISATION.csv"):
    shutil.copy2(R / f, E / f)
shutil.copy2(R / "M12_BENEFIT/BENEFIT.csv", E / "BENEFIT.csv"); shutil.copy2(P / "STATUS.txt", E / "PATH_CHECK3_STATUS.txt")
print(sorted(p.name for p in E.iterdir()))
