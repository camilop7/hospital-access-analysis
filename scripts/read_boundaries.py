#!/usr/bin/env python3
import os, argparse, random
import geopandas as gpd
from shapely.geometry import Point

def main():
    p = argparse.ArgumentParser(
        description="Sample random points inside a single city polygon"
    )
    p.add_argument("--folder", required=True,
                   help="Directory containing the GADM shapefiles for this country (e.g. data/boundaries/Colombia_level2)")
    p.add_argument("--city", required=True,
                   help="Exact NAME_2 of the municipality (e.g. 'Bogotá D.C.')")
    p.add_argument("-n", type=int, default=100,
                   help="Number of random points to generate")
    args = p.parse_args()

    # find the single level-2 shapefile
    shp_files = [f for f in os.listdir(args.folder) if f.endswith("_2.shp")]
    if not shp_files:
        raise FileNotFoundError(f"No level-2 .shp in {args.folder}")
    shp_path = os.path.join(args.folder, shp_files[0])
    print(f"Loading {shp_path}…")
    gdf2 = gpd.read_file(shp_path)

    # filter to the desired city
    city_gdf = gdf2[gdf2["NAME_2"] == args.city]
    if city_gdf.empty:
        raise ValueError(f"No feature named '{args.city}' in {shp_path}")
    print(f"Found polygon for {args.city}, generating {args.n} points…")

    # generate random points
    poly = city_gdf.unary_union
    minx, miny, maxx, maxy = poly.bounds

    def random_point():
        while True:
            p = Point(random.uniform(minx, maxx),
                      random.uniform(miny, maxy))
            if poly.contains(p):
                return p

    points = [random_point() for _ in range(args.n)]
    pts_gdf = gpd.GeoDataFrame(geometry=points, crs=gdf2.crs)

    # write out
    safe = args.city.replace(" ", "_").replace(".", "")
    out_folder = os.path.join("data", "samples")
    os.makedirs(out_folder, exist_ok=True)
    out_path = os.path.join(out_folder, f"{safe}_points.geojson")
    pts_gdf.to_file(out_path, driver="GeoJSON")
    print(f"Saved {len(points)} points to {out_path}")

if __name__=="__main__":
    main()
