#!/bin/bash
# S4O-1.2: copy the S4N deliverables from the Windows work folder into research/06_scope_redesign/p1_step4n_20261019/
# (report, progress, evidence JSON, instruction + supplements + SHA files, environment lock, evidence/, scripts/ without __pycache__,
# pilot light package: tarball + .sha256 + POST_STATUS + unpacked members <= 500 kB; the larger members stay inside the tarball).
set -euo pipefail
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
D=$R/research/06_scope_redesign/p1_step4n_20261019
mkdir -p "$D"
for f in S4N_CLAUDE_CODE_INSTRUCTION.md S4N_INSTRUCTION_SHA256.txt S4N_SUPPLEMENT_01.md S4N_SUPPLEMENT_01_SHA256.txt S4N_SUPPLEMENT_02.md \
         S4N_SUPPLEMENT_02_SHA256.txt S4N_REPORT.md S4N_PROGRESS.md S4N_EVIDENCE.json ENV_LOCK_LOCAL.txt; do
  cp -p "$W/$f" "$D/$f"
done
rsync -a --exclude "__pycache__" "$W/evidence/" "$D/evidence/"
rsync -a --exclude "__pycache__" "$W/scripts/" "$D/scripts/"
C=cloud_results/20261019T072454Z_5125
mkdir -p "$D/$C"
cp -p "$W/$C/POST_STATUS.txt" "$W/$C/s4n_pilot_light_20261019T072454Z_5125.tar.gz" "$W/$C/s4n_pilot_light_20261019T072454Z_5125.tar.gz.sha256" "$D/$C/"
rsync -a --max-size=500k "$W/$C/unpacked/" "$D/$C/unpacked/"
echo "large members left inside the tarball only:"
cd "$W/$C/unpacked" && find . -type f -size +500k -printf "%s %p\n"
cd "$D/$C" && sha256sum -c s4n_pilot_light_20261019T072454Z_5125.tar.gz.sha256 2>&1 | sed "s#$D/##"
echo "files: $(find "$D" -type f | wc -l); size: $(du -sh "$D" | cut -f1)"
# work-folder vs repo copies of the top-level files must be byte-identical
cd "$W" && for f in S4N_REPORT.md S4N_PROGRESS.md S4N_EVIDENCE.json; do cmp "$f" "$D/$f" && echo "same: $f"; done
