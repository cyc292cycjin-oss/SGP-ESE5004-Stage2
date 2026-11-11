#!/bin/bash
# X20 ①7：注册表片段 biomass 中 irena_text_sha256 与现文件不同的来由（只读）
cd /home/jin/wt_v5_x20
grep -n "IRENA_TXT =" scripts_project/d1_biomass.py scripts_project/d1_common.py | head -3
f=$(cd scripts_project && /home/jin/miniforge3/envs/pypsa-earth/bin/python -c 'import d1_biomass as m; print(m.IRENA_TXT)')
g=${f#/home/jin/wt_v5_x20/}
echo "file $g"; sha256sum "$f"; file "$f"
git ls-files --error-unmatch "$g" > /dev/null 2>&1 && echo tracked || echo "not tracked"; git check-ignore -v "$g"
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; echo "main checkout:"; sha256sum "$M/$g" 2>&1
git log --format="%h %ad %s" --date=short -3 -- "$g" | cut -c1-120
git log --format="%h %ad %s" --date=short -2 -- research_inputs/registry_v5/fragments/biomass.json | cut -c1-120
for h in $(git log --format=%h -3 -- "$g"); do echo "$h $(git show $h:$g 2>/dev/null | sha256sum | cut -c1-16)"; done
