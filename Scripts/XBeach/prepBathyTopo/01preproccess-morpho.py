"""
01preprocess-morpho.py
Author: Mandi Thran
Date: 01/10/21

DESCRIPTION:
This script takes XBeach output and converts it to an xyz (.csv) file. 
"""

import os
import xarray as xr
import numpy as np
import pandas as pd


#============== Paths / inputs ==============#
regionHome = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus"
siteName = "Narrabeen"
gridsDir = os.path.join(regionHome, "Data\\Grids\\%s\\xb-ready-files\\lowres-testing" % siteName)
depDir = os.path.join(regionHome, "Data\\TopoBathy\\%s\\prep\\xb-ready-files\\lowres-testing" % siteName)
xBeachNC = os.path.join(regionHome, 
                        "Data\\TopoBathy\\Narrabeen\\prep\\ofiles",
                        "xbNarra_zb_2021_testing.nc")


#============== Load XBeach mesh NC file ==============#
# Load XBeach mesh as geodataframe - netCDF format
ds = xr.open_dataset(xBeachNC)
ncolXB = ds.ncols
nrowXB = ds.nrows

xx = ds["globalx"][:,:].values
yy = ds["globaly"][:,:].values
zz = ds["zb"][:,:].values

np.savetxt(os.path.join(gridsDir,"x_testing.grd"), xx, delimiter="  ", fmt='%4d')
np.savetxt(os.path.join(gridsDir,"y_testing.grd"), yy, delimiter="  ", fmt='%4d')
np.savetxt(os.path.join(depDir,"bed_testing.DEP"), zz, delimiter="  ", fmt='%1.2f')