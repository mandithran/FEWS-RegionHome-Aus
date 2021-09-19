from datetime import datetime, timedelta
import os
import pytz
import numpy as np
import pandas as pd

drive = "\\\\ad.unsw.edu.au\\OneUNSW\\ENG\\WRL\\WRL1"
workDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs"
outDir = os.path.join(drive,"Coastal\\Data\\Tide\\WL Forecast\\BOM Storm Surge\\raw\\corrected")

fixPeriodStart = datetime(2019,9,13,0)
fixPeriodStart = pytz.utc.localize(fixPeriodStart)
fixPeriodEnd = datetime(2020,7,14)
fixPeriodEnd = pytz.utc.localize(fixPeriodEnd)

# Generate time series
timeSeries = np.arange(fixPeriodStart,fixPeriodEnd,timedelta(hours=6))
df = pd.DataFrame({'time_series':timeSeries})
df['index'] = df['time_series']
df = df.set_index("index")
df.index = pd.to_datetime(df.index, format="%Y-%m-%d %H:%M:%S")

# Load a list of files in that directory
filesdf = pd.DataFrame({"FileName": os.listdir(outDir)}) 
filesdf['dt_string'] = filesdf['FileName'].apply(lambda s:s.split('_')[3].split('.')[0])
filesdf['index'] = pd.to_datetime(filesdf['dt_string'],format="%Y%m%d%H")
filesdf = filesdf.set_index('index')

# Merge df on left
df = pd.merge(df, filesdf, how='left',left_index=True,right_index=True)
dfna = df[df.isna().any(axis=1)]
dfna.to_csv(os.path.join(workDir,"missingFiles.csv"))
