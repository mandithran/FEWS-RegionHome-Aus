import os
import re
import traceback
from datetime import datetime
import pandas as pd
import shutil
from xbfewsTools import fewsUtils
from xbfewsTools import preProcWaves
import wget
import sys
import numpy as np
import pickle

# Debugging:
# python C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\WaveDownload_dev/python/retrieveAusWaves.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\WaveDownload_dev 20200627_0500 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus


def main(args=None):

    """The main routine."""

    #============== Parse arguments from FEWS ==============#
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    workDir = str(args[0])
    sysTimeStr = str(args[1])
    regionHome = str(args[2])
    
    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    serverLoc = "http://dapds00.nci.org.au/thredds/fileServer/rr6/waves/"


    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTimeStr)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M")
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)
    # Subtract twelve hours from this rounded time to give a proper spin-up period
    #rt = pd.to_datetime(str(roundedTime))
    #roundedTimeSpin = rt - np.timedelta64(12, "h") 

    #============== Purge any existing files from that directory ==============#
    # Make target directory if it doesn't exist
    ncTargetDir = os.path.join(workDir,'ncFiles')
    if not os.path.exists(ncTargetDir):
        os.makedirs(ncTargetDir)
    #substr = ".msh."
    #for _file in os.listdir(ncTargetDir):
    #    if re.search(substr,_file):
    #        os.remove(os.path.join(ncTargetDir,_file))

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
            drive = "\\\\ad.unsw.edu.au\\OneUNSW\\ENG\\WRL\\WRL1"
            serverLoc = os.path.join(drive,"Coastal\\Data\\Wave\\Forecast\\BOM products\\BOM nearshore wave transformation tool\\raw\\Mesh")

        #============== Fetch file from server  ==============#
        downloadDir = os.path.join(workDir,"ncFiles")
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir)
        if fcst.mode == "forecast":
            servDir = serverLoc + "%s/%s/" %(bomDate,bomTime)
            url = servDir + fname
            bomFile = wget.download(url, out=ncTargetDir)
        elif fcst.mode == "hindcast":
            url = os.path.join(serverLoc,fname)
            shutil.copy(url,ncTargetDir)


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