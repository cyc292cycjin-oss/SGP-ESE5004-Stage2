#!/bin/bash
# proof that the test subprocesses resolve "bash" through the PATH shim (subprocess with env = a copy of os.environ, as T._clean_env), and nested "bash x.sh" too
export PATH=/home/jin/v3h/bash42/shim:$PATH
/home/jin/miniforge3/envs/pypsa-earth/bin/python -I -c "
import os, subprocess
e = {k: v for k, v in os.environ.items()}
print('subprocess bash:', subprocess.run(['bash', '--version'], env=e, capture_output=True, text=True).stdout.splitlines()[0])
print('nested bash:', subprocess.run(['bash', '-c', 'bash -c \"echo \$BASH_VERSION\"'], env=e, capture_output=True, text=True).stdout.strip())
"
