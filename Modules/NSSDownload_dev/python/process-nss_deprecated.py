# Main script for retrieving and importing storm surge
import sys
import os
import glob
import pandas as pd
from xbfewsTools import fewsUtils
from xbfewsTools import fewspreproc
from datetime import datetime
import traceback
import shutil
import pickle

# For debugging
# Forecast:
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload/python/process-nss.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus/Import/AusSurge/ Narrabeen C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload hotspotLocations.csv C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus 20210627_0500
# Hindcast:
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload/python/process-nss.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus/Import/AusSurge/ Narrabeen C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload hotspotLocations.csv C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus 20210627_0500

def main(args=None):
    """The main routine."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    foo

    #============== Parse arguments from FEWS ==============#
    # First argument in Module config file is the path to this python script
    # First argument read by this python script is the second argument in the config file
    # First argument: Import Directory
    importDir = str(args[0])
    # Second argument is the site name, specified as part of a Location Set
    siteName = str(args[1])
    # Third argument is working directory
    # Same as working directory for process-surge.py
    workDir = str(args[2])
    # Fourth argument is Location Set file name
    locSetFilename = str(args[3])
    # Fifth argument is Region Home Path
    regionHome = str(args[4])
    # Sixth is system time
    sysTimeStr = str(args[5])

    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")

    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTimeStr)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)

    #============== Load FEWS forecast object ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))


    #============== Write out initial commands to diag file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Current directory: %s" %currDir))
        fileObj.write(fewsUtils.write2DiagFile(3,"Import Directory: % s" % importDir))
        fileObj.write(fewsUtils.write2DiagFile(3,"Site: % s" % siteName))
        fileObj.write(fewsUtils.write2DiagFile(3,"If Python error exit code 1 is triggered, see exceptions.log file in Module directory."))
        fileObj.write("</Diag>")


    #============== Load Location Set ==============#
    locSetPath = os.path.join(regionHome, "./Config/MapLayerFiles", locSetFilename)
    df = pd.read_csv(locSetPath)

    # Debugging: 
    # Hindcast:
    # C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSS_dev/python/process-surge.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus/Import/AusSurge/ Narrabeen C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSS hotspotLocations.csv C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus 20200620_010
    # Forecast: 
    # C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSS_dev/python/process-surge.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus/Import/AusSurge/ Narrabeen C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\ hotspotLocations.csv C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus 20200620_010

    #============== Parse downloaded surge nc file ==============#
    # Uses a function from processSurge.py
    downloadDir = os.path.join(workDir,"ncFiles")
    # Parse BOM file name
    bomDT = str(str(fcst.roundedTime.year)+
            str(fcst.roundedTime.month).zfill(2)+
            str(fcst.roundedTime.day).zfill(2)+
            str(fcst.roundedTime.hour).zfill(2))
    fname = "IDZ00154_StormSurge_national_" + bomDT + ".nc"

    #============== Grab Site Lat/Lon corresponding to NSS Output ==============#
    # Manually look up this point for csv file
    siteLat = df.loc[df['Name']==siteName,"Lat_NSS"].iloc[0]
    siteLon = df.loc[df['Name']==siteName,"Lon_NSS"].iloc[0]


    #============== Process nc file as time series .csv for site ==============#
    csvFile = fewspreproc.processSurge_nc(importDir=importDir, 
                                          downloadDir=downloadDir, 
                                          workDir=workDir,
                                          fname=fname, site=siteName,
                                          scale="hotspot",
                                          siteLat=siteLat,
                                          siteLon=siteLon, fewsForecast=fcst)
    
    #============== Write more info to diagnostics file ==============#
    # Remove </Diag> line since you are appending more lines
    fewsUtils.clearDiagLastLine(diagFile)
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "Target nc file: % s" % os.path.join(importDir,fname)))
        fileObj.write(fewsUtils.write2DiagFile(3, "Processed timeseries csv file: %s" % csvFile))
        fileObj.write("</Diag>")


## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
            print(str(e))
            print(traceback.format_exc())
        raise