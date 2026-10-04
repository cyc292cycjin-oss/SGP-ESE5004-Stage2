"""Auditable mass-basis petroleum/biofuel reconciliation, never missing=zero."""
from decimal import Decimal as D

def reconcile(parent,bio,memo):
    if memo is None:raise ValueError('NO_MATCHING_TRANSACTION_RETURNED: blend memo required')
    for field in ('Country','Year','Transaction','Unit','Vintage'):
        if len({str(r.get(field)) for r in (parent,bio,memo)})!=1 or parent.get(field) is None:
            raise ValueError('VERSION_OR_SCOPE_CONFLICT: '+field)
    allowed={('MO','AL','ZG'),('DL','BD','ZD')}
    if tuple(r['CommodityCode'] for r in (parent,bio,memo)) not in allowed:
        raise ValueError('Wrong commodity inclusion relation')
    if memo.get('InclusionVerified') is not True:raise ValueError('Unverified memo inclusion')
    if parent['Unit']!='Metric tons,  thousand':raise ValueError('Unqualified mass/volume reconciliation basis')
    p,b,m=(D(str(r['Quantity'])) for r in (parent,bio,memo))
    if any(not x.is_finite() or x<0 for x in (p,b,m)) or m>p or m>b:
        raise ValueError('Invalid parent/bio/memo quantities')
    for r in (parent,bio,memo):
        if not r.get('SourceRow'):raise ValueError('Missing original row identity')
    return dict(FossilMass=str(p-m),BioTotalMass=str(b),BlendedBioMass=str(m),
                ParentRawMass=str(p),RawUnit=parent['Unit'],
                Rule='(parent mass - compatible blended memo mass) * petroleum NCV; bio total mass * its own NCV; memo not separately posted',
                SourceRows=[r['SourceRow'] for r in (parent,bio,memo)])
