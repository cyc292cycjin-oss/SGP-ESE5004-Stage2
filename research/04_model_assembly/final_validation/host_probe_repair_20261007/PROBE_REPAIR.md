# Gate5 host probe serialization repair

Scope: Windows host-resource JSON collection and serialization only. Model freeze
is `8b6a50c75d688cd69ce360580d32dd80e8003ed7`. No model, scientific input,
memory threshold, solver tolerance, pagefile, WSL configuration or run authorization
is changed. Real solver, Gate6 and Formal Phase5 runs remain zero.

## Field isolation and evidence limits

The installed Windows PowerShell is 5.1.26100.9549. The applied `.wslconfig` hash
is `b5cbcf3b01080214efb73f32a9ad872074ec6d3124edfe4abd31650d130b938f`.
The exact problematic field is `wslconfig_resource_settings`: `Get-Content`
strings have ETS properties PSPath, PSParentPath, PSChildName, PSDrive, PSProvider,
and ReadCount. In particular PSDrive and PSProvider are rich PowerShell objects.
Replacing only this field with File.ReadAllLines strings while keeping every other
collected object unchanged lets the complete legacy sample serialize at Depth 8
to 7,551 characters. Every original non-config field serializes individually.
This is a controlled one-field substitution, not an inferred Process/CIM cause.

The unchanged complete legacy serialization was also attempted in PowerShell 5.1.
It expanded the object graph until the diagnostic process used 8,580,935,680 bytes
RSS; it was stopped when host available physical memory crossed the unchanged
2 GiB guard. No final JSON was produced. The user's reported
ArgumentOutOfRangeException (requiredLength) was NOT independently captured in
this bounded attempt; exact-exception reproduction remains unverified. Do not
claim the resource stop reproduced that exception, or count it as a Gate5 failure.
Detailed evidence is on D under work/gate5_probe_repair_20261007.

## Repair

The probe builds ordered dictionaries and plain arrays with copied strings,
int64 values, bools and nulls. Every process, pagefile, pagefile setting and disk
is projected by named fields; byte quantities and original CIM MiB fields keep
their original names and units. Configuration text uses File.ReadAllLines.
A bounded schema normalizer removes any ETS metadata from strings and rejects
unknown rich objects, floats, overflow and recursive object graphs before JSON
serialization. All prior collection fields and optional CIM-error diagnostics
remain present. No resource checks are removed.

JSON is validated in memory, written to a unique sibling temporary file, read back
and parsed, then atomically moved (first publication) or File.Replace'd (updates).
The previous complete record is retained as .previous; failed conversion publishes
nothing, and failed replacement preserves the old complete record and removes
the temporary file. The preflight aborts on a probe error; stale prior evidence is
not accepted as a new sample.

The active D wrapper calls the repaired D probe directly and offers no Execute
switch. Archived delivery scripts remain byte-identical. The research repository
contains the probe and test; windows_workspace contains the deployable D wrapper.
The existing post-activation entrypoint is unchanged and works in PowerShell 5.1.

## Verification

All 15 checks PASS in Windows PowerShell 5.1.26100.9549 and PowerShell 7.6.5:
absent/current candidate config, empty/multiple process/pagefile/disk records,
primitive/int64 schema, Unicode/multiline and JSON disk roundtrip, the actual
Get-Content ETS-string shape, first atomic publication/replacement/backup,
rich-object and float/overflow/DateTime rejection, bounded recursive-graph
rejection, failed serialization, locked-target replacement and temp cleanup,
CIM diagnostic preservation and native byte-valued memory sampling.

PowerShell 7 automatically interprets ISO timestamps on JSON readback, so the
atomic replacement test compares exact file bytes rather than assuming a parsed
timestamp remains a string. Production JSON and its timestamp format are unchanged.
No PowerShell installation or upgrade is needed.

After the minimal engineering commit, the D freeze verifier's exact HEAD pin must
point to that new engineering HEAD; the original model freeze identity and all
scientific/input/test/qualification hash checks remain unchanged. This deployment
pin is not a Gate5 authorization. The only final run is the preflight-only entrypoint.
