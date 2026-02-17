# -*- coding: utf-8 -*-
"""
Collier_Austin_MiniProject.py

===========================================================
ALGORITHM (Step-by-step)
===========================================================

INPUTS:
  1) INPUT_GDB = Path to the input geodatabase (Austin.gdb)
  2) OUTPUT_FOLDER = Folder where all outputs will be created
  3) CSV_NAME_OR_PATH = Name (or full path) of the CSV for Part 2

PART 1 (Austin -> Austannum in ALL data in the geodatabase):
  1) Create a new file geodatabase named "Austannum.gdb" inside OUTPUT_FOLDER.
  2) Copy all Feature Datasets (and their contents) from INPUT_GDB to Austannum.gdb.
  3) Copy all Tables in the root of INPUT_GDB to Austannum.gdb.
  4) Loop through every Feature Class and Table in Austannum.gdb:
       a) Find all text (String) fields.
       b) Scan those fields to see which ones contain the word "Austin" (any case).
       c) For any field that contains "Austin", increase the field length to 255
          to prevent "Field length exceeded" errors when writing "Austannum".
       d) Update all rows: replace "Austin" with "Austannum" (case-insensitive).

PART 2 (Speed limit changes + CSV output):
  1) Use Streets feature class: Transportation\\streets
  2) Use Schools feature class: Facilities\\schools
  3) Make feature layers for streets and schools.
  4) Select streets within 250 meters of schools.
  5) Create CSV with UNIQUE street names (no duplicates) from selected streets:
       - Store full street name, old speed, new speed
       - If a street name appears multiple times, use the MODE (most common) old speed
  6) Update selected streets (within 250m of schools): decrease speed by 10 mph.
  7) Switch selection to remaining streets and update:
       - speed <= 40 mph: decrease by 5 mph
       - speed > 40 mph: decrease by 10 mph
  8) Save CSV to the location specified by CSV_NAME_OR_PATH.

OUTPUTS:
  - OUTPUT_FOLDER\\Austannum.gdb
  - CSV file listing unique street names within 250m of schools and old/new speeds
===========================================================
"""

import os
import re
import csv
from collections import Counter
import arcpy


# ===========================================================
# REQUIRED INPUTS (ONLY CHANGE THESE 3 VARIABLES)
# ===========================================================
INPUT_GDB = r"C:\Users\scollier\Downloads\Austin_Data\Austin.gdb"
OUTPUT_FOLDER = r"C:\Users\scollier\Downloads\Austin_Output"
CSV_NAME_OR_PATH = r"SchoolZone_Streets_Speeds.csv"
# ===========================================================


# -------------------------
# Progress message helper
# -------------------------
def msg(text):
    """Print messages to the Python window and ArcGIS Pro Geoprocessing window."""
    print(text)
    try:
        arcpy.AddMessage(text)
    except Exception:
        pass


# -------------------------
# Make sure output folder exists
# -------------------------
def ensure_folder(folder_path):
    """Create the folder if it does not exist."""
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)


# -------------------------
# Build the final CSV path
# -------------------------
def resolve_csv_path(output_folder, csv_name_or_path):
    """
    If only a filename is provided, put it in OUTPUT_FOLDER.
    If a full path is provided, use it as-is.
    """
    if os.path.dirname(csv_name_or_path) == "":
        return os.path.join(output_folder, csv_name_or_path)
    return csv_name_or_path


# -------------------------
# Create the output geodatabase
# -------------------------
def create_output_gdb(output_folder):
    """Create OUTPUT_FOLDER\\Austannum.gdb (delete if it already exists)."""
    out_gdb = os.path.join(output_folder, "Austannum.gdb")

    # If the output gdb already exists, delete it for a clean run
    if arcpy.Exists(out_gdb):
        msg(f"[Part 1] Deleting existing geodatabase: {out_gdb}")
        arcpy.management.Delete(out_gdb)

    # Create the new output geodatabase
    msg(f"[Part 1] Creating output geodatabase: {out_gdb}")
    arcpy.management.CreateFileGDB(output_folder, "Austannum.gdb")

    return out_gdb


