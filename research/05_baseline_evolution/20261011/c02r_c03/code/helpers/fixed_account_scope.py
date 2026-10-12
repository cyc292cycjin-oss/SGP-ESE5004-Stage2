"""Human-authorized additional commodity scope; no inferred acceptance."""
from pathlib import Path
import json,hashlib
FILE='research_inputs/assembly_v1/sources/ANIMAL_WASTE_FIXED_ACCOUNT_DECISION.json'
def load_scope(repo):
 p=Path(repo)/FILE
 if not p.exists():return []
 d=json.loads(p.read_text());manifest=json.loads((Path(repo)/'research_inputs/assembly_v1/manifest.json').read_text())
 if hashlib.sha256(p.read_bytes()).hexdigest()!=manifest['files']['sources/ANIMAL_WASTE_FIXED_ACCOUNT_DECISION.json']:raise ValueError('Additional fixed-account authorization hash changed')
 if d['ApprovalStatus']!='HUMAN_ACCEPTED' or d['MethodID']!='ASSEMBLY_V1_EXTERNAL_PENDING_FIXED_ACCOUNTS' or not d['ActualStructuralValidationRequired']:raise ValueError('Additional commodity boundary not approved')
 if d['UnitPriceEUR2020PerMWh'] is not None or d['PhysicalCO2_tPerMWh'] is not None:raise ValueError('Unknown fixed parameter cannot become accepted zero')
 return [d]
def matching_scope(n,commodity,country,account,row):
 matches=[s for s in n.meta.get('additional_fixed_account_scope',[]) if s.get('ApprovalStatus')=='HUMAN_ACCEPTED' and s.get('MethodID')=='ASSEMBLY_V1_EXTERNAL_PENDING_FIXED_ACCOUNTS' and s.get('ActualStructuralValidationRequired') and (s.get('Commodity'),s.get('Country'),s.get('SourceAccountID'),s.get('SourceRow'))==(commodity,country,account,row)]
 if len(matches)>1:raise ValueError('Duplicate fixed-account authorization')
 return matches[0] if matches else None
