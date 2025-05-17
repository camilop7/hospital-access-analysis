#!/usr/bin/env bash
set -euo pipefail

: "${GOOGLE_MAPS_API_KEY:?Please export your Maps API key first}"

# country:city1,city2,...
COUNTRY_CITIES=(
  "Colombia: Bogotá D.C.,Medellín,Santiago de Cali"
  "China: Beijing,Shanghai,Guangzhou"
)

source venv/bin/activate

for entry in "${COUNTRY_CITIES[@]}"; do
  country="${entry%%:*}"
  cities="${entry#*: }"
  # shapefile folder name
  folder="data/boundaries/${country}_level2"

  IFS=',' read -r -a arr <<< "$cities"
  for city in "${arr[@]}"; do
    safe=$(echo "$city" | tr ' ' '_' | tr -d '.')
    echo "=== $country → $city ($safe) ==="

    # 1. Sample points
    python scripts/read_boundaries.py \
      --folder "$folder" \
      --city "$city" \
      -n 100

    # 2. Fetch hospitals
    python scripts/fetch_hospitals.py \
      --folder "$folder" \
      --city   "$city"

    # 3. Compute travel times
    python scripts/compute_travel_times.py \
      --samples  "data/samples/${safe}_points.geojson" \
      --hospitals "data/hospitals/${safe}_hospitals.csv" \
      --output   "data/results/${safe}_travel_times.csv" \
      -k 10

    # 4. Clean & integrate
    python scripts/clean_and_integrate.py --city "$safe"

    echo
  done
done

echo "🎉 Done!"
