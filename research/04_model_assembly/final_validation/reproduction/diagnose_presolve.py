from pathlib import Path
import json,highspy,time,resource
E=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_final_validation/evidence');R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/validation/gate5_20261006_01')
h=highspy.Highs();h.setOptionValue('threads',1);h.setOptionValue('log_file',str(E/'gate5_presolve_diagnostic.log'));h.setOptionValue('log_dev_level',3)
print(h.readModel(str(R/'gate5_problem.lp')),flush=True)
t=time.monotonic();s=h.presolve();print(s,h.getModelPresolveStatus(),flush=True)
r=dict(method='Native presolve only on unchanged saved LP; no optimizing run and no elastic IIS model',status=str(s),presolve_status=str(h.getModelPresolveStatus()),elapsed_seconds=time.monotonic()-t,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
(E/'PRESOLVE_DIAGNOSTIC_RECEIPT.json').write_text(json.dumps(r,indent=2)+'\n')
