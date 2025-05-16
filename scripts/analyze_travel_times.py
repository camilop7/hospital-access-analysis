#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

def main():
    # 1. Load the final merged CSV
    df = pd.read_csv("data/final/Bogotá_D.C._access.csv")
    
    # 2. Extract non-missing driving durations
    durations = df["dur_s"].dropna()
    
    # 3. Print summary statistics
    print("Summary statistics for driving times (seconds):")
    print(durations.describe(percentiles=[0.25, 0.5, 0.75]))
    
    # 4. Boxplot of the distribution
    plt.boxplot(durations)
    plt.title("Driving Times to Nearest Hospital (Bogotá D.C.)")
    plt.ylabel("Duration (seconds)")
    plt.show()

if __name__ == "__main__":
    main()
