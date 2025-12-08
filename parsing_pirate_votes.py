import os
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm  # progress bar

# ----------------------------------------------------------
# 1. Define paths
# ----------------------------------------------------------
base_dir = Path(r"C:\Users\david\OneDrive - Univerzita Karlova\GAUK Michal\parsing piratske forum\Political-Party-Elites\data HELIOS")
output_dir = base_dir / "xlsx"
output_dir.mkdir(exist_ok=True)

# List all XML files
xml_files = list(base_dir.glob("*.xml"))

print(f"Found {len(xml_files)} XML files.\n")

# ----------------------------------------------------------
# 2. Process each XML file separately
# ----------------------------------------------------------
for file in tqdm(xml_files, desc="Parsing XML files"):
    with open(file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    # ------------------------------------------------------
    # Extract title
    # ------------------------------------------------------
    title_tag = soup.find("h3", class_="title")
    if title_tag:
        raw_title = title_tag.get_text(strip=True)
        title = raw_title.split("—")[0].strip()
    else:
        title = "Unknown"

    # ------------------------------------------------------
    # Extract voter table
    # ------------------------------------------------------
    table = soup.find("table", class_="pretty")
    rows = table.find_all("tr")[1:]  # skip header row

    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        name = cols[0].get_text(strip=True)
        vote_raw = cols[1].get_text(strip=True)

        # Convert vote to {0, 1}
        vote = 0 if vote_raw in ["—", "&mdash;", ""] else 1

        data.append({
            "title": title,
            "name": name,
            "vote": vote
        })

    # ------------------------------------------------------
    # Save one XLSX per XML
    # ------------------------------------------------------
    df = pd.DataFrame(data)
    out_file = output_dir / f"{file.stem}.xlsx"
    df.to_excel(out_file, index=False)

print("\nDone! All XML files have been converted to XLSX.")
