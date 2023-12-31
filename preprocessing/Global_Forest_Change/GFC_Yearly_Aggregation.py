import os
import rasterio

# --------------------------------------------------------------------------#
# Script for preprocessing Global Forest Change deforestation lossyear data #
# --------------------------------------------------------------------------#

# Function to create TIFF files for each unique value in a raster
# Places each group of TIFF into organized directories 
def create_tiff_for_each_value(input_tiff_path, output_folder):
    with rasterio.open(input_tiff_path) as src:
        band_data = src.read(1)
        unique_values = set(band_data.flatten())

        # Input file without base directory
        input_file = os.path.splitext(os.path.basename(input_tiff_path))[0]

	# Places each set of TIFF files with the same value into organized directories
        for i in range(1, len(unique_values)):
            mask = (band_data == i).astype(rasterio.uint8)
            if i < 10:
                output_tiff_path = os.path.join(output_folder, f"200{i}_GFC_tiles/{input_file}_Year_{i}.tif")
            else:
                output_tiff_path = os.path.join(output_folder, f"20{i}_GFC_tiles/{input_file}_Year_{i}.tif")

            profile = src.profile
            profile.update(count=1)
            profile.update(dtype=rasterio.uint8)

            with rasterio.open(output_tiff_path, 'w', **profile) as dst:
                dst.write(mask, 1)

            print(f"Created TIFF file for {input_file} for Year {i}: {output_tiff_path}")

# Directory containing input TIFF files
input_directory = "/path/to/tiff/files"

# Output directory for the processed TIFF files
output_directory = "/path/to/output/directory"

# Iterate over all TIFF files in the input directory
for filename in os.listdir(input_directory):
    if filename.endswith(".tif"):
        input_tiff_path = os.path.join(input_directory, filename)
        create_tiff_for_each_value(input_tiff_path, output_directory)
