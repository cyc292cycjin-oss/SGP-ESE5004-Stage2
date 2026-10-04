# Approved engineering integration

Five exact source commits integrated individually by `git cherry-pick -x`; each tested before its push. All are ENGINEERING_ONLY. This means bug corrections can change erroneous outputs; it does not mean byte-identical model behavior. No demand assumption, price, cost, policy scope, time/space resolution, technology menu or growth assumption was changed.

| Fix | Original source SHA | Research SHA |
| --- | --- | --- |
| GDP | `a7a8f06b43f0dcce0dbd7005b989d8f73d142b81` | `948784b7da4dd9a6e07e885b365d6423d2910eda` |
| E1 | `92e9118be20f0b3802f385adac2f56650d57299d` | `9c06bdd6d075444b2ba06a39cb38af2cbbf0cf9e` |
| E2 | `31037d60d69fa762c9ed8ec9ce8289d95bd6a181` | `1b73547a3e8eab02e440f4d46c26014a26b7cbdd` |
| E4 | `5d761eceeeb0d0519208d760224a41ff50ec1e30` | `f8a5dd59930593b8ea1b4278e1ecf1eb9a739ff1` |
| CARBON | `753ac81c23f8b9a1ca8ceed531d0630b56f6953d` | `1c476b1b6a8466d617709e2445f111bbf5df6c60` |

- GDP: restores the selected raw NC/year cache identity and national normalization; rejects missing countries/invalid weights. Synthetic cache and national allocation tests pass. Previously verified 10-country/48-node real-data recovery is reused as historical evidence, not rerun or claimed as 11-country assembly.
- E1: preserves residential/services heat identities and district losses. E2: rejects positive annual heat without a valid profile and invalid consumer profiles. E4: preserves canonical `services electricity` through filtering. Original regressions and 1062 combined strict rows pass.
- Carbon: one YAML key rename only: `co2.budget.co2base_value` → `base_value`. Value 1e9, factors and enable=false remain unchanged. Tests cover legacy/new keys, all six years, 8760/144-hour scaling. 1000/820/640/460/280/100 Mt/year is recovered when the budget function is used; budget is not newly enabled. Power policy versus full-system reporting scope is still unimplemented. Initial automatic approval rejection was resolved through read-only exact diff/equivalence evidence before an approved retry; no approval remains pending for this integration.

Shipping source `512c6cc2e53c579976d269486a7e328a0f372017` conflicts in `scripts/prepare_sector_network.py`. The pick was aborted; no conflict resolution was invented. The original commit rewrites whole-file line endings, whereas E1/E2 preserve CRLF and modify this file. Dependent target `cf4b0f816086470dce40ec950e20c045044eec0c` and byte-fidelity `85a32dc231458fd753445df38d422b78435b8aad` were not cherry-picked. Before-patch shipping tests fail on U (15-test set: 13 failures/1 error; 17-test set: 15 failures/1 error). These are known-unfixed candidate regressions, not a claim that all approved fixes now pass.

Recommendation for human review: authorize a separately reviewable shipping integration candidate preserving current E1/E2 source bytes, trace both original functional SHAs, and demand 17 shipping checks plus the Buildings combined suite. Gate1 does not create that candidate. Do not bypass the stopped conflict with copy-paste or an alternative merge strategy.

No combined validation branch was imported wholesale. Source commits contain their original small regression records; those historical records retain their dates. Current tests are under `evidence/final_tests/`.
