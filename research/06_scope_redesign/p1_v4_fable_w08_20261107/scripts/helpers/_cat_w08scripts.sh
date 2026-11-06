cd /home/jin/wt_v4_fable/research/06_scope_redesign/p1_v4_w08_20261106/scripts || exit 1
for f in run_base.sh run_cache.sh run_cp.sh run_items.sh run_outputs.sh run_registry.sh run_s8.sh run_anchor_tables.sh build_v4.sh ref_runs.sh smoke_w08.sh pre_solve.sh ut.sh full_tests.sh copy_sdmx.sh patch_s30.py; do
  echo "##### $f"; cat "$f"; echo
done
echo "##### results_project/v4w08 in main checkout"
ls -la /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/
find /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/ -maxdepth 3 -type f | head -80
du -sh /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/
