import rasterio, numpy as np
pts = {"Singapore Strait": (103.85, 1.20), "Malacca Strait": (100.80, 2.60), "Hong Kong approach": (114.05, 22.20), "Laos inland": (103.0, 18.0),
       "South China Sea open": (113.0, 12.0), "Zhoushan": (122.3, 29.9), "Ningbo-Zhoushan in box": (122.12, 29.40), "Gulf of Thailand": (101.0, 10.0)}
for f in ["/home/jin/m08a_offshore_work/shipdensity_asean_cutout_extent.tif", "/vsizip//mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/raw12/shipdensity_global.zip/shipdensity_global.tif"]:
    with rasterio.open(f) as r:
        print(f.split("/")[-1], r.bounds, r.res, r.crs)
        for k, p in pts.items():
            if r.bounds.left <= p[0] <= r.bounds.right and r.bounds.bottom <= p[1] <= r.bounds.top:
                row, col = r.index(*p)
                win = r.read(1, window=((max(row - 10, 0), row + 11), (max(col - 10, 0), col + 11)))
                print(f"  {k:24s} value {int(win[10, 10]) if win.shape[0] > 10 else None:>10d}  max in +-10 px {int(win.max()):>10d}")
