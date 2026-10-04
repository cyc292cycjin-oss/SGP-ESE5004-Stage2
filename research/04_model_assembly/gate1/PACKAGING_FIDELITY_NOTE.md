# Gate1 audit packaging correction

The first foundation commit inherited broad upstream ignores for CSV/log/PNG,
and text-auto normalized some new audit text in the index. A separate packaging
commit retains the three requested CSVs, test logs and previews, disables text
normalization only inside this audit directory, and preserves the copied Phase3
test fixture bytes with a local tests/research attribute. New audit files are
regular non-executable files. No upstream model source, scientific parameter,
or test behavior changes. All tested physical bytes still match release hashes.

The prior foundation commit remains in history. Use the subsequent complete
snapshot named by the final model manifest for reproducible checks.
