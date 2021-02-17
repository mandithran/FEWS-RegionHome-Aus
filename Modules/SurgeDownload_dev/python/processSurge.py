# The BOM national storm surge system has a forecast horizon of 3 days.

# Water levels should start one day before desired start of
# forecast window to allow for spin-up of xbeach

#TODO: Turn coordinates into dimensions

# =================== Import Modules =================== #
import netCDF4 as nc
import numpy as np
import os
import warnings
import xarray as xr
import pandas as pd
import re
warnings.filterwarnings("ignore", category=DeprecationWarning)

# =================== Variables =================== #
# Relative to Region Home, since that is where executable is called from
importDir = ".\Import\AusSurge"
fname = 'IDZ00154_StormSurge_national_2021021118.nc'
site = "Narrabeen"

# =================== Paths =================== #
ifile = os.path.join(importDir,fname)

# Lat/lon - for selecting the best point for the timeseries
# These points need to be determined ahead of time by looking at nc file
d = {"Narrabeen": {'lat': -33.71775, 'lon': 151.32191},
     "Mandurah": {'lat': -32.508728, 'lon': 115.72912}}

# Take a look at existing coordinates, dimensions, and variables
ds = xr.open_dataset(ifile)
print("NetCDF file metadata:")
print(ds.keys)

# ds.keys will reveal that the NetCDF file does not have lat/lon dimensions - it has a "point" and "time" dimensions
# These "point" dimensions are essentially the index of a given point
# The "point dimension" has the same shape as the lat and lon fields
# This is because this is not a regular grid; each point has a unique lat, lon value
# The following will return the index that matches the lat/lon point of interest
# This index allows for selection of subsets of the xarray
df = pd.DataFrame({"lon":ds.coords['lon'].values,"lat":ds.coords['lat'].values})
ind = df[(df['lon']==d[site]["lon"]) & 
        (df['lat']==d[site]["lat"])].index

# Select surge timeseries for the point of interest
surge = ds.surge[ind].values

# Create new pandas df to export timeseries
dfOut = pd.DataFrame({"time":ds.coords['time'].values,
                    "surge (m)":surge[0]
                    })
                    
# File name based on site and date time given in original nc file
dateTime = re.split("[_.]", fname)[3]
ofname = "nss_%s_%s.csv" % (site, dateTime)
dfOut.to_csv(os.path.join(importDir,ofname),index=False)