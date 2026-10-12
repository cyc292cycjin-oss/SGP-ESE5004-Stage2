from load import *
import math, json
S=np.load('S.npy'); Sr=np.zeros(m,bool); Sr[np.load('Srows.npy')]=True
M=~S; Mr=~Sr
Am=A[Mr][:,M].tocsc(); Rm=Am.tocsr()
xm,ym,cm=x[M],y[Mr],c[M]; rlm,rum,lbm,ubm=rl[Mr],ru[Mr],lb[M],ub[M]
print('main LP',Am.shape,Am.nnz)
ax=Am@xm; v=np.maximum(rlm-ax,0)+np.maximum(ax-rum,0); v[np.isnan(v)]=0
print('main primal max row viol (canonical)',v.max(),' n>1e-9',(v>1e-9).sum())
P=math.fsum(cm*xm)+off; print('P main (=full)',P, ' block cost contribution',math.fsum(c[S]*x[S]))
nnzr=np.diff(Rm.indptr); sing=nnzr==1
si=np.where(sing)[0]; sj=Rm.indices[Rm.indptr[si]]; sa=Rm.data[Rm.indptr[si]]
lo=np.where(sa>0,rlm[si]/sa,rum[si]/sa); hi=np.where(sa>0,rum[si]/sa,rlm[si]/sa)
L2=lbm.copy();U2=ubm.copy(); np.maximum.at(L2,sj,lo); np.minimum.at(U2,sj,hi)
finL,finU=np.isfinite(L2),np.isfinite(U2)
gl,gu=np.isfinite(rlm),np.isfinite(rum)
yy=ym.copy(); yy[sing]=0; yy[((yy>0)&~gl)|((yy<0)&~gu)]=0
rp=cm-Am.T@yy
def badm(rp): return ((rp>0)&~finL)|((rp<0)&~finU)
print('bad cols before repair',badm(rp).sum())
for it in range(3):
    bad=np.where(badm(rp))[0]; fixed=0
    for j in bad:
        rho=rp[j]
        for p in range(Am.indptr[j],Am.indptr[j+1]):
            i=Am.indices[p]; a=Am.data[p]
            if sing[i]: continue
            d=rho/a; yn=yy[i]+d
            if (yn>0 and not gl[i]) or (yn<0 and not gu[i]): continue
            ks=Rm.indices[Rm.indptr[i]:Rm.indptr[i+1]]; as_=Rm.data[Rm.indptr[i]:Rm.indptr[i+1]]
            ok=True
            for k,ak in zip(ks,as_):
                if k==j: continue
                nr=rp[k]-ak*d
                if (nr>0 and not finL[k]) or (nr<0 and not finU[k]): ok=False;break
            if not ok: continue
            yy[i]=yn
            for k,ak in zip(ks,as_): rp[k]-=ak*d
            rp[j]=0.0; fixed+=1; break
    print('iter',it,'bad',len(bad),'fixed',fixed)
rp=cm-Am.T@yy
bad=badm(rp)
noise=np.finfo(float).eps*(np.abs(cm)+abs(Am).T@np.abs(yy))*np.maximum(np.diff(Am.indptr),1)
print('after exact recompute: bad',bad.sum(),' of which above 10x noise',(bad&(np.abs(rp)>10*noise)).sum(),' sum|rp| bad',np.abs(rp[bad]).sum(),' max',np.abs(rp[bad]).max() if bad.any() else 0)
print(' max noise on bad',noise[bad].max() if bad.any() else 0)
rowterm=np.where(yy>0,yy*np.where(gl,rlm,0),np.where(yy<0,yy*np.where(gu,rum,0),0))
okc=~bad
colterm=np.where(okc&(rp>0),rp*np.where(finL,L2,0),np.where(okc&(rp<0),rp*np.where(finU,U2,0),0))
D=math.fsum(rowterm)+math.fsum(colterm)+off
print('D finite part',D,' gap',P-D,' rel',(P-D)/P)
print('bad cols |x| max',np.abs(xm[bad]).max() if bad.any() else 0, ' sum |rp*x| on bad',math.fsum(np.abs(rp[bad]*xm[bad])))
cf=np.load('colfam.npy')[M]; names=json.load(open('famnames.json'))
import collections; print(collections.Counter(names[k] for k in cf[bad&(np.abs(rp)>10*noise)]))
np.savez('main_cert.npz',yy=yy,rp=rp,bad=bad,L2=L2,U2=U2)
