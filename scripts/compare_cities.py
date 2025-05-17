#!/usr/bin/env python3
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

def main():
    # 1. Discover all final access CSVs
    pattern = os.path.join("data", "final", "*_access.csv")
    csv_files = sorted(glob.glob(pattern))
    if not csv_files:
        raise FileNotFoundError(f"No files matching {pattern}")

    labels = []
    data = []
    stats = []

    # 2. Load each file, extract durations and build stats
    for fp in csv_files:
        # fp e.g. data/final/Bogotá_D.C._access.csv
        base = os.path.basename(fp)
        city_label = base.replace("_access.csv", "")
        labels.append(city_label)

        df = pd.read_csv(fp)
        durations = df["dur_s"].dropna()
        data.append(durations)

        stats.append({
            "city": city_label,
            "count":    len(durations),
            "mean_s":   durations.mean(),
            "median_s": durations.median(),
            "25th_pct": durations.quantile(0.25),
            "75th_pct": durations.quantile(0.75),
            "min_s":    durations.min(),
            "max_s":    durations.max()
        })

    # 3. Print summary statistics
    stats_df = pd.DataFrame(stats)
    print(stats_df.to_string(index=False))

    # 4. Boxplot comparison
    plt.figure(figsize=(10, 6))
    plt.boxplot(data, labels=labels, showfliers=False)
    plt.xticks(rotation=45)
    plt.ylabel("Driving time (seconds)")
    plt.title("Comparison of Driving Times to Nearest Hospital")
    plt.tight_layout()
    plt.show()

if __name__=="__main__":
    main()
