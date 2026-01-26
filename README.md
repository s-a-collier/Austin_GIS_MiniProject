# Austin GIS Mini Project

This Python script uses ArcPy to automate updates to a geodatabase of Austin, Texas. The script renames all occurrences of "Austin" to "Austannum" and adjusts street speed limits based on proximity to schools. Streets near schools are reduced by 10 mph, and remaining streets are reduced based on their current speed.

## Features
- Rename all city references in feature classes and tables
- Reduce speed limits for streets within 250 meters of schools
- Adjust remaining street speed limits based on speed thresholds
- Export results to a CSV file with old and new speed limits

## Requirements
- Python 3.x
- ArcGIS Pro with ArcPy installed

## Usage
1. Open `Austin_MiniProject.py` in your Python environment within ArcGIS Pro.
2. Set the following variables at the top of the script:
   - `input_gdb` → path to your Austin geodatabase
   - `output_folder` → path where outputs will be saved
   - `csv_filename` → name of the CSV file for speed limits
3. Run the script in Python.
4. Check the output folder for:
   - `Austannum.gdb` (updated geodatabase)
   - CSV file with updated street speed limits
     
This README provides a clear overview, instructions for running the script, and a sample output format. It works well for a portfolio or sharing on GitHub.
