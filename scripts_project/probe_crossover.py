from pathlib import Path
import json,sys
import highspy,numpy as np
from scipy.sparse import csr_matrix
from inventory_audit import evaluate_block
root=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');out=root/'results_project/validation/inventory_local_20261006_01';g=json.loads((out/'FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json').read_text())['groups'][79]
d=dict(np.load(out/'block_79.npz'));names=json.loads((out/'block_79_row_names.json').read_text());a=csr_matrix((d['data'],d['indices'],d['indptr']),shape=tuple(d['shape']));s=g['scale']
h=highspy.Highs();h.setOptionValue('threads',2);h.setOptionValue('solver','ipm');h.setOptionValue('run_crossover','on');h.setOptionValue('log_file',str(out/'block_79_A_CROSSOVER.log'))
h.addVars(a.shape[1],d['var_lower']/s,d['var_upper']/s);h.addRows(a.shape[0],d['row_lower']/s,d['row_upper']/s,a.nnz,a.indptr.astype(np.int32),a.indices.astype(np.int32),a.data)
h.run();x=np.asarray(h.getSolution().col_value)*s
r={'test':'block_79_A_CROSSOVER','solver_status':h.getModelStatus().name,'local_solver_runs':1,'synthetic_solver_runs':0,'real_gate5_runs':0,'primal_feasibility_tolerance':h.getOptionValue('primal_feasibility_tolerance')[1],'original_unit_validation':evaluate_block(d,x,g['original_energy_error_bound_mwh'],g['original_power_error_bound_mw'],names)}
(out/'CROSSOVER_JUSTIFICATION_PROBE.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
