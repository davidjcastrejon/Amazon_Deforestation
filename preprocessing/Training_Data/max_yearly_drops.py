import os
import glob
import numpy as np
from osgeo import gdal
import subprocess
from multiprocessing import Pool
import rasterio
from rasterio.merge import merge
from rasterio.enums import Resampling

appears_dir = '/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/APPEARS/EVI/2015-2023-EVI'

def merge_tiles(year):
    # Input directory containing the TIFF files
    if year < 10:
        input_directory = f'/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/GFC/GFC_Tiles/200{year}_GFC_tiles'
        output_file = f'/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/QGIS/200{year}_gfc.tif'
    else:
        input_directory = f'/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/GFC/GFC_Tiles/20{year}_GFC_tiles'
        output_file = f'/Users/davidcastrejon/Documents/Amazon_Rainforest/Data/QGIS/20{year}_gfc.tif'

    # Returns if output file already exists
    if os.path.exists(output_file):
        print(f'The GFC output file for year {year} already exists. Aborting.\n')
        return
    
    # Get a list of all TIFF files in the directory
    input_files = glob.glob(os.path.join(input_directory, '*.tif'))

    # Check if there are any TIFF files
    if not input_files:
        print(f'No TIFF files found in the specified directory.\n')
        return

    # Read all input files
    src_files_to_mosaic = [rasterio.open(file) for file in input_files]

    # Merge files
    mosaic, out_trans = merge(src_files_to_mosaic, resampling=Resampling.nearest)

    # Update metadata of the output file
    out_meta = src_files_to_mosaic[0].meta.copy()
    out_meta.update({
        "driver": "GTiff", 
        "height": mosaic.shape[1], 
        "width": mosaic.shape[2], 
        "transform": out_trans, 
        "dtype": src_files_to_mosaic[0].dtypes[0],
        "compress": "lzw"
    })
    
    # Write the mosaic to the output file
    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(mosaic)



def subtract_tifs(sorted_tifs):
    filename = os.path.basename(sorted_tifs[0])
    year = int(filename.split("_doy")[1][:4])
    print(year)

    prev = None
    cur = None
    mask = None
    max_drops = None
    day = 1

    for appears_tif in sorted_tifs:
        print(day)
        if prev is None:
            try:
                with rasterio.open(appears_tif) as apps:
                    prev = apps.read(1)
                if day == 1:
                    max_drops = np.full(prev.shape, 255, dtype=np.float32)
                if mask is None:
                    mask = (prev != -3000)
            except Exception as e:
                print(f'Could not open {appears_tif}')
                prev = None
        else:
            try:
                with rasterio.open(appears_tif) as apps:
                    cur = apps.read(1)
                diff = np.where(mask, cur - prev, 255)
                max_drops[mask] = np.where(diff < max_drops, diff, max_drops)[mask]
            except Exception as e:
                print(f'Could not open {appears_tif}')
                cur = None
                prev = None
        print(np.mean(max_drops[mask]))
        day += 16

    print(f'Minimum value for {year}: {np.min(max_drops[mask])}')
    print(f'Maximum value for {year}: {np.max(max_drops[mask])}')

    print(year)
    print(f'Finished making max_drops for year {year}!')
    output_raster = f'{year}_max_drops.tif'

    output_meta = None
    geo = None
    day = 1
    for appears_tif in sorted_tifs:
        try:
            with rasterio.open(appears_tif) as apps:
                cur = apps.read(1)
            output_meta = apps.meta.copy()
            geo = apps.transform
            break
        except Exception as e:
            print(f'Could not read APPEARS after all calculations for day {day} of year {year}.\n')
    
    output_meta.update({
        "driver": "GTiff",
        "height": max_drops.shape[0],  
        "width": max_drops.shape[1],   
        "transform": geo,
        "dtype": max_drops.dtype,
        "compress": "lzw",
        "nodata": 255
    })

    with rasterio.open(output_raster, "w", **output_meta) as dest:
        dest.write(max_drops, 1) 

if __name__ == '__main__':
    all_tifs = []
    for year in range(17, 18):
        # Create sorted list of appears tifs for the year
        if year < 10:
            pattern = f'MOD13Q1.061__250m_16_days_EVI_doy200{year}*.tif'
        else:
            pattern = f'MOD13Q1.061__250m_16_days_EVI_doy20{year}*.tif'
        appears_tifs = glob.glob(f'{appears_dir}/{pattern}')
        sorted_tifs = sorted(appears_tifs, key=lambda x: int(x.split("_doy")[1][:7]))
        all_tifs.append(sorted_tifs)

    print('Passed in the list!')
    with Pool() as pool:
        pool.map(subtract_tifs, all_tifs)

    








            



