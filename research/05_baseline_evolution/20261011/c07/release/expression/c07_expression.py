"""Independent numerical-expression adapter. No optimizer, environment or launch.

Input arrays and old science stay read-only. Canonicalization is a derived copy
AFTER raw persistence; it is not a correction of any scientific solution.
"""
from pathlib import Path
import numpy as np
import json,hashlib,os,time

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()

def checked_ldexp(a,k):
 v=np.asarray(a);out=np.ldexp(v,k)
 if np.any(np.isfinite(v)&~np.isfinite(out)):raise ValueError('numerical expression overflow')
 back=np.ldexp(out,-np.asarray(k))
 if not np.array_equal(back.view('u8'),v.view('u8')):raise ValueError('non-reversible binary64 expression')
 return out

class PowerView:
 """Bounded slices only; prevent accidental materialization of a full new CSC."""
 def __init__(self,source,exponent):
  self.source=source;self.exponent=exponent;self.shape=source.shape
  self.size=source.size;self.dtype=np.dtype('<f8');self.nbytes=source.nbytes;self.ndim=1
 def __len__(self):return self.size
 def __getitem__(self,key):return checked_ldexp(self.source[key],self.exponent(key))
 def __array__(self,*args,**kwargs):raise TypeError('full expression allocation prohibited; slice in bounded chunks')

def overlay(meta,a,D_old,R_old,d_new,r_new,alpha_exp=0):
 if alpha_exp!=0:raise ValueError('only the frozen alpha=1 proposal is enabled')
 de=np.rint(np.log2(D_old)).astype(np.int16);re=np.rint(np.log2(R_old)).astype(np.int16)
 if not np.array_equal(np.exp2(de.astype(float)),D_old) or not np.array_equal(np.exp2(re.astype(float)),R_old):raise ValueError('old scales are not exact positive powers of two')
 if d_new.shape!=de.shape or r_new.shape!=re.shape or d_new.dtype!=np.int16 or r_new.dtype!=np.int16:raise ValueError('exponent identity/shape')
 dc=d_new-de;rr=r_new-re
 def matrix_exp(key):
  if not isinstance(key,slice) or key.step not in (None,1):raise TypeError('contiguous CSC slices only')
  s,e,_=key.indices(len(a['value']));j=np.searchsorted(a['start'],np.arange(s,e,dtype=np.int64),side='right')-1
  return rr[a['index'][s:e]]+dc[j]
 out=dict(a)
 out['value']=PowerView(a['value'],matrix_exp)
 out['cost']=PowerView(a['cost'],lambda key:dc[key])
 for key in ('col_lower','col_upper'):out[key]=PowerView(a[key],lambda key:-dc[key])
 for key in ('row_lower','row_upper'):out[key]=PowerView(a[key],lambda key:rr[key])
 return dict(meta),out,{'delta_D_exponent':dc,'delta_R_exponent':rr}

def canonicalize_saved_raw(raw,destination,delta_D,delta_R,expression_sha,deadline_epoch,stop_check=lambda:False):
 """Preserve native raw; derive old solver coordinates for unchanged V4 code."""
 raw=Path(raw);dest=Path(destination)
 if not (raw/'RAW_DURABLE.json').is_file():raise ValueError('raw persistence must precede mapping')
 native=json.loads((raw/'vectors/RAW_RECEIPT.json').read_text())
 if any(native.get('vectors',{}).get(k,{}).get('status')!='SAVED_UNQUALIFIED' for k in ('X','Pi','RC')):raise ValueError('raw vectors incomplete; keep real NOT_AVAILABLE status')
 if dest.exists() or dest.resolve()==raw.resolve():raise ValueError('new independent canonical directory required')
 dest.mkdir(parents=True);(dest/'vectors').mkdir()
 receipt={'qualification':'DERIVED_UNQUALIFIED_NOT_NATIVE_OUTPUT','native_status':native['native_status'],'vectors':{},
   'native_info':{},'basis':'NOT_REQUESTED','source_native_receipt':str(raw/'vectors/RAW_RECEIPT.json'),
   'source_native_receipt_sha256':sha(raw/'vectors/RAW_RECEIPT.json'),'expression_sha256':expression_sha,
   'quality_attributes':'native values belong to candidate input space; see source receipt, never relabel as canonical'}
 def check():
  if time.time()>=deadline_epoch or stop_check():raise TimeoutError('canonical mapping stopped at fixed postprocess deadline')
 def put():
  p=dest/'vectors/RAW_RECEIPT.json';p.write_text(json.dumps(receipt,indent=2)+'\n')
 for k,shift in [('X',delta_D),('Pi',delta_R),('RC',-delta_D)]:
  check();source=raw/'vectors'/(k+'.npy');info=native['vectors'][k]
  if sha(source)!=info['sha256']:raise ValueError('raw source SHA mismatch')
  v=np.load(source,mmap_mode='r',allow_pickle=False)
  if v.shape!=shift.shape or v.dtype!=np.float64:raise ValueError('raw vector shape/dtype')
  p=dest/'vectors'/(k+'.partial.npy');out=np.lib.format.open_memmap(p,mode='w+',dtype='<f8',shape=v.shape)
  for s in range(0,len(v),200000):
   check();e=min(len(v),s+200000);out[s:e]=checked_ldexp(v[s:e],shift[s:e])
  out.flush();del out
  with open(p,'r+b') as f:os.fsync(f.fileno())
  final=p.with_name(k+'.npy');p.rename(final)
  receipt['vectors'][k]={'status':'SAVED_UNQUALIFIED','sha256':sha(final),'count':len(v),'derivation':'canonical old solver coordinates, not a new solver result'};put()
  v._mmap.close();del v
 put()
 return receipt

