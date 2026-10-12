from load import *
import math, json, pickle
S=np.load('S.npy'); Sr=np.zeros(m,bool); Sr[np.load('Srows.npy')]=True
M=~S; Mr=~Sr
Am=A[Mr][:,M].tocsc(); Rm=Am.tocsr()
xm,cm=x[M],c[M]; rlm,rum=rl[Mr],ru[Mr]
z=np.load('main_cert.npz'); yy,rp,bad,L2,U2=z['yy'],z['rp'],z['bad'],z['L2'],z['U2']
cf=np.load('colfam.npy')[M]; names=json.load(open('famnames.json'))
P=math.fsum(cm*xm)+off
print('negative costs in main:',(cm<0).sum(),' cols with c!=0 and L2 not finite',((cm!=0)&~np.isfinite(L2)).sum(), ' L2<0 among costed',((cm>0)&(L2<0)).sum())
# min of each objective term over its singleton box
tmin=np.where(cm>0,cm*np.where(np.isfinite(L2),L2,-np.inf),np.where(cm<0,cm*np.where(np.isfinite(U2),U2,np.inf),0.0))
print('any -inf term mins',np.isneginf(tmin).sum())
base=math.fsum(tmin[np.isfinite(tmin)])
UB=1.01*(P-off)   # generous upper bound on c^T x at optimum (P from near-feasible x; 1% margin)
# cutoff bounds for capacity columns (p_nom / s_nom)
U3=U2.copy()
for nm in ['Line-s_nom','Link-p_nom','Generator-p_nom','Store-e_nom']:
    s=(cf==names.index(nm))&(cm>0)&~np.isfinite(U2)
    U3[s]=L2[s]+(UB-base)/cm[s]
print('cutoff example Line-s_nom U3 range',U3[cf==names.index('Line-s_nom')].min(),U3[cf==names.index('Line-s_nom')].max())
# propagate: dispatch columns bounded by capacity rows of form a*x + b*nom <= / >= 0
U4,L4=U3.copy(),L2.copy()
nnzr=np.diff(Rm.indptr)
two=np.where(nnzr==2)[0]
for i in two:
    ks=Rm.indices[Rm.indptr[i]:Rm.indptr[i+1]]; vs=Rm.data[Rm.indptr[i]:Rm.indptr[i+1]]
    if not (np.isfinite(rlm[i])^np.isfinite(rum[i])): continue
    for (j,a),(k,b) in [((ks[0],vs[0]),(ks[1],vs[1])),((ks[1],vs[1]),(ks[0],vs[0]))]:
        if np.isfinite(U4[j]) and np.isfinite(L4[j]): continue
        # a x_j + b x_k <= ru  or >= rl ; x_k in [L4,U4]
        if np.isfinite(rum[i]):
            # a x_j <= ru - b x_k  -> use min of b x_k
            mb=min(b*L4[k],b*U4[k]) if np.isfinite(L4[k]) and np.isfinite(U4[k]) else (b*L4[k] if b>0 and np.isfinite(L4[k]) else (b*U4[k] if b<0 and np.isfinite(U4[k]) else -np.inf))
            if np.isfinite(mb):
                bnd=(rum[i]-mb)/a
                if a>0: U4[j]=min(U4[j],bnd)
                else: L4[j]=max(L4[j],bnd)
        else:
            Mb=max(b*L4[k],b*U4[k]) if np.isfinite(L4[k]) and np.isfinite(U4[k]) else (b*U4[k] if b>0 and np.isfinite(U4[k]) else (b*L4[k] if b<0 and np.isfinite(L4[k]) else np.inf))
            if np.isfinite(Mb):
                bnd=(rlm[i]-Mb)/a
                if a>0: L4[j]=max(L4[j],bnd)
                else: U4[j]=min(U4[j],bnd)
nb=bad&~((rp>0)&np.isfinite(L4)|(rp<0)&np.isfinite(U4))
print('bad cols still unbounded after cutoff+propagation',nb.sum())
gl,gu=np.isfinite(rlm),np.isfinite(rum)
rowterm=np.where(yy>0,yy*np.where(gl,rlm,0),np.where(yy<0,yy*np.where(gu,rum,0),0))
colterm=np.where(rp>0,rp*np.where(np.isfinite(L4),L4,-np.inf),np.where(rp<0,rp*np.where(np.isfinite(U4),U4,np.inf),0.0))
# rounding safety: add -noise*max(|L4|,|U4|) per column
noise=np.finfo(float).eps*(np.abs(cm)+abs(Am).T@np.abs(yy))*np.maximum(np.diff(Am.indptr),1)*4
bigb=np.maximum(np.abs(np.where(np.isfinite(L4),L4,0)),np.abs(np.where(np.isfinite(U4),U4,0)))
safety=math.fsum(noise*bigb)
print('-inf colterms',np.isneginf(colterm).sum())
if not np.isneginf(colterm).any():
    D=math.fsum(rowterm)+math.fsum(colterm)+off-safety
    print('RIGOROUS-ish lower bound D',D,' P',P,' gap',P-D,' rel',(P-D)/P,' safety term',safety)
    badc=bad
    print(' contribution of formerly-bad cols',math.fsum(colterm[badc]))
