#============================================================================#

#============================================================================#


# TODO: uncomment out
#try:
#%%
#============================== Modules ==============================#
import os
from datetime import datetime,timedelta
import numpy as np
import pandas as pd

#============================== Paths ==============================#
# TODO: get it to accept region home and system time as arguments
regionHomeDir = "C:\\Users\\z3531278\Documents\\01_FEWS-RegionHome-Aus"
workDir = os.path.join(regionHomeDir,"Scripts\\runForecast")
mapLayersDir = os.path.join(regionHomeDir,"Config\MapLayerFiles")
ausStates = os.path.join(mapLayersDir,"ausStates.csv")
moduleDir = os.path.join(regionHomeDir,"")

#============================== Scripts that FEWS Runs ==============================#


#============================== Variables ==============================#
# Times. Assumes UTC.
startSystemTime = "2020-02-07 00:00" #YYYY-mm-DD HH:mm
endSystemTime = "2020-02-07 12:00"
forecastInt = timedelta(hours=12)

#============================== Local functions ==============================#



#============================== Load preliminary information ==============================#
ausStates_df = pd.read_csv(ausStates)
regions = ausStates_df['ID'].unique()
#%%
#============================== Main forecast loop ==============================#
# Log file
logf = open(os.path.join(workDir,"exceptionsWaves.log"), "w")

# Main Coastal Forecast loop
# Construct the series of times to test 
startSystemTime = datetime.strptime(startSystemTime, '%Y-%m-%d %H:%M')
endSystemTime = datetime.strptime(endSystemTime, '%Y-%m-%d %H:%M')
forecastTimes = np.arange(startSystemTime,endSystemTime+forecastInt,forecastInt)

# Loop through times
for systemTime in forecastTimes:
    for region in regions:
        # Initialize forecast. Essentially does what WF_InitializeForecast.xml workflow does
        # Adapters InitForecastAdapter.xml and InitHotspotAdapter.xml are contained within
        # this worklfow
        # TODO: unzip module dataset in correct location


        print(region)
        print(systemTime)

# Then through the hotspot locations in those regions


# TODO: uncomment out
#except Exception as e:     # most generic exception you can catch
#    logf.write("Failed. {0}\n".format(str(e)))
#    logf.write('Recorded at %s.\n' % 
#                (datetime.datetime.now()))
# %%
