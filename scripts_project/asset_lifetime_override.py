"""Source-pinned lifetime overrides for explicitly named existing cohorts only."""
from pathlib import Path
import hashlib,json,copy
METHOD='ASSEMBLY_V1_AVION_OCGT_25Y_LIFETIME_PROXY'
DECISION='GATE4-20261006-LIMITED-OCGT-SOURCE-UNCERTAINTY#A'
FILE='research_inputs/asset_survival/asset_lifetime_overrides.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_overrides(repo):
 p=Path(repo)/FILE
 if not p.exists():return {'records':[]}
 d=json.loads(p.read_text())
 for rel,h in d['source_pins'].items():
  if sha(Path(repo)/rel)!=h:raise ValueError('Asset lifetime override source changed: '+rel)
 return d
def apply_override(unit,decisions):
 out=copy.deepcopy(unit);matches=[r for r in decisions.get('records',[]) if r['AssetID']==out['AssetID']]
 if len(matches)>1:raise ValueError('Duplicate asset lifetime decision')
 if not matches:return out
 d=matches[0]
 if d.get('ApprovalStatus')!='HUMAN_ACCEPTED':return out
 if out.get('AssetClass')!='OBSERVED_EXISTING':return out # no effect on new-build candidates
 if d['MethodID']!=METHOD or d['DecisionReference']!=DECISION:raise ValueError('Unrecognised limited lifetime authorization')
 for key in ['Country','Technology','OriginalCapacity','CommissioningYear']:
  if out.get(key)!=d[key]:raise ValueError('Material identity/year/capacity conflict: '+key)
 if out.get('MaterialSourceConflict') or out.get('UnresolvedRefurbishmentEvidence'):raise ValueError('New material asset conflict requires review')
 if d['Lifetime']!=25 or d.get('AcceptsPerformanceOrOM') is not False:raise ValueError('Lifetime-only boundary changed')
 out.update(Lifetime=d['Lifetime'],LifetimeAccepted=True,LifetimeSource=d['Source'],LifetimeDecisionReference=d['DecisionReference'],LifetimeMethodID=d['MethodID'],LifetimeMeaning='Explicit historical cohort proxy, not observed retirement forecast',DependableCapacityMW=d['DependableCapacityMW'],CapacityEvidenceLevel=d['CapacityEvidenceLevel'])
 return out
