from load import *
import json, collections
cf=np.load('colfam.npy'); names=json.load(open('famnames.json'))
B='/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/'
vl=np.load(B+'bridge/mapping/vlabels.npy')
d=json.load(open(B+'artifacts/mapping/LABELS.json'))
big=np.where(np.abs(y)>1e9)[0]
R=A.tocsr()
cols=np.concatenate([R.indices[R.indptr[i]:R.indptr[i+1]] for i in big[:20000]])
print('families of cols in huge-y rows:',collections.Counter(names[k] for k in cf[cols]))
# map some columns to asset names
vmeta={}
for v in d['variables']:
    if v['name'] in ('Store-p','Link-p','Store-e'):
        lab=np.load(B+'artifacts/mapping/'+v['labels_file'])
        vmeta[v['name']]=(lab,v)
inv={}
names_seen=collections.Counter()
for nm,(lab,v) in vmeta.items():
    dims=v['dims']; comp=v['coordinates'][dims[1]]
    pos={int(l):(t,a) for (t,a),l in np.ndenumerate(lab) if l>=0}
    for j in set(cols.tolist()):
        if names[cf[j]]==nm:
            t,a=pos[int(vl[j])]; names_seen[(nm,comp[a].split('@')[0][-40:] if '@' in comp[a] else comp[a][-60:])]+=0
            names_seen[(nm,' '.join(comp[a].split()[-3:]))]+=1
for k,v in names_seen.most_common(12): print(v,k)
print('distinct |y| values among huge',np.unique(np.abs(y[big]))[:5], len(np.unique(np.abs(y[big]))))
