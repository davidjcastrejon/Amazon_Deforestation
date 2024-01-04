#!/usr/bin/python3

from multiprocessing import Pool
import sys
import numpy as np
from PIL import Image
import os
import tifffile
import subprocess
import json

Image.MAX_IMAGE_PIXELS = 9331200


def generate(f):
    

    try:
        tiff_values = tifffile.imread(f)
    except Exception as e:
        print(e)
        return;
    value_array = np.array(tiff_values)
    result = subprocess.run("./process", input=bytes(value_array), capture_output=True)

    array = np.frombuffer(result.stdout, dtype=np.uint16)
    resize = np.resize(array,(len(value_array),len(value_array[0]),3))
    image = Image.fromarray(resize.astype(np.uint8))
    image.save("PNGS/EVI_" + f[f.index("doy"):f.index("doy")+10] + ".png")

if __name__ == '__main__':
    directory = 'inputs'
    files = []
    # iterate over files in
    # that directory
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f):
            files.append(f)
    pool = Pool(processes=20)                         # Create a multiprocessing Pool
    pool.map(generate, files)  # process data_inputs iterable with pool

