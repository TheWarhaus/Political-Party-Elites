import os
import pandas as pd
import re
from pathlib import Path
from collections import defaultdict

def merge_excel_files():
    """
    Merge Excel files with same topic ID from C:\\test folder into C:\\test\\merged folder
    """
    
    # Define paths
    source_folder = Path(r"C:\Users\david\OneDrive - Univerzita Karlova\GAUK Michal\parsing piratske forum\data\xlsx")
    target_folder = Path(r"C:\Users\david\OneDrive - Univerzita Karlova\GAUK Michal\parsing piratske forum\data\xlsx\00_merged")

    # Create target folder if it doesn't exist
    target_folder.mkdir(parents=True, exist_ok=True)
    
    # Dictionary to group files by topic ID
    topic_files = defaultdict(list)
    
    # Pattern to extract topic ID from filename
    pattern = r"topic_(\d+)-\d+_parsed\.xlsx"
    
    # Scan source folder for Excel files
    print("Scanning for Excel files...")
    for file in source_folder.glob("*.xlsx"):
        match = re.match(pattern, file.name)
        if match:
            topic_id = match.group(1)
            topic_files[topic_id].append(file)
            print(f"Found: {file.name} -> Topic ID: {topic_id}")
        else:
            print(f"Skipped: {file.name} (doesn't match pattern)")
    
    if not topic_files:
        print("No matching Excel files found!")
        return
    
    # Process each topic group
    for topic_id, files in topic_files.items():
        print(f"\nProcessing Topic ID: {topic_id}")
        print(f"Files to merge: {[f.name for f in files]}")
        
        # Sort files by the number after the dash (00, 10, 20, etc.)
        files.sort(key=lambda x: int(re.search(r"-(\d+)_", x.name).group(1)))
        
        merged_data = []
        
        # Read and combine all files for this topic
        for file in files:
            try:
                print(f"  Reading: {file.name}")
                
                # Read Excel file (all sheets if multiple exist)
                excel_file = pd.ExcelFile(file)
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(file, sheet_name=sheet_name)
                    
                    merged_data.append(df)
                    print(f"    Sheet '{sheet_name}': {len(df)} rows")
                    
            except Exception as e:
                print(f"  Error reading {file.name}: {str(e)}")
                continue
        
        if merged_data:
            # Combine all dataframes
            combined_df = pd.concat(merged_data, ignore_index=True)
            
            # Create output filename
            output_file = target_folder / f"topic_{topic_id}.xlsx"
            
            try:
                # Save merged data
                combined_df.to_excel(output_file, index=False, engine='openpyxl')
                print(f"  ✓ Saved: {output_file.name} ({len(combined_df)} total rows)")
                
            except Exception as e:
                print(f"  ✗ Error saving {output_file.name}: {str(e)}")
        else:
            print(f"  ✗ No data to merge for topic {topic_id}")
    
    print(f"\nMerging complete! Check the '{target_folder}' folder for results.")

def preview_files():
    """
    Preview what files would be processed without actually merging them
    """
    source_folder = Path(r"C:\test")
    pattern = r"topic_(\d+)-\d+_parsed\.xlsx"
    topic_files = defaultdict(list)
    
    print("Preview of files that would be processed:")
    print("-" * 50)
    
    for file in source_folder.glob("*.xlsx"):
        match = re.match(pattern, file.name)
        if match:
            topic_id = match.group(1)
            topic_files[topic_id].append(file.name)
    
    if not topic_files:
        print("No matching Excel files found!")
        return
    
    for topic_id, filenames in topic_files.items():
        print(f"Topic {topic_id} -> topic_{topic_id}.xlsx")
        for filename in sorted(filenames):
            print(f"  - {filename}")
        print()

if __name__ == "__main__":
    print("Excel File Merger by Topic ID")
    print("=" * 40)
    
    # First show preview
    preview_files()
    
    # Ask for confirmation
    response = input("Proceed with merging? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        merge_excel_files()
    else:
        print("Operation cancelled.")
