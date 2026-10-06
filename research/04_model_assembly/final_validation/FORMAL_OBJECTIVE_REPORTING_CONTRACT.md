# Formal objective/reporting contract — freeze not reached

The installed Gate5 objective includes native annualized extendable-capacity costs and weighted variable costs, plus the existing fixed O&M scalar exactly once. There is no usable objective value because the LP is infeasible. The independent post-solve reconciliation routine was not executed and is not certified by its existence.

Candidate reporting definitions retained for the later freeze:

- PricedOptimizationObjective: solved priced subset including installed KnownFixedTerms exactly once.
- KnownFixedTerms: a disclosed subset of that objective, not an amount to add again.
- PendingFixedTerms:807exclusive fixed commodity terms Q×unknown_price, with prices null. Unknown physical emissions similarly remain Q×unknown_factor.
- ComparableScenarioCost: undefined until both accepted scenario results, equal accounting boundaries and a tested fixed-term invariance check exist.
- FullSystemCostComplete=false; FullSystemEmissionsComplete=false.

No assumption of cancellation and no Integrated/Disconnected cost difference is made. Future invariance must compare source IDs, commodity identities, quantities, time weights, exclusive uses, price boundary and direction hooks. A structure change revokes external-fixed-account qualification.
