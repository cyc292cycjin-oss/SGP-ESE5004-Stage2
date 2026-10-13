"""C10: conditional rigorous lower bound for the C09 daily LP (read-only, no solver).
Assumption H: optimal objective <= U = P_hat + delta (delta = DELTA_REL*|P_hat|).
Under H: every optimal x satisfies c^T x + offset <= U, used as a cutoff row in bound propagation.
All bound/propagation/sum steps are rounded OUTWARD (loosened) with explicit safety margins.
Block (884,472 cols / 2,203,217 rows): zero cost, exactly feasible (C08 certificate) -> contributes exactly 0."""
import sys, json, math, time, numpy as np, scipy.sparse as sp
sys.path.insert(0, sys.argv[1] if len(sys.argv)>1 else '.')
from load import A, rl, ru, c, lb, ub, off, n, m
DELTA_REL=float(sys.argv[2]) if len(sys.argv)>2 else 1e-3
EPS=np.finfo(float).eps
t0=time.time()
B='/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/c09_daily_diagnostic/c09_daily122_20261012T185116Z_b867e3d3/cloud_run/merged_for_V4/vectors/'
x,y=np.load(B+'X.npy'),np.load(B+'Pi.npy')
S=np.load('S.npy'); Sr=np.zeros(m,bool); Sr[np.load('Srows.npy')]=True
M=~S; Mr=~Sr
Am=A[Mr][:,M].tocsc(); xm,ym,cm=x[M],y[Mr],c[M]; rlm,rum=rl[Mr].copy(),ru[Mr].copy(); L=lb[M].copy(); U=ub[M].copy()
P=math.fsum(cm*xm)+off
Ucut=P+DELTA_REL*abs(P)
# cutoff row: c^T x <= Ucut - off   (valid for optimal x under H)
# plus an EXACT per-store telescoped aggregate of it (removes free Store-p columns):
#   sum_t c_s p_t = (c_s/24)(e_init - e_T) >= (c_s/24)(e_init - e_max)   [lossless rows e_{t-1}-e_t-24p_t=0 verified]
#   cyclic store: sum_t p_t = 0 exactly -> contribution 0
import pickle
from meta import rowfam
ci=pickle.load(open('colinfo.pkl','rb')); midx=np.where(M)[0]; pos={j:k for k,j in enumerate(midx)}
Rf=A.tocsr(); g=cm.copy(); rhs_adj=0.0; store_log=[]
stores={}
for k,j in enumerate(midx):
    v,nm,t=ci[j]
    if v in ('Store-p','Store-e'): stores.setdefault(nm,{})[(v,t)]=k
    if v=='Store-e_nom': stores.setdefault(nm,{})[('e_nom',None)]=k
for nm,d in stores.items():
    T=max(t for (v,t) in d if v=='Store-p')
    cs=float(cm[d[('Store-p',0)]]); assert all(cm[d[('Store-p',t)]]==cs for t in range(T+1))
    for t in range(T+1): g[d[('Store-p',t)]]=0.0
    if cs==0: continue
    e0=midx[d[('Store-e',0)]]; eT=midx[d[('Store-e',T)]]
    # t=0 energy row of this store
    r0=[i for i in A.indices[A.indptr[e0]:A.indptr[e0+1]] if rowfam(i)=='Store-energy_balance' and midx[d[('Store-p',0)]] in Rf.indices[Rf.indptr[i]:Rf.indptr[i+1]]]
    assert len(r0)==1; i0=r0[0]; ks=set(Rf.indices[Rf.indptr[i0]:Rf.indptr[i0+1]])
    if eT in ks: store_log.append((nm,'cyclic',cs)); continue      # exact zero
    assert len(ks)==2 and rl[i0]==ru[i0]; einit=-float(rl[i0])     # -e0 -24p0 = -e_init
    if ('e_nom',None) in d:   # e_T <= e_nom (ext): -(cs/24) e_T >= -(cs/24) e_nom
        g[d[('e_nom',None)]]-=cs/24.0; rhs_adj+=cs/24.0*einit; store_log.append((nm,'ext',cs))
    else:
        emax=float(U[d[('Store-e',T)]]) if np.isfinite(U[d[('Store-e',T)]]) else None
        if emax is None:  # fixed store: singleton upper on e_T
            ups=[ru[i] for i in A.indices[A.indptr[eT]:A.indptr[eT+1]] if rowfam(i)=='Store-fix-e-upper']; emax=float(ups[0])
        rhs_adj+=cs/24.0*(einit-emax); store_log.append((nm,'fixed',cs))
