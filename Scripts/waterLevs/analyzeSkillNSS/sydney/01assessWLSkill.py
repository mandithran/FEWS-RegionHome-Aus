####################### Modules #######################
import os
import pandas as pd
import pytz # for handling time zones
from datetime import datetime, timedelta
import xarray as xr
import re


####################### Parameters #######################
siteName = "Narrabeen"
# Location of the NSS output node to compare (closes to observation gauge)
# Sydney gauge: 
lat = -33.819923
lon = 151.27188
# Mandurah gauge: 
#lat = -32.593870000000003
#lon = 115.629069999999999


datumCorrection = .925 # Observations are in ZFD, which needs to be converted to AHD
forecastInterval = 6 # hours
leadtimes = [0,6,12,24,48,66] # in hours
# Tide predictions In GMT
ifile = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Data\\Tides\\Sydney\\processed\\SydneyTidesGMT.csv"
timezoneUTC = pytz.utc

####################### Paths #######################
workDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs\\analyzeSkillNSS\\sydney"
oDir = os.path.join(workDir,"ofiles")


####################### Local functions #######################
def parseTimeNSS(string=None):
    dateTimeStr = re.split("_", string)[3].split(".")[0]
    dateTime = datetime.strptime(dateTimeStr, '%Y%m%d%H')
    dateTime = timezoneUTC.localize(dateTime)
    return dateTime

############## Water Levels and Non-tidal residuals ##############

# ==== Load astronomical tide predictions ==== #
dft = pd.read_csv(ifile, names=['datetime_gmt','tide_m'], header=0)
dft['datetime_gmt'] = pd.to_datetime(dft['datetime_gmt'], format="%d-%m-%Y %H:%M")
dft.index=dft['datetime_gmt']
dft = dft.drop(columns=['datetime_gmt'])
dft = dft.tz_localize(timezoneUTC)


# ==== Load observed water level data (HMAS Penguin) ==== #
# Input file with observations, from Manly hydraulics laboratory
# Date/time in AEST for this file
ifile = "observedWL_Station-213470_2020.csv"
# Read above file 
df_wl = pd.read_csv(os.path.join(workDir,"ifiles/%s" % ifile))
# Combine date/time into one column
df_wl["datetime"] = df_wl["Date"] + " " + df_wl["Time"]
# Convert date time string to date time object
df_wl["datetime"] = pd.to_datetime(df_wl["datetime"], format="%d/%m/%Y %H:%M:%S")
# Remove other date/time columns and set datetime column as dataframe index
df_wl = df_wl.drop(["Date", "Time","State of value"],1)
df_wl = df_wl.set_index(["datetime"])
# Rename column for readability
df_wl.columns = ["wl_obs"]
# Subtract 10 hours from time series (convert AEST to UTC)
# This is done manually rather than using the timezone-aware Australia/Sydney zone in pytz
# pytz assumes there should be a daylight savings correction and throws an error for "non-existent times" being present
# AEST does not have a correction for daylight savings, so no need to account for "double times" or "non-existent" times
df_wl.index = df_wl.index - timedelta(hours=int(10))
# Set time zone (now UTC)
df_wl= df_wl.tz_localize(timezoneUTC)

# ==== Datum correction ==== #
df_wl["wl_obs"] = df_wl["wl_obs"]-datumCorrection

# ==== Merge the two dataframes ==== #
# Merge the two dfs on their indeces since they have the same temporal resolution
# Inner merge... we want to discard anything where there is not a value for
# both the observed and predicted.
df = pd.merge(dft, df_wl, how="inner", left_index=True, right_index=True)

# ==== Subtract astronomical tide from observed water level to get non-tidal residuals ==== #
df["nts"] = df["wl_obs"] - df["tide_m"]
df.to_csv(os.path.join(oDir,"WL-NTR-obs_%s.csv" % siteName))


####################### NSS #######################
# Note there was a bug in the NSS from at least before July 10, 2020
# This caused a time lag of the surge signal by 48 hrs
# Paths
wlDir = "J:\\Coastal\\Data\\Tide\\WL_Forecast\\BOM_Storm_Surge\\raw\\corrected"
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
forecastPeriodStart = timezoneUTC.localize(datetime(year=2020,month=1,day=1)) 
forecastPeriodEnd = forecastPeriodStart + timedelta(days=366) # leap year!
df_files = df_files[df_files.index>=forecastPeriodStart]
df_files = df_files[df_files.index<forecastPeriodEnd]

counter = 1
df_for = pd.DataFrame(columns=['surge','tide',"twl_for",'leadtime_hrs','IntervalStartTime'])
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
        for leadTime in leadtimes:
            # Append these vars to df
            df_nss = ds.to_dataframe()
            df_nss = df_nss.drop(["lat","lon"],axis=1)
            # Make dataset timezone aware
            df_nss = df_nss.tz_localize(timezoneUTC)
            print("Leadtime: %s" % leadTime)
            # Select correct time window to compare to observed water levels
            # Based on lead time and forecast interval
            # Basically chops up each file into 6 hour windows,
            # Assigns the lead time of that window relative to the start time in the file
            # Then concatenates each of the windows to a larger dataframe
            # This then allows for a "continuous" time series of, for example, the 6-hour lead time windows
            startTime = dateTime + timedelta(hours=leadTime)
            endTime = startTime + timedelta(hours=forecastInterval)
            df_nss = df_nss[df_nss.index>=startTime] 
            df_nss = df_nss[df_nss.index<endTime]
            # Compute tide+surge (forecast, exclude setup because XBeach handles it)
            df_nss["twl_for"] = df_nss["surge"] + df_nss["tide"]
            # Interpolate surge at same temporal resolution as the observations
            # 15 min intervals, starting at df beginning
            upsampled = df_nss.resample('30T', origin=df_nss.index[0]).asfreq()
            df_nss = upsampled.interpolate(method='linear')
            # Assign lead time
            df_nss['leadtime_hrs'] = leadTime
            # Record start time for time interval being tested
            df_nss['IntervalStartTime'] = startTime
            # Append to df containing all NSS forecasts\
            # The result is a dataframe with forecasts all stitched together
            # as one continuous timeseries.
            # This should result in one continuous timeseries per lead time
            df_for = df_for.append(df_nss)
        print("File processed")
        counter += 1
    except:
        pass


# Merge NSS forecast with non-tidal residual observations
df = pd.merge(df, df_for, how="inner", left_index=True, right_index=True)

# Send all observations and predictions, with corresponding lead times, to a csv file
df.to_csv(os.path.join(oDir,"WL-NTR-obsAndpred_%s_2020_NoNTS.csv" % siteName))
