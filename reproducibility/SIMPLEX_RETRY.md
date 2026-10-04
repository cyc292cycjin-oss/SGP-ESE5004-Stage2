# Tutorial 2040 solver retry

Observed: HiGHS 1.11.0 IPM failed with internal_solver_error. The later missing Network.objective exception is secondary. This does not prove infeasibility.

Test: use HiGHS simplex, threads=1, parallel=off; retain the original numerical tolerances and all other solver options from the saved 2030 network metadata. No physical-model changes are made. This test has not yet demonstrated successful optimization.

Run from the project with the pypsa-earth conda environment active:

    bash reproducibility/retry_2040_simplex.sh --dry-run
    bash reproducibility/retry_2040_simplex.sh --run

The runner restricts execution to solve_network_myopic with existing 2040 inputs. This is a targeted diagnostic, not a command for the full workflow. The mtime rerun policy is scoped to this command. Existing 2030 outputs are not recomputed. Records are saved under a timestamped logs/reproduction directory, including old 2040 logs, input hashes, code diff, environment, command, and new log. The original solve script remains unchanged; an unsuccessful solve may still produce the secondary objective AttributeError.

Acceptance requires an optimal solver termination, a successfully exported 2040 result, exit code 0, and unchanged input checksums. This is still the short tutorial, not paper reproduction acceptance. The previously documented simplification discrepancy remains unresolved.

## Verified 2040 result and continuation

2040 retry on 2026-09-29: Status ok, termination optimal, Snakemake exit 0, 2030 output and 2040 input checksums unchanged. Records: logs/reproduction/retry-2040-simplex-20260929-231037. This demonstrates successful tutorial optimization with simplex, not a definitive diagnosis of the original IPM failure.

Continue using `bash reproducibility/resume_2050_simplex.sh --run`. Preview using `--dry-run`. The full aggregate target with the command-scoped mtime policy was checked: only add_brownfield for 2050, solve_network_myopic for 2050, and the aggregate completion rule remain. 2030 used IPM; 2040 used simplex; 2050 will use simplex. No completed experiment is rerun. The continuation script archives records and checks the 2030/2040 output hashes.
