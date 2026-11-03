#!/bin/bash
# V3 supplement 06: list the networks the diagnosis reads (read-only)
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
for d in builds_op smoke_s5 smoke_s1 smoke_r2; do echo "== $d"; ls -la "$R/$d" 2>/dev/null | grep -E "\.nc|/$|^d" | head -30; done
echo "== smoke_s5 tree"; find "$R/smoke_s5" -maxdepth 3 -name "*.nc" 2>/dev/null | head
echo "== smoke_s1 tree"; find "$R/smoke_s1" -maxdepth 3 -name "*.nc" 2>/dev/null | head
echo "== truncated"; find "$R" -maxdepth 3 -name "*56*" 2>/dev/null | head -20
