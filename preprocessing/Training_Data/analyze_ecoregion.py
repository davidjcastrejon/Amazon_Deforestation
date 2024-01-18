import os
import re
import csv
import time
import glob
import ctypes
import rasterio
import subprocess
import numpy as np
from functools import partial
import pandas as pd
import geopandas as gpd
from rasterio.merge import merge
from osgeo import ogr, gdal, osr
from multiprocessing import Pool
from rasterio.enums import Resampling

# Global variables
PRODES = '/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/PRODES/prodes_amazonia_raster_2000_2022_v20231109/prodes_amazonia_raster_2000_2022_v20231109.tif'
ecoregions_dir = '/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/Ecoregions/Brazilian_Amazon_Ecoregions'
deforested_ecoregions = '/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/Ecoregions/Deforested_Ecoregions'
ecoregions = [filename for filename in os.listdir(ecoregions_dir) if filename.endswith('.shp')]
APPEARS_dir = '/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/APPEARS/EVI/2015-2023-EVI'
csv_dir = f'/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/QGIS/Ecoregion_Analysis.csv'
working_dir = f'/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/QGIS'
years = [22]

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
    print(f'this is geo_transform_2: {geo_transform[2]}')
    print(f'this is geo_transform_5: {geo_transform[5]}')
    print(f'this is geo_transform_3: {geo_transform[3]}')
    
    lon = geo_transform[0] + col * geo_transform[1] + row * geo_transform[2]
    lat = geo_transform[3] + col * geo_transform[4] + row * geo_transform[5]
    return lat, lon

def crop_ecoregion(shp_path, ecoregion, year):
    if year < 10:
        prodes_yearly = f'200{year}_prodes.tif'
        gfc_yearly = f'200{year}_gfc.tif'
        gfc_ecoregion = f'gfc_{ecoregion}_200{year}.tif'
        prodes_ecoregion = f'prodes_{ecoregion}_200{year}.tif'
    else:
        prodes_yearly = f'20{year}_prodes.tif'
        gfc_yearly = f'20{year}_gfc.tif'
        gfc_ecoregion = f'gfc_{ecoregion}_20{year}.tif'
        prodes_ecoregion = f'prodes_{ecoregion}_20{year}.tif'

    prodes_path = os.path.join(deforested_ecoregions, prodes_ecoregion)
    gfc_path = os.path.join(deforested_ecoregions, gfc_ecoregion)

    if os.path.exists(prodes_path):
        print(f'{prodes_ecoregion} already exists.\n')
    else:
        temp_path = f'{ecoregion}_prodes_temp.tif'
        crop_to_ecoregion = f'gdalwarp -tr 0.0002689996094039614474 -0.0002690007898141364893 -cutline {shp_path} -crop_to_cutline -dstnodata 255 -of GTiff {prodes_yearly} {temp_path}'
        subprocess.run(crop_to_ecoregion, shell=True)

        lzw_compress = f'gdal_translate -co COMPRESS=LZW {temp_path} {prodes_path}'
        subprocess.run(lzw_compress, shell=True)
        os.remove(temp_path)

    if os.path.exists(gfc_path):
        print(f'{gfc_ecoregion} already exists.\n')
    else:
        temp_path = f'{ecoregion}_gfc_temp.tif'
        crop_to_ecoregion = f'gdalwarp -tr 0.0002689996094039614474 -0.0002690007898141364893 -cutline {shp_path} -crop_to_cutline -dstnodata 255 -of GTiff {gfc_yearly} {temp_path}'
        subprocess.run(crop_to_ecoregion, shell=True)

        lzw_compress = f'gdal_translate -co COMPRESS=LZW {temp_path} {gfc_path}'
        subprocess.run(lzw_compress, shell=True)
        os.remove(temp_path)

    return prodes_path, gfc_path

# Path to shared object (dynamically linked library)
lib = ctypes.CDLL('./libml_data_generator.so')

