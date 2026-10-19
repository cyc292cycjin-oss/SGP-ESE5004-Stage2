"""check: CO2-row duals mapped from Pi.npy (model rebuild) == the dual file of the identical integrated LP (S4M-S2 re-run). Read only."""
import sys, json
sys.path.insert(0, "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/scripts")
from pathlib import Path
from s4n_c2_compare import co2_duals_from_file, co2_duals_from_pi
RM = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
a = co2_duals_from_pi(RM, RM / "results_project/s4m/s4m2/solves/s4m_A_integrated", RM / "results_project/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc", "integrated")
b = co2_duals_from_file(RM / "results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun")
print(json.dumps({c: (a.get(c), b.get(c), (a.get(c) - b.get(c)) if (a.get(c) is not None and b.get(c) is not None) else None) for c in sorted(set(a) | set(b))}))
print("MAX_ABS_DIFF", max(abs(a[c] - b[c]) for c in a if c in b))
