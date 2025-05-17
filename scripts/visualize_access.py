#!/usr/bin/env python3
import os, glob
import pandas as pd
import matplotlib.pyplot as plt

def load_stats():
    files = sorted(glob.glob("data/final/*_access.csv"))
    stats = []
    for fp in files:
        city = os.path.basename(fp).replace("_access.csv","")
        df = pd.read_csv(fp)
        d = df["dur_s"].dropna()
        stats.append({
            "city": city,
            "median":  d.median(),
            "q1":      d.quantile(0.25),
            "q3":      d.quantile(0.75),
        })
    return pd.DataFrame(stats)

def main():
    df = load_stats().sort_values("median")
    x = range(len(df))
    medians = df["median"]
    q1 = df["q1"]
    q3 = df["q3"]
    err_low  = medians - q1
    err_high = q3 - medians

    plt.figure(figsize=(10,6))
    plt.bar(x, medians, yerr=[err_low, err_high], capsize=5)
    plt.xticks(x, df["city"], rotation=45, ha="right")
    plt.ylabel("Median driving time (s)")
    plt.title("Median ± IQR of Driving Times by City")
    plt.tight_layout()
    plt.show()

if __name__=="__main__":
    main()
