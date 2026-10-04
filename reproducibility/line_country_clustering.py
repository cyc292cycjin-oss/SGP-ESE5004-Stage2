"""Keep derived line-country metadata consistent with PyPSA endpoint ordering.

For the pinned PyPSA 0.30.3 workflow, line.country means bus0 country.
Only this derived field is temporarily normalized; electrical attributes,
bus mapping, aggregation strategies and country-consensus checks are retained.
"""
import pandas as pd
from pypsa.clustering.spatial import (
    make_consense,
    get_clustering_from_busmap as _pypsa_get_clustering_from_busmap,
)


def get_clustering_from_busmap(n, busmap, *args, **kwargs):
    if "country" not in n.lines.columns:
        return _pypsa_get_clustering_from_busmap(n, busmap, *args, **kwargs)
    mapping = pd.Series(busmap).reindex(n.buses.index)
    strategy = (kwargs.get("bus_strategies") or {}).get(
        "country", make_consense("Bus", "country")
    )
    mapped_country = n.buses["country"].groupby(mapping).agg(strategy)
    mapped0 = n.lines["bus0"].map(mapping)
    mapped1 = n.lines["bus1"].map(mapping)
    # Match aggregatelines in PyPSA 0.30.3: swap endpoints when bus0 > bus1.
    canonical0 = mapped0.where(~(mapped0 > mapped1), mapped1)
    original_lines = n.lines
    n.lines = original_lines.assign(country=canonical0.map(mapped_country))
    try:
        return _pypsa_get_clustering_from_busmap(n, busmap, *args, **kwargs)
    finally:
        n.lines = original_lines
