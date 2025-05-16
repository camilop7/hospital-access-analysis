#!/usr/bin/env python3
import os
import time
import argparse

import geopandas as gpd
import googlemaps
from shapely.geometry import Point
from shapely.ops import unary_union

def load_city_layer(boundaries_dir, admin_level=2, city_name=None):
    layers = []
    for country in os.listdir(boundaries_dir):
        folder = os.path.join(boundaries_dir, country)
        if not os.path.isdir(folder):
            continue
        for f in os.listdir(folder):
            if f.endswith(f"_{admin_level}.shp"):
                path = os.path.join(folder, f)
                gdf = gpd.read_file(path)
                layers.append((path, gdf))

    if not layers:
        raise FileNotFoundError(
            f"No level-{admin_level}.shp files found under {boundaries_dir}"
        )

    path, gdf = layers[0]
    if city_name:
        if "NAME_2" not in gdf.columns:
            raise KeyError(f"'NAME_2' column not in {path}")
        city_gdf = gdf[gdf["NAME_2"] == city_name]
        if city_gdf.empty:
            raise ValueError(f"No feature named '{city_name}' in {path}")
        return city_gdf, path

    return gdf, path


def fetch_nearby_hospitals(gmaps_client, location, radius):
    all_places = []
    next_token = None

    while True:
        if next_token:
            # Google requires a short delay before using next_page_token
            time.sleep(2)

        resp = gmaps_client.places_nearby(
            location=location,
            radius=radius,
            type="hospital",
            page_token=next_token
        )

        status = resp.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            raise RuntimeError(f"Places API error: {status}")

        all_places.extend(resp.get("results", []))
        next_token = resp.get("next_page_token")
        if not next_token:
            break

    return all_places


def main():
    parser = argparse.ArgumentParser(
        description="Fetch hospital locations via the Google Places API"
    )
    parser.add_argument(
        "--city", default="Bogotá D.C.",
        help="Exact NAME_2 of the municipality to query"
    )
    parser.add_argument(
        "--level", type=int, default=2,
        help="GADM admin level (2 = municipality)"
    )
    parser.add_argument(
        "--hosp-dir", default="data/hospitals",
        help="Directory to save hospital outputs"
    )
    args = parser.parse_args()

    # 1. Load the polygon for the target city
    boundaries_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "boundaries")
    )
    city_gdf, layer_path = load_city_layer(boundaries_dir, args.level, args.city)
    print(f"Loaded polygon for {args.city} from {layer_path}")

    # 2. Compute a bounding‐box‐based radius (in metres)
    city_3857 = city_gdf.to_crs(epsg=3857)
    poly_3857 = unary_union(city_3857.geometry)

    minx, miny, maxx, maxy = poly_3857.bounds
    half_width  = (maxx - minx) / 2
    half_height = (maxy - miny) / 2
    radius_m    = int(max(half_width, half_height) * 1.1)  # 10% buffer
    if radius_m > 50_000:
        print(f"Warning: computed radius {radius_m}m > 50km, capping to 50km")
        radius_m = 50_000

    # Convert centroid back to lat/lng for the API
    centroid_3857 = poly_3857.centroid
    centroid_ll = gpd.GeoSeries([centroid_3857], crs="EPSG:3857") \
                   .to_crs(epsg=4326).geometry[0]
    location = (centroid_ll.y, centroid_ll.x)
    print(f"Querying around {location} with radius {radius_m}m")

    # 3. Initialize the Maps client
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    print("DEBUG: GOOGLE_MAPS_API_KEY =", api_key)
    if not api_key:
        raise EnvironmentError("Please set $GOOGLE_MAPS_API_KEY to your Maps API key")
    gmaps = googlemaps.Client(key=api_key)

    # 4. Fetch hospital data
    places = fetch_nearby_hospitals(gmaps, location, radius_m)
    print(f"Retrieved {len(places)} hospital records")

    # 5. Build a GeoDataFrame of results
    records = []
    for place in places:
        loc = place["geometry"]["location"]
        records.append({
            "place_id": place["place_id"],
            "name": place.get("name"),
            "address": place.get("vicinity") or place.get("formatted_address"),
            "lat": loc["lat"],
            "lng": loc["lng"]
        })

    hosp_gdf = gpd.GeoDataFrame(
        records,
        geometry=[Point(r["lng"], r["lat"]) for r in records],
        crs="EPSG:4326"
    )

    # 6. Save to GeoJSON & CSV
    os.makedirs(args.hosp_dir, exist_ok=True)
    safe_city = args.city.replace(" ", "_")
    out_geo = os.path.join(args.hosp_dir, f"{safe_city}_hospitals.geojson")
    out_csv = os.path.join(args.hosp_dir, f"{safe_city}_hospitals.csv")

    hosp_gdf.to_file(out_geo, driver="GeoJSON")
    hosp_gdf.drop(columns="geometry").to_csv(out_csv, index=False)

    print(f"Saved GeoJSON → {out_geo}")
    print(f"Saved CSV     → {out_csv}")


if __name__ == "__main__":
    main()