agg_rhs=(Ucut-off)-rhs_adj
agg_rhs=agg_rhs+1e-9*abs(agg_rhs)   # outward (loosen)
Aext=sp.vstack([Am.tocsr(),sp.csr_matrix(cm.reshape(1,-1)),sp.csr_matrix(g.reshape(1,-1))]).tocsr()
rlx=np.append(rlm,[-np.inf,-np.inf]); rux=np.append(rum,[Ucut-off,agg_rhs])
print('stores aggregated:',dict(__import__('collections').Counter(s[1] for s in store_log)),flush=True)
R=Aext; nr=R.shape[0]
rows=np.repeat(np.arange(nr),np.diff(R.indptr)); cols=R.indices; a=R.data
def outward_lo(v,scale): return v-(1e-9*np.abs(v)+1e-9*scale+1e-300)
def outward_hi(v,scale): return v+(1e-9*np.abs(v)+1e-9*scale+1e-300)
hist=[]
for it in range(40):
    lo_c=np.where(a>0,a*L[cols],a*U[cols]); hi_c=np.where(a>0,a*U[cols],a*L[cols])
    lo_inf=~np.isfinite(lo_c); hi_inf=~np.isfinite(hi_c)
    lo_f=np.where(lo_inf,0,lo_c); hi_f=np.where(hi_inf,0,hi_c)
    rmin=np.bincount(rows,lo_f,nr); rmax=np.bincount(rows,hi_f,nr)
    nlo=np.bincount(rows,lo_inf,nr); nhi=np.bincount(rows,hi_inf,nr)
    rabs=np.bincount(rows,np.abs(lo_f)+np.abs(hi_f),nr)
    # others' min/max for each entry
    o_min=np.where(lo_inf, np.where(nlo[rows]==1, rmin[rows], np.nan), np.where(nlo[rows]==0, rmin[rows]-lo_f, np.nan))
    o_max=np.where(hi_inf, np.where(nhi[rows]==1, rmax[rows], np.nan), np.where(nhi[rows]==0, rmax[rows]-hi_f, np.nan))
    sc=rabs[rows]/np.abs(a)
    newU=np.full(len(a),np.inf); newL=np.full(len(a),-np.inf)
    # upper row: a x <= ru - o_min
    ok=np.isfinite(rux[rows])&np.isfinite(o_min)
    v=(rux[rows]-o_min)/a
    pos=ok&(a>0); neg=ok&(a<0)
    newU[pos]=outward_hi(v[pos],sc[pos]); newL[neg]=outward_lo(v[neg],sc[neg])
    # lower row: a x >= rl - o_max
    ok2=np.isfinite(rlx[rows])&np.isfinite(o_max)
    v2=(rlx[rows]-o_max)/a
    pos2=ok2&(a>0); neg2=ok2&(a<0)
    newL[pos2]=np.maximum(newL[pos2],outward_lo(v2[pos2],sc[pos2])); newU[neg2]=np.minimum(newU[neg2],outward_hi(v2[neg2],sc[neg2]))
    Unew=U.copy(); Lnew=L.copy()
    np.minimum.at(Unew,cols,newU); np.maximum.at(Lnew,cols,newL)
    # never cross: keep consistency (crossing would indicate infeasibility under H; record)
    cross=(Lnew>Unew+1e-6*(1+np.abs(Unew)))
    impU=np.sum(Unew<U*(1-1e-6)-1e-9); impL=np.sum(Lnew>L*(1+1e-6)+1e-9)
    nfinU=np.isfinite(Unew).sum(); nfinL=np.isfinite(Lnew).sum()
    U,L=Unew,Lnew
    hist.append({'it':it,'finite_U':int(nfinU),'finite_L':int(nfinL),'improved':int(impU+impL),'crossings':int(cross.sum())})
    print(hist[-1],flush=True)
    if impU+impL==0: break
