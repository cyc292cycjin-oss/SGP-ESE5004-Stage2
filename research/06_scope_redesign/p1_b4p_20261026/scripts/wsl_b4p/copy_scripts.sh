#!/bin/bash
# mirror the B4P helper scripts into the deliverable folders (work/ and the research/ mirror); no host / port / licence content in any of them
set -u
S=/home/jin/b4p; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/scripts; R=/home/jin/wt_b4p_20261026/research/06_scope_redesign/p1_b4p_20261026/scripts/wsl_b4p
mkdir -p "$W" "$R"
for f in solve.sh solve3.sh chain_c2_c3.sh chain_c4_c8_v2.sh chain_v3.sh builds.sh compare_solves.py cmp1.sh wait_cmp.sh wait_done.sh wait_tests.sh a1_analysis.py a1_summary.py report_tables.py b4p_evidence.py \
         regress5.sh tests_all.sh pipeline_a5.sh pipeline_pkg.sh dryrun_b4.sh local_logs.sh kill_c3.sh pause_chain2.sh stop_chain.sh setup_wt.sh netscheck.sh st.sh showfail.sh commit123.sh copy_scripts.sh; do
  [ -f "$S/$f" ] && cp "$S/$f" "$W/" && cp "$S/$f" "$R/"
done
P='wls(access|secret)|licen[cs]e[i]d|registered[[:space:]]+to|academic[[:space:]]+licen'   # character classes: this file must not match itself
grep -rIilE "$P" "$W" "$R" && echo "LICENCE-LIKE STRING FOUND" || echo "scripts copied: $(ls "$R" | wc -l); no licence-like strings"
