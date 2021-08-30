# Determine the storm periods from the wave data AND forecasts
# ================== Modules ================== #
import os
import pandas as pd
import re
import pytz # for handling time zones
from datetime import datetime, timedelta
import xarray as xr


# ================== Paths ================== #
waveDirectory = "J:\\Coastal\\Data\\Wave"
waveForecastDir = os.path.join(waveDirectory,"Forecast\\BOM products\\BOM nearshore wave transformation tool\\raw\\Mesh")
waveAnalysisDir = ("C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves")
waveObs = os.path.join(waveAnalysisDir, "ifiles\\offshoreSydneyWaveObs.csv")
waveOutDir = os.path.join(waveAnalysisDir,"ofiles")
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs"
print(waveObs)
oDir = os.path.join(workDir,'ofiles')


# ================== Parameters ================== #
siteName = "Narrabeen"
# Location of the Auswave output node to compare (closest to observation gauge)
# SYDDOW offshore wave buoy is at -33.771667, 151.408611
# Source: https://s3-ap-southeast-2.amazonaws.com/www-data.manly.hydraulics.works/www/stations/wave/sydney_LocationHistory.pdf
lat = -33.762729999999998
lon = 151.403240000000011
timezoneUTC = pytz.utc



####################### Local functions #######################
def parseTimeAusWv(string=None):
    dateTimeStr = re.split("msh.", string)[1].split("Z.nc")[0]
    dateTime = datetime.strptime(dateTimeStr, '%Y%m%dT%H%M')
    dateTime = timezoneUTC.localize(dateTime)
    return dateTime


# ================== Analyze forecast wave data ================== #
# Load list of files - NSS Forecast
filesList = []
# We only want the netcdf files
for fi in os.listdir(waveForecastDir):
    if fi.endswith(".nc"):
        filesList.append(fi)
# Add these to a dataframe
df_files = pd.DataFrame(filesList,columns=['fileName'])
# Parse the forecast start time from filename, and add as a new column
df_files['fileDateTime'] = [parseTimeAusWv(str(row)) for row in df_files['fileName']]
# Make datetime the new index for this df
df_files = df_files.set_index(["fileDateTime"])
# Keep only files for certain time period (2020)
forecastPeriodStart = timezoneUTC.localize(datetime(year=2020,month=1,day=1)) 
forecastPeriodEnd = forecastPeriodStart + timedelta(days=366)
df_files = df_files[df_files.index>=forecastPeriodStart]
df_files = df_files[df_files.index<forecastPeriodEnd]


# Empty df that will contain the storm periods
df_storms = pd.DataFrame(columns=['hs','storm'])

counter = 1
# Loop through files and determine the storm periods
for fi in df_files['fileName']:
    print("Processing file: %s" % fi)
    print("File number: %s " % str(counter))
    # Load forecast file
    ds = xr.open_dataset(os.path.join(waveForecastDir,fi))
    # Keep only the variables of interest
    ds = ds[['time','hs','latitude','longitude']]
    # Keep only the point to compare to (nearest point to actual gauge where
    # observations came from)
    ds = ds.where((ds.latitude==lat) & (ds.longitude==lon), drop=True).squeeze()
    # Append these vars to df
    df = ds.to_dataframe()
    df = df.drop(["latitude","longitude"],axis=1)
    # Make dataset timezone aware
    df = df.tz_localize(timezoneUTC)
    # Keep all points in time series where significant wave height
    # is greater than or equal to 3 m 
    df = df[df['hs']>=3.]
    df['storm'] = True
    df_storms = df_storms.append(df)
    counter += 1

df_storms.to_csv(os.path.join(waveOutDir, "forecastedStorms_%s_2020.csv" % siteName))

# ================== Analyze observed wave data ================== #
# ==== Load wave observations ==== #
# Waves in AEST
ifile = waveObs
dfw_obs = pd.read_csv(ifile)
dfw_obs.columns = ['datetime','hrms','hsig','h10','hmax','tz','Tp','wdir','nan']
# Keep only the parameters of interest
dfw_obs = dfw_obs[['datetime','hsig']]
# Convert date time string to date time object
dfw_obs["datetime"] = pd.to_datetime(dfw_obs["datetime"], format="%d/%m/%Y %H:%M")
# Set datetime as index
dfw_obs.index = dfw_obs['datetime']
dfw_obs = dfw_obs.drop('datetime',axis=1)
# Subtract 10 hours from time series (convert AEST to UTC)
dfw_obs.index = dfw_obs.index - timedelta(hours=int(10))
# Set time zone (now UTC)
dfw_obs= dfw_obs.tz_localize(timezoneUTC)
# Keep only points where Hsig is greater than 
# or equal to 3 m 
dfw_obs = dfw_obs[dfw_obs['hsig']>=3.]
dfw_obs['storm'] = True
dfw_obs.to_csv(os.path.join(waveOutDir,"observedStorms_%s_2020.csv" % siteName))
