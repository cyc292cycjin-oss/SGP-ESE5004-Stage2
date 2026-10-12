# Exact rational feasibility certificate for the decoupled fixed-resource block
from load import *
from meta import rowfam
from fractions import Fraction as F
import pickle, collections, json, hashlib, time
t0=time.time()
ci=pickle.load(open('colinfo.pkl','rb'))
S=np.load('S.npy'); Srows=np.load('Srows.npy')
R=A.tocsr()
col={}  # (var, name, t) -> j
for j in np.where(S)[0]: col[ci[j]]=j
stores=sorted({n for (v,n,t) in (ci[j] for j in np.where(S)[0]) if v=='Store-e'})
meter=lambda s: s.replace('fixed resource','final-energy meter')
T=365
# --- read Q_a from initial energy balance RHS and e-upper rows, exactly
def rowsof(j): return A.indices[A.indptr[j]:A.indptr[j+1]]
Q={}; Eup={}
for s in stores:
    j0=col[('Store-e',s,0)]
    for i in rowsof(j0):
        f=rowfam(i)
        if f=='Store-energy_balance' and R.indptr[i+1]-R.indptr[i]==2: assert rl[i]==ru[i]; Q[s]=-F(float(rl[i]))
        if f=='Store-fix-e-upper': Eup[s]=F(float(ru[i]))
assert len(Q)==807 and len(Eup)==807
print('e_upper == initial for all accounts:',all(Eup[s]==Q[s] for s in stores))
# --- groups from load-bus rows
groups=collections.defaultdict(lambda:[None]*T); members={}
for i in Srows:
    ks=R.indices[R.indptr[i]:R.indptr[i+1]]
    if rowfam(i)=='Bus-nodal_balance' and rl[i]>0:
        assert rl[i]==ru[i]
        names=tuple(sorted(ci[k][1] for k in ks)); t=ci[ks[0]][2]
        assert all(ci[k][0]=='Link-p' and ci[k][2]==t for k in ks)
        assert all(R.data[p]==1.0 for p in range(R.indptr[i],R.indptr[i+1]))
        groups[names][t]=F(float(rl[i])); members[names]=[n.replace('final-energy meter','fixed resource') for n in names]
print('groups',len(groups))
# --- feasibility inequality per group
res=[]
for g,d in groups.items():
    assert all(v is not None for v in d)
    Dg=24*sum(d); Qg=sum(Q[s] for s in members[g])
    res.append((g,Dg,Qg,Qg-Dg))
print('D<=Q for all groups:',all(r[3]>=0 for r in res),' min slack',float(min(r[3] for r in res)),' max',float(max(r[3] for r in res)))
# compare to Scheme A file
sa=json.load(open('/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/artifacts/SCHEME_A_DAILY_EXACT_GROUPS.json'))
sad={tuple(sorted(a.replace('fixed resource','final-energy meter') for a in x['accounts'])):(F(x['D']),F(x['Q'])) for x in sa['groups']}
match=sum(1 for g,Dg,Qg,_ in res if sad.get(g)==(Dg,Qg)); print('exact match with SCHEME_A_DAILY_EXACT_GROUPS:',match,'/',len(res))
# --- construct greedy rational solution
X={}
for g,d in groups.items():
    acc=members[g]; rem={s:Q[s] for s in acc}
    for t in range(T):
        need=d[t]
        for s in acc:
            take=min(need, rem[s]/24) if need>0 else F(0)
            X[('Store-p',s,t)]=take; X[('Link-p',meter(s),t)]=take
            rem[s]-=24*take; need-=take
            X[('Store-e',s,t)]=rem[s]
        assert need==0, ('infeasible',g,t)
    for s in acc:
        X[('Link-p_nom',meter(s),None)]=max(X[('Link-p',meter(s),t)] for t in range(T))
assert len(X)==S.sum(), (len(X),S.sum())
# --- verify every block row exactly
xj={col[k]:v for k,v in X.items()}
viol=0; worst=F(0)
for i in Srows:
    a=F(0)
    for p in range(R.indptr[i],R.indptr[i+1]): a+=F(float(R.data[p]))*xj[R.indices[p]]
    lo=None if np.isneginf(rl[i]) else F(float(rl[i])); hi=None if np.isposinf(ru[i]) else F(float(ru[i]))
    if (lo is not None and a<lo) or (hi is not None and a>hi): viol+=1
print('block rows verified exactly:',len(Srows),' violations:',viol)
print('objective contribution of block (all c=0):',sum(F(float(c[j]))*v for j,v in xj.items()))
out={'status':'BLOCK_FEASIBLE_EXACT' if viol==0 else 'FAIL','rows':int(len(Srows)),'cols':int(S.sum()),'groups':len(res),'accounts':807,
     'violations':viol,'min_group_slack_MWh_scaled':str(min(r[3] for r in res)),'scheme_A_exact_match':match,'e_upper_equals_initial':all(Eup[s]==Q[s] for s in stores)}
json.dump(out,open('C08_BLOCK_EXACT_FEASIBILITY.json','w'),indent=1); print(out, 'secs',time.time()-t0)

