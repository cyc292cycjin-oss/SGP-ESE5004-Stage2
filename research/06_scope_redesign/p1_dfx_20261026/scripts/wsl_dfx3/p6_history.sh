#!/bin/bash
# DFX v3 P6 background: do the key-name literals already exist in the repository history before this branch (counts only; pattern at run time)?
cd /home/jin/wt_dfx_v3_20261026 || exit 1
P='WLSACCESSID|WLSSECRET|LICENSEID'
echo "tracked files at base 55ab07c0 containing a key-name literal: $(git grep -l -E "$P" 55ab07c0 -- . | wc -l)"
git grep -l -E "$P" 55ab07c0 -- . | sed 's/^55ab07c0://' | head -12
echo "commits on main-side history (55ab07c0 and ancestors) whose patch adds such a literal: $(git log --format=%h -S'WLSACCESSID' 55ab07c0 | wc -l)"
echo "full test suite running: $(ps -eo args= | grep -c '[p]ytest')"
