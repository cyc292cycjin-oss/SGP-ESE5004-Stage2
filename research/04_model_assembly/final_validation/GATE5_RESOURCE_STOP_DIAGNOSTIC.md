# Run04 resource stop — bounded evidence

Verified: available memory fell to 400.438 MiB, below the unchanged 512 MiB guard, after 4666.203 s (wall limit 14400 s). The latest manifest records STOPPED_RESOURCE_GUARD. This is not a final native time-limit or infeasibility result. Process peak RSS in the manifest is 6937.0625 MiB; sampled peak is 6937.7852 MiB.

The full log includes starred iterations 106*, 107*, 108*. IPM and crossover both report imprecise. HiGHS automatically performed serial dual-simplex cleanup, then logged “Solving the original LP from the solution after postsolve”. The memory rise and interruption occur after this log sequence. This temporal evidence does not identify an individual allocation or prove a kernel OOM event. The monitor's solve phase does not separately time crossover/cleanup.

The cleanup log's Pr:0 and internal valid-solution message do not establish an accepted primal of the full original model. The backend did not return to capture native flags, scalar diagnostics, original-unit remapping or PyPSA assignment. Their status is NOT_CAPTURED_PROCESS_INTERRUPTED / NOT_REACHED, not PASS. No objective or result network is published; dynamic checks remain NOT_RUN.

The existing 12-case mock suite verifies the interface safeguards, not this interrupted run's solution. The transformed model matches run03 in labels, sparse coefficients, bounds, objective, all 1037 constraint groups and scaling receipt (PREVIOUS_MODEL_COMPARISON.json). Transfer fidelity PASS does not imply feasibility.

No fifth solve, IIS, new algorithm, tolerance change, WSL memory change or data modification was attempted. A future attempt needs a reviewed memory plan for the full postsolve/qualification path as well as a new bounded authorization; more time alone has not resolved this run. The observed peak is a lower bound on required headroom, not a prediction of final peak usage.

Raw log, monitor and manifest hashes are in bounded_gate5_20261006/GATE5_RESOURCE_STOP_DIAGNOSTIC.json. Historical failures remain unchanged.
