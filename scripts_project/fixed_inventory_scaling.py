"""Reversible power-of-two scale map for qualified fixed inventory groups only."""
import hashlib,json,math
import numpy as np
from precision_handoff import exact,digest
from fixed_accounts import validate_exported_accounting

class FixedInventoryScaling:
    def __init__(self,n,audit):
        validate_exported_accounting(n)
        self.audit=audit;self.groups=audit['groups'];m=n.model
        self.label_group=np.full(m.shape[1],-1,dtype=np.int32)
        self.group_scales=np.array([g['scale'] for g in self.groups],dtype=float)
        for g in self.groups:
            stores=g['stores'];resource_buses=n.stores.loc[stores,'bus']
            links=n.links.index[n.links.bus0.isin(resource_buses)]
            if len(links)!=len(stores):raise ValueError('Fixed-group meter identity changed')
            for kind,names in [('Store',stores),('Link',links)]:
                d=n.df(kind).loc[names]
                if d.capital_cost.ne(0).any() or d.marginal_cost.ne(0).any():raise ValueError('Scaled fixed group has an optimizing economic coefficient')
            labels=[]
            for var,dim,ids in [('Store-e','Store',stores),('Store-p','Store',stores),('Link-p','Link',links),('Link-p_nom','Link-ext',links)]:
                labels.extend(m[var].labels.sel({dim:ids}).values.ravel())
            labels=np.asarray(labels,dtype=int)
            if (labels<0).any() or (self.label_group[labels]!=-1).any():raise ValueError('Missing/duplicate fixed variable ownership')
            self.label_group[labels]=g['group']
        self.row_factors=[];self.scaled_rows=0;self.mapped_rows=0

    def columns(self,vl,lower,upper,cost):
        self.vgroups=self.label_group[vl]
        self.d=np.ones(len(vl));mask=self.vgroups>=0;self.d[mask]=self.group_scales[self.vgroups[mask]]
        if np.any(cost[mask]!=0):raise ValueError('Fixed-account objective no longer constant/external')
        lo=lower/self.d;up=upper/self.d;c=cost*self.d
        exact(lo*self.d,lower,'invertible column lower');exact(up*self.d,upper,'invertible column upper');exact(c/self.d,cost,'invertible objective')
        return lo,up,c

    def rows(self,cl,a,lower,upper):
        counts=np.diff(a.indptr)
        if (counts==0).any():raise ValueError('Empty active row needs separate treatment')
        gids=self.vgroups[a.indices];rg=gids[a.indptr[:-1]]
        if not np.array_equal(gids,np.repeat(rg,counts)):
            raise ValueError('Fixed inventory variable participates in an external/cross-group row')
        r=np.ones(len(cl));active=rg>=0;r[active]=1/self.group_scales[rg[active]]
        factor=self.d[a.indices]*np.repeat(r,counts)
        before=a.data;after=before*factor
        exact(after/factor,before,'invertible A prime=R A D')
        a.data=after
        lo=lower*r;up=upper*r
        exact(lo/r,lower,'invertible row lower');exact(up/r,upper,'invertible row upper')
        self.row_factors.append(r);self.scaled_rows+=int((r!=1).sum());self.mapped_rows+=int(active.sum())
        return a,lo,up

    def finish(self):
        self.r=np.concatenate(self.row_factors);self.row_factors=[]
        return dict(kind='REVERSIBLE_POWER_OF_TWO_FIXED_INVENTORY_NORMALISATION',groups=len(self.groups),stores=self.audit['store_count'],
            mapped_variables=int((self.vgroups>=0).sum()),scaled_variables=int((self.d!=1).sum()),mapped_rows=self.mapped_rows,scaled_rows=self.scaled_rows,
            column_scale_sha256=digest(self.d),row_scale_sha256=digest(self.r),
            primal_map='x_original=D*x_solver',dual_map='dual_original=R*dual_solver',reduced_cost_map='rc_original=rc_solver/D',
            matrix_map='A_solver=R*A_original*D; lhs/rhs_solver=R*lhs/rhs_original; bounds_solver=bounds_original/D; cost_solver=D*cost_original',
            inverse_mapping_exact_binary64=True,scientific_quantity_changes=0,original_binary64_infeasibility_preserved=True,
            finite_precision_acceptance='Independent original MW/MWh bounds derived before any solve, not expanded after results',
            physical_chain_eliminated=False,multi_commodity_timing_freedom_preserved=True)

    def restore(self,result):
        if len(result.solution.primal):
            raw=result.solution.primal.to_numpy(copy=True);result.solution.primal*=self.d
            exact(result.solution.primal.to_numpy()/self.d,raw,'primal inverse scale')
        if len(result.solution.dual):
            raw=result.solution.dual.to_numpy(copy=True);result.solution.dual*=self.r
            exact(result.solution.dual.to_numpy()/self.r,raw,'dual inverse scale')
        return result

def physical_checks(n,audit):
    """Strict independent MW/MWh acceptance for all 807 fixed stores."""
    from fixed_accounts import validate_exported_accounting
    validate_exported_accounting(n);checks=[]
    demand=n.get_switchable_as_dense('Load','p_set');h=n.snapshot_weightings.stores.to_numpy()
    for g in audit['groups']:
        be,bp=g['original_energy_error_bound_mwh'],g['original_power_error_bound_mw'];stores=g['stores'];supplies=[];violations=[]
        def add(name,values,bound,unit):
            a=np.asarray(values,dtype=float);maximum=float(np.max(np.abs(a))) if a.size else 0.
            good=bool(np.isfinite(a).all() and np.all(np.abs(a)<=bound))
            checks.append(dict(Check='FIXED_ORIGINAL:'+str(g['group'])+':'+name,Status='PASS' if good else 'FAIL',MaxAbsoluteResidual=maximum,Bound=bound,Unit=unit,Tolerance='PRE_SOLVE_OPERATION_CHAIN_BOUND',Detail='Source identity '+g['source_account_id']))
        for s in stores:
            z=n.stores.loc[s];p=n.stores_t.p[s].to_numpy();e=n.stores_t.e[s].to_numpy();prev=np.r_[z.e_initial,e[:-1]]
            link=n.links.index[n.links.bus0.eq(z.bus)][0];p0=n.links_t.p0[link].to_numpy();p1=n.links_t.p1[link].to_numpy();supplies.append(-p1)
            add('state:'+s,e-prev+p*h,be,'MWh');add('stock_lower:'+s,np.minimum(e,0),be,'MWh');add('stock_upper:'+s,np.maximum(e-z.e_nom,0),be,'MWh')
            add('release_direction:'+s,np.minimum(p,0),bp,'MW');add('source_meter:'+s,p-p0,bp,'MW');add('efficiency:'+s,p1+p0,bp,'MW')
            add('meter_capacity:'+s,np.maximum(p0-n.links.at[link,'p_nom_opt'],0),bp,'MW')
            energy=math.fsum(float(v)*float(w) for v,w in zip(p,h))
            add('annual_release:'+s,energy-z.e_initial,be,'MWh');add('terminal:'+s,e[-1],be,'MWh')
        add('final_obligation',np.sum(supplies,axis=0)-demand[g['load']].to_numpy(),bp,'MW')
    return checks
