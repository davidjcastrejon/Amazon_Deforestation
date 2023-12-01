import os
import glob
import rasterio
from rasterio.merge import merge
from rasterio.enums import Resampling

# ----------------------
# PURPOSE OF THIS SCRIPT
# ----------------------
# Global Forest Change data comes in a grid of distinct .tif files.
# This script merges a set of specified GFC tiles together into one .tif file. 

# Input directory containing the GFC TIFF files
input_directory = '/GFC/.tif/files/path'

# Get a list of all TIFF files in the directory
input_files = glob.glob(os.path.join(input_directory, '*.tif'))

# Check if there are any TIFF files
if not input_files:
    print("No TIFF files found in the specified directory.")
    exit()

# Read all input files
src_files_to_mosaic = [rasterio.open(file) for file in input_files]

# Merge files
mosaic, out_trans = merge(src_files_to_mosaic, resampling=Resampling.nearest)

# Output file path
output_file = "/path/for/output.tif"

# Update metadata of the output file
out_meta = src_files_to_mosaic[0].meta.copy()
#out_meta.update({"driver": "GTiff", "height": mosaic.shape[1], "width": mosaic.shape[2], "transform": out_trans})
out_meta.update({"driver": "GTiff", "height": mosaic.shape[1], "width": mosaic.shape[2], "transform": out_trans, "dtype": src_files_to_mosaic[0].dtypes[0]})

# Write the mosaic to the output file
with rasterio.open(output_file, "w", **out_meta) as dest:
    dest.write(mosaic)
