#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import re
import glob
import ctypes
import rasterio
import subprocess
import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio import mask
from rasterio.plot import show
from rasterio.transform import from_origin
from tqdm.notebook import tqdm
import matplotlib.pyplot as plt
from osgeo import ogr, gdal, osr
from rasterio.merge import merge
from geopy.distance import geodesic
from rasterio.windows import Window
from shapely.geometry import mapping
from rasterio.enums import Resampling
from shapely.geometry import Point, MultiPoint


# In[11]:


def latlon_to_pixel(lat, lon, geotransform):
    
    """
    Convert latitude and longitude to pixel coordinates in a GeoTIFF file.

    Parameters:
    - lat: Latitude
    - lon: Longitude
    - geotransform: GeoTransform information from the GeoTIFF file

    Returns:
    - x_pixel: Pixel x-coordinate
    - y_pixel: Pixel y-coordinate
    """

    # Extracting GeoTransform parameters
    x_geo, pixel_width, _, y_geo, _, pixel_height = geotransform

    # Calculating pixel coordinates
    x_pixel = int((lon - x_geo) / pixel_width)
    y_pixel = int((lat - y_geo) / pixel_height)

    return x_pixel, y_pixel


# In[12]:


def get_lat_lon_from_pixel(geo_transform, col, row):
    
    """
    Convert pixel coordinates in a GeoTIFF file to latitude and longitude.

    Parameters:
    - column
    - row
    - geotransform: GeoTransform information from the GeoTIFF file

    Returns:
    - latitude
    - longitude
    """
    
    lon = geo_transform[0] + col * geo_transform[1] + row * geo_transform[2]
    lat = geo_transform[3] + col * geo_transform[4] + row * geo_transform[5]
    return lat, lon


# In[13]:


def get_geotransform_from_file(tif_path):
    """
    Get GeoTransform information from a GeoTIFF file.

    Parameters:
    - tif_path: Path to the GeoTIFF file

    Returns:
    - geotransform: GeoTransform information as a tuple
    """
    dataset = gdal.Open(tif_path)
    geotransform = dataset.GetGeoTransform()
    dataset = None  # Close the dataset
    return geotransform


# In[14]:


def merge_tiles(year):
    # Input directory containing the TIFF files
    input_directory = f'/home/davidjcastrejon/GFC_Tiles/20{year}_GFC_tiles'

    # Get a list of all TIFF files in the directory
    input_files = glob.glob(os.path.join(input_directory, '*.tif'))
    
    # print(f"Input directory: {input_directory}")
    # print(f"Input files: {input_files}")

    # Check if there are any TIFF files
    if not input_files:
        print("No TIFF files found in the specified directory.")
        return

    # Read all input files
    src_files_to_mosaic = [rasterio.open(file) for file in input_files]

    # Merge files
    mosaic, out_trans = merge(src_files_to_mosaic, resampling=Resampling.nearest)

    # Output file
    output_file = "/home/davidjcastrejon/merged_output.tif"

    # Update metadata of the output file
    out_meta = src_files_to_mosaic[0].meta.copy()
    out_meta.update({"driver": "GTiff", "height": mosaic.shape[1], "width": mosaic.shape[2], "transform": out_trans, "dtype": src_files_to_mosaic[0].dtypes[0]})

    # Write the mosaic to the output file
    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(mosaic)


# In[18]:


def get_day_from_filename(file_path):
    # Use regular expression to extract the day from the filename
    match = re.search(r'doy2022(\d{3})', file_path)
    if match:
        return int(match.group(1))
    else:
        return 0  # Return 0 if day information is not found


# In[ ]:





# In[25]:


PRODES = '/home/davidjcastrejon/prodes_amazonia_raster_2000_2022_v20231109.tif'
ecoregions_dir = '/home/davidjcastrejon/Brazilian_Amazon_Ecoregions'
APPEARS_dir = '/home/davidjcastrejon/EVI/2015-2023/MOD13Q1.061_2015351_to_2023365'
merged_output_dir = './'
GFC_directory = '/home/davidjcastrejon/GFC_Tiles'

# List of ecoregion .shp filenames
ecoregions = [filename for filename in os.listdir(ecoregions_dir) if filename.endswith('.shp')]

# Path to shared object
lib = ctypes.CDLL('./libsub_arrays.so')

# Total amount of deforestation:
prodes_total = 0
gfc_total = 0
total = 0

