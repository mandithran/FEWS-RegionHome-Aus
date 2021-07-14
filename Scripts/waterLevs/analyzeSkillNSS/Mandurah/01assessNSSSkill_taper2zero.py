####################### Modules #######################
import os
import pandas as pd
import pytz # for handling time zones
from datetime import datetime, timedelta
import xarray as xr
import re
import numpy as np

####################### Parameters #######################
siteName = "Mandurah"
# Location of the NSS output node to compare (closes to observation gauge)
# Sydney gauge: 
#lat = -33.819923
#lon = 151.27188
# Mandurah gauge: 
# About 2 km away from actual gauge, BVD, Cape Bouvard
# BVD Gauge
#lat = -32.593870000000003
#lon = 115.629069999999999
# Mandurah Gauge
lat = -32.508727999999998
lon = 115.704099999999997
timezoneUTC = pytz.utc
forecastPeriodStart = timezoneUTC.localize(datetime(year=2020,month=1,day=1)) 
forecastPeriodEnd = forecastPeriodStart + timedelta(days=366) # leap year!
#forecastPeriodEnd = forecastPeriodStart + timedelta(days=366) # leap year!

datumCorrection = .54 # Observations are in ZFD, which needs to be converted to AHD

forecastInterval = 6 # hours
leadtimes = [0,6,12,24,48,72,96,120,144,162] # in hours


####################### Paths and parameters #######################
# Tide predictions In UTC, as per Mike's email
# Did a sanity check plot on observed water levels vs, predicted tides
# Obs vs pred are in sync
dataDir = 'C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\waterLevs\\Mandurah'
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs\\analyzeSkillNSS\\mandurah"
oDir = os.path.join(workDir,"ofiles")


####################### Local functions #######################
def parseTimeNSS(string=None):
    dateTimeStr = re.split("_", string)[3].split(".")[0]
    dateTime = datetime.strptime(dateTimeStr, '%Y%m%d%H')
    # Datetime for NSS is in UTC
    dateTime = timezoneUTC.localize(dateTime)
    return dateTime



############## Water Levels and Non-tidal residuals ##############
# ==== Load astronomical tide predictions ==== #
ifile = os.path.join(dataDir,'tidePredictions',
                    'Mandurah_Marina_2019-2022_15min_Harmonic.csv')
dft = pd.read_csv(ifile)
# Convert datetime column to datetime objects and set as index
dft.index = pd.to_datetime(dft['time_utc'], utc=True)
dft = dft.drop('time_utc',1)
# Rename column for readability
dft.columns = ["tide_m"]



# ==== Load observed water level data (Mandurah) ==== #
# Provided by Mike Cuttler
# But can be found here: https://www.transport.wa.gov.au/imarine/download-tide-wave-data.asp
# On checking thorough checking, these datasets are exactly the same for the relevant period of 2020.
# Date/time in AWST for this file
ifile = os.path.join(dataDir,'observations',
                    'MAN2020.txt')
df_wl = pd.read_csv(ifile)
# Drop metadata rows (for some reason, skiprows in read_csv doesn't work)
df_wl = df_wl.drop(df_wl.index[0:16])
# Rename columns
df_wl.columns = ['h_cm','datetime']
# Convert cm to m
df_wl['h_cm'] = pd.to_numeric(df_wl["h_cm"], downcast="float")
df_wl['h_meters'] = df_wl['h_cm']/100.
# Datum correction
df_wl['h_meters'] = df_wl['h_meters'] - datumCorrection
df_wl = df_wl.drop('h_cm',1)
# Convert datetime column to datetime objects and set as index
df_wl.index = pd.to_datetime(df_wl['datetime'], format="%Y%m%d.%H%M/")
# Convert AWST to UTC
awst = pytz.timezone("Australia/Perth")
df_wl.index = df_wl.index.tz_localize(awst).tz_convert(pytz.utc)
df_wl = df_wl.drop('datetime',1)
# Rename column for readability
df_wl.columns = ["wl_obs"]



# ==== Merge the two dataframes ==== #
# Merge the two dfs on their indeces since they have the same temporal resolution
# Inner merge... we want to discard anything where there is not a value for
# both the observed and predicted.
df = pd.merge(dft, df_wl, how="inner", left_index=True, right_index=True)


# ==== Subtract astronomical tide from observed water level to get non-tidal residuals ==== #
df["nts"] = df["wl_obs"] - df["tide_m"]
df.to_csv(os.path.join(oDir,"WL-NTR-obs_%s_taper.csv" % siteName))


####################### NSS #######################
# Note there was a bug in the NSS from at least before July 10, 2020
# This caused a time lag of the surge signal by 48 hrs
# Paths
wlDir = "J:\\Coastal\\Data\\Tide\\WL Forecast\\BOM Storm Surge\\raw\\corrected"
# Load list of files - NSS Forecast
filesList = []
# We only want the netcdf files
for fi in os.listdir(wlDir):
    if fi.endswith(".nc"):
        filesList.append(fi)
# Add these to a dataframe
df_files = pd.DataFrame(filesList,columns=['fileName'])
# Parse the forecast start time from filename, and add as a new column
df_files['fileDateTime'] = [parseTimeNSS(str(row)) for row in df_files['fileName']]
# Make datetime the new index for this df
df_files = df_files.set_index(["fileDateTime"])
# Keep only files for certain time period (2020)
df_files = df_files[df_files.index>=forecastPeriodStart]
df_files = df_files[df_files.index<forecastPeriodEnd]


