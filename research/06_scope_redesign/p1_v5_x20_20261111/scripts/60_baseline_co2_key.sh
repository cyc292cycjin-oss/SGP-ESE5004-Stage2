#!/bin/bash
# X20 ③1：baseline.yaml 的 research.co2 段（第 372 行 lao_transit_th_store 之后）加 extra_asean_capacity_mt: null；行号先核对
set -eu
cd /home/jin/wt_v5_x20
L=$(grep -n '^    lao_transit_th_store:' configs/research/baseline.yaml | cut -d: -f1); echo "insert after line $L"
[ "$(sed -n "$((L+1))p" configs/research/baseline.yaml | cut -c1-5)" = "  s2:" ] || { echo "unexpected next line"; exit 1; }
grep -q "extra_asean_capacity_mt" configs/research/baseline.yaml && { echo "key already present"; exit 1; }
printf '%s\n' '    extra_asean_capacity_mt: null        # V5 X20 (3-1, decision 244; Q13; scripts_project/s4c_layers.extra_asean_capacity): null (main: uncapped, the 26c2e47d behaviour) | one number (Mt/a, every country) | {country: Mt/a}; applied as e_nom_max of the country extra-ASEAN store; 0 removes the store and its export links; no ASEAN total (Owen SHARED rows). Values for X21' > /tmp/x20_co2key.txt
sed -i "${L}r /tmp/x20_co2key.txt" configs/research/baseline.yaml; rm -f /tmp/x20_co2key.txt
sed -n "$((L-1)),$((L+2))p" configs/research/baseline.yaml | cut -c1-120
/home/jin/miniforge3/envs/pypsa-earth/bin/python -c "import yaml; b=yaml.safe_load(open('configs/research/baseline.yaml')); print('extra_asean_capacity_mt =', b['research']['co2']['extra_asean_capacity_mt'])"
