"""Verify the existing raw-row capsule; no new data download or source correction."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,hashlib
W=Path(__file__).resolve().parent; E=W/'evidence'
capsule=json.loads((W/'stage/research_inputs/assembly_v1/sources/bunker_review.json').read_text())
paths={r['file']:r['file_sha256'] for x in capsule['records'] for r in x['selected_raw_records']+x['omitted_account_related_raw_records']}
raw={}
for name,digest in paths.items():
 p=Path(name); assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
 with p.open(encoding='utf-8-sig',newline='') as f:
  raw[name]=list(csv.DictReader(f,delimiter=';'))
proof=[]
for x in capsule['records']:
 total=D(0)
 for r in x['selected_raw_records']:
  matches=[s for s in raw[r['file']] if all(s.get(k)==r.get(k) for k in ['Country or Area','Commodity - Transaction','Year','Unit','Quantity'])]
  assert len(matches)==1,(x['country'],x['account'])
  total+=D(r['Quantity'])*D(str(r['audit_source_conversion_factor_to_TWh']))
 base=D(x['base_text']) if x['base_text'] else None
 exact=bool(x['selected_raw_records']) and base is not None and abs(total-base)<=D('0.000051')
 clean=exact and not x['omitted_account_related_raw_records'] and base>0
 proof.append(dict(country=x['country'],account=x['account'],base_text=x['base_text'],base_TWh=str(base) if base is not None else None,raw_selected_sum_TWh=str(total) if x['selected_raw_records'] else None,original_hashes_verified=True,selected_rows_verified=len(x['selected_raw_records']),cache_rounding_verified=exact,omitted_rows=len(x['omitted_account_related_raw_records']),source_status=x['status'],eligible_verified_2019_obligation=clean,rounding_tolerance_TWh='0.000051',heat_basis='Frozen upstream mass-to-energy constants; UNSD 2014 standard NCV lineage for liquid fuel; no second conversion'))
(E/'BUNKER_BASE_VERIFICATION.json').write_text(json.dumps(dict(raw_file_sha256=paths,records=proof),indent=2)+'\n')
print(json.dumps(dict(raw_files_verified=len(paths),verified_accounts=sum(x['eligible_verified_2019_obligation'] for x in proof),pending_accounts=[(x['country'],x['account'],x['source_status']) for x in proof if not x['eligible_verified_2019_obligation']]),indent=2))
