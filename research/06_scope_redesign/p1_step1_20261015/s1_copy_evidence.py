"""Copy the S1 machine-readable receipts (JSON/CSV/log) from results_project/s1 into work/p1_step1_20261015/evidence (read-only copy; .nc networks stay in results_project, their SHA is recorded)."""
from pathlib import Path
import hashlib,json,shutil
REPO=Path(r'\\wsl.localhost\Ubuntu\home\jin\research\SGP_ESE5004_Stage2\phase2\research_model');S1=REPO/'results_project'/'s1';OUT=Path(__file__).resolve().parent/'evidence'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True);index={}
    for p in sorted(S1.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(S1)
        if p.suffix=='.nc':index[str(rel).replace('\\','/')]=dict(copied=False,sha256=sha(p),bytes=p.stat().st_size);continue
        if p.suffix in ('.json','.csv','.log') and 'lp' not in rel.parts and 'solution' not in rel.parts and 'v5' not in rel.parts and 'kkt' not in rel.parts:
            dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);index[str(rel).replace('\\','/')]=dict(copied=True,sha256=sha(dst),bytes=dst.stat().st_size)
    for p in sorted(S1.rglob('MATH_PROBLEM.json')):
        rel=p.relative_to(S1);dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);index[str(rel).replace('\\','/')]=dict(copied=True,sha256=sha(dst),bytes=dst.stat().st_size)
    (OUT/'EVIDENCE_INDEX.json').write_text(json.dumps(dict(source=str(S1),files=index),indent=2)+'\n',encoding='utf-8');print('copied',sum(v['copied'] for v in index.values()),'files; recorded',len(index))
if __name__=='__main__':main()
