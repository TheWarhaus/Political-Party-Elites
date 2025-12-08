import os
import re
import pandas as pd
from tqdm import tqdm

# -----------------------------
# PATHS (EDIT IF NEEDED)
# -----------------------------
input_folder = r"C:\Users\david\OneDrive - Univerzita Karlova\GAUK Michal\parsing piratske forum\Political-Party-Elites\data HELIOS\xlsx"
output_folder = r"C:\Users\david\OneDrive - Univerzita Karlova\GAUK Michal\parsing piratske forum\Political-Party-Elites\data HELIOS\xlsx\00_merged"

os.makedirs(output_folder, exist_ok=True)

# -----------------------------
# REGEX to extract election ID
# -----------------------------
pattern = re.compile(r"^(election_[a-zA-Z0-9\-]+)_page_\d+\.xlsx$")

# -----------------------------
# Group files by election ID
# -----------------------------
groups = {}

files = [f for f in os.listdir(input_folder) if f.endswith(".xlsx")]

for filename in files:
    match = pattern.match(filename)
    if match:
        election_id = match.group(1)
        groups.setdefault(election_id, []).append(filename)

# -----------------------------
# Merge each group
# -----------------------------
print(f"Found {len(groups)} election groups to merge.\n")

for election_id, file_list in tqdm(groups.items(), desc="Merging elections", unit="election"):
    merged_df = pd.DataFrame()

    # Sort pages by number
    file_list_sorted = sorted(
        file_list,
        key=lambda x: int(re.search(r"_page_(\d+)\.xlsx$", x).group(1))
    )

    for f in file_list_sorted:
        file_path = os.path.join(input_folder, f)
        df = pd.read_excel(file_path)
        merged_df = pd.concat([merged_df, df], ignore_index=True)

    # Save merged file
    output_path = os.path.join(output_folder, f"{election_id}.xlsx")
    merged_df.to_excel(output_path, index=False)

print("\n✅ Done! All files merged successfully.")
