set -u
T=/home/jin/v4fable/tests_copy; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
cd $T || exit 1
grep -lE 'optimize\(|\.solve\(|linprog' tests/research/test_v4_*.py && { echo "REFUSED: solver call in a v4 test"; exit 4; }
echo "start $(date -u +%H:%M:%S)"
$PY -m pytest -q -p no:cacheprovider tests/research/test_v4_a2_fallback.py tests/research/test_v4_anchor_iid.py tests/research/test_v4_base_sdmx.py tests/research/test_v4_biomass_potential.py tests/research/test_v4_captive.py tests/research/test_v4_industry_cache.py tests/research/test_v4_products.py tests/research/test_v4_profiles.py tests/research/test_v4_registry.py tests/research/test_v4_transport_accounts.py > /home/jin/v4fable/tests_v4.txt 2>&1
echo "EXIT:$?" >> /home/jin/v4fable/tests_v4.txt
echo "end $(date -u +%H:%M:%S)"; tail -5 /home/jin/v4fable/tests_v4.txt
