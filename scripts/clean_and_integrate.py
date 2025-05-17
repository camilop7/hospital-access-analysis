#!/usr/bin/env python3
import os
import argparse
import pandas as pd
import geopandas as gpd

def main():
    p = argparse.ArgumentParser(
        description="Merge samples, travel times, and hospital info for one city"
    )
    p.add_argument("--city", required=True,
                   help="Safe city name (no spaces/dots), e.g. Bogotá_DC or Shanghai")
    args = p.parse_args()

    safe = args.city

    # 1. Paths for this city
    samples_fp = os.path.join("data", "samples",     f"{safe}_points.geojson")
    travel_fp  = os.path.join("data", "results",     f"{safe}_travel_times.csv")
    hosp_fp    = os.path.join("data", "hospitals",   f"{safe}_hospitals.csv")

    # 2. Load
    samples = gpd.read_file(samples_fp).reset_index().rename(columns={"index":"sample_idx"})
    travel  = pd.read_csv(travel_fp, dtype={"place_id": str}).astype({"sample_idx": int})
    hosps   = pd.read_csv(hosp_fp, dtype={"place_id": str})
    hosps   = hosps[["place_id","name","address","lat","lng"]]

    # 3. Merge travel into samples
    merged = samples.merge(travel, on="sample_idx", how="left")
    merged["place_id"] = merged["place_id"].astype(str)

    # 4. Merge hospital info
    final = merged.merge(hosps,
                         how="left",
                         on="place_id",
                         suffixes=("","_hosp"))

    # 5. Report missing
    miss = final["dur_s"].isna().sum()
    total = len(final)
    print(f"⚠️  {miss}/{total} samples without a valid route for {safe}")

    # 6. Save to per‐city files
    out_dir = os.path.join("data","final")
    os.makedirs(out_dir, exist_ok=True)
    geo_out = os.path.join(out_dir, f"{safe}_access.geojson")
    csv_out = os.path.join(out_dir, f"{safe}_access.csv")

    final.to_file(geo_out, driver="GeoJSON")
    final.drop(columns="geometry").to_csv(csv_out, index=False)

    print(f"✔️  Wrote {geo_out} and {csv_out}")

if __name__=="__main__":
    main()
