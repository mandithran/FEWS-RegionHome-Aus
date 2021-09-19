####################### Modules #######################
import os
import pandas as pd
import pytz # for handling time zones
from datetime import datetime, timedelta
import xarray as xr
import re
from sklearn.metrics import mean_squared_error, r2_score

# TODO:
# Need to evaluate:
# - offshore Sydney observations
    # - for different parameters
    # - at different lead times
# - nearshore observations (Narra) - indicates how well wave transformation to nearshore is handled

####################### Parameters #######################
siteName = "Narrabeen"
# Location of the Auswave output node to compare (closest to observation gauge)
# SYDDOW offshore wave buoy is at -33.771667, 151.408611
# Source: https://s3-ap-southeast-2.amazonaws.com/www-data.manly.hydraulics.works/www/stations/wave/sydney_LocationHistory.pdf
lat = -33.762729999999998
lon = 151.403240000000011
forecastInterval = 12 # hours
leadtimes = [12,24,48,72,96,120,144,168] # in hours
timezoneUTC = pytz.utc
forecastPeriodStart = timezoneUTC.localize(datetime(year=2020,month=1,day=1)) 
forecastPeriodEnd = forecastPeriodStart + timedelta(days=366) # leap year!


####################### Paths #######################
workDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves"
oDir = os.path.join(workDir,"ofiles")


####################### Local functions #######################
def parseTimeAusWv(string=None):
    dateTimeStr = re.split("msh.", string)[1].split("Z.nc")[0]
    dateTime = datetime.strptime(dateTimeStr, '%Y%m%dT%H%M')
    dateTime = timezoneUTC.localize(dateTime)
    return dateTime


############## Wave observations ##############
# ==== Load wave observatins ==== #
# Waves in AEST
ifile = os.path.join(workDir,"ifiles\\%s" % "offshoreSydneyWaveObs.csv")
dfw_obs = pd.read_csv(ifile)
dfw_obs.columns = ['datetime','hrms','hs','h10','hmax','tz','tp','dir','nan']
# Keep only the parameters of interest
dfw_obs = dfw_obs[['datetime','hs','tp','dir']]
# Convert date time string to date time object
dfw_obs["datetime"] = pd.to_datetime(dfw_obs["datetime"], format="%d/%m/%Y %H:%M")
# Set datetime as index
dfw_obs.index = dfw_obs['datetime']
dfw_obs = dfw_obs.drop('datetime',axis=1)
# Subtract 10 hours from time series (convert AEST to UTC)
dfw_obs.index = dfw_obs.index - timedelta(hours=int(10))
# Set time zone (now UTC)
dfw_obs = dfw_obs.tz_localize(timezoneUTC)
# Rename columns for readability
dfw_obs.columns = ['hs_obs','tp_obs','dir_obs']


####################### Auswave #######################
waveDirectory = "J:\\Coastal\\Data\\Wave\\Forecast\\BOM products\\BOM nearshore wave transformation tool\\raw\\Mesh"
# Load list of files - NSS Forecast
filesList = []
# We only want the netcdf files
for fi in os.listdir(waveDirectory):
    if fi.endswith(".nc"):
        filesList.append(fi)
# Add these to a dataframe
df_files = pd.DataFrame(filesList,columns=['fileName'])
# Parse the forecast start time from filename, and add as a new column
df_files['fileDateTime'] = [parseTimeAusWv(str(row)) for row in df_files['fileName']]
# Make datetime the new index for this df
df_files = df_files.set_index(["fileDateTime"])
# Keep only files for certain time period (2020)
df_files = df_files[df_files.index>=forecastPeriodStart]
df_files = df_files[df_files.index<forecastPeriodEnd]
counter = 1
df_for = pd.DataFrame(columns=['hs_pred','tp_pred','dir_pred'])


for fi in df_files['fileName']:
    print("Processing file: %s" % fi)
    print("File number: %s " % str(counter))
    # Load forecast file
    ds = xr.open_dataset(os.path.join(waveDirectory,fi))
    # Parse time from file
    dateTime = parseTimeAusWv(string=fi)
    print(dateTime)
    # Keep only surge and tide components of forecast (assume here that surge = non-tidal residuals)
    ds = ds[['dir','hs','tp','latitude','longitude']]
    # Keep only the point to compare to (nearest point to actual gauge where
    # observations came from)
    ds = ds.where((ds.latitude==lat) & (ds.longitude==lon), drop=True).squeeze()
    for leadTime in leadtimes:
        # Append these vars to df
        df_sub = ds.to_dataframe()
        df_sub = df_sub.drop(["latitude","longitude"],axis=1)
        df_sub.columns = ['dir_pred','hs_pred','tp_pred']
        # Make dataset timezone aware
        df_sub = df_sub.tz_localize(timezoneUTC)
        print("Leadtime: %s" % leadTime)
        # Select correct time window to compare to observed waves
        # Based on lead time and forecast interval
        startTime = dateTime+(timedelta(hours=leadTime)-timedelta(hours=forecastInterval))
        endTime = (dateTime+(timedelta(hours=leadTime)))
        df_sub = df_sub[df_sub.index>=startTime] 
        df_sub = df_sub[df_sub.index<endTime]
        # Interpolate surge at same temporal resolution as the observations
        # 15 min intervals, starting at df beginning
        upsampled = df_sub.resample('60T', origin=df_sub.index[0]).asfreq()
        df_sub = upsampled.interpolate(method='linear')
        # Assign lead time
        df_sub['leadtime_hrs'] = leadTime
        # Record start time for time interval being tested
        df_sub['IntervalStartTime'] = startTime
        # Append to df containing all forecasts
        # The result is a dataframe with forecasts all stitched together
        # as one continuous timeseries.
        # This should result in one continuous timeseries per lead time
        df_for = df_for.append(df_sub)
    print("File processed")
    counter += 1


# Merge Auswave forecast with wave observations
df = pd.merge(dfw_obs, df_for, how="inner", left_index=True, right_index=True)

# Send all observations and predictions, with corresponding lead times, to a csv file
df.to_csv(os.path.join(oDir,"waves-obsAndpred_%s_2020.csv" % siteName))

