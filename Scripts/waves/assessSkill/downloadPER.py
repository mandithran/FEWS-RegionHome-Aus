import datetime
import pytz
import os
from datetime import timedelta
import numpy as np
import pandas as pd
import wget

# Downloads retrieved:
# PER
#   msh - March 05 2020 to June 15 2021 (nowish)
#   spec - 
# SYD
#   msh - 
#   spec - 

drive = "\\\\ad.unsw.edu.au\\OneUNSW\\ENG\\WRL\\WRL1"
workDir = "C:\\Users\\z3531278\Documents\\01_FEWS-RegionHome-Aus\\Scripts"

# TODO: run again for spectral
# Starts from March 5th 2020
startTime = datetime.datetime(year=2021,month=3,day=4,tzinfo=pytz.utc)
endTime = datetime.datetime.now()

# Convert end time to UTC
endTime=endTime.astimezone(pytz.utc)

times = np.arange(startTime,endTime-timedelta(hours=12),timedelta(hours=12))

locations = ['PER']
forecastTypes = {'Mesh':'msh', 'Spectral':'spec'}
forecastTypes = {'Spectral':'spec'}
# TODO: iterate through and generate the necessary paths based on datetime
for key in forecastTypes:
    for location in locations:
        targetDir = os.path.join(drive,"Coastal\\Data\\Wave\\Forecast\\BOM products\\BOM nearshore wave transformation tool\\raw\\%s\\test\\%s" % (key,location))
        for t in times:
            dtstr = pd.to_datetime(str(t))
            datestr = dtstr.strftime("%Y%m%d")
            timestr = dtstr.strftime("%H%M")
            fname = "%s.%s.%sT%sZ.nc" % (location,forecastTypes[key],datestr,timestr)
            main_url = "http://dapds00.nci.org.au/thredds/fileServer/rr6/waves"
            fullPath = "%s/%s/%s/%s" % (main_url, datestr, timestr, fname)
            print("Downloading %s" % fullPath)
            file = wget.download(fullPath, out=targetDir)

            # Remove any duplicates
            for fi in os.listdir(targetDir):
                if "(1)" in fi:
                    os.remove(os.path.join(targetDir,fi))
