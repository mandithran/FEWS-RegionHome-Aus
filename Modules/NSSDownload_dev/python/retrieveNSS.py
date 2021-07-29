# Main script for retrieving and importing storm surge
# ============= Modules ============= #
import sys
import os
import re
from xbfewsTools import fewsUtils
from datetime import datetime
import traceback
import shutil
import pickle
import fewsForecast
import wget

# For debugging:
    # Forecast mode
    # C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload_dev/python/retrieveNSS.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload 20200627_0500 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus
    # Hindcast mode
    # C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload_dev/python/retrieveNSS.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload 20200627_0500 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus


def main(args=None):

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # First argument in Module config file is the path to this python script
    # First argument read by this python script is the second argument in the config file
    # First argument is the current working directory
    workDir = str(args[0])
    # Third argument is the system time
    sysTimeStr = str(args[1])
    # Fourth argument is the region home
    regionHome = str(args[2])


    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")


    #============== Params ==============#
    serverLoc = "http://opendap.bom.gov.au:8080/thredds/fileServer/surge/forecast/RnD/"


    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTimeStr)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Load FEWS forecast object ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))

    
    #============== Parse BOM file name  ==============#
    bomDT = str(str(roundedTime.year)+
            str(roundedTime.month).zfill(2)+
            str(roundedTime.day).zfill(2)+
            str(roundedTime.hour).zfill(2))
    fname = "IDZ00154_StormSurge_national_" + bomDT + ".nc"


    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)

    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Current directory: %s" %currDir))
        fileObj.write(fewsUtils.write2DiagFile(3, "Current system time: %s \n" % systemTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Rounding system time down to: % s \n" % roundedTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Destination directory: % s \n" % workDir))
        fileObj.write(fewsUtils.write2DiagFile(3, "Downloading file: % s \n" %fname))
        fileObj.write(fewsUtils.write2DiagFile(3,"If Python error exit code 1 is triggered, see exceptions.log file in Module directory."))
        fileObj.write("</Diag>")

    #============== Purge any existing files from that directory ==============#
    ncTargetDir = os.path.join(workDir,'ncFiles')
    substr = "IDZ00154_"
    for _file in os.listdir(ncTargetDir):
        if re.search(substr,_file):
            os.remove(os.path.join(ncTargetDir,_file))


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
        serverLoc = os.path.join(drive,"Coastal\\Data\\Tide\\WL Forecast\\BOM Storm Surge\\raw")
    

    #============== Fetch file from server  ==============#
    url = os.path.join(serverLoc,fname)
    downloadDir = os.path.join(workDir,"ncFiles")
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)
    if fcst.mode == "forecast":
        bomFile = wget.download(url, out=ncTargetDir)
    elif fcst.mode == "hindcast":
        shutil.copy(url,ncTargetDir)

    
    #============== Write out new pickle file again  ==============#
    with open(os.path.join(fcst.forecastDir,"forecast.pkl"), "wb") as output:
            pickle.dump(fcst, output, pickle.HIGHEST_PROTOCOL)


## If Python throws an error, send to exceptions.log file that appears in module dataset file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
            print(traceback.format_exc())
        raise