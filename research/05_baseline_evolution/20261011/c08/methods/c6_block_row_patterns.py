from load import *
from meta import rowfam
import pickle, collections
ci=pickle.load(open('colinfo.pkl','rb'))
Srows=np.load('Srows.npy'); S=np.load('S.npy')
R=A.tocsr()
pat=collections.Counter()
for i in Srows:
    f=rowfam(i); f='ResearchStoreDirection' if f.startswith('ResearchStoreDirection') else f
    ks=R.indices[R.indptr[i]:R.indptr[i+1]]; vs=R.data[R.indptr[i]:R.indptr[i+1]]
    sig=tuple(sorted((ci[k][0],float(v)) for k,v in zip(ks,vs))) if len(ks)<=3 else ('n=%d'%len(ks),tuple(sorted(set(float(v) for v in vs))))
    rhs=('rl=0' if rl[i]==0 else ('rl-inf' if np.isneginf(rl[i]) else 'rl>0' if rl[i]>0 else 'rl<0'), 'ru=0' if ru[i]==0 else ('ru+inf' if np.isposinf(ru[i]) else 'ru>0' if ru[i]>0 else 'ru<0'))
    pat[(f,sig,rhs)]+=1
for k,v in pat.most_common(40): print(v,k)
print('col bounds in S: finite lb',np.isfinite(lb[S]).sum(),' finite ub',np.isfinite(ub[S]).sum())
