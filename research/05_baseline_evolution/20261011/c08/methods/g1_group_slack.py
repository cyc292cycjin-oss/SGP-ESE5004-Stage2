import json
from fractions import Fraction as F
import collections, math
g=json.load(open('/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/artifacts/SCHEME_A_DAILY_EXACT_GROUPS.json'))
print(g.keys() if isinstance(g,dict) else None, len(g['groups']))
print({k:v for k,v in g.items() if k!='groups'})
rows=[]
for x in g['groups']:
    D,Q,S=F(x['D']),F(x['Q']),F(x['slack']); assert Q-D==S
    rows.append((float(S),float(D),len(x['accounts']),x['load']))
S=sorted(r[0] for r in rows)
print('n',len(S),'Sg min',S[0],'median',S[len(S)//2],'max',S[-1])
print('Sg==0:',sum(s==0 for s in S),' Sg<1e-9:',sum(s<1e-9 for s in S),' <1e-7:',sum(s<1e-7 for s in S),' <1e-6:',sum(s<1e-6 for s in S))
print('Sg/D max',max(r[0]/r[1] for r in rows),' D range',min(r[1] for r in rows),max(r[1] for r in rows))
print('accounts per group',collections.Counter(r[2] for r in rows))
print('n accounts total',sum(r[2] for r in rows))
json.dump(rows,open('groups_sg.json','w'))
