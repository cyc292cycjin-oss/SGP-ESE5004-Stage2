"""C09 block primal: binary64 feasible point for the decoupled zero-cost fixed-resource block.
Read-only on the frozen C03 CSC. Duals on the block are set to exactly 0 (valid: block cost 0)."""
import sys, json, hashlib, collections, numpy as np
from fractions import Fraction as F
sys.path.insert(0,'.')
from load import A, rl, ru, c, n, m
import pickle
from meta import rowfam
ci=pickle.load(open('colinfo.pkl','rb'))
S=np.load('S.npy'); Srows=np.load('Srows.npy'); bcols=np.where(S)[0]
R=A.tocsr()
col={ci[j]:j for j in bcols}
stores=sorted({ci[j][1] for j in bcols if ci[j][0]=='Store-e'})
meter=lambda s:s.replace('fixed resource','final-energy meter')
T=365
Q={}
for s in stores:
    for i in A.indices[A.indptr[col[('Store-e',s,0)]]:A.indptr[col[('Store-e',s,0)]+1]]:
        if rowfam(i)=='Store-energy_balance' and R.indptr[i+1]-R.indptr[i]==2: Q[s]=-float(rl[i])
groups=collections.defaultdict(lambda:[None]*T); members={}
for i in Srows:
    if rowfam(i)=='Bus-nodal_balance' and rl[i]>0:
        ks=R.indices[R.indptr[i]:R.indptr[i+1]]; names=tuple(sorted(ci[k][1] for k in ks)); t=ci[ks[0]][2]
        groups[names][t]=float(rl[i]); members[names]=[nm.replace('final-energy meter','fixed resource') for nm in names]
x=np.zeros(n)
for g,d in sorted(groups.items()):
    acc=members[g]; rem={s:F(Q[s]) for s in acc}
    for t in range(T):
        need=F(d[t])
        for k,s in enumerate(acc):
            last=(k==len(acc)-1)
            cap=rem[s]/24
            if last: take=need                      # last account takes the remainder (feasible since D<=Q)
            else:
                take=min(need,cap)
                tf=float(take)
                if F(tf)>take: tf=np.nextafter(tf,-np.inf)   # round DOWN so no overdraw
                take=F(max(tf,0.0))
            tf=float(take)
            x[col[('Store-p',s,t)]]=tf; x[col[('Link-p',meter(s),t)]]=tf
            rem[s]-=24*F(tf); need-=F(tf)
            ef=float(rem[s]); x[col[('Store-e',s,t)]]=ef
        # need may be ~ulp nonzero due to float(take) of last account
    for s in acc:
        x[col[('Link-p_nom',meter(s),None)]]=max(x[col[('Link-p',meter(s),t)]] for t in range(T))
# exact rational residuals of the binary64 point on all block rows
worst=collections.defaultdict(lambda:F(0)); cnt=collections.Counter()
for i in Srows:
    a=sum(F(float(R.data[p]))*F(float(x[R.indices[p]])) for p in range(R.indptr[i],R.indptr[i+1]))
    v=F(0)
    if np.isfinite(rl[i]) and a<F(float(rl[i])): v=F(float(rl[i]))-a
    if np.isfinite(ru[i]) and a>F(float(ru[i])): v=max(v,a-F(float(ru[i])))
    f=rowfam(i); f='ResearchStoreDirection' if f.startswith('ResearchStoreDirection') else f
    if v>0: cnt[f]+=1; worst[f]=max(worst[f],v)
xb=x[bcols]
np.save('c09/C09_BLOCK_PRIMAL.npy',xb); np.save('c09/C09_BLOCK_COLUMNS.npy',bcols.astype(np.int64)); np.save('c09/C09_BLOCK_ROWS.npy',np.sort(Srows).astype(np.int64))
h=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()
rec={'status':'BLOCK_PRIMAL_BINARY64_BUILT','block_columns':int(len(bcols)),'block_rows':int(len(Srows)),
 'exact_rational_residual_on_binary64_point':{'rows_with_nonzero_violation':dict(cnt),'max_violation_LP_units':{k:float(v) for k,v in worst.items()}},
 'block_duals':'exactly 0 (Pi on block rows, RC on block columns); valid because block cost is identically 0 and block is decoupled',
 'files':{f:h('c09/'+f) for f in ['C09_BLOCK_PRIMAL.npy','C09_BLOCK_COLUMNS.npy','C09_BLOCK_ROWS.npy']}}
json.dump(rec,open('c09/C09_BLOCK_PRIMAL_RECEIPT.json','w'),indent=1); print(json.dumps(rec,indent=1))
