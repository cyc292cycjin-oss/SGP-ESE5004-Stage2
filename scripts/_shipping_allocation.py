# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict annual shipping allocation; no data correction or missing-to-zero fill.

Candidate engineering fix against PyPSA-ASEAN a3616a68. The input table retains
one column per domestic/international account. Values are annual final-energy
TWh, not accepted new model inputs. A missing account must be resolved upstream.
"""
import numpy as np
import pandas as pd


def allocate_shipping_demand(ports, national, ac_buses):
    """Allocate each national annual account to verified AC nodes, in TWh.

    Repeated port nodes are allowed. Fractions must already sum to one per
    country: this routine neither normalizes invalid weights nor fills demand.
    Nodes without ports receive structural zero ONLY after country coverage,
    source completeness, and country-total conservation have been checked.
    """
    def fail(message):
        raise ValueError("shipping allocation: " + message)

    if national.index.has_duplicates or ac_buses.index.has_duplicates:
        fail("duplicate country or AC node")
    if national.empty or national.shape[1] != 2 or national.columns.has_duplicates:
        fail("two distinct domestic/international accounts are required")
    try:
        values = national.astype(float)
    except (ValueError, TypeError):
        fail("non-numeric national account")
    if not np.isfinite(values.to_numpy()).all() or (values < 0).any().any():
        fail("missing, non-finite or negative national account")
    if "country" not in ac_buses or ac_buses.country.isna().any():
        fail("AC node country is required")
    if not set(national.index).issubset(set(ac_buses.country)):
        fail("national country lacks an AC node")
    if not {"country", "fraction"}.issubset(ports.columns):
        fail("port country/fraction is required")
    if ports.country.isna().any() or not ports.country.isin(national.index).all():
        fail("port country is outside national account")
    if ports.index.isna().any() or not ports.index.isin(ac_buses.index).all():
        fail("port mapped to unknown AC node")
    if not (ports.index.map(ac_buses.country).to_numpy() == ports.country.to_numpy()).all():
        fail("port mapped across country boundary")
    try:
        fractions = ports.fraction.astype(float)
    except (ValueError, TypeError):
        fail("non-numeric port fraction")
    if not np.isfinite(fractions.to_numpy()).all() or (fractions < 0).any():
        fail("invalid port fraction")
    sums = fractions.groupby(ports.country).sum()
    if not np.isclose(sums.to_numpy(), 1.0, rtol=0, atol=1e-9).all():
        fail("port fractions do not sum to one within country")
    uncovered = values.loc[~values.index.isin(sums.index)]
    if (uncovered != 0).any().any():
        fail("nonzero national account has no ports")

    # Numeric allocation precedes aggregation. Never sum/map country strings.
    allocated = pd.DataFrame(0.0, index=ac_buses.index, columns=values.columns)
    for account in values.columns:
        port_values = fractions * ports.country.map(values[account])
        grouped = port_values.groupby(level=0).sum(min_count=1)
        allocated.loc[grouped.index, account] = grouped
    observed = allocated.groupby(ac_buses.country).sum().reindex(values.index)
    if not np.isfinite(allocated.to_numpy()).all() or not np.allclose(
        observed.to_numpy(), values.to_numpy(), rtol=1e-12, atol=1e-10
    ):
        fail("national annual conservation failed")
    return allocated
