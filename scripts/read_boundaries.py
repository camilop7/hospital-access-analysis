#!/usr/bin/env python3
import os
import geopandas as gpd
import random
from shapely.geometry import Point

# 1. Point to your boundaries folder
BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "boundaries")
)
if not os.path.isdir(BASE):
    raise FileNotFoundError(f"No boundaries directory at {BASE}")

# 2. Load all shapefiles
loaded_layers = []
for country in sorted(os.listdir(BASE)):
    folder = os.path.join(BASE, country)
    if not os.path.isdir(folder):
        continue
    for fname in os.listdir(folder):
        if fname.endswith(".shp"):
            path = os.path.join(folder, fname)
            print(f"Loading {path}…")
            gdf = gpd.read_file(path)
            loaded_layers.append((path, gdf))
            print(f"  • rows: {len(gdf)}, CRS: {gdf.crs}")

# 3. Filter for level-2 shapefile(s)
level2 = [(p, g) for p, g in loaded_layers if p.endswith("_2.shp")]
if not level2:
    raise ValueError("No level-2 (_2.shp) layers found.")
shp2_path, gdf2 = level2[0]
print(f"\n→ Using level-2 layer: {shp2_path}\n")
print(gdf2.head())

# 4. (Optional) sample random points inside one municipality
TARGET = "Bogotá D.C."   # change to whichever NAME_2 you need
if "NAME_2" not in gdf2.columns:
    raise KeyError(f"'NAME_2' column missing (found: {gdf2.columns.tolist()})")

city = gdf2[gdf2["NAME_2"] == TARGET]
if city.empty:
    raise ValueError(f"No feature named '{TARGET}' in NAME_2")

poly = city.unary_union
minx, miny, maxx, maxy = poly.bounds

def random_point(poly):
    while True:
        pt = Point(random.uniform(minx, maxx),
                   random.uniform(miny, maxy))
        if poly.contains(pt):
            return pt

N = 100
pts = [random_point(poly) for _ in range(N)]
pts_gdf = gpd.GeoDataFrame(geometry=pts, crs=gdf2.crs)
print(f"\nGenerated {len(pts_gdf)} points inside {TARGET}:")
print(pts_gdf.head())

# 5. Save out if you like
out = os.path.join(os.path.dirname(__file__),
                   "..", "data", "samples",
                   f"{TARGET.replace(' ', '_')}_points.geojson")
os.makedirs(os.path.dirname(out), exist_ok=True)
pts_gdf.to_file(out, driver="GeoJSON")
print(f"\nSaved samples to: {out}")
