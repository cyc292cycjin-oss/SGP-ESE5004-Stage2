def define_primary_energy_limit(n: Network, sns: pd.Index) -> None:
    """
    Defines primary energy constraints. It limits the byproducts of primary
    energy sources (defined by carriers) such as CO2.

    Parameters
    ----------
    n : pypsa.Network
    sns : list-like
        Set of snapshots to which the constraint should be applied.

    Returns
    -------
    None.
    """
    m = n.model
    weightings = n.snapshot_weightings.loc[sns]
    glcs = n.global_constraints.query('type == "primary_energy"')

    if n._multi_invest:
        period_weighting = n.investment_period_weightings.years[sns.unique("period")]
        weightings = weightings.mul(period_weighting, level=0, axis=0)

    for name, glc in glcs.iterrows():
        if isnan(glc.investment_period):
            sns_sel = slice(None)
        elif glc.investment_period in sns.unique("period"):
            sns_sel = sns.get_loc(glc.investment_period)
        else:
            continue

        lhs = []
        rhs = glc.constant
        emissions = n.carriers[glc.carrier_attribute][lambda ds: ds != 0]

        if emissions.empty:
            continue

        # generators
        gens = n.generators.query("carrier in @emissions.index")
        if not gens.empty:
            efficiency = get_as_dense(
                n, "Generator", "efficiency", snapshots=sns[sns_sel], inds=gens.index
            )
            em_pu = gens.carrier.map(emissions) / efficiency
            em_pu = em_pu.multiply(weightings.generators[sns_sel], axis=0)
            p = m["Generator-p"].loc[sns[sns_sel], gens.index]
            expr = (p * em_pu).sum()
            lhs.append(expr)

        # storage units
        cond = "carrier in @emissions.index and not cyclic_state_of_charge"
        sus = n.storage_units.query(cond)
        if not sus.empty:
            em_pu = sus.carrier.map(emissions)
            sus_i = sus.index
            soc = m["StorageUnit-state_of_charge"].loc[sns[sns_sel], sus_i]
            soc = soc.ffill("snapshot").isel(snapshot=-1)
            lhs.append(m.linexpr((-em_pu, soc)).sum())
            rhs -= em_pu @ sus.state_of_charge_initial

        # stores
        stores = n.stores.query("carrier in @emissions.index and not e_cyclic")
        if not stores.empty:
            em_pu = stores.carrier.map(emissions)
            e = m["Store-e"].loc[sns[sns_sel], stores.index]
            e = e.ffill("snapshot").isel(snapshot=-1)
            lhs.append(m.linexpr((-em_pu, e)).sum())
            rhs -= em_pu @ stores.e_initial

        if not lhs:
            continue

        lhs = merge(lhs)
        sign = "=" if glc.sense == "==" else glc.sense
        m.add_constraints(lhs, sign, rhs, name=f"GlobalConstraint-{name}")
