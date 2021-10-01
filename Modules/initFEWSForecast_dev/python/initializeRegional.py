"""
initializeRegional.py
Author: Mandi Thran
Date: 29/09/2021

DESCRIPTION:
This script initializes the regional component of the entire forecast, setting key parameters 
and generating key folders/files. More specifically, the script does the following:
    - Determines the current forecast using the System Time as an argument
    - Makes key directory/directories for each of the regions
    - Uses the above instance of the fewsForecast class to create a new instance of a class 
    called “regionalForecast”
    - Loads information from the regional Location set (ausStates.csv) and sets this information 
    as attributes
    - Sets key attributes for the regional forecast 
    - Writes out a pickle file for the regional forecast


ARGUMENTS FOR THE SCRIPT:
Arguments for this script are set in run_forecast_loop*.bat and run_forecast_loop.py if running the 
Python wrapper, and in the initRegionalAdapter.xml file if using FEWS. The following are the 
script’s arguments:
    - regionHome: The path to the Region Home directory
    - systemTime: The system time for the forecast/hindcast, in the format: “YYYYMMDD_HHMM”
    - regionName: The name of the region. This will either be “NSW” or “WA”, and it is designated 
    in ausStates.csv
    - workDir: Working directory. This should be the Module directory 
    ([Region Home]\Modules\initFEWSForecast).



KEY INPUTS:
    - forecastHorizon (set in fewsForecast.py, class regionalForecast): This is where the 
    forecast horizon is set. Currently, it is set to a default value of 7 days.
    - deltat (set in fewsForecast.py, class regionalForecast): This is where the time step for 
    the output is set. Currently, it is set to a default of 15 minutes.
    - epsgWL (set in fewsForecast.py, class regionalForecast): The EPSG code for the water 
    level forecast. Currently, it is set to a default value of EPSG:4326


KEY OUTPUTS:
    - diag.xml: The resulting diagnostic file that FEWS populates and uses (i.e. prints to its 
    console) 
    - forecast_regional.pkl: The output pickle file that stores all the attributes of the 
    newly-created instance of the fewsForecast class


COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
python [path to this script] [path to Region Home] [System time in format YYYYMMDD_HHMM] [Region ID] [working directory, i.e. the path to the folder containing this script]
e.g.
python C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initializeRegional.py C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus 20210910_0000 NSW C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\initFEWSForecast

"""


# Modules
import traceback
import sys
import os
import shutil


def main(args=None):

    
    
    ############ Arguments ############ 
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # Path to Region Home, defined in global properties file
    regionHome = str(args[0])
    # System time according to FEWS
    sysTimeStr = str(args[1])
    # Region Name
    regionName = str(args[2])
    # Work dir
    workDir = str(args[3])


    ############ Modules ############ 
    from datetime import timedelta
    import pickle
    from xbfewsTools import fewsUtils
    from xbfewsTools import fewsForecast


    ############ Paths ############ 
    diagFile = os.path.join(workDir,"diagOpen.txt")


    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTimeStr)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Load FEWS forecast object ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))

    
    #============== Initialize regional forecast ==============#
    fcstRegional = fewsForecast.regionalForecast(fcst, regionName)
    # Make the hotspot forecast directory if it doesn't exist
    fcstRegional.init_directory()
    fcstRegional.init_runInfo()


    #============== Write out pickle for regional forecast ==============#
    with open(os.path.join(fcstRegional.forecastDir,"forecast_%s.pkl" % fcstRegional.type), "wb") as output:
            pickle.dump(fcstRegional, output, pickle.HIGHEST_PROTOCOL)

    
    #============== Generate diagnostics file ==============#
    diagBlankFile = fcst.blankDiagFilePath
    diagFile = os.path.join(fcstRegional.forecastDir, "diag.xml")
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    # Write to diagnostic file
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Regional forecast for %s initiated" % regionName ))
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