from contextlib import contextmanager
import gc,ctypes

def install_existing_asset_constraints(n):
    """Future hook after model/objective creation; never calls a solver."""
    if getattr(n,'_research_existing_assets_model',None) is n.model:raise ValueError('Existing cost/resource hook already installed')
    for key,g in n.meta.get('existing_resource_groups',{}).items():
        terms=[n.model[c['ComponentType']+'-p_nom'].sel({c['ComponentType']+'-ext':c['Name']})*c['CapacityToMW'] for c in g['candidates']]
        if terms:n.model.add_constraints(sum(terms)<=g['new_build_limit_mw'],name='ResearchExistingResource-'+key)
    # This frozen Linopy version rejects literal objective constants. A scalar
    # fixed at one carries the audited annual FOM without introducing capacity,
    # dispatch, a financing assumption or an optimisation choice.
    cost=float(n.meta.get('existing_annual_fixed_om_eur',0.))
    if cost:
        one=n.model.add_variables(lower=1.,upper=1.,name='Research-existing-FOM-constant')
        n.model.objective+=one*cost
    n._research_existing_assets_model=n.model

@contextmanager
def bounded_build_allocator():
    """Return completed construction temporaries at existing block boundaries.

    The frozen methods, arguments, order, stored datasets and labels are used
    verbatim. This only collects unreachable objects and trims free libc pages.
    """
    import linopy
    from unittest.mock import patch
    count = [0]
    def wrap(original):
        def call(*args, **kwargs):
            result = original(*args, **kwargs)
            count[0] += 1
            if count[0] % 16 == 0:
                gc.collect()
            try:
                ctypes.CDLL(None).malloc_trim(0)
            except (AttributeError, OSError):
                pass
            return result
        return call
    with patch.object(linopy.Model, 'add_variables', wrap(linopy.Model.add_variables)), \
         patch.object(linopy.Model, 'add_constraints', wrap(linopy.Model.add_constraints)):
        yield
