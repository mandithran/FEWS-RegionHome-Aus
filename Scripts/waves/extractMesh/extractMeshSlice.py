"""
extractMeshSlice.py
Author: Mandi Thran
Date: 01/10/21

DESCRIPTION:
This script extracts a mesh slice from the BoM nearshore wave forecasting system. 
"""

# Modules
import os
import xarray as xr
import pandas as pd

# Paths
# Region Home
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
# Path where the example forecast is held
ncPath = os.path.join(regionHome,"Data\\Waves\\Sydney\\auswave\\example")
# Example forecast file (from the BoM)
ifile = os.path.join(ncPath,"SYD.msh.20200208T0000Z.nc")

# Load netCDF file with xarray
ds = xr.open_dataset(ifile)
# Slice mesh at a given time step (doesn't have to be 100 necessarily)
ds = ds.isel({"time":100})
# Prints the variables and attributes of the dataset
print(ds.keys())
# Generate a new dataframe from the dataset for exporting
df = pd.DataFrame({"lon":ds["longitude"].values,
                   "lat":ds["latitude"].values,
                   "dir":ds["dir"].values,
                   "hs":ds["hs"].values})

# Export dataframe to csv file, which can be loaded
# as a delimited text layer into QGIS
df.to_csv(os.path.join(ncPath,"Syd_samplemesh.csv"),index=False)
