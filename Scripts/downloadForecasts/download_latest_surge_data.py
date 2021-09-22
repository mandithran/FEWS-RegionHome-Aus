import os
import datetime
workDir = "C:\\Users\\mandiruns\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\downloadForecasts"


logf = open(os.path.join(workDir,"exceptionsWLs.log"), "w")
print("downloading surge data...")
try:    

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
    drive = "\\\\ad.unsw.edu.au\\OneUNSW\\ENG\\WRL\\WRL1"
    targetDir = os.path.join(drive,"Coastal\\Data\\Tide\\WL_Forecast\\BOM_Storm_Surge\\raw\\corrected")

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
        gaps = deltas[deltas > timedelta(hours=6)]
        if not gaps.empty:
            targetIndex = int(min(gaps.index)-1)
            download_start_date = df["Time"].iloc[targetIndex]
        
        # Otherwise the download start time is the latest time in the list
        else:
            download_start_date = df["Time"].iloc[-1]

    print('Starting download of BOM Storm Surge files from ' + str(download_start_date))
        
        
    #============================================================================#
    # Parse HTML page and download .nc files
    #============================================================================#

    http = urllib3.PoolManager()
    url = 'http://opendap.bom.gov.au:8080/thredds/catalog/surge/forecast/RnD/catalog.html'
    response = http.request('GET', url)
    soup = BeautifulSoup(response.data, 'html.parser')
    soup_str = soup.text
    soup_split = soup_str.split('.nc')
    # Only keep the items containing "IDZ" - the netcdf files
    soup_split = [string for string in soup_split if ("IDZ" in string)]

    main_url = 'http://opendap.bom.gov.au:8080/thredds/fileServer/surge/forecast/RnD/'


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
            file = wget.download(url, out=rawfilepath) 
        
    # Remove any duplicates
    for fi in os.listdir(targetDir):
        if "(" in fi:
            os.remove(os.path.join(targetDir,fi))

except Exception as e:     # most generic exception you can catch
    logf.write("Failed. {0}\n".format(str(e)))
    logf.write('Recorded at %s.\n' % 
                (datetime.datetime.now()))
