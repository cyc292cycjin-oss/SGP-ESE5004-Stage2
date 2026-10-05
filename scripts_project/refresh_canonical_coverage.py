"""Refresh existing bounded-source exclusions only; no new demand or method."""
from pathlib import Path
import json,hashlib,argparse
from reconstruct_base_accounts import reconstruct

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def refresh(folder,output):
    s=folder/'sources';old=json.loads((s/'BASE_RECONSTRUCTION.json').read_text());new=reconstruct(s)
    by={r['AccountID']:r for r in new['accounts']};changes=[]
    for r in old['accounts']:
        z=by[r['AccountID']]
        if r==z:continue
        if r['Status']!=z['Status']:
            if r['Status']!='UNRESOLVED' or z['Status']!='SOURCE_BOUNDED_ZERO' or r['SelectedRawRows'] or not z['ZeroEvidence']:raise ValueError('Unapproved source qualification change: '+r['AccountID'])
            changes.append(dict(AccountID=r['AccountID'],Before=r['Status'],After=z['Status'],Rule='EXISTING_BOUNDED_FEC_EXHAUSTION; strict canonical identity and source scope; no new sector exclusion',ZeroEvidence=z['ZeroEvidence']))
        elif r['ValueMWh']!=z['ValueMWh']:raise ValueError('Positive demand changed')
    # Preserve established source files if nothing changed on repeat execution.
    if not changes:
        save(output,dict(changes=[],status='IDEMPOTENT_NO_CHANGE',physical_values_changed=0));return
    save(s/'BASE_RECONSTRUCTION.json',new);digest=sha(s/'BASE_RECONSTRUCTION.json');data=json.loads((folder/'registry.json').read_text())
    for r in data['records']:
        if r.get('Source')!='sources/BASE_RECONSTRUCTION.json':continue
        r['SourceSHA256']=digest
        if r.get('Locator') not in by:continue
        b=by[r['Locator']]
        if r.get('Year')==2050 and any(c['AccountID']==r['Locator'] for c in changes):
            if r.get('Value') is not None:raise ValueError('Would remove positive demand')
            r.update(BaseValueMWh=b['ValueMWh'],BaseStatus=b['Status'],Classification='SOURCE_SUPPORTED_NOT_APPLICABLE',NumericStatus='SOURCE_BOUNDED_ZERO',ZeroEvidence=';'.join(b['ZeroEvidence']),ExclusionEvidence='Existing source-bounded FEC exhaustion rule; original row IDs and commodity controls preserved; not a claim about missing commodity inventory',Reason=b['Reason'],SourceQualified=True)
    save(folder/'registry.json',data);pins=json.loads((folder/'manifest.json').read_text())
    for rel in ['sources/BASE_RECONSTRUCTION.json','registry.json']:pins['files'][rel]=sha(folder/rel)
    save(folder/'manifest.json',pins)
    save(output,dict(changes=changes,physical_values_changed=0,new_scientific_assumption=False,registry_sha256=sha(folder/'registry.json'),base_sha256=digest))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();refresh(a.folder,a.output)
