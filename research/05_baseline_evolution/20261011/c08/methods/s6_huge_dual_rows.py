from load import *
import json,bisect
yy=np.load('yy.npy')
d=json.load(open('/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/bridge/mapping/MAPPING_MANIFEST.json'))
starts=[r['start'] for r in d['row_ranges']]
def fam(i): return d['row_ranges'][bisect.bisect_right(starts,i)-1]['family']
o=np.argsort(-np.abs(yy))[:8]
R=A.tocsr()
for i in o: print(i,fam(i),yy[i],'orig y',y[i],'nnz',R.indptr[i+1]-R.indptr[i],'rl/ru',rl[i],ru[i])
print('count |y|>1e6',(np.abs(yy)>1e6).sum(),' >1e9',(np.abs(yy)>1e9).sum(), ' orig y max',np.abs(y).max())
