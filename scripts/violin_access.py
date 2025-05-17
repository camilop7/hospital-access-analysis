#!/usr/bin/env python3
import glob, os, pandas as pd
import matplotlib.pyplot as plt

def load_distributions():
    files = sorted(glob.glob("data/final/*_access.csv"))
    data, labels = [], []
    for fp in files:
        city = os.path.basename(fp).replace("_access.csv","")
        df = pd.read_csv(fp)
        d = df["dur_s"].dropna()
        data.append(d)
        labels.append(city)
    return data, labels

def violin():
    data, labels = load_distributions()
    plt.figure(figsize=(10,6))
    plt.violinplot(data, showextrema=True, showmeans=True)
    plt.xticks(range(1, len(labels)+1), labels, rotation=45, ha="right")
    plt.ylabel("Driving time (s)")
    plt.title("Distribution of Driving Times by City")
    plt.tight_layout()
    plt.show()

if __name__=="__main__":
    violin()
