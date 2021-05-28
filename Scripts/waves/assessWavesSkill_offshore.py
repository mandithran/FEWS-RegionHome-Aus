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
leadtimes = [12] # in hours
timezoneUTC = pytz.utc
params = ['hsig','tp','wdir']


####################### Paths #######################
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves"
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
ifile = os.path.join(workDir,"ifiles\\%s" % "SYDDOW 1_1_2020 to 1_2_2021.csv")
dfw_obs = pd.read_csv(ifile)
dfw_obs.columns = ['datetime','hrms','hsig','h10','hmax','tz','Tp','wdir','nan']
# Keep only the parameters of interest
dfw_obs = dfw_obs[['datetime','hsig','Tp','wdir']]
# Convert date time string to date time object
dfw_obs["datetime"] = pd.to_datetime(dfw_obs["datetime"], format="%d/%m/%Y %H:%M")
# Set datetime as index
dfw_obs.index = dfw_obs['datetime']
dfw_obs = dfw_obs.drop('datetime',axis=1)
# Subtract 10 hours from time series (convert AEST to UTC)
dfw_obs.index = dfw_obs.index - timedelta(hours=int(10))
# Set time zone (now UTC)
dfw_obs= dfw_obs.tz_localize(timezoneUTC)


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

"""


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
            startTime = dateTime+(timedelta(hours=leadTime)-timedelta(hours=forecastInterval))
            endTime = (dateTime+(timedelta(hours=leadTime)))
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
df.to_csv(os.path.join(oDir,"WL-NTR-obsAndpred_%s_2020.csv" % siteName))

"""