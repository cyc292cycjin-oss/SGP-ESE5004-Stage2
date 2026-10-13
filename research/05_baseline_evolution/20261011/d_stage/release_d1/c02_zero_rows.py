"""Exactly three schema-proven infinite nominal-upper masks, no general waiver."""
from pathlib import Path
import numpy as np
from c02_common import sha
APPROVED={
 'Line-ext-s_nom-upper':('Line','s_nom','lines','fba19b98d375eaada3867a87cfa1a41d4150ef8467f46d0206413f9add11b265',105),
 'Link-ext-p_nom-upper':('Link','p_nom','links','cccac4202846ad96dcb2fbab1b387cc8f144fbaf8d8e3bbbe060cfda493ca847',3263),
 'Store-ext-e_nom-upper':('Store','e_nom','stores','65d5bf433bdfd8424c76d649641cc7fd49984914d1474b12426ba34aeb1fcd6c',297),
}
def certify_values(family,values,labels,signs,default,schema_sha,ids,expected_ids):
    if family not in APPROVED:raise ValueError('UNAUTHORIZED_ZERO_ROW_FAMILY:'+family)
    _,_,_,expected,count=APPROVED[family]
    a=np.asarray(values);l=np.asarray(labels);s=np.asarray(signs)
    if schema_sha!=expected or not np.isposinf(default):raise ValueError('SCHEMA_IDENTITY_OR_DEFAULT')
    if len(a)!=count or a.shape!=l.shape or a.shape!=s.shape:raise ValueError('ZERO_ROW_SHAPE')
    if list(ids)!=list(expected_ids) or len(set(ids))!=count:raise ValueError('ASSET_MASK_IDENTITY')
    if not np.isposinf(a).all():raise ValueError('FINITE_OR_NAN_BOUND_REQUIRES_ROW')
    if not np.all(l==-1) or not np.all(s=='<='):raise ValueError('UNEXPECTED_LABEL_MASK_OR_DIRECTION')
    return {'family':family,'status':'EXPLICIT_INFINITE_NOMINAL_UPPER_ZERO_ROWS','assets':count,'finite_upper_bounds':0,'active_labels':0,'schema_sha256':schema_sha,'asset_ids':list(ids),'default':'+Inf'}
def certify_network(n,family):
    import pypsa
    comp,nom,file,expected,count=APPROVED[family]
    ids=n.get_extendable_i(comp);b=n.model.constraints[family];dim=comp+'-ext'
    source=Path(pypsa.__file__).parent/'component_attrs'/(file+'.csv')
    rec=certify_values(family,n.df(comp).loc[ids,nom+'_max'].to_numpy(),b.labels.values,b.sign.broadcast_like(b.labels).values,
        n.component_attrs[comp].at[nom+'_max','default'],sha(source),b.labels.get_index(dim),ids)
    # The finite operating/energy inequalities are independent and remain mandatory.
    required={'Line':['Line-ext-s-upper','Line-ext-s-lower'], 'Link':['Link-ext-p-upper','Link-ext-p-lower'], 'Store':['Store-ext-e-upper','Store-ext-e-lower','Store-fix-e-lower','Store-fix-e-upper']}[comp]
    for name in required:
        if name not in n.model.constraints or not np.any(n.model.constraints[name].labels.values>=0):raise ValueError('OPERATING_BOUND_MISSING:'+name)
    rec['operating_families_present']=required;return rec
