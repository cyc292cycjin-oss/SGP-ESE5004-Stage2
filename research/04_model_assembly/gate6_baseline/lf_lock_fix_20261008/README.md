# Gate6 exact LF execution identity repair

Only two explicit root .gitattributes rules were added. The two working files
were changed strictly by CRLF-to-LF replacement (31 and 178 occurrences);
their resulting bytes are identical to the pre-existing Git blobs. No scientific
source, configuration, input or test assertion changed.

The old 48-entry lock and old local test receipt are preserved byte-for-byte in
history, alongside the prior cloud failure and its verified diagnosis. The
current lock changes only those two byte hashes and sizes; all other 46 entries
are identical. Gate5 historical evidence is untouched. Historical tests/ remains
the earlier record; local_tests/ here and the top-level current receipt bind the
new LF lock. Test receipts bind exact source bytes, not later evidence-only commits.

New actual local verification: complete Gate6 suite (10 suites, 87 checks) plus
60 directly affected existing asset regressions from eight modules. The explicit
class/method selection is retained in the supplementary driver and receipt;
unrelated historical source-count, policy and transmission cases were not rerun.
All original assertions are intact; two legacy output receipts are redirected to
the unique test directory. No test was skipped. Native run/presolve are hard
trapped. Production input validation hard-traps full model construction; only
bounded synthetic fixtures are built by the ordinary Gate6 suite.

Six checkout checks confirm these two files remain exact LF under autocrlf=true,
false and input, even with core.eol=crlf. All 40 locked source/config bytes match
their existing Git blobs. No global Git configuration was modified.

Cloud deployment/testing follows only after this passing local evidence and a
normal research/full-sc-baseline commit/push. No Gate6/DEC/Phase5 authorization
is created. Full production matrix builds, native run and native presolve: 0.
