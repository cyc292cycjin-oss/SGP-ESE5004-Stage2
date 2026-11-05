#!/bin/bash
# Show the installed PyPSA / linopy versions and the assign_duals source. Read-only.
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY - <<'EOF'
import inspect, pypsa, linopy
print("pypsa", pypsa.__version__, "linopy", linopy.__version__)
from pypsa.optimization import optimize
src = inspect.getsource(optimize.assign_duals)
print(src)
EOF
