"""G2: figure of the VN 'other' share by step and NCV scheme (VN_OTHER_SHARE_STEPS.csv) -> fig_vn_other_share_steps.png (English labels: no CJK font in WSL)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import pandas as pd   # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402

LAB = {0: "v3", 1: "hybrid split", 2: "captive (b)=0", 3: "steel", 4: "cement (ii)", 5: "pulp & paper", 6: "glass+alumina", 7: "biomass kept", 8: "+ diesel (mode I)"}


def main():
    s = pd.read_csv(cm.WORK / "VN_OTHER_SHARE_STEPS.csv")
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for scheme, st in (("v3", "o--"), ("207", "s-")):
        z = s[s.ncv_scheme == scheme]
        ax[0].plot(z.step, z.other_share * 100, st, label=f"NCV {scheme}")
        ax[1].plot(z.step, z.T_v2_2050_TWh, st, label=f"T_v2 NCV {scheme}")
        ax[1].plot(z.step, z.other_2050_TWh, st, alpha=0.5, label=f"other NCV {scheme}")
    for a in ax:
        a.set_xticks(list(LAB)); a.set_xticklabels([LAB[k] for k in LAB], rotation=35, ha="right", fontsize=8); a.grid(alpha=0.3); a.legend(fontsize=8)
    ax[0].axhspan(30, 40, color="grey", alpha=0.15); ax[0].set_ylabel("'other' share of T_v2 2050 (%)"); ax[0].set_title("Viet Nam: 'other' share by step")
    ax[1].set_ylabel("TWh (2050)"); ax[1].set_title("T_v2 and 'other' (2050)")
    fig.tight_layout(); fig.savefig(cm.WORK / "fig_vn_other_share_steps.png", dpi=130)


if __name__ == "__main__":
    main()
