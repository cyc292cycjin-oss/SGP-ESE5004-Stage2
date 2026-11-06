set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; WT=/home/jin/wt_v4_fable; T=/home/jin/v4fable
echo "== build.err tail =="; tail -8 $T/build_off/build.err; tail -3 $T/build_off/build.log
echo "== copy upstream scripts/ into both copies =="
rsync -a --exclude __pycache__ $WT/scripts $T/repo/ && rsync -a --exclude __pycache__ $WT/scripts $T/tests_copy/ && echo copied
ls $T/repo/scripts | head -5
echo "== rerun test_v4_registry in tests_copy =="
cd $T/tests_copy && $PY -m pytest -q -p no:cacheprovider tests/research/test_v4_registry.py 2>&1 | tail -4
echo "== paper fuelwood literal-reading sensitivity (repo copy) =="
cd $T/repo && $PY /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107/scripts/sens_paper_fuelwood.py $T/work_sens /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107/evidence/SENS_PAPER_FUELWOOD.json 2>&1 | tail -5
