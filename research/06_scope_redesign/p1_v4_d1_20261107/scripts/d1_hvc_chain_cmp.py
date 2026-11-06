"""D1 section 2 item 2: per-country T_v2 / other of the repository chain (hvc_basis b and a, I2 main switch set) against I2 (main and hvc_s2)."""
import json
import sys

import pandas as pd

sb, sa, sens, out = sys.argv[1:5]
b = json.load(open(sb))["countries"]; a = json.load(open(sa))["countries"]
s = pd.read_csv(sens); s = s[s.sensitivity == "hvc_s2"].set_index("country")
rows = []
for cc in sorted(b):
    i2_a = float(s.at[cc, "T_v2_TWh"]); i2_b = i2_a - float(s.at[cc, "dT_v2_TWh"])
    oa = float(s.at[cc, "other_TWh"]); ob = oa - float(s.at[cc, "dOther_TWh"])
    rows.append(dict(country=cc, repo_b_T_v2_TWh=b[cc]["T"] / 1e6, i2_main_T_v2_TWh=i2_b, diff_b=b[cc]["T"] / 1e6 - i2_b,
                     repo_a_T_v2_TWh=a[cc]["T"] / 1e6, i2_hvc_s2_T_v2_TWh=i2_a, diff_a=a[cc]["T"] / 1e6 - i2_a,
                     repo_a_other_TWh=a[cc]["other"] / 1e6, i2_hvc_s2_other_TWh=oa, diff_other_a=a[cc]["other"] / 1e6 - oa, diff_other_b=b[cc]["other"] / 1e6 - ob))
t = pd.DataFrame(rows); t.to_csv(out, index=False, float_format="%.9f", lineterminator="\n")
print(t[["country", "repo_b_T_v2_TWh", "diff_b", "repo_a_T_v2_TWh", "diff_a", "diff_other_a"]].to_string())
print("max |diff| b", t.diff_b.abs().max(), "a", t.diff_a.abs().max(), "other a", t.diff_other_a.abs().max(), "other b", t.diff_other_b.abs().max())