# get_ipython().system('rm *.tif')
# get_ipython().system('rm *.xml')

txt_file_path = f'/home/davidjcastrejon/2022_Analysis.txt'

with open(txt_file_path, 'w') as file:
    gdal_command_1 = f'gdal_calc.py -A {PRODES} --outfile=out.tif --calc="A==22" --NoDataValue=255'
    subprocess.run(gdal_command_1, shell=True)
    merge_tiles(22)
    
    for ecoregion in ecoregions:
        # Path to ecoregion shapefile
        shp_path = os.path.join(ecoregions_dir, ecoregion)
        import geopandas as gpd
        gdf = gpd.read_file(shp_path)

        # Analyze 2022
        for year in range(22,23):
            # Replace with os before converting to .py
            # !rm *.tif
            # !rm *.xml
            
            line = f'{ecoregion} {year}\n'
            file.write(line)
            
            # Create prodes raster 
            # gdal_command_1 = f'gdal_calc.py -A {PRODES} --outfile=out.tif --calc="A=={year}" --NoDataValue=255'
            gdal_command_2 = f'gdalwarp -tr 0.0002689996094039614474 -0.0002690007898141364893 -cutline {shp_path} -crop_to_cutline -dstnodata 255 -of GTiff out.tif prodes_{ecoregion}_20{year}.tif'
            # subprocess.run(gdal_command_1, shell=True)
            subprocess.run(gdal_command_2, shell=True)
            # os.remove('out.tif')
            
            prodes_path = f'prodes_{ecoregion}_20{year}.tif'
            with rasterio.open(prodes_path) as prodes:
                prodes_data = prodes.read(1)
            prodes_def_mask = (prodes_data == 1)
            prodes_non_mask = (prodes_data == 0)
            
            # Total PRODES pixels of deforestation
            prodes_def_count = np.count_nonzero(prodes_def_mask)
            prodes_total += prodes_def_count
            line = f'PRODES: {prodes_def_count} pixels\n'
            file.write(line)

            prodes_geotransform = get_geotransform_from_file(prodes_path)
            os.remove(prodes_path)
            lat, lon = get_lat_lon_from_pixel(prodes_geotransform, 0, 0)
            height, width = prodes_data.shape
            diff = np.zeros((height, width), dtype=np.float32)
            
            # Create GFC raster
            # merge_tiles(year)
            gdal_command_3 = f'gdalwarp -tr 0.0002689996094039614474 -0.0002690007898141364893 -cutline {shp_path} -crop_to_cutline -dstnodata 255 -of GTiff merged_output.tif gfc_{ecoregion}_20{year}.tif'
            subprocess.run(gdal_command_3, shell=True)
            # os.remove('merged_output.tif')
            
            gfc_path = f'gfc_{ecoregion}_20{year}.tif'
            with rasterio.open(gfc_path) as gfc:
                gfc_data = gfc.read(1)
            os.remove(gfc_path)
            gfc_def_mask = (gfc_data == 1)
            gfc_non_mask = (gfc_data == 0)
            
            # Total GFC pixels of deforestation
            gfc_def_count = np.count_nonzero(gfc_def_mask)
            gfc_total += gfc_def_count
            line = f'GFC: {gfc_def_count} pixels\n'
            file.write(line)
            
            # Combine Masks for Ones
            combined_def_mask = np.logical_and(prodes_def_mask, gfc_def_mask)

            # Combine Masks for Zeros
            combined_non_mask = np.logical_and(prodes_non_mask, gfc_non_mask)
            
            total += np.count_nonzero(combined_def_mask)

            # Create ordered list of APPEARS tifs
            pattern = f'MOD13Q1.061__250m_16_days_EVI_doy20{year}*.tif'
            tifs = glob.glob(f'{APPEARS_dir}/{pattern}')

            # Sort the file paths based on the day of the year
            appears_tifs = sorted(tifs, key=get_day_from_filename)

            day = 1

            # Replace with os before converting to .py
            # !rm appears.tif

            # Analysis for each .tif of each year
            prodes_max_def = []
            prodes_max_non = []
            gfc_max_def = []
            gfc_max_non = []
            for snapshot in appears_tifs:
                # Creates appears.tif with same spatial resolution as prodes data
                gdal_command_4 = f'gdalwarp -tr 0.0002689996094039614474 -0.0002690007898141364893 -of GTiff {snapshot} appears.tif'
                subprocess.run(gdal_command_4, shell=True)

                # Could also use gdal to open raster instead
                with rasterio.open('appears.tif') as apps:
                    appears_data = apps.read(1)

                appears_geotransform = get_geotransform_from_file(snapshot)
                os.remove('appears.tif')
                
                # Convert coordinate to upper left pixel
                # Extracting GeoTransform parameters
                x_geo, pixel_width, _, y_geo, _, pixel_height = appears_geotransform
                
                # Calculating pixel coordinates
                x = int((lon - x_geo) / pixel_width)
                y = int((lat - y_geo) / pixel_height)

                current = appears_data[x:x+height, y:y+width]

                if day == 1:   
                    prev = appears_data[x:x+height, y:y+width]       
                else: # Perform c++ calculations
                    # Convert numpy arrays to ctypes pointers
                    print(prev.dtype, current.dtype, diff.dtype)
                    prev_ptr = prev.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                    current_ptr = current.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                    diff_ptr = diff.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                    lib.sub_arrays(prev_ptr, current_ptr, diff_ptr, height, width)
                    prev = current

                selected_values = diff[prodes_def_mask]
                # selected_values *= .0001
                mean = np.mean(selected_values)
                if not prodes_max_def:
                    prodes_max_def = [mean, day]
                elif mean < prodes_max_def[0]:
                    prodes_max_def = [mean, day]
                line = f'Average drop in PRODES deforestated pixels for day {day}:\n'
                file.write(line)
                line = f'{mean}\n'
                file.write(line)
                
                selected_values = diff[prodes_non_mask]
                # selected_values *= .0001
                mean = np.mean(selected_values)
                if not prodes_max_non:
                    prodes_max_non = [mean, day]
                elif mean < prodes_max_non[0]:
                    prodes_max_non = [mean, day]
                line = f'Average drop in PRODES non-deforestated pixels for day {day}:\n'
                file.write(line)
                line = f'{mean}\n'
                file.write(line)
                
                selected_values = diff[gfc_def_mask]
                # selected_values *= .0001
                mean = np.mean(selected_values)
                if not gfc_max_def:
                    gfc_max_def = [mean, day]
                elif mean < gfc_max_def[0]:
                    gfc_max_def = [mean, day]
                line = f'Average drop in GFC deforestated pixels for day {day}:\n'
                file.write(line)
                line = f'{mean}\n'
                file.write(line)
                
                selected_values = diff[gfc_non_mask]
                # selected_values *= .0001
                mean = np.mean(selected_values)
                if not gfc_max_non:
                    gfc_max_non = [mean, day]
                elif mean < gfc_max_non[0]:
                    gfc_max_non = [mean, day]
                line = f'Average drop in GFC non-deforestated pixels for day {day}:\n'
                file.write(line)
                line = f'{mean}\n'
                file.write(line)
                
                selected_values = diff[combined_def_mask]
                # selected_values *= .0001
                mean = np.mean(selected_values)
                line = f'Average drop in PRODES+GFC deforestated pixels for day {day}:\n'
                file.write(line)
                line = f'{mean}\n'
                file.write(line)
                
                selected_values = diff[combined_non_mask]
                # selected_values *= .0001
                mean = np.mean(selected_values)
                line = f'Average drop in PRODES+GFC non-deforestated pixels for day {day}:\n'
                file.write(line)
                line = f'{mean}\n'
                file.write(line)

                day += 16

                # !rm appears.tif
                # !rm appears.tif.aux.xml

            # Breaks year loop
            line = f'Max PRODES deforestated change: {prodes_max_def[0]}, day {prodes_max_def[1]}\n'
            file.write(line)
            line = f'Max PRODES non-deforestated change: {prodes_max_non[0]}, day {prodes_max_non[1]}\n'
            file.write(line)
            line = f'Max GFC deforestated change: {gfc_max_def[0]}, day {gfc_max_def[1]}\n'
            file.write(line)
            line = f'Max GFC non-deforestated change: {gfc_max_non[0]}, day {gfc_max_non[1]}\n'
            file.write(line)

        # Breaks ecoregion loop
        file.write('\n\n')

    # !rm *.tif
    line = f'Total PRODES deforestation: {prodes_total} pixels'
    file.write(line)
    line = f'Total GFC deforestation: {gfc_total} pixels'
    file.write(line)
    line = f'Total PRODES+GFC deforestation: {total} pixels'
    
    


# In[ ]:





# In[ ]:




