"""
Script to convert CSV files from the latest folder in .claude/skills/fetchAPI/data
to parquet format and save them to .claude/skills/migrate/data.

The files are saved in a folder with the same datetime name as the source folder.
"""

import os
import pandas as pd
from pathlib import Path


def get_latest_folder(source_path: str) -> tuple[str, str]:
    """
    Get the latest folder from the source path based on datetime naming.
    
    Args:
        source_path: Path to the source directory containing datetime-named folders
        
    Returns:
        Tuple of (folder_name, full_path) for the latest folder
        
    Raises:
        FileNotFoundError: If source path doesn't exist or contains no folders
    """
    source = Path(source_path)
    
    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")
    
    folders = [d for d in source.iterdir() if d.is_dir()]
    
    if not folders:
        raise FileNotFoundError(f"No folders found in {source_path}")
    
    latest_folder = max(folders, key=lambda x: x.name)
    return latest_folder.name, str(latest_folder)


def convert_csv_to_parquet(
    source_folder: str,
    output_base_path: str,
    folder_name: str
) -> None:
    """
    Convert all CSV files in source folder to parquet format.
    
    Args:
        source_folder: Path to the source folder containing CSV files
        output_base_path: Base path where output folder will be created
        folder_name: Name of the datetime folder (used for creating output folder)
    """
    source = Path(source_folder)
    output_folder = Path(output_base_path) / folder_name
    
    # Create output folder if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Get all CSV files in source folder
    csv_files = list(source.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {source_folder}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) in {source_folder}")
    print(f"Output folder: {output_folder}")
    print(f"\nConverting files:")
    
    for csv_file in csv_files:
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Create parquet filename (same name as CSV but with .parquet extension)
            parquet_filename = csv_file.stem + ".parquet"
            parquet_path = output_folder / parquet_filename
            
            # Save as parquet
            df.to_parquet(parquet_path, engine="pyarrow", index=False)
            
            print(f"  [OK] {csv_file.name} -> {parquet_filename}")
            print(f"    Shape: {df.shape} | Size: {parquet_path.stat().st_size / 1024:.2f} KB")

        except Exception as e:
            print(f"  [ERROR] Error converting {csv_file.name}: {str(e)}")


def main():
    """Main function to orchestrate the conversion process."""
    # Define paths
    source_base = r".\.claude\skills\fetchAPI\data"
    output_base = r".\.claude\skills\migrate\data"
    
    print("=" * 70)
    print("CSV to Parquet Converter")
    print("=" * 70)
    
    try:
        # Get the latest folder
        latest_folder_name, latest_folder_path = get_latest_folder(source_base)
        print(f"\nLatest source folder: {latest_folder_name}")
        print(f"Full path: {latest_folder_path}\n")
        
        # Convert CSV files to parquet
        convert_csv_to_parquet(latest_folder_path, output_base, latest_folder_name)
        
        print("\n" + "=" * 70)
        print("[SUCCESS] Conversion completed successfully!")
        print("=" * 70)

    except FileNotFoundError as e:
        print(f"\n[ERROR] Error: {str(e)}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()