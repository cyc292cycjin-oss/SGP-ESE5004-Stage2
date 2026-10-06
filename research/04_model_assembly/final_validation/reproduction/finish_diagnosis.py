from pathlib import Path
import re,json,hashlib
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');E=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_final_validation/evidence')
proof=json.loads((E/'EXACT_LP_CONTRADICTION.json').read_text());targets={x['variable_label'] for x in proof['remaining_lhs']};bounds={}
lp=R/'results_project/validation/gate5_20261006_01/gate5_problem.lp';lines=[];terms={};label=None
with lp.open() as f:
 for line in f:
  match=re.fullmatch(r'c(\d+):\s*',line)
  if match:label=int(match[1]);lines=[line.strip()];terms={}
  elif label is not None:
   s=line.strip();lines.append(s);term=re.fullmatch(r'([+-]?[\d.eE+-]+) x(\d+)',s)
   if term:terms[int(term[2])]=float(term[1])
   elif s.startswith(('=','<=','>=')):
    if len(terms)==1 and set(terms)<=targets and s.split()[0]=='>=' and float(s.split()[1])==0. and next(iter(terms.values()))==1.:
     k=next(iter(terms));bounds[k]={'constraint_label':label,'raw_lines':lines}
    label=None
assert set(bounds)==targets
proof['nonnegative_inventory_bounds_verified_from_actual_lp']={str(k):v for k,v in bounds.items()}
proof['original_lp_sha256']=hashlib.sha256(lp.read_bytes()).hexdigest()
(E/'EXACT_LP_CONTRADICTION.json').write_text(json.dumps(proof,indent=2)+'\n')
(E/'IIS_DIAGNOSTIC_LIMITATION.json').write_text(json.dumps({'status':'NO_IIS_CERTIFICATE_RETURNED','process_exit_code':1,'observation':'HiGHS getIis constructed an internal elastic diagnostic with10179104columns and exited without returning a certificate; WSL restarted during this interval. No exit traceback or kernel OOM record recovered. Resource exhaustion is inferred, not proven.','diagnostic_model_is_not_a_research_solve':True,'no_elastic_solution_used':True,'subsequent_exact_algebra_certificate':'EXACT_LP_CONTRADICTION.json'},indent=2)+'\n')
print(json.dumps(proof['nonnegative_inventory_bounds_verified_from_actual_lp'],indent=2))
