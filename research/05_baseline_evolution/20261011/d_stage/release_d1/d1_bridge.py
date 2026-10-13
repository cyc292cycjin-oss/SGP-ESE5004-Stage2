"""Lossless storage conversion of certified D-1 2920 CSR chunks to legacy native CSC (derived from daily_bridge.py)."""
from pathlib import Path
import gc,os
import numpy as np
from scipy.sparse import csr_matrix,csc_matrix
from c02_common import read,write,sha
from adapter import validate

def bridge(source,dest,progress=lambda s:None):
    source=Path(source);dest=Path(dest);dest.mkdir(exist_ok=False)
    m=read(source/'lp/MATH_PROBLEM.json');labels=source/'mapping/LABELS.json'
    assert m['version']=='D1_2920_CHUNKED_CSR_LP' and m['status']=='EXACT_NUMPY_EXPORT_READBACK_PASS' and m['sense']=='min'
    assert sha(labels)==m['label_manifest_sha256']
    n,r,nz=m['columns'],m['rows'],m['nnz'];assert max(n,r,nz)<2_000_000_000
    maps=dest/'mapping';maps.mkdir();mathdir=dest/'math_problem';mathdir.mkdir()
    def save(folder,key,a):
        p=folder/(key+'.npy');np.save(p,a,allow_pickle=False)
        with p.open('rb') as f:os.fsync(f.fileno())
        back=np.load(p,mmap_mode='r',allow_pickle=False)
        assert np.array_equal(back,a) and back.dtype==a.dtype
        return {'file':p.name,'count':len(a),'dtype':a.dtype.str,'bytes':p.stat().st_size,'sha256':sha(p)}
    def arr(chunk,key):
        p=source/'lp'/chunk['dir']/(key+'.npy')
        assert sha(p)==chunk['arrays'][key]['sha256'],str(p)
        return np.load(p,mmap_mode='r',allow_pickle=False)
    ptr=np.lib.format.open_memmap(dest/'csr_indptr.npy',mode='w+',dtype='<i8',shape=(r+1,));ptr[0]=0
    ix=np.lib.format.open_memmap(dest/'csr_indices.npy',mode='w+',dtype='<i4',shape=(nz,))
    val=np.lib.format.open_memmap(dest/'csr_value.npy',mode='w+',dtype='<f8',shape=(nz,))
    vec={k:np.empty(r,dtype='<i8' if k=='clabels' else '<f8') for k in ['clabels','R','row_lower','row_upper']}
    rs=ns=0; row_ranges=[]
    for chunk in m['chunks']:
        a={k:arr(chunk,k) for k in ['clabels','R','indptr','indices','value_scaled','row_lower_scaled','row_upper_scaled']}
        nr,nn=chunk['rows'],chunk['nnz'];assert a['indptr'][0]==0 and a['indptr'][-1]==nn and len(a['clabels'])==nr
        assert np.all(np.diff(a['indptr'])>0) and len(a['indices'])==len(a['value_scaled'])==nn
        ptr[rs+1:rs+nr+1]=a['indptr'][1:]+ns;ix[ns:ns+nn]=a['indices'];val[ns:ns+nn]=a['value_scaled']
        for key in vec:vec[key][rs:rs+nr]=a[key+'_scaled'] if key.startswith('row_') else a[key]
        row_ranges.append({'start':rs,'end':rs+nr,'family':chunk['family'],'source_chunk':chunk['dir']});rs+=nr;ns+=nn
        progress('BRIDGE_COPY')
    assert rs==r and ns==nz and len(np.unique(vec['clabels']))==r
    ptr.flush();ix.flush();val.flush()
    csr=csr_matrix((val,ix,ptr),shape=(r,n),copy=False);assert csr.has_canonical_format
    csc=csr.tocsc();assert csc.has_canonical_format and csc.nnz==nz
    # Independent reverse sparse permutation proves each source row, including order.
    back=csc.tocsr();assert np.array_equal(back.indptr,ptr) and np.array_equal(back.indices,ix) and np.array_equal(back.data,val)
    del back;gc.collect()
    files={k:save(mathdir,k,a) for k,a in [('start',csc.indptr),('index',csc.indices),('value',csc.data),('row_lower',vec['row_lower']),('row_upper',vec['row_upper'])]}
    mapping={k:save(maps,k,vec[k]) for k in ('R','clabels')}
    for target,key in [('cost','cost_V3_scaled'),('col_lower','col_lower_scaled'),('col_upper','col_upper_scaled'),('cost_scientific','cost_scientific_scaled')]:
        p=source/'lp'/m['arrays'][key]['file'];assert sha(p)==m['arrays'][key]['sha256']
        files[target]=save(mathdir,target,np.load(p,mmap_mode='r',allow_pickle=False))
    for key in ('D','vlabels'):
        p=source/'lp'/m['arrays'][key]['file'];assert sha(p)==m['arrays'][key]['sha256']
        mapping[key]=save(maps,key,np.load(p,mmap_mode='r',allow_pickle=False))
    meta={'num_col':n,'num_row':r,'nnz':nz,'sense':1,'offset':m['V3_offset'],'scientific_offset':m['scientific_offset'],'arrays':files,'source_manifest_sha256':sha(source/'lp/MATH_PROBLEM.json'),'network_sha256':m['network_sha256'],'label_manifest_sha256':sha(labels),'row_order':'source chunks in manifest order','same_scientific_problem_as_2920_CSR':True,'snapshots':m['snapshots']}
    write(mathdir/'MATH_PROBLEM.json',meta)
    write(maps/'MAPPING_MANIFEST.json',{'arrays':mapping,'source_labels_path':str(labels),'source_labels_sha256':sha(labels),'row_ranges':row_ranges,'snapshots':m['snapshots'],'labels_from_actual_build':True})
    from adapter import open_problem
    mm,aa=open_problem(mathdir);check=validate(mm,aa)
    rec={'status':'EXACT_CSR_CSC_REVERSE_PERMUTATION_PASS','source_manifest_sha256':meta['source_manifest_sha256'],'native_manifest_sha256':sha(mathdir/'MATH_PROBLEM.json'),'mapping_manifest_sha256':sha(maps/'MAPPING_MANIFEST.json'),'row_order_checked':True,'all_values_bounds_objective_preserved':True,'cost_binding':'cost_V3_scaled','V3_offset':meta['offset'],'scientific_offset':meta['scientific_offset'],'dimensions':check,'native_model_created':False}
    write(dest/'BRIDGE_RECEIPT.json',rec);return rec
