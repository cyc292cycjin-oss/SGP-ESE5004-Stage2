"""One authorized read-only CSC structure pass, restricted row extraction.
No solver, scientific builder, dense matrix, matrix multiplication or mutation.
"""
import collections,datetime,hashlib,json,math,os,resource,shutil,time
from pathlib import Path
from fractions import Fraction
import numpy as np

W=Path('/mnt/d/ResearchWorkspaces/ASEAN')
WORK=W/'work/baseline_evolution_audit_20261011/a03_full_support_20261011'
E=W/'work/baseline_evolution_audit_20261011/delivery/evidence/a03_full_lp'
P=W/'work/baseline_evolution_audit_20261011/delivery/evidence/A03_EXACT_LOCAL_LP_EVIDENCE.json'
H=W/'outputs/cloud_gate6/cloud_gate6_hipo_capture_20261008T200734Z/completed_backup/runs/cloud_gate6_hipo_capture_20261008T200734Z'
CHUNK=1<<20
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sig(p):s=p.stat();return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def filehash(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(8<<20):h.update(b)
 return h.hexdigest()
def seq(q):
 a=np.arange(q['count'],dtype=np.int64)*q['stride']+q['first']
 assert int(a[-1])==q['last'] and sha_bytes(a.astype('<i8').tobytes())==q['int64_le_sha256']
 return a
def avail():
 return int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
def safe():
 if avail()<1<<30:raise RuntimeError('LOCAL_AVAILABLE_MEMORY_BELOW_1_GIB')
 if shutil.disk_usage(W).free<1<<30:raise RuntimeError('LOCAL_DISK_BELOW_1_GIB')
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>1<<30:raise RuntimeError('LOCAL_AUDIT_RSS_ABOVE_1_GIB')
def open_npy(p,expected):
 f=p.open('rb');version=np.lib.format.read_magic(f)
 shape,fortran,dtype=np.lib.format._read_array_header(f,version)
 assert shape==(expected['count'],) and dtype.str==expected['dtype'] and not fortran
 offset=f.tell();f.seek(0);header=f.read(offset)
 assert p.stat().st_size==offset+dtype.itemsize*shape[0]
 return f,header,dtype

t0=time.monotonic();safe();WORK.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
claim=WORK/'STRUCTURE_SCAN_ONCE.json'
assert not claim.exists(),'No repeat scan permitted: use already extracted support'
prior=json.loads(P.read_text());assert filehash(P)=='76364cb31e48ef0cecba6620caa8a4ffe26165a7681bd4288a249207eb6a17ec'
mp=H/'math_problem/MATH_PROBLEM.json';mm=H/'mapping/MAPPING_MANIFEST.json';fp=H/'SOLVER_TRANSFER_FIDELITY.json'
assert filehash(mp)==prior['source_math_manifest_sha256']
m=json.loads(mp.read_text());mapping=json.loads(mm.read_text())
assert filehash(mm)==m['provenance']['mapping_sha256']
assert filehash(fp)==m['provenance']['fidelity_sha256']
assert m['arrays']==prior['source_array_identities']
assert (m['num_col'],m['num_row'],m['arrays']['index']['count'])==(19568505,48301938,90782037)
assert m['matrix_format']==1 and m['canonical_storage_roundtrip_verified']
assert m['provenance']['input_sha256']==mapping['input_sha256']=='238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d'
for name,h in prior['coordinate_sha_checks'].items():
 assert any(b['coordinate_sha256'].get(name)==h for k in ['variables','constraints'] for b in mapping[k])

families=[];targets=[]
for s in prior['row_specs']:
 fam=s['family'];rs=seq(s['rows'])
 if fam.startswith('ResearchStoreDirection'):continue
 if fam=='Store-fix-e-lower':rs=rs[-1:]
 assert fam in ['Store-energy_balance','Store-fix-e-lower','Bus-nodal_balance']
 idx=len(families);families.append({'id':idx,'asset':s['asset'],'family':fam,'rows':rs.tolist(),'original_multiplier':0 if fam=='Store-fix-e-lower' else 3 if fam=='Bus-nodal_balance' else 1})
 targets.extend(rs.tolist())
target=np.array(sorted(targets),dtype='<i8');assert len(target)==len(set(targets))==26284
selection={'group':prior['group'],'zero_based':True,'target_row_count':len(target),'target_sorted_int64_sha256':sha_bytes(target.tobytes()),'families':families,'source_prior_evidence_sha256':filehash(P)}
dump(E/'TARGET_ROW_SELECTION.json',selection)
selected_cols=np.unique(np.concatenate([seq(s['columns']) for s in prior['column_specs']]))
identities=[];before={}
# Reverify identities without recomputing the scientific model or constraint residuals.
for folder,entries in [('math_problem',m['arrays']),('mapping',mapping['arrays'])]:
 for name,meta in entries.items():
  path=H/folder/meta['file'];before[str(path)]=sig(path)
  if folder=='math_problem' and name in ['index','value']:continue
  a=np.load(path,mmap_mode='r',allow_pickle=False)
  assert a.shape==(meta['count'],) and a.dtype.str==meta['dtype'];del a
  actual=filehash(path);assert actual==meta['sha256'],str(path)
  identities.append({'path':str(path).replace('/mnt/d/','D:/'),'sha256':actual,'expected_sha256':meta['sha256'],'bytes':path.stat().st_size,'status':'MATCH'})
  safe()
print(json.dumps({'stage':'IDENTITIES_READY_FOR_SINGLE_STRUCTURE_SCAN','target_rows':len(target),'elapsed_seconds':time.monotonic()-t0}),flush=True)
starts=np.load(H/'math_problem/start.npy',mmap_mode='r');assert int(starts[0])==0 and int(starts[-1])==90782037
for lo in range(0,len(starts)-1,CHUNK):assert np.all(starts[lo+1:min(lo+CHUNK+1,len(starts))]>=starts[lo:min(lo+CHUNK,len(starts)-1)])
D=np.load(H/'mapping/D.npy',mmap_mode='r');R=np.load(H/'mapping/R.npy',mmap_mode='r')
rl=np.load(H/'math_problem/row_lower.npy',mmap_mode='r');ru=np.load(H/'math_problem/row_upper.npy',mmap_mode='r')
membership=np.zeros(m['num_row'],dtype=np.bool_);membership[target]=True
rows={int(r):[] for r in target};stored_positions=[]
control={'state':'STARTED','started_utc':utc(),'source_math_sha256':filehash(mp),'maximum_structure_passes':1,'chunk_entries':CHUNK,'pid':os.getpid()}
with claim.open('x') as f:json.dump(control,f,indent=2);f.flush();os.fsync(f.fileno())
scan0=time.monotonic();nf=m['arrays']['index']['count'];ii=H/'math_problem/index.npy';vv=H/'math_problem/value.npy'
fi,hi,di=open_npy(ii,m['arrays']['index']);fv,hv,dv=open_npy(vv,m['arrays']['value'])
ih=hashlib.sha256(hi);vh=hashlib.sha256(hv);ivh=hashlib.sha256();vvh=hashlib.sha256()
with fi,fv:
 for lo in range(0,nf,CHUNK):
  n=min(CHUNK,nf-lo);ib=fi.read(n*di.itemsize);vb=fv.read(n*dv.itemsize)
  assert len(ib)==n*di.itemsize and len(vb)==n*dv.itemsize
  ih.update(ib);vh.update(vb);ivh.update(ib);vvh.update(vb)
  ix=np.frombuffer(ib,dtype=di);vals=np.frombuffer(vb,dtype=dv)
  assert ix.min()>=0 and ix.max()<m['num_row']
  k=np.flatnonzero(membership[ix]);pos=k.astype(np.int64)+lo
  cols=np.searchsorted(starts,pos,side='right')-1
  for local,absolute,col in zip(k,pos,cols):
   row=int(ix[local]);val=float(vals[local]);assert math.isfinite(val)
   rows[row].append([int(col),val.hex()]);stored_positions.append(int(absolute))
  if lo%(CHUNK*16)==0:safe();print(json.dumps({'stage':'SCANNING_ONCE','entries_processed':lo+n,'total':nf,'target_entries':sum(len(v) for v in rows.values())}),flush=True)
 assert fi.read(1)==fv.read(1)==b''
for name,path,actual,valuehash in [('index',ii,ih.hexdigest(),ivh.hexdigest()),('value',vv,vh.hexdigest(),vvh.hexdigest())]:
 meta=m['arrays'][name];assert actual==meta['sha256'] and valuehash==meta['value_sha256'],name
 identities.append({'path':str(path).replace('/mnt/d/','D:/'),'sha256':actual,'expected_sha256':meta['sha256'],'value_sha256':valuehash,'bytes':path.stat().st_size,'status':'MATCH_SAME_STREAM_AS_EXTRACTION'})
del membership
for p,old in before.items():assert sig(Path(p))==old,('source_changed_during_read',p)
entries=sum(len(v) for v in rows.values());zero_count=sum(float.fromhex(v)==0 for row in rows.values() for c,v in row)
actual_cols={c for row in rows.values() for c,v in row if float.fromhex(v)!=0};omitted=sorted(actual_cols-set(selected_cols.tolist()))
assert all(rows[int(r)] for r in target)
shards=[];original_support_mismatches=[]
col_lookup={}
for s in prior['column_specs']:col_lookup[(s['asset'],s['family'])]=seq(s['columns'])
resource_to_account={}
stores=[s for s in prior['column_specs'] if s['family']=='Store-e']
for f in families:
 if f['family']=='Bus-nodal_balance' and f['asset']!=prior['group']:
  # Match by shared frozen input/commodity prefix, then confirm using actual local entries.
  candidates=[s for s in stores if s['asset']==f['asset'].replace(' :: ',' ')+' fixed resource']
  assert len(candidates)==1,(f['asset'],candidates)
  resource_to_account[f['asset']]=candidates[0]['asset']
for fam in families:
 records=[];family=fam['family'];asset=fam['asset']
 for t,row in enumerate(fam['rows']):
  terms=sorted(rows[row]);assert len({c for c,v in terms})==len(terms),'duplicate CSC entries in a target row'
  rr=float(R[row]);assert math.isfinite(rr) and rr>0
  orig={c:Fraction(float.fromhex(v))/Fraction(rr)/Fraction(float(D[c])) for c,v in terms if float.fromhex(v)!=0}
  if family=='Store-energy_balance':
   es=col_lookup[(asset,'Store-e')];ps=col_lookup[(asset,'Store-p')];exp={int(es[t]):Fraction(-1),int(ps[t]):Fraction(-3)}
   if t:exp[int(es[t-1])]=Fraction(1)
  elif family=='Store-fix-e-lower':exp={int(col_lookup[(asset,'Store-e')][-1]):Fraction(1)}
  elif asset==prior['group']:exp={int(seq(s['columns'])[t]):Fraction(1) for s in prior['column_specs'] if s['family']=='Link-p'}
  else:
   a=resource_to_account[asset];meter=a.removesuffix(' fixed resource')+' final-energy meter'
   exp={int(col_lookup[(a,'Store-p')][t]):Fraction(1),int(col_lookup[(meter,'Link-p')][t]):Fraction(-1)}
  if orig!=exp:original_support_mismatches.append({'row':row,'asset':asset,'actual':{str(k):str(v) for k,v in orig.items()},'expected':{str(k):str(v) for k,v in exp.items()}})
  records.append([row,float(rl[row]).hex(),float(ru[row]).hex(),rr.hex(),terms])
 path=E/f'SUPPORT_{fam["id"]:02d}.json'
 # One line per actual row: small, reviewable shards, all exact binary64 values in hex.
 meta={k:v for k,v in fam.items() if k!='rows'};meta.update(record_schema=['row','native_lower_hex','native_upper_hex','R_hex','terms:[[column,native_coefficient_hex],...]'],row_count=len(records),complete_row_support=True)
 with path.open('w') as f:
  f.write('{"metadata":'+json.dumps(meta,ensure_ascii=False,separators=(',',':'))+',"rows":[\n')
  for k,rec in enumerate(records):f.write(json.dumps(rec,separators=(',',':'))+(',' if k+1<len(records) else '')+'\n')
  f.write(']}\n');f.flush();os.fsync(f.fileno())
 shards.append({'file':path.name,'bytes':path.stat().st_size,'sha256':filehash(path),'row_count':len(records),'stored_entries':sum(len(rec[4]) for rec in records),'family':family,'asset':asset})
scale_groups=collections.defaultdict(list)
for c in sorted(actual_cols):scale_groups[float(D[c]).hex()].append(c)
actual_column_records={'column_count':len(actual_cols),'groups':[{'D_hex':h,'columns':cs} for h,cs in sorted(scale_groups.items())]}
cp=E/'SELECTED_COLUMN_SCALES.json';dump(cp,actual_column_records)
identity={'schema':'A03_FROZEN_IDENTITY_V1','math_manifest_sha256':filehash(mp),'mapping_manifest_sha256':filehash(mm),'transfer_fidelity_sha256':filehash(fp),'input_network_sha256_reused':mapping['input_sha256'],'dimensions':{'columns':m['num_col'],'rows':m['num_row'],'nonzeros':nf},'array_identities':identities,'coordinate_hashes_reused_and_manifest_matched':prior['coordinate_sha_checks'],'all_source_stat_unchanged':True,'proof_objective_independent':True,'historical_cost_and_offset_not_scope_v3':'MATH_PROBLEM archives earlier objective; certificate uses only unchanged constraints/bounds. No objective is modified.'}
dump(E/'FROZEN_IDENTITY_CHECK.json',identity)
result={'status':'FULL_SUPPORT_EXTRACTED','started_utc':control['started_utc'],'finished_utc':utc(),'one_CSC_structure_pass':True,'entries_scanned':nf,'chunk_entries':CHUNK,'target_rows':len(target),'target_entries':entries,'target_explicit_zero_entries':zero_count,'target_nonzero_columns':len(actual_cols),'unexpected_columns_outside_prior_local_set':omitted,'original_formula_support_mismatches':original_support_mismatches,'source_index_sha256':ih.hexdigest(),'source_value_sha256':vh.hexdigest(),'selected_CSC_positions_int64_sha256':sha_bytes(np.array(stored_positions,dtype='<i8').tobytes()),'structure_scan_seconds':time.monotonic()-scan0,'total_seconds_including_identity':time.monotonic()-t0,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'available_memory_bytes_at_end':avail(),'D_drive_free_bytes_at_end':shutil.disk_usage(W).free,'read_method':'1,048,576 entries per aligned sequential index/value read; SHA computed in same stream. mmap read-only start/D/R/bounds; 48,301,938-byte row membership vector, no dense matrix or residual scan.','shards':shards,'scales_file':{'file':cp.name,'sha256':filehash(cp),'bytes':cp.stat().st_size},'solver_calls':0,'model_builds':0,'autodl_operations':0,'science_mutations':0}
dump(E/'COMPLETE_SUPPORT_RECEIPT.json',result)
dump(WORK/'STRUCTURE_SCAN_COMPLETED.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ['shards','original_formula_support_mismatches']},indent=2),flush=True)
