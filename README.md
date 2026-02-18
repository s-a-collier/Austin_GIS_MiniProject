# Austin GIS Mini Project

This project is a Python script built using ArcPy in ArcGIS Pro. The script renames all occurrences of "Austin" to "Austannum" and adjusts street speed limits based on proximity to schools. I created this project to practice automating spatial data tasks while making sure updates were accurate and not applied more than once.

## Project Objectives

Part 1  
Rename every instance of the word "Austin" to "Austannum" across feature classes, tables, and attribute fields in the geodatabase.

Part 2  
Adjust street speed limits using the following rules:
- Streets within 250 meters of schools are reduced by 10 mph.
- Remaining streets with speed limits of 40 mph or less are reduced by 5 mph.
- Remaining streets with speed limits above 40 mph are reduced by 10 mph.
- Streets reduced due to proximity to schools are not reduced again.
- A CSV file is created that lists unique street names along with their old and new speed limits.

## Skills Demonstrated

- Python programming using variables, loops, conditional statements, and update cursors
- Use of ArcPy geoprocessing tools such as Copy, Buffer, and SelectLayerByLocation
- Spatial analysis using proximity and attribute selection
- Writing results to a CSV file
- Automating repetitive geodatabase tasks
- Adding error handling to prevent crashes if layers or fields are missing

## Requirements

- ArcGIS Pro
- Python environment that includes ArcPy
- Access to the provided Austin geodatabase

## How to Run the Script

1. Open ArcGIS Pro.
2. Open the Python window or run the script from the ArcGIS Pro Python environment.
3. Modify the three variables at the top of the script:
   - input_gdb: Path to the input geodatabase
   - output_folder: Folder where outputs will be saved
   - csv_filename: Name of the CSV file for Part 2 results
4. Run the script.
5. Check the output folder for:
   - Austannum.gdb
   - CSV file with updated street speed limits

## Expected Output

The script produces:
- A new geodatabase named Austannum.gdb
- A CSV file containing unique street names with their original and updated speed limits

## Notes

The data used for this project is not included in this repository. Users must provide their own copy of the Austin geodatabase to run the script.