def analyze_ecoregion(ecoregion):
    # Path to ecoregion shapefile
    shp_path = os.path.join(ecoregions_dir, ecoregion)
    
    for year in years:
        # Creates deforestation data of ecoregion 
        prodes_path, gfc_path = crop_ecoregion(shp_path, ecoregion, year)

        # Extracting geotransform from PRODES deofrestation data
        prodes_geotransform = get_geotransform_from_file(prodes_path)
        prodes_x, prodes_pixel_width, _, prodes_y, _, prodes_pixel_height = prodes_geotransform
        print(type(prodes_x), type(prodes_pixel_width), type(prodes_y), type(prodes_pixel_height))
        print(f'PRODES top left coordinate (lat, lon): {prodes_y}, {prodes_x}\n')
        
        # Reading PRODES deforestation data
        with rasterio.open(prodes_path) as prodes:
                prodes_data = prodes.read(1)
        print(f'prodes_data type: {prodes_data.dtype}\n')
        print(f'prodes_data mean values: {np.mean(prodes_data)}')
        # uint8
        
        prodes_height, prodes_width = prodes_data.shape
        
        # Calculate coordinates of top right and bottom left corners
        eco_top_right_lon = prodes_x + prodes_width * prodes_pixel_width
        eco_top_right_lat = prodes_y
        eco_bottom_left_lon = prodes_x
        eco_bottom_left_lat = prodes_y + prodes_height * prodes_pixel_height

        print(f'{ecoregion} Top Right Corner Coordinates (lat, lon): ({eco_top_right_lat}, {eco_top_right_lon})')
        print(f'{ecoregion} Bottom Left Corner Coordinates (lat, lon): ({eco_bottom_left_lat}, {eco_bottom_left_lon})')
        
        # Reading Global Forest Change (GFC) deforestation data
        with rasterio.open(gfc_path) as gfc:
            gfc_data = gfc.read(1)
        print(f'gfc_data type: {gfc_data.dtype}\n')
        # uint8
        
        # Creating list of APPEARS tifs for the year sorted by day
        if year < 10:
            pattern = f'MOD13Q1.061__250m_16_days_EVI_doy200{year}*.tif'
        else:
            pattern = f'MOD13Q1.061__250m_16_days_EVI_doy20{year}*.tif'   
        tifs = glob.glob(f'{APPEARS_dir}/{pattern}')
        sorted_tifs = sorted(tifs, key=lambda x: int(x.split("_doy")[1][:7]))
        
        # Extracting APPEARS tif geotransform 
        appears_geotransform = get_geotransform_from_file (sorted_tifs[0])
        appears_x, appears_pixel_width, _, appears_y, _, appears_pixel_height = appears_geotransform
        print(type(appears_x), type(appears_pixel_width), type(appears_y), type(appears_pixel_height))
        
        # Calculate the pixel index for the top-left coordinate of the PRODES & GFC tif within the APPEARS tif
        eco_top_left_x, eco_top_left_y = latlon_to_pixel(prodes_y, prodes_x, appears_geotransform)
        print(f'{ecoregion} top left corner of index within APPEARS {eco_top_left_x}, {eco_top_left_y}')
        
        # Calculate the pixel index for the top-right coordinate of the PRODES & GFC tif within the APPEARS tif
        eco_top_right_x, eco_top_right_y = latlon_to_pixel(eco_top_right_lat, eco_top_right_lon, appears_geotransform)
        eco_top_right_x = int(eco_top_right_x)
        print(f'{ecoregion} top right corner of index within APPEARS {eco_top_right_x}, {eco_top_right_y}')
        
        # Calculate the pixel index for the bottom-left coordinate of the PRODES & GFC tif within the APPEARS tif
        eco_bottom_left_x, eco_bottom_left_y = latlon_to_pixel(eco_bottom_left_lat, eco_bottom_left_lon, appears_geotransform)
        eco_bottom_left_y = int(eco_bottom_left_y)
        print(f'{ecoregion} bottom left corner of index within APPEARS {eco_bottom_left_x}, {eco_bottom_left_y}\n')

        print(f'ECO_TOP_RIGHT_x data type: {type(eco_top_right_x)}')
        print(f'ECO_BOTTOM_LEFT_y data type: {type(eco_bottom_left_y)}')

        # Convert to int16 before passing to ctypes
        prodes_data_int16 = prodes_data.astype(np.int16)
        gfc_data_int16 = gfc_data.astype(np.int16)
        
        # Keepts track of day within the year
        day = 1
        
        # Boolean to check if an error occured reading the previous tif file
        error = False
        
        prev = None
        cur = None
        max_drop = None
        prodes_output_path = os.path.join(working_dir, f'PRODES_{ecoregion[:-4]}.csv')
        gfc_output_path = os.path.join(working_dir, f'GFC_{ecoregion[:-4]}.csv')

        # Create ML training data CSV's if they do not exists
        if os.path.exists(prodes_output_path):
            print(f'{prodes_output_path} already exists.')
        else:
            # Open a CSV 
            with open(prodes_output_path, 'w', newline='') as csv_file:
                # Create a CSV writer
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['EVI', 'Deforested'])
                
        if os.path.exists(gfc_output_path):
            print(f'{gfc_output_path} already exists.')
        else:
            # Open a CSV
            with open(gfc_output_path, 'w', newline='') as csv_file:
                # Create a CSV writer
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['EVI', 'Deforested'])
        
        # Convert geo transforms to NumPy arrays
        prodes_geotransform_array = np.array(prodes_geotransform, dtype=np.float64)
        appears_geotransform_array = np.array(appears_geotransform, dtype=np.float64)
        print(f'Prodes geotransform array data type: {prodes_geotransform_array.dtype}')
        print(f'APPEARS geotransform array data type: {appears_geotransform_array.dtype}')
        
        for i, image in enumerate(sorted_tifs): # Processes all APPEARS tif files
            print(day)
            try: # Reading image
                with rasterio.open(image) as appears:
                    appears_data = appears.read(1)
                print(f'original appears data dtype: {appears_data.dtype}')
                
                # Sets prev if it is day 1 or an error occured reading the previous tif file
                if prev is None or error: 
                    # Slicing APPEARS tif to ecoregion
                    prev = appears_data[eco_top_left_y:eco_bottom_left_y+1, eco_top_left_x:eco_top_right_x+1]
                    print(f'prev mean values: {np.mean(prev)}')
                    print(f'APPEARS slice dimensions: {prev.shape}')
                    print(f'prev data type: {prev.dtype}')
                    # int16
                    if day == 1:
                        max_drop = np.zeros(prev.shape)
                        print(f'max_drop data type: {max_drop.dtype}')
                        # float64
                else:
                    cur = appears_data[eco_top_left_y:eco_bottom_left_y+1, eco_top_left_x:eco_top_right_x+1]
                    cur_height, cur_width = cur.shape
                    print(f'Cur mean values: {np.mean(cur)}')
                    print(f'cur data type: {cur.dtype}')
                    # int16
                    
                    # convert to c_types
                    # uint8_array = ctypes.POINTER(ctypes.c_uint8)
                    int16_array = ctypes.POINTER(ctypes.c_int16)
                    float64_array = ctypes.POINTER(ctypes.c_double)
 
                    # Convert tif variables to ctypes
                    day_ptr = ctypes.c_int(day)
                    prev_ptr = prev.ctypes.data_as(int16_array)
                    cur_ptr = cur.ctypes.data_as(int16_array)
                    max_drop_ptr = max_drop.ctypes.data_as(float64_array)
                    prodes_data_ptr = prodes_data_int16.ctypes.data_as(int16_array)
                    gfc_data_ptr = gfc_data_int16.ctypes.data_as(int16_array)

                    # Convert geo transforms to ctypes
                    prodes_geotransform_ptr = prodes_geotransform_array.ctypes.data_as(float64_array)
                    appears_geotransform_ptr = appears_geotransform_array.ctypes.data_as(float64_array)

                    # Convert shape and path variables to ctypes
                    prodes_height_ptr = ctypes.c_int(prodes_height)
                    prodes_width_ptr = ctypes.c_int(prodes_width)
                    cur_height_ptr = ctypes.c_int(cur_height)
                    cur_width_ptr = ctypes.c_int(cur_width)
                    prodes_output_path_ptr = ctypes.c_char_p(prodes_output_path.encode('utf-8'))
                    gfc_output_path_ptr = ctypes.c_char_p(gfc_output_path.encode('utf-8'))
                    eco_top_left_x_ptr = ctypes.c_int(eco_top_left_x)
                    eco_top_left_y_ptr = ctypes.c_int(eco_top_left_y)
                    eco_top_right_x_ptr = ctypes.c_int(eco_top_right_x)
                    eco_bottom_left_y_ptr = ctypes.c_int(eco_bottom_left_y)
                    
                    
                    print('\nCalling c++ program')
                    
                    lib.ml_data_generator(day_ptr, prev_ptr, cur_ptr, max_drop_ptr, prodes_data_ptr,
                                         gfc_data_ptr, prodes_geotransform_ptr, appears_geotransform_ptr,
                                         prodes_height_ptr, prodes_width_ptr, cur_height_ptr, cur_width_ptr,
                                         prodes_output_path_ptr, gfc_output_path_ptr, eco_top_right_x_ptr,
                                         eco_bottom_left_y_ptr, eco_top_left_x_ptr, eco_top_left_y_ptr)
                    
                     
                    prev = cur
                error = False

            except Exception as e: # Error with image
                print(f"Error reading data from {image}: {e}")
                error = True
            
            day += 16 
            
    print(f'Processed {ecoregion}!')
            
