#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()


import os
import argparse
import pandas as pd
import geopandas as gpd
import googlemaps
from shapely.geometry import Point
import math

def load_data(samples_fp, hospitals_fp):
    # samples are in EPSG:4326 (lat/lng)
    samples = gpd.read_file(samples_fp)
    # hospitals CSV already has lat,lng
    hosps   = pd.read_csv(hospitals_fp)
    hosps['geometry'] = hosps.apply(lambda r: Point(r.lng, r.lat), axis=1)
    hosps = gpd.GeoDataFrame(hosps, geometry='geometry', crs="EPSG:4326")
    return samples, hosps

def nearest_k_indices(pt, hosp_coords, k):
    dists = [math.hypot(x - pt.x, y - pt.y) for x, y in hosp_coords]
    return sorted(range(len(dists)), key=lambda i: dists[i])[:k]

def main():
    p = argparse.ArgumentParser(
        description="Compute driving times from sample points to nearest hospitals"
    )
    p.add_argument("--samples",  required=True,
                   help="GeoJSON of sample points (EPSG:4326)")
    p.add_argument("--hospitals", required=True,
                   help="CSV of hospitals with lat,lng columns")
    p.add_argument("--output",   default="data/results/travel_times.csv",
                   help="Where to save the matched travel times")
    p.add_argument("-k", type=int, default=10,
                   help="How many nearest hospitals to try per sample (≤25)")
    args = p.parse_args()

    # 1. Load input data
    samples_ll, hosps_ll = load_data(args.samples, args.hospitals)

    # 2. Make a projected copy for Euclidean-nearest filtering
    samples_3857 = samples_ll.to_crs(epsg=3857)
    hosps_3857   = hosps_ll.to_crs(epsg=3857)
    hosp_coords  = [(pt.x, pt.y) for pt in hosps_3857.geometry]

    # 3. Initialize Google Maps client
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise EnvironmentError("Set $GOOGLE_MAPS_API_KEY to your Maps API key")
    gmaps = googlemaps.Client(key=api_key)

    rows = []
    for idx, samp_proj in samples_3857.iterrows():
        # 4a. Find k nearest by Euclidean distance
        nearest_idx = nearest_k_indices(samp_proj.geometry, hosp_coords, args.k)
        dests = [(hosps_ll.iloc[i].lat, hosps_ll.iloc[i].lng) for i in nearest_idx]

        # 4b. Build correct origin in lat/lng from the original GeoDataFrame
        samp_ll = samples_ll.loc[idx]
        origin = (samp_ll.geometry.y, samp_ll.geometry.x)

        # 5. Call the Distance Matrix API
        resp = gmaps.distance_matrix(
            origins=[origin],
            destinations=dests,
            mode="driving"
        )
        elements = resp['rows'][0]['elements']

        # 6. Filter for OK routes
        valid = [(i, el) for i, el in enumerate(elements)
                  if el.get('status') == "OK"]

        if valid:
            best_i, best_el = min(valid, key=lambda t: t[1]['duration']['value'])
            hosp = hosps_ll.iloc[nearest_idx[best_i]]
            rows.append({
                "sample_idx": idx,
                "sample_lat": samp_ll.geometry.y,
                "sample_lng": samp_ll.geometry.x,
                "place_id":   hosp.place_id,
                "hosp_name":  hosp.name,
                "hosp_addr":  hosp.address,
                "hosp_lat":   hosp.lat,
                "hosp_lng":   hosp.lng,
                "dist_m":     best_el['distance']['value'],
                "dur_s":      best_el['duration']['value']
            })
        else:
            # no valid route found
            rows.append({
                "sample_idx": idx,
                "sample_lat": samp_ll.geometry.y,
                "sample_lng": samp_ll.geometry.x,
                "place_id":   None,
                "hosp_name":  None,
                "hosp_addr":  None,
                "hosp_lat":   None,
                "hosp_lng":   None,
                "dist_m":     None,
                "dur_s":      None
            })

    # 7. Save to CSV
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Saved travel‐time matches to {args.output}")

if __name__=="__main__":
    main()
