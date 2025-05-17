#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

load_dotenv()

import os
import time
import argparse
import geopandas as gpd
import googlemaps
from shapely.geometry import Point
from shapely.ops import unary_union


def load_city_layer(shp_folder, admin_level, city_name):
    # Find the one level-N shapefile in this folder
    files = [f for f in os.listdir(shp_folder) if f.endswith(f"_{admin_level}.shp")]
    if not files:
        raise FileNotFoundError(f"No level-{admin_level}.shp in {shp_folder}")
    path = os.path.join(shp_folder, files[0])
    gdf = gpd.read_file(path)
    # Filter by municipality name
    if "NAME_2" not in gdf.columns:
        raise KeyError(f"'NAME_2' not in {path}")
    city_gdf = gdf[gdf["NAME_2"] == city_name]
    if city_gdf.empty:
        raise ValueError(f"No feature named '{city_name}' in {path}")
    return city_gdf, path

def fetch_nearby_hospitals(gmaps_client, location, radius):
    all_places, token = [], None
    while True:
        if token: time.sleep(2)
        resp = gmaps_client.places_nearby(
            location=location,
            radius=radius,
            type="hospital",
            page_token=token
        )
        status = resp.get("status")
        if status not in ("OK","ZERO_RESULTS"):
            raise RuntimeError(f"Places API error: {status}")
        all_places.extend(resp.get("results",[]))
        token = resp.get("next_page_token")
        if not token:
            break
    return all_places

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--folder", required=True,
                   help="GADM folder for this country (e.g. data/boundaries/Colombia_level2)")
    p.add_argument("--city",   required=True,
                   help="Exact NAME_2 of the municipality (e.g. 'Bogotá D.C.')")
    p.add_argument("--level",  type=int, default=2,
                   help="GADM admin level (2 = municipality)")
    p.add_argument("--hosp-dir", default="data/hospitals",
                   help="Where to save hospital outputs")
    args = p.parse_args()

    # 1. Load the city polygon from the given folder
    city_gdf, shp_path = load_city_layer(args.folder, args.level, args.city)
    print(f"Loaded polygon for {args.city} from {shp_path}")

    # 2. Compute centroid & radius
    city_3857 = city_gdf.to_crs(epsg=3857)
    poly = unary_union(city_3857.geometry)
    minx, miny, maxx, maxy = poly.bounds
    half_w = (maxx - minx)/2
    half_h = (maxy - miny)/2
    radius_m = int(max(half_w, half_h)*1.1)
    if radius_m > 50000:
        print(f"Radius {radius_m}m >50km, capping.")
        radius_m = 50000
    centroid = poly.centroid
    centroid_ll = gpd.GeoSeries([centroid], crs="EPSG:3857")\
                    .to_crs(epsg=4326).geometry[0]
    location = (centroid_ll.y, centroid_ll.x)
    print(f"Querying around {location} radius {radius_m}m")

    # 3. Init client
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    print("DEBUG: API key:", api_key)
    if not api_key:
        raise EnvironmentError("Set $GOOGLE_MAPS_API_KEY")
    gmaps = googlemaps.Client(key=api_key)

    # 4. Fetch and build GeoDataFrame
    places = fetch_nearby_hospitals(gmaps, location, radius_m)
    print(f"Retrieved {len(places)} hospital records")
    records = []
    for p in places:
        loc = p["geometry"]["location"]
        records.append({
            "place_id": p["place_id"],
            "name":     p.get("name"),
            "address":  p.get("vicinity") or p.get("formatted_address"),
            "lat":      loc["lat"],
            "lng":      loc["lng"]
        })
    hosp_gdf = gpd.GeoDataFrame(
        records,
        geometry=[Point(r["lng"], r["lat"]) for r in records],
        crs="EPSG:4326"
    )

    # 5. Safe city name (no spaces, no dots)
    safe = args.city.replace(" ","_").replace(".","")
    os.makedirs(args.hosp_dir, exist_ok=True)
    geo_out = os.path.join(args.hosp_dir, f"{safe}_hospitals.geojson")
    csv_out = os.path.join(args.hosp_dir, f"{safe}_hospitals.csv")
    hosp_gdf.to_file(geo_out, driver="GeoJSON")
    hosp_gdf.drop(columns="geometry").to_csv(csv_out,index=False)
    print(f"Saved → {geo_out}, {csv_out}")

if __name__=="__main__":
    main()
