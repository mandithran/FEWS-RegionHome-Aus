#============================================================================#
# Script to download the AUSWAVE global wave data from the BOM OpenDap servers
# for the previous day. This script is used in automatically downloading the
# forecasts
#============================================================================#

import os, ssl
import numpy as np
import urllib3
from bs4 import BeautifulSoup
import wget
import re
import datetime
from datetime import timedelta
import pytz
import pandas as pd
import smtplib, ssl
import time

np.seterr(all='ignore') # raise/ignore divisions by 0 and nans

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)): 
    ssl._create_default_https_context = ssl._create_unverified_context

#============================================================================#
#                                   Paths                                    #
#============================================================================#
targetDir = "J:\\Coastal\\Data\\Wave\\Forecast\\BOM products\AUSWAVE-R\\raw\\test"

#============================================================================#
# Get today's date, check when the last time that the data was successfully
# download and decide on when the download should be started from.
#============================================================================#

# Test Case 1: No files exist, do the download
# Test Case 2: Several days gap in downloads (a weekend), check and download
# Test Case 3: Files already exist, grab start time from most recent file

todaysdate=datetime.datetime.now()
local = pytz.timezone("Australia/Sydney")
todaysdate=todaysdate.astimezone(pytz.utc)
rawfilepath=targetDir
files_found = None

def parseTime(timeString=None):
    filedate=timeString.split('_')
    filedate=filedate[-1]
    filedatetime = datetime.datetime.strptime(filedate, '%Y%m%d%H')
    timezone = pytz.timezone("UTC")
    filedatetime = timezone.localize(filedatetime)
    return filedatetime


# Case 1 - No previous files exist, downloads initiated for previous day's files 
if os.listdir(rawfilepath) == []:
    files_found = False
    download_start_date = todaysdate - timedelta(days=1.5)
    print(download_start_date)
# Case 2 - Files exist with gaps; parse times and set download_start_date to right before earliest gap 
else:
    files_found = True

    # Generate a list of times from files in directory
    file_times = []
    columnNames = ["FileName","Time"]
    df = pd.DataFrame(columns=columnNames)
    for filename in os.listdir(rawfilepath):
        filestr = filename.split(".nc")[0]
        ftime = parseTime(filestr)
        df = df.append({"FileName":filename,
                    "Time":ftime}, ignore_index=True)
    df = df.sort_values(by="Time", ignore_index=True)

    # Check for files greater than 4 weeks (### hrs). Removes those from the df. Assumes no gaps around this time.
    df = df[df["Time"] > (todaysdate - timedelta(days=28))]

    # Check for gaps in times > 6 hrs. Implication is that there was a gap in downloads
    deltas = df['Time'].diff()[1:]
    gaps = deltas[deltas > timedelta(hours=12)]
    if not gaps.empty:
        targetIndex = int(min(gaps.index)-1)
        download_start_date = df["Time"].iloc[targetIndex]

    # Otherwise the download start time is the latest time in the list
    else:
        download_start_date = df["Time"].iloc[-1]
        print(download_start_date)
    
print('Starting download of BOM Storm Wave files from ' + str(download_start_date))
    
    
#============================================================================#
# TODO: build a list of files to download
#============================================================================#

times = np.arange(download_start_date, todaysdate, timedelta(hours=12))
for t in times:
    try:
        print(t.strftime("%Y%m%d%H"))
    except:
        print("Error downloading wave file for time: %s" % t)





"""main_url = 'http://opendap.bom.gov.au:8080/thredds/fileServer/surge/forecast/RnD/'

for i,text in enumerate(soup_split):
    download_flag=0 #flag to initiate download
    
    # Parse all the file dates and times 
    fn = text[text.find('IDZ00154'):]
    filedatetime = parseTime(timeString=fn)
    
    if filedatetime>download_start_date:
        download_flag=1

    if download_flag:
        print('Downloading BOM Storm Surge file: ' + fn + '.nc')
        url = main_url + fn + '.nc'
        # download file (try until host responds)
        attempts=0
        print("Downloading %s" % url)
        # TODO: uncomment this line
        file = wget.download(url, out=rawfilepath) """
    