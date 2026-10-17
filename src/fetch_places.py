"""
src/fetch_places.py
-------------------
Downloads the CDC PLACES 2022 release, Census Tract Data (GIS Friendly
Format), Socrata dataset shc3-fzig, from data.cdc.gov (no authentication).

Output:
  ckd_pipeline/data/raw/cdc_places/places_2022_tract.csv

Idempotent — skipped if the file is already present.
"""

import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "ckd_pipeline", "data", "raw", "cdc_places")
URL = "https://data.cdc.gov/api/views/shc3-fzig/rows.csv?accessType=DOWNLOAD"

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "places_2022_tract.csv")
    if os.path.exists(path):
        print(f"  skip  {path}")
    else:
        print(f"  fetch {URL}")
        urllib.request.urlretrieve(URL, path)