# -------------------------
# Copy all data into the new geodatabase
# -------------------------
def copy_gdb_contents(src_gdb, dst_gdb):
    """Copy feature datasets (and their contents) + root tables into dst_gdb."""
    msg("[Part 1] Copying data to output geodatabase...")

    # Set workspace to the input gdb so List functions work
    arcpy.env.workspace = src_gdb

    # Copy each feature dataset (this includes all feature classes inside it)
    datasets = arcpy.ListDatasets() or []
    for ds in datasets:
        msg(f"  - Copy dataset: {ds}")
        arcpy.management.Copy(os.path.join(src_gdb, ds), os.path.join(dst_gdb, ds))

    # Copy each table at the root of the input gdb
    tables = arcpy.ListTables() or []
    for t in tables:
        msg(f"  - Copy table: {t}")
        arcpy.management.CopyRows(os.path.join(src_gdb, t), os.path.join(dst_gdb, t))

    msg("[Part 1] Copy complete.")


# -------------------------
# PART 1: Replace Austin -> Austannum in all text field values
# -------------------------
def replace_austin_everywhere(gdb_path):
    """Replace Austin (any case) with Austannum throughout the copied geodatabase."""
    msg("[Part 1] Replacing 'Austin' -> 'Austannum' in attribute values...")

    # Regex for case-insensitive matching
    pattern = re.compile("austin", re.IGNORECASE)
    replacement = "Austannum"

    # Walk through every feature class and table in the output geodatabase
    for dirpath, dirnames, filenames in arcpy.da.Walk(gdb_path, datatype=["FeatureClass", "Table"]):
        for name in filenames:
            item = os.path.join(dirpath, name)
            msg(f"  Processing: {item}")

            # Get all string fields
            text_fields = [f for f in arcpy.ListFields(item) if f.type == "String"]
            if not text_fields:
                msg("    No text fields found; skipping.")
                continue

            text_field_names = [f.name for f in text_fields]

            # Identify which fields contain "Austin" so we can safely expand them
            fields_needing_growth = set()

            # Search cursor to scan values (read-only)
            with arcpy.da.SearchCursor(item, text_field_names) as sc:
                for row in sc:
                    for i, val in enumerate(row):
                        if isinstance(val, str) and pattern.search(val):
                            fields_needing_growth.add(text_field_names[i])

            # Expand only the fields that need it (prevents field length errors)
            for fld in sorted(fields_needing_growth):
                fobj = [f for f in text_fields if f.name == fld][0]
                if fobj.length is not None and fobj.length < 255:
                    msg(f"    Expanding field length: {fld} {fobj.length} -> 255")
                    arcpy.management.AlterField(item, fld, field_length=255)

            # Update cursor to perform replacement in place
            updated_rows = 0
            with arcpy.da.UpdateCursor(item, text_field_names) as uc:
                for row in uc:
                    row = list(row)
                    changed = False

                    # Replace Austin -> Austannum in every text field value where it occurs
                    for i, val in enumerate(row):
                        if isinstance(val, str) and pattern.search(val):
                            row[i] = pattern.sub(replacement, val)
                            changed = True

                    # Write the updated row only if something changed
                    if changed:
                        uc.updateRow(row)
                        updated_rows += 1

            msg(f"    Rows updated: {updated_rows}")

    msg("[Part 1] Attribute replacement complete.")


