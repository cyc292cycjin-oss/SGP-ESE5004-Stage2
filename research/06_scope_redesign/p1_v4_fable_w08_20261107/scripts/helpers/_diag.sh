set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; WT=/home/jin/wt_v4_fable; T=/home/jin/v4fable
echo "== build traceback =="; grep -n -A14 Traceback $T/build_off/build.err | tail -22
echo "== phase4_static.config =="; sed -n 160,200p $WT/scripts_project/phase4_static.py
echo "== test failure =="; cd $T/tests_copy && $PY -m pytest -q -p no:cacheprovider tests/research/test_v4_registry.py::test_switches_default_off_and_config_hash 2>&1 | grep -E "Error|error|No such|config" | head -8
echo "== top-level of worktree =="; ls $WT | head -40
