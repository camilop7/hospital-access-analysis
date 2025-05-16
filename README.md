# Hospital Access Analysis

This repository contains scripts and data for analyzing travel times and distances from random points within city boundaries to the nearest hospital, using Google Cloud APIs.

## Structure

- **data/boundaries/**: Place GADM shapefile folders here (one per country).
- **credentials/**: Your Google Cloud service account JSON key.
- **lib_wheels/**: Locally cached Python wheels.
- **scripts/**: Python scripts for reading boundaries and later sampling & API calls.
- **install.sh**: Bootstrap script to create a virtual environment and install dependencies offline.

## Setup

```bash
# 1. Clone the repo
# 2. Place your GCP JSON in credentials/
# 3. Add shapefiles under data/boundaries/
./install.sh
source venv/bin/activate