# safe dual bound on main LP
gl,gu=np.isfinite(rlm),np.isfinite(rum)
yy=ym.copy(); wrong=((yy>0)&~gl)|((yy<0)&~gu); yy[wrong]=0.0
r=cm-Am.T@yy
err=4*EPS*(np.abs(cm)+abs(Am).T@np.abs(yy))*(np.diff(Am.indptr)+2)
rlo,rhi=r-err,r+err
def minprod(r1,r2,l,u):
    c1=np.where(np.isfinite(l),r1*l,np.where(r1>0,-np.inf,np.where(r1<0,np.inf,0)))
    c2=np.where(np.isfinite(u),r1*u,np.where(r1>0,np.inf,np.where(r1<0,-np.inf,0)))
    c3=np.where(np.isfinite(l),r2*l,np.where(r2>0,-np.inf,np.where(r2<0,np.inf,0)))
    c4=np.where(np.isfinite(u),r2*u,np.where(r2>0,np.inf,np.where(r2<0,-np.inf,0)))
    return np.minimum(np.minimum(c1,c2),np.minimum(c3,c4))
with np.errstate(invalid='ignore'):
    colterm=minprod(rlo,rhi,L,U)
colterm=np.where(np.isnan(colterm),0.0,colterm)
rowterm=np.where(yy>0,yy*np.where(gl,rlm,0),np.where(yy<0,yy*np.where(gu,rum,0),0.0))
bad=np.isneginf(colterm)
cf=np.load('colfam.npy')[M]; names=json.load(open('famnames.json'))
import collections
res={'store_aggregation':dict(__import__('collections').Counter(s[1] for s in store_log)),'assumption_H':f'optimal objective <= U = P_hat*(1+{DELTA_REL})','P_hat_EUR':P,'U_EUR':Ucut,'propagation_history':hist,
     'wrong_sign_duals_zeroed':int(wrong.sum()),'columns_with_minus_inf_contribution':int(bad.sum()),
     'bad_by_family':dict(collections.Counter(names[k] for k in cf[bad]))}
if not bad.any():
    terms=np.concatenate([colterm,rowterm])
    safety=EPS*4*math.fsum(np.abs(terms))+EPS*abs(off)
    Lb=math.fsum(terms)+off-safety
    res.update({'rigorous_lower_bound_EUR':Lb,'gap_EUR':P-Lb,'relative_gap':(P-Lb)/abs(P),'summation_safety_EUR':safety,
                'colterm_sum':math.fsum(colterm),'rowterm_sum':math.fsum(rowterm),
                'largest_negative_colterms':[{'family':names[cf[j]],'r_interval':[float(rlo[j]),float(rhi[j])],'L':float(L[j]),'U':float(U[j]),'term':float(colterm[j]-(r[j]*xm[j]))} for j in np.argsort(colterm-r*xm)[:5]]})
res['seconds']=time.time()-t0
print(json.dumps({k:v for k,v in res.items() if k!='propagation_history'},indent=1,default=float))
json.dump(res,open(f'c10/C10_BOUND_delta{DELTA_REL:g}.json','w'),indent=1,default=float)
np.savez_compressed(f'c10/c10_bounds_delta{DELTA_REL:g}.npz',L=L,U=U)
