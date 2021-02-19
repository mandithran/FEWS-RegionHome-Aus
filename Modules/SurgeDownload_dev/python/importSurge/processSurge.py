# The BOM national storm surge system has a forecast horizon of 3 days.

# Water levels should start one day before desired start of
# forecast window to allow for spin-up of xbeach

# =================== System packages =================== #
import os
import warnings
import glob
import re
import ntpath

# =================== Import Modules =================== #
import netCDF4 as nc
import numpy as np
import xarray as xr
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)


def getMostRecentFile(importDir=None):
        # glob.glob returns all paths matching the pattern.
        nc_files = list(glob.glob(os.path.join(importDir, '*.nc*')))
        mod_dates = [os.path.getmtime(f) for f in nc_files]
        # sort by mod_dates.
        file_date = zip(nc_files, mod_dates)
        sort_date = sorted(file_date, key=lambda d: d[1], reverse=True)
        newest_file_path = sort_date[0][0]
        newest_file_name = ntpath.basename(newest_file_path)
        return newest_file_name

def processSurge_nc(importDir=None, fname=None, 
                    site=None):
                    
        # =================== Paths =================== #
        ifile = os.path.join(importDir,fname)

        # Lat/lon - for selecting the best point for the timeseries
        # These points need to be determined ahead of time by looking at nc file
        d = {"Narrabeen": {'lat': -33.71775, 'lon': 151.32191},
        "Mandurah": {'lat': -32.508728, 'lon': 115.72912}}

        # Load dataset
        ds = xr.open_dataset(ifile)

        # Take a look at existing coordinates, dimensions, and variables
        # if verbose mode is specified
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

        # Create new pandas df
        dfOut = pd.DataFrame({"Datetime":ds.coords['time'].values,
                        "surge (m)":surge[0]
                        })

        # Add 12-hour spin-up timeseries that retains the first value
        # of the surge forecast
        dt_delta = dfOut.Datetime[1]-dfOut.Datetime[0]
        spinUpTime = np.timedelta64(12,"h") # argument in hours
        spinUpEndTime = dfOut.Datetime[0]
        spinUpStartTime = spinUpEndTime-(spinUpTime)
        spinUp_series = pd.date_range(start=spinUpStartTime,
                                end=spinUpEndTime,
                                freq=dt_delta)
        spinUp_df = pd.DataFrame({"Datetime":spinUp_series,
                                "surge (m)":dfOut["surge (m)"][0]
                                }).set_index("Datetime")

        # Concatenate spin-up timeseries with real timeseries
        dfOut = dfOut.set_index("Datetime")
        dfOut = pd.concat([spinUp_df,dfOut])

        # File name based on site and date time given in original nc file
        dateTime = re.split("[_.]", fname)[3]
        ofname = "nss_%s_%s.csv" % (site, dateTime)
        ofPath = os.path.join(importDir,ofname)
        dfOut.to_csv(ofPath)

        return ofPath 