# -------------------------
# PART 2: Speed limit changes + CSV output
# -------------------------
def part2_speed_updates_and_csv(gdb_path, output_folder, csv_name_or_path):
    """Apply speed limit rules and export CSV of unique street names near schools."""
    msg("[Part 2] Starting speed limit updates + CSV export...")

    # Build feature class paths using variables (no hard-coded directories outside gdb)
    streets_fc = os.path.join(gdb_path, "Transportation", "streets")
    schools_fc = os.path.join(gdb_path, "Facilities", "schools")

    # Field names found in your streets feature class
    name_field = "FULL_STREE"
    speed_field = "SPEED_LIMI"

    # Ensure required inputs exist
    if not arcpy.Exists(streets_fc):
        raise RuntimeError(f"Streets feature class not found: {streets_fc}")
    if not arcpy.Exists(schools_fc):
        raise RuntimeError(f"Schools feature class not found: {schools_fc}")

    msg(f"[Part 2] Streets: {streets_fc}")
    msg(f"[Part 2] Schools: {schools_fc}")

    # Create feature layers (needed for selections)
    streets_lyr = "streets_lyr"
    schools_lyr = "schools_lyr"
    arcpy.management.MakeFeatureLayer(streets_fc, streets_lyr)
    arcpy.management.MakeFeatureLayer(schools_fc, schools_lyr)

    # Select streets within 250 meters of schools
    msg("[Part 2] Selecting streets within 250 meters of schools...")
    arcpy.management.SelectLayerByLocation(
        in_layer=streets_lyr,
        overlap_type="WITHIN_A_DISTANCE",
        select_features=schools_lyr,
        search_distance="250 Meters",
        selection_type="NEW_SELECTION"
    )

    # Build unique street-name list for CSV (no duplicates)
    msg("[Part 2] Building CSV rows (unique street names)...")
    name_to_oldspeeds = {}

    # Collect old speeds for selected streets
    with arcpy.da.SearchCursor(streets_lyr, [name_field, speed_field]) as sc:
        for nm, spd in sc:
            if nm is None or spd is None:
                continue
            nm = str(nm).strip()
            if nm == "":
                continue
            name_to_oldspeeds.setdefault(nm, []).append(spd)

    # Convert dictionary into CSV rows (use MODE old speed)
    csv_rows = []
    for nm, speeds in name_to_oldspeeds.items():
        old_mode = Counter(speeds).most_common(1)[0][0]
        new_mode = max(0, old_mode - 10)
        csv_rows.append((nm, old_mode, new_mode))

    # Sort rows so output is consistent
    csv_rows.sort(key=lambda r: r[0].upper())

    msg(f"[Part 2] Unique streets within 250m of schools: {len(csv_rows)}")

    # Update selected (near-school) streets: -10 mph
    msg("[Part 2] Updating school-proximity streets: -10 mph")
    with arcpy.da.UpdateCursor(streets_lyr, [speed_field]) as uc:
        for (spd,) in uc:
            if spd is None:
                continue
            uc.updateRow((max(0, spd - 10),))

    # Switch selection to everything else (ensures no double-reduction for school streets)
    msg("[Part 2] Selecting remaining streets (not near schools)...")
    arcpy.management.SelectLayerByAttribute(streets_lyr, "SWITCH_SELECTION")

    # Update remaining streets based on speed thresholds
    msg("[Part 2] Updating remaining streets: <=40 => -5, >40 => -10")
    with arcpy.da.UpdateCursor(streets_lyr, [speed_field]) as uc2:
        for (spd,) in uc2:
            if spd is None:
                continue
            if spd <= 40:
                uc2.updateRow((max(0, spd - 5),))
            else:
                uc2.updateRow((max(0, spd - 10),))

    # Write the CSV file
    csv_path = resolve_csv_path(output_folder, csv_name_or_path)
    ensure_folder(os.path.dirname(csv_path) or output_folder)

    msg(f"[Part 2] Writing CSV to: {csv_path}")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["StreetName", "OldSpeedLimit", "NewSpeedLimit"])
        for row in csv_rows:
            w.writerow(list(row))

    msg("[Part 2] CSV export complete.")
    msg("[Part 2] Speed updates complete.")


# -------------------------
# Main script runner
# -------------------------
def main():
    msg("==========================================================")
    msg("Austin Mini Project - Starting")
    msg("==========================================================")

    # Ensure output folder exists
    ensure_folder(OUTPUT_FOLDER)

    # Verify the input geodatabase exists
    if not arcpy.Exists(INPUT_GDB):
        raise RuntimeError(f"Input geodatabase not found: {INPUT_GDB}")

    # PART 1: Create output gdb, copy contents, replace Austin->Austannum
    out_gdb = create_output_gdb(OUTPUT_FOLDER)
    copy_gdb_contents(INPUT_GDB, out_gdb)
    replace_austin_everywhere(out_gdb)

    # PART 2: Update speeds and export CSV
    part2_speed_updates_and_csv(out_gdb, OUTPUT_FOLDER, CSV_NAME_OR_PATH)

    msg("==========================================================")
    msg("Austin Mini Project - Finished Successfully")
    msg("==========================================================")


# Run main (with error reporting)
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg("!!! Script failed with an error:")
        msg(str(e))
        # Print ArcPy geoprocessing messages if available
        try:
            msg(arcpy.GetMessages())
        except Exception:
            pass
        raise
