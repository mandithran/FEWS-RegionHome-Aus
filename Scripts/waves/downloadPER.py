"""
downloadPER.py
Author: Mandi Thran
Date: 01/10/21
DESCRIPTION:
This script was used to download some of the BoM nearshore wave forecast files for the 
Perth area and surrounds. This was done to retain local copies of the forecasts, which 
are not permanently stored on BoM servers. This will allow for hindcasts for 2020-2021 
in Western Australia.
"""

# Modules
import datetime
import pytz
import os
from datetime import timedelta
import numpy as np
import pandas as pd
import wget


drive = "\\\\ad.unsw.edu.au\\OneUNSW\\ENG\\WRL\\WRL1"
workDir = "C:\\Users\\mandiruns\Documents\\01_FEWS-RegionHome-Aus\\Scripts"

# Starts from March 5th 2020
startTime = datetime.datetime(year=2021,month=3,day=4,tzinfo=pytz.utc)
endTime = datetime.datetime.now()

# Convert end time to UTC
endTime=endTime.astimezone(pytz.utc)

times = np.arange(startTime,endTime-timedelta(hours=12),timedelta(hours=12))

locations = ['PER']
forecastTypes = {'Mesh':'msh', 'Spectral':'spec'}
forecastTypes = {'Spectral':'spec'}
for key in forecastTypes:
    for location in locations:
        targetDir = os.path.join(drive,"Coastal\\Data\\Wave\\Forecast\\BOM_products\\BOM_nearshore_wave_transformation_tool\\raw\\%s\\test\\%s" % (key,location))
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
