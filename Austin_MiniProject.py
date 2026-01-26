# Austin GIS Mini Project
# -----------------------
# Python script for ArcGIS Pro (ArcPy)
# Part 1: Rename "Austin" -> "Austannum" in all fields
# Part 2: Adjust street speed limits based on proximity to schools
# Script includes placeholders for layers and error handling

import arcpy
import os
import csv

# ----------------------------
# Required Inputs (change only these)
# ----------------------------
input_gdb = r"C:\Path\To\Austin_Data.gdb"        # Input geodatabase
output_folder = r"C:\Path\To\OutputFolder"      # Folder to store outputs
csv_filename = "Austannum_SpeedLimits.csv"      # CSV file for Part 2

# ----------------------------
# Setup
# ----------------------------
arcpy.env.overwriteOutput = True

# Output geodatabase
output_gdb = os.path.join(output_folder, "Austannum.gdb")

# ----------------------------
# Part 1: Rename "Austin" -> "Austannum"
# ----------------------------
try:
    print("Copying geodatabase...")
    arcpy.management.Copy(input_gdb, output_gdb)
    print(f"Copied geodatabase to {output_gdb}")
except Exception as e:
    print(f"Error copying geodatabase: {e}")

# Set workspace to new geodatabase
arcpy.env.workspace = output_gdb

# Loop through feature datasets (or root if none)
datasets = arcpy.ListDatasets() or [""]

for ds in datasets:
    feature_classes = arcpy.ListFeatureClasses(feature_dataset=ds) or []
    for fc in feature_classes:
        print(f"Processing feature class: {fc}")
        # Loop through string fields
        fields = [f.name for f in arcpy.ListFields(fc) if f.type in ["String", "Text"]]
        for field in fields:
            print(f"Checking field: {field}")
            try:
                with arcpy.da.UpdateCursor(fc, [field]) as cursor:
                    for row in cursor:
                        if row[0] and "austin" in row[0].lower():
                            row[0] = row[0].replace("Austin", "Austannum").replace("AUSTIN", "Austannum")
                            cursor.updateRow(row)
            except Exception as e:
                print(f"Error processing field {field} in {fc}: {e}")

# ----------------------------
# Part 2: Adjust Speed Limits
# ----------------------------
# Placeholder layer names (update with actual layer names in your GDB)
streets_layer = "Streets"   # Name of the street feature class
schools_layer = "Schools"   # Name of the schools feature class

# Create output CSV path
csv_path = os.path.join(output_folder, csv_filename)

try:
    # Create feature layers
    arcpy.management.MakeFeatureLayer(streets_layer, "streets_lyr")
    arcpy.management.MakeFeatureLayer(schools_layer, "schools_lyr")

    # Buffer schools by 250 meters
    buffer_layer = "schools_buffer"
    arcpy.analysis.Buffer("schools_lyr", buffer_layer, "250 Meters")

    # Select streets within buffer
    arcpy.management.SelectLayerByLocation("streets_lyr", "INTERSECT", buffer_layer)

    # Dictionary to track updated streets
    updated_streets = {}

    # Update speed limits for streets near schools (-10 mph)
    with arcpy.da.UpdateCursor("streets_lyr", ["StreetName", "SpeedLimit"]) as cursor:
        for row in cursor:
            street = row[0]
            old_speed = row[1]
            if old_speed is not None:
                row[1] = max(old_speed - 10, 0)
                cursor.updateRow(row)
                updated_streets[street] = (old_speed, row[1])

    # Select remaining streets not near schools
    arcpy.management.SelectLayerByAttribute("streets_lyr", "SWITCH_SELECTION")

    # Update remaining streets based on speed
    with arcpy.da.UpdateCursor("streets_lyr", ["StreetName", "SpeedLimit"]) as cursor:
        for row in cursor:
            street = row[0]
            old_speed = row[1]
            if old_speed is not None:
                if old_speed <= 40:
                    row[1] = max(old_speed - 5, 0)
                else:
                    row[1] = max(old_speed - 10, 0)
                cursor.updateRow(row)
                # Avoid overwriting streets already updated
                if street not in updated_streets:
                    updated_streets[street] = (old_speed, row[1])

    # Write results to CSV
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["StreetName", "OldSpeedLimit", "NewSpeedLimit"])
        for street, speeds in updated_streets.items():
            writer.writerow([street, speeds[0], speeds[1]])

    print(f"Speed limit updates written to {csv_path}")

except Exception as e:
    print(f"Error in Part 2 processing: {e}")

print("Script completed.")

