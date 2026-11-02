from pathlib import Path
f=Path("/home/jin/wt_v3_20261102/scripts_project/v3_liquids_data.py"); t=f.read_text()
R=[("def grid():\n    land = gpd.read_file(C.LAND).to_crs(\"EPSG:4326\")","def grid(land_path: Path):\n    land = gpd.read_file(land_path).to_crs(\"EPSG:4326\")"),
   ("import s4d_1_coastline as C\n",""),
   ("ap = argparse.ArgumentParser(); ap.add_argument(\"--network\", type=Path, required=True); a = ap.parse_args()","ap = argparse.ArgumentParser(); ap.add_argument(\"--network\", type=Path, required=True); ap.add_argument(\"--land\", type=Path, required=True, help=\"author country_shapes.geojson (s4d_1_coastline.LAND)\"); a = ap.parse_args()"),
   ("G, lon, lat, orr, occ = grid()","G, lon, lat, orr, occ = grid(a.land)"),
   ("land_sha256=sha256(C.LAND)","land_sha256=sha256(a.land)")]
for a,b in R:
    assert a in t,a
    t=t.replace(a,b)
f.write_text(t)
g=Path("/home/jin/v3/run_liq.sh"); s=g.read_text(); a2="--network $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc"; assert a2 in s
g.write_text(s.replace(a2,a2+" --land /home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/shapes/country_shapes.geojson"))
