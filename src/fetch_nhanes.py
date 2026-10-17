"""
src/fetch_nhanes.py
-------------------
Downloads the NHANES public-use XPT files used by src/train_nhanes_model.py:
the 2017-March 2020 pre-pandemic combined release (P_*) and the
2021-August 2023 cycle (*_L), from wwwn.cdc.gov (no authentication).

Outputs:
  ckd_pipeline/data/raw/nhanes/P_2017-2020/P_<STEM>.xpt
  ckd_pipeline/data/raw/nhanes/L_2021-2022/<STEM>_L.xpt

Idempotent — files already present on disk are skipped.
"""

import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE_DIR, "ckd_pipeline", "data", "raw", "nhanes")
CDC = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"

STEMS = ["DEMO", "BIOPRO", "ALB_CR", "BMX", "BPXO", "DIQ", "BPQ", "MCQ", "INQ"]
CYCLES = [
    # (local dir, CDC begin-year folder, filename template)
    ("P_2017-2020", "2017", "P_{stem}.xpt"),
    ("L_2021-2022", "2021", "{stem}_L.xpt"),
]

if __name__ == "__main__":
    for local_dir, year, template in CYCLES:
        out_dir = os.path.join(RAW, local_dir)
        os.makedirs(out_dir, exist_ok=True)
        for stem in STEMS:
            name = template.format(stem=stem)
            path = os.path.join(out_dir, name)
            if os.path.exists(path):
                print(f"  skip  {local_dir}/{name}")
                continue
            url = f"{CDC}/{year}/DataFiles/{name}"
            print(f"  fetch {url}")
            urllib.request.urlretrieve(url, path)
