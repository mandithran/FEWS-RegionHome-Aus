# Determine the storm periods from the wave data AND forecasts
# ================== Modules ================== #
import os
import pandas as pd
import re
import pytz # for handling time zones
from datetime import datetime, timedelta
import xarray as xr


# ================== Paths ================== #
siteName = "Mandurah"
waveDirectory = "J:\\Coastal\\Data\\Wave"
waveForecastDir = os.path.join(waveDirectory,"Forecast\\BOM_products\\BOM_nearshore_wave_transformation_tool\\raw\\Mesh\\test\\PER")
waveAnalysisDir = ("C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves\\assessSkill\\%s" % siteName)
dataDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Data"
waveObs = os.path.join(dataDir, "Waves\\Mandurah\\MAN54_YEARLY_PROCESSED",
                       "MDW2020_Z.csv")
waveOutDir = os.path.join(waveAnalysisDir,"ofiles")
workDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs\\analyzeSkillNSS\\mandurah"
oDir = os.path.join(workDir,'ofiles')


# ================== Parameters ================== #
# Sydney gauge
#lat = -33.762729999999998
#lon = 151.403240000000011
# Location of the Auswave output node to compare (closest to observation gauge)
# Mandurah offshore wave buoy is at -32.452787 115.572227 (GDA2020)
# Source: https://www.transport.wa.gov.au/imarine/download-tide-wave-data.asp
lat = -32.45543
lon = 115.56795

timezoneUTC = pytz.utc

####################### Local functions #######################
def parseTimeAusWv(string=None):
    dateTimeStr = re.split("msh.", string)[1].split("Z.nc")[0]
    dateTime = datetime.strptime(dateTimeStr, '%Y%m%dT%H%M')
    dateTime = timezoneUTC.localize(dateTime)
    return dateTime

# TODO: comment back in
"""# ================== Analyze forecast wave data ================== #
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

df_storms.to_csv(os.path.join(waveOutDir, "forecastedStorms_%s_2020.csv" % siteName))"""


# ================== Analyze observed wave data ================== #
# ==== Load wave observations ==== #
# Waves in AEST
ifile = waveObs
dfw_obs = pd.read_csv(ifile, skiprows=4)
dfw_obs = dfw_obs.iloc[:,0:2]
# Convert datetime column to datetime objects and set as index
dfw_obs.index = pd.to_datetime(dfw_obs['Unnamed: 0'], format="%d/%m/%Y %H:%M")
awst = pytz.timezone("Australia/Perth")
dfw_obs.index = dfw_obs.index.tz_localize(awst).tz_convert(pytz.utc)
dfw_obs = dfw_obs.drop('Unnamed: 0',1)
# Rename columns
dfw_obs.columns = ['hsig']
# Interpolate onto even half-hourly intervals
originTime = datetime(2020,1,1,tzinfo=pytz.utc)
upsampled = dfw_obs.resample('2T', origin=originTime).asfreq()
interpolated = upsampled.interpolate(method='linear')
dfw_obs = interpolated.resample('30T', origin=originTime).asfreq()
# Keep only points where Hsig is greater than 
# or equal to 3 m 
dfw_obs = dfw_obs[dfw_obs['hsig']>=3.]
dfw_obs['storm'] = True
dfw_obs.to_csv(os.path.join(waveOutDir,"observedStorms_%s_2020.csv" % siteName))
print(waveOutDir)