counter = 1
df_for = pd.DataFrame(columns=['surge','tide',"twl_for",'leadtime_hrs','IntervalStartTime'])
df_continuous = pd.DataFrame(['surge','tide'])
for fi in df_files['fileName']:
    try:
        print("Processing file: %s" % fi)
        print("File number: %s " % str(counter))
        # Load forecast file
        ds = xr.open_dataset(os.path.join(wlDir,fi))
        # Parse time from file
        dateTime = parseTimeNSS(string=fi)
        # Keep only surge and tide components of forecast (assume here that surge = non-tidal residuals)
        ds = ds[['time','surge','tide']]
        # Keep only the point to compare to (nearest point to actual gauge where
        # observations came from)
        ds = ds.where((ds.lat==lat) & (ds.lon==lon), drop=True).squeeze()
        # Append these vars to df
        df_file = ds.to_dataframe()
        df_file = df_file.drop(["lat","lon"],axis=1)
        # Make dataset timezone aware
        df_file = df_file.tz_localize(timezoneUTC)
        # Append this with continuous dataframe
        #===== Add a 4-7 day period where you taper the surge component to 0 over 2 hours ====#
        # Generate a new time series based on last value of the forecast
        delta_t = df_file.index[1]-df_file.index[0]
        lastTimeStep = df_file.index[-1] 
        taperStart = lastTimeStep + delta_t
        taperDuration = timedelta(hours=2)
        taperEnd = lastTimeStep+taperDuration
        seriesTapered_time = pd.date_range(start=taperStart,
                        end=taperEnd,
                        freq=delta_t)
        tapered_df = pd.DataFrame({"Datetime_gmt":seriesTapered_time})
        tapered_df['surge'] = np.nan
        # Set beginning of the tapered df to the last value of the forecast
        tapered_df.iloc[0, tapered_df.columns.get_loc('surge')] = df_file.surge[-1]
        # Set the end of the tapered df to zero
        tapered_df.iloc[-1, tapered_df.columns.get_loc('surge')] = 0.
        tapered_df = tapered_df.set_index('Datetime_gmt')
        tapered_df = tapered_df.interpolate(method='linear')
        flatStart = taperEnd+delta_t
        flatEnd = lastTimeStep + timedelta(days=4)
        seriesFlat = pd.date_range(start=flatStart,
                        end=flatEnd,
                        freq=delta_t)
        df_flat = pd.DataFrame({"Datetime_gmt":seriesFlat,
                                'surge':0}).set_index("Datetime_gmt")
        # Concatenate all of these together
        df_file = pd.concat([df_file,tapered_df,df_flat])
        df_file['fileName'] = fi
        df_file['fileDatetime'] = dateTime
        df_continuous = df_continuous.append(df_file)
        for leadTime in leadtimes:
            print("Leadtime: %s" % leadTime)
            # Drop the 'fileName' and 'fileDatetime' columns
            df_nss = df_file.drop(['fileDatetime'],axis=1).drop(['fileName'],axis=1)
            # Select correct time window to compare to observed water levels
            # Based on lead time and forecast interval
            # Basically chops up each file into 6 hour windows,
            # Assigns the lead time of that window relative to the start time in the file
            # Then concatenates each of the windows to a larger dataframe
            # This then allows for a "continuous" time series of, for example, the 6-hour lead time windows
            startTime = dateTime + timedelta(hours=leadTime)
            endTime = startTime + timedelta(hours=forecastInterval)
            #print("startTime, endTime")
            #print(startTime, endTime)
            df_nss = df_nss[df_nss.index>=startTime] 
            df_nss = df_nss[df_nss.index<endTime]
            # Compute tide+surge (forecast, exclude setup because XBeach handles it)
            #df_nss["twl_for"] = df_nss["surge"] + df_nss["tide"]
            # Interpolate surge at same temporal resolution as the observations
            # 15 min intervals, starting at df beginning
            upsampled = df_nss.resample('30T', origin=df_nss.index[0]).asfreq()
            df_nss = upsampled.interpolate(method='linear')
            # Assign lead time
            df_nss['leadtime_hrs'] = leadTime
            # Record start time for time interval being tested
            df_nss['IntervalStartTime'] = startTime
            df_nss['fileName'] = fi
            df_nss['fileDatetime'] = dateTime
            # Append to df containing all NSS forecasts\
            # The result is a dataframe with forecasts all stitched together
            # as one continuous timeseries.
            # This should result in one "continuous" timeseries per lead time
            df_for = df_for.append(df_nss)
        print("File processed")
        counter += 1
    except:
        # TODO: change back to "pass"
        pass

# Merge NSS forecast with non-tidal residual observations
df = pd.merge(df, df_for, how="inner", left_index=True, right_index=True)

# Send all observations and predictions, with corresponding lead times, to a csv file
df.to_csv(os.path.join(oDir,"WL-NTR-LeadTimeSeries_%s_2020_taper.csv" % siteName))

# Send continuous time series forecasts to a csv file
df_continuous.to_csv(os.path.join(oDir,"WL-NTR-ContinuousTimeSeries_%s_2020_taper.csv" % siteName))