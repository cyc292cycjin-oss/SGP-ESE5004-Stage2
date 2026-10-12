"""Finalize light evidence serialization and perform publication-only checks."""
from pathlib import Path
import ast,hashlib,json,shutil,re
from compact_exact_evidence import compact
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c07_v4_reliability_20261013')
O=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research/05_baseline_evolution/20261011/c07')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
put(O/'evidence/C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json',compact(W/'C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json'))
for name in ['finalize_c07.py','compact_exact_evidence.py','finish_local_review.py']:
    shutil.copyfile(W/name,O/'methods'/name)
report=O/'C07_V4_RELIABILITY_AND_REMEDIATION_RESULT.md'
text=report.read_text(encoding='utf-8')
anchor='见C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json，不把浮点差异归咎于坐标回映射。'
assert text.count(anchor)==1
if '审阅JSON保留全部533行' not in text:
    text=text.replace(anchor,anchor+' 审阅JSON保留全部533行的精确结果摘要、7列核算及关键库存/各家族最大残差行的完整支撑；其余完整支撑留在12,737,224字节的本地原始核算记录，附准确路径、SHA和逐支撑哈希。此处仅压缩公开表示，未重算、改变或省略失败结论。')
report.write_text(text,encoding='utf-8')
checked=[];ast_count=0
for p in sorted(O.rglob('*')):
    if not p.is_file() or p.name in ('C07_EVIDENCE_INDEX.json','C07_PUBLICATION_CHECK.json'):continue
    data=p.read_bytes()
    assert len(data)<4_000_000,(p,len(data))
    assert p.suffix.lower() not in ('.npy','.npz','.nc','.zip','.gz','.lic','.so','.pyc'),p
    assert b'-----BEGIN '+b'OPENSSH PRIVATE KEY-----' not in data and b'-----BEGIN '+b'RSA PRIVATE KEY-----' not in data,p
    assert not re.search(rb'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}',data),p
    if p.suffix=='.py':ast.parse(data.decode('utf-8-sig'),filename=str(p));ast_count+=1
    checked.append({'relative':p.relative_to(O).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
put(O/'evidence/C07_PUBLICATION_CHECK.json',{'status':'PASS','python_AST_files':ast_count,'files_checked':len(checked),
    'checks':['Each public member below 4MB','No array/NetCDF/archive/license/library payload','No private key blocks or GitHub credential tokens','Python AST parse only; no imported execution'],
    'secrets_not_read':True,'model_or_solver_calls':0,'full_exact_record_preserved':True})
files=[{'relative':p.relative_to(O).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
       for p in sorted(O.rglob('*')) if p.is_file() and p.name!='C07_EVIDENCE_INDEX.json']
put(O/'C07_EVIDENCE_INDEX.json',{'files':files,'large_arrays_included':False,'formal_V4_changed':False,
    'optimization_calls':2,'all_new_local_backups_verified':True})
print(json.dumps({'files':len(files),'bytes':sum(x['bytes'] for x in files),'largest':max(files,key=lambda x:x['bytes']),
                  'AST':ast_count,'full_record_sha':sha(W/'C07_EXACT_LOCAL_CROSS_COORDINATE_CHECK.json')},indent=2))
