#==================================================================================================
# retrieveNSS.py
# Author: Mandi Thran
# Date: 29/09/2021


# DESCRIPTION:
# This module retrieves the BoM’s National Storm surge forecasts for pre-processing. Depending on 
# whether the run is a forecast or a hindcast, the script will grab the relevant file either directly 
# from the BoM server (forecast mode), from our local WRL1 server (hindcast mode), or from a local 
# folder. The netCDF file is used by the hotspot forecast, and it will probably be used by the 
# regional forecast. More specifically, this script does the following: 
#     - Determines the current running forecast/hindcasts
#     - Loads the relevant pickle file containing the object instance of the fewsForecast class
#     - Parses the correct BoM file name to fetch using the system time
#     - Determines the correct location to download the BoM file from (either the BoM server or the 
#     WRL1 Coastal folder)
#     - Fetches the file and downloads it to a local directory
#     - Writes out diagnostics
#     - Updates the original pickle file


# ARGUMENTS FOR THE SCRIPT:
# Arguments for this script are set in run_forecast_loop*.bat and run_forecast_loop.py if running 
# the Python wrapper, and in the RetrieveNSSAdapter.xml file if using FEWS. The following are the 
# script’s arguments:
#     - regionHome: The path to the Region Home directory
#     - systemTime: The system time for the forecast/hindcast, in the format: “YYYYMMDD_HHMM”
#     - workDir: Working directory. This should be the Module directory 
#     ([Region Home]\Modules\NSSDownload).
#     - forecastLocation: If running a hindcast, this is where the BoM forecast files location is 
#     specified. For more info on how to set this, see Section 5.1.2.  


# KEY INPUTS:
#     - diagOpen.txt: A template file that FEWS populates and uses as a log file
#     - serverLoc: The full path to the BoM server, where the forecasts are hosted. The script will 
#     use this location if running in “forecast” mode. 


# KEY OUTPUTS:
#     - diag.xml: The resulting diagnostic file that FEWS populates and uses (i.e. prints to its 
#     console) 
#     - IDZ00154_StormSurge_national_YYMMDDHH.nc: The BoM National Storm Surge System forecast file 
#     that the script fetches and sends to [Region Home]\ Modules\NSSDownload\ncFiles
#     - forecast.pkl: Updated pickle file for the instance of the fewsForecast class. 


# COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
# python [path to this script] [path to Region Home] [System time in format YYYYMMDD_HHMM] [working directory, i.e. the path to the folder containing this script] [path to local folder where forecasts are stored]
# e.g.
# python C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\NSSDownload_dev\python\retrieveNSS.py C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus 20200208_0000 C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\WaveDownload_dev C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\ExternalForecasts\BOM\surge
#==================================================================================================


# ============= Modules ============= #
import sys
import os
import re
from datetime import datetime
import traceback
import shutil
import wget


def main(args=None):

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # First argument in Module config file is the path to this python script
    # First argument read by this python script is the second argument in the config file
    # First argument is the region home
    regionHome = str(args[0])
    # Second argument is the system time
    sysTimeStr = str(args[1])
    # Third argument is the current working directory
    workDir = str(args[2])
    # Fourth argument is the folder location
    forecastLocation = str(args[3])


    # ========== More Modules ========== #
    from xbfewsTools import fewsForecast, fewsUtils
    import pickle


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


    #============== Logic for forecast v hindcast ==============#
    # BOM doesn't store files indefinitely, so we grab them from our own local server
    # If in forecast mode, grab from BOM server
    if fcst.mode == "forecast":
        serverLoc = serverLoc
    # Otherwise grab it from the WRL J: drive
    elif fcst.mode == "hindcast":
        serverLoc = forecastLocation
    

    #============== Fetch file from server  ==============#
    url = os.path.join(serverLoc,fname)
    downloadDir = os.path.join(workDir,"ncFiles")
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)
    if fcst.mode == "forecast":
        bomFile = wget.download(url, out=downloadDir)
    elif fcst.mode == "hindcast":
        shutil.copy(url,downloadDir)

    
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