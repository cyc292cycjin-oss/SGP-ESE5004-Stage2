import logging
import pypsa
logging.disable(logging.WARNING)
n = pypsa.Network("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke_r2/no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc")
c = n.buses.country.astype(str); s = n.storage_units[n.storage_units.bus.map(c) == "LA"]
print((s.groupby(s.carrier.astype(str)).p_nom_opt.sum() / 1e3).round(2).to_dict(), "existing part GW", round(float(s.p_nom.sum()) / 1e3, 2), "units", len(s))
