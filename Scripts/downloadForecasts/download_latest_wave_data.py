#============================================================================#
# Script to download the AUSWAVE global wave data from the BOM OpenDap servers
# for the previous day. This script is used in automatically downloading the
# forecasts
#============================================================================#

import os
import datetime
import traceback
workDir = "C:\\Users\\z3531278\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\downloadForecasts"
print("Downloading waves...")

logf = open(os.path.join(workDir,"exceptionsWaves.log"), "w")

try:

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
    import smtplib
    import time

    np.seterr(all='ignore') # raise/ignore divisions by 0 and nans

    if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)): 
        ssl._create_default_https_context = ssl._create_unverified_context

    #============================================================================#
    #                                   Paths                                    #
    #============================================================================#
    drive = "\\\\ad.unsw.edu.au\\OneUNSW\\ENG\\WRL\\WRL1"

    #============================================================================#
    # Get today's date, check when the last time that the data was successfully
    # download and decide on when the download should be started from.
    #============================================================================#

    # Test Case 1: No files exist, do the download
    # Test Case 2: Several days gap in downloads (a weekend), check and download
    # Test Case 3: Files already exist, grab start time from most recent file

    todaysdate=datetime.datetime.now()
    print(todaysdate)
    local = pytz.timezone("Australia/Sydney")
    todaysdate=todaysdate.astimezone(pytz.utc)
    files_found = None

    def parseTime(timeString=None):
        timeString = timeString.replace("T","").replace("Z","")
        filedatetime = datetime.datetime.strptime(timeString, '%Y%m%d%H%M')
        timezone = pytz.timezone("UTC")
        filedatetime = timezone.localize(filedatetime)
        return filedatetime

    def round_hours(dt, resolutionInHours):
        """round_hours(datetime, resolutionInHours) => datetime rounded to lower interval
        Works for hour resolution up to a day (e.g. cannot round to nearest week).
        """
        from datetime import datetime, timedelta
        # First zero out minutes, seconds and micros
        dtTrunc = dt.replace(minute=0,second=0, microsecond=0)
        # Figure out how many minutes we are past the last interval
        excessHours = (dtTrunc.hour) % resolutionInHours
        # Subtract off the excess minutes to get the last interval
        return dtTrunc + timedelta(hours=-excessHours)


    locations = ['SYD','PER']
    forecastTypes = {'Mesh':'msh', 'Spectral':'spec'}

    for forecastType in forecastTypes:
        for location in locations:

            targetDir = os.path.join(drive,"Coastal\\Data\\Wave\\Forecast\\BOM products\\BOM nearshore wave transformation tool\\raw\\%s\\%s" % (forecastType,location))

            # Case 1 - No previous files exist, downloads initiated for previous day's files 
            if os.listdir(targetDir) == []:
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
                for filename in os.listdir(targetDir):
                    try:
                        filestr = filename.split(".nc")[0].split('.')[2]
                        ftime = parseTime(filestr)
                        df = df.append({"FileName":filename,
                                    "Time":ftime}, ignore_index=True)
                    except:
                        pass
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

            # Round start time down to nearest 12 hours
            download_start_date = round_hours(download_start_date,12)
                
            print('Starting download of BOM Storm Wave files from ' + str(download_start_date))
                
            #============================================================================#

            times = np.arange(download_start_date, todaysdate, timedelta(hours=12))

            for t in times:
                dtstr = pd.to_datetime(str(t))
                try:
                    datestr = dtstr.strftime("%Y%m%d")
                    timestr = dtstr.strftime("%H%M")
                    fname = "%s.%s.%sT%sZ.nc" % (location,forecastTypes[forecastType],datestr,timestr)
                    main_url = "http://dapds00.nci.org.au/thredds/fileServer/rr6/waves"
                    fullPath = "%s/%s/%s/%s" % (main_url, datestr, timestr, fname)
                    print("Downloading %s" % fullPath)
                    file = wget.download(fullPath, out=targetDir)
                except:
                    print("Error downloading wave file for time: %s" % t)

                # Remove any duplicates
                for fi in os.listdir(targetDir):
                    if "(" in fi:
                        os.remove(os.path.join(targetDir,fi))

except Exception as e:     # most generic exception you can catch
    logf.write("Failed. {0}\n".format(str(e)))
    logf.write(traceback.format_exc())
    logf.write('Recorded at %s.\n' % 
                (datetime.datetime.now()))