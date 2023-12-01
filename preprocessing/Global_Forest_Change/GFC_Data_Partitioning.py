import os
import rasterio

# ----------------------
# PURPOSE OF THIS SCRIPT
# ----------------------
# GFC Lossyear data are .tif files with a grayscale value between 0-22. A pixel value of   
# 0 represents no deforestation. Any nonzero value represents a deforestated pixel where
# the pixel value is the year which the deforestation occured. Thus, this script creates 
# .tif files for each distinct year of deforestation given a directory of GFC .tif files.

# Function to create TIFF files for each unique value in a raster
def create_tiff_for_each_value(input_tiff_path, output_folder):
    with rasterio.open(input_tiff_path) as src:
        band_data = src.read(1)
        unique_values = set(band_data.flatten())

        # Input file without base directory
        input_file = os.path.splitext(os.path.basename(input_tiff_path))[0]

        for i in range(1, len(unique_values)):
            mask = (band_data == i).astype(rasterio.uint8)

            # Generates directory path for each distinct year
            year_prefix = f"20{i}" if i >= 10 else f"200{i}"
            year_directory = os.path.join(output_folder, f"{year_prefix}_GFC_tiles")

            # Creates directory if it does not already exist
            if not os.path.exists(year_directory):
                os.makedirs(year_directory)

            output_tiff_path = os.path.join(year_directory, f"{input_file}_Year_{i}.tif")

            profile = src.profile
            profile.update(count=1)
            profile.update(dtype=rasterio.uint8)

            with rasterio.open(output_tiff_path, 'w', **profile) as dst:
                dst.write(mask, 1)

            print(f"Created TIFF file for {input_file} for Year {i}: {output_tiff_path}")

# Directory containing input GFC TIFF files
input_directory = "/path/to/input/files.tif"

# Output directory for the processed TIFF files
output_directory = "/output/directory"

# Iterate over all TIFF files in the input directory
for filename in os.listdir(input_directory):
    if filename.endswith(".tif"):
        input_tiff_path = os.path.join(input_directory, filename)
        create_tiff_for_each_value(input_tiff_path, output_directory)
