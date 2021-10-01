"""
retrieveAusWaves.py
Author: Mandi Thran
Date: 30/09/2021

DESCRIPTION
This script fetches the BoM nearshore wave forecast netCDF file needed to 
run a forecast. The netCDF file is used by the hotspot forecast, and it 
will probably be used by the regional forecast. More specifically, this 
script does the following: 
    - Determines the current running forecast/hindcasts
    - Loads the relevant pickle file containing the object instance of the 
    fewsForecast class
    - Parses the correct BoM file name to fetch using the system time, for 
    each city code
    - Determines the correct location to download the BoM file from (either 
    the BoM server, the WRL1 Coastal server, or a local folder)
    - Fetches the file and downloads it to a local directory
    - Writes out diagnostics
    - Updates the original pickle file


ARGUMENTS FOR THE SCRIPT:
Arguments for this script are set in run_forecast_loop*.bat and 
run_forecast_loop.py if running the Python wrapper, and in the 
RetrieveAusWavesAdapter.xml file if using FEWS. The following are the 
script’s arguments:
    - regionHome: The path to the Region Home directory
    - systemTimeStr: The system time for the forecast/hindcast, in the 
    format: “YYYYMMDD_HHMM”
    - workDir: Working directory. This should be the Module directory 
    ([Region Home]\Modules\WaveDownload).
    - forecastLocation: If running a hindcast, this is where the BoM 
    forecast files location is specified. For more info on how to set this, 
    see Section 5.1.2.  


KEY VARIABLES/INPUTS/PARAMETERS:
    - diagOpen.txt: A template file that FEWS populates and uses as a log 
    file
    - serverLoc: The full path to the BoM server, where the forecasts are 
    hosted. The script will use this location if running in “forecast” 
    mode.
    - forecast.pkl: The pickle file that stores all the attributes of the 
    instance of the fewsForecast class


KEY OUTPUTS:
    - diag.xml: The resulting diagnostic file that FEWS populates and uses 
    (i.e. prints to its console) 
    - [city code].msh.YYYYMMDDTHHMMZ.nc: The BoM National Storm Surge 
    System forecast file that the script fetches and sends to 
    [Region Home]\ Modules\WaveDownload\ncFiles
    - forecast.pkl: Updated pickle file for the instance of the 
    fewsForecast class. 

COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
python [path to this script] [path to Region Home] [System time in format YYYYMMDD_HHMM] [working directory, i.e. the path to the folder containing this script] [location of BoM forecasts]
e.g.
python C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\WaveDownload_dev/python/retrieveAusWaves.py C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus 20200208_0000 C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\WaveDownload_dev [Region Home]\ExternalForecasts\BOM\waves

"""

import os
import re
import traceback
from datetime import datetime
import shutil
import sys



def main(args=None):

    #============== Parse arguments from FEWS ==============#
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    regionHome = str(args[0])
    sysTimeStr = str(args[1])
    workDir = str(args[2])
    forecastLocation = str(args[3])
    
    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    serverLoc = "http://dapds00.nci.org.au/thredds/fileServer/rr6/waves/"


    #============== Modules ==============#
    import pandas as pd
    import numpy as np
    import pickle
    from xbfewsTools import fewsUtils
    from xbfewsTools import preProcWaves
    import wget


    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTimeStr)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M")
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Load FEWS forecast object ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))

    #============== Load hotspot location set from FEWS forecast object ==============#
    df = fcst.hotspotDF
    # Return all unique city codes as a list
    wave_codes = df.wave_code.unique()

    for code in wave_codes:

        #============== Parse BOM file name  ==============#
        fname, bomDate, bomTime = preProcWaves.parse_BOMWaveFile(dt=roundedTime,waveCode=code)

        #============== Logic for forecast v hindcast ==============#
        # BOM doesn't store files indefinitely, so we grab them from our own local server
        # If in forecast mode, grab from BOM server
        if fcst.mode == "forecast":
            serverLoc = serverLoc
            url = os.path.join(serverLoc,fname)
        # Otherwise grab it from the WRL J: drive
        elif fcst.mode == "hindcast":
            # Typical os.path.join() doesn't work here because of mixed up slashes
            serverLoc = forecastLocation +"/%s" % code

        #============== Fetch file from server  ==============#
        downloadDir = os.path.join(workDir,"ncFiles")
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir)
        if fcst.mode == "forecast":
            servDir = serverLoc + "%s/%s/" %(bomDate,bomTime)
            url = servDir + fname
            bomFile = wget.download(url, out=downloadDir)
        elif fcst.mode == "hindcast":
            # Typical os.path.join() doesn't work here because of mixed up slashes
            url = serverLoc + "/%s" % fname
            shutil.copy(url,downloadDir)


    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)

    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Current directory: %s" %currDir))
        fileObj.write(fewsUtils.write2DiagFile(3,"Server location: % s \n" % serverLoc))
        fileObj.write(fewsUtils.write2DiagFile(3, "Current system time: %s \n" % systemTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Rounding system time down to: % s \n" % roundedTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Destination directory: % s \n" % workDir))
        fileObj.write(fewsUtils.write2DiagFile(3, "Downloading file: % s \n" %fname))
        fileObj.write(fewsUtils.write2DiagFile(3,"If Python error exit code 1 is triggered, see exceptions.log file in Module directory."))
        fileObj.write("</Diag>")


## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise