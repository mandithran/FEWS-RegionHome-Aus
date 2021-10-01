"""
extractMeshSliceWaterLevels.py
Author: Mandi Thran
Date: 01/10/21

DESCRIPTON:
This script extracts a mesh slice from the BoM National Storm Surge system.
"""

# Modules
import os
import xarray as xr
import pandas as pd

# Paths
# Region Home
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
# Path where the example forecast is held
ncPath = os.path.join(regionHome,"Data\\waterLevs\\nss\\example")
# Example forecast file (from the BoM)
ifile = os.path.join(ncPath,"IDZ00154_StormSurge_national_2020020200.nc")

# Load netCDF file with xarray
ds = xr.open_dataset(ifile)
# Prints the variables and attributes of the dataset
print(ds.keys())
# Slice mesh at a given time step (doesn't have to be 100 necessarily)
ds = ds.isel({"time":100})
# Generate a new dataframe from the dataset for exporting
df = pd.DataFrame({"lon":ds["lon"].values,
                   "lat":ds["lat"].values,
                   "surge":ds["surge"].values})

# Export dataframe to csv file, which can be loaded
# as a delimited text layer into QGIS
df.to_csv(os.path.join(ncPath,"surge_samplemesh.csv"),index=False)
