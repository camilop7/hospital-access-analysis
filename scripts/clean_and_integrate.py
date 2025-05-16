import os
import pandas as pd
import geopandas as gpd

def main():
    # 1. Load sample points and travel‐time matches
    samples_path = os.path.join("data", "samples", "Bogotá_D.C._points.geojson")
    travel_path  = os.path.join("data", "results", "Bogotá_D.C._travel_times.csv")

    samples = gpd.read_file(samples_path)
    # read place_id as string
    travel  = pd.read_csv(travel_path, dtype={"place_id": str})

    # 2. Prepare sample_idx for join
    samples = samples.reset_index().rename(columns={"index": "sample_idx"})
    travel  = travel.astype({"sample_idx": int})

    # 3. Merge travel times into samples
    merged = samples.merge(travel, on="sample_idx", how="left")

    # 4. Ensure place_id in merged is string (will turn NaN→"nan")
    merged["place_id"] = merged["place_id"].astype(str)

    # 5. Load hospital attributes, also as strings
    hosp_path = os.path.join("data", "hospitals", "Bogotá_D.C._hospitals.csv")
    hosps = pd.read_csv(hosp_path, dtype={"place_id": str})
    hosps = hosps[["place_id", "name", "address", "lat", "lng"]]

    # 6. Merge hospital info on place_id
    final = merged.merge(
        hosps,
        how="left",
        on="place_id",
        suffixes=("", "_hosp")
    )

    # 7. Report missing routes
    num_missing = final["dur_s"].isna().sum()
    total       = len(final)
    print(f"⚠️  {num_missing} of {total} samples have no valid driving route.")

    # 8. Save the cleaned & integrated dataset
    out_dir = os.path.join("data", "final")
    os.makedirs(out_dir, exist_ok=True)
    geo_out = os.path.join(out_dir, "Bogotá_D.C._access.geojson")
    csv_out = os.path.join(out_dir, "Bogotá_D.C._access.csv")

    final.to_file(geo_out, driver="GeoJSON")
    final.drop(columns="geometry").to_csv(csv_out, index=False)

    print("✔️  Final dataset written to:")
    print(f"   • {geo_out}")
    print(f"   • {csv_out}")

if __name__ == "__main__":
    main()
