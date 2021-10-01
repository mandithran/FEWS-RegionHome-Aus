"""
initializeHotspot.py
Author: Mandi Thran
Date: 29/09/2021

DESCRIPTION:
This script initializes the hotspot component of the entire forecast, setting key 
parameters and generating key folders/files. More specifically, the script does the 
following:
    - Determines the current forecast using the System Time as an argument
    - Makes key directory/directories for each of the hotspots
    - Uses the above instance of the fewsForecast class to create a new instance of a 
    class called “hotspotForecast”
    - Sets several key attributes for the hotspot forecast
    - Writes out a pickle file for the hotspot forecast


ARGUMENTS FOR THE SCRIPT:
Arguments for this script are set in run_forecast_loop*.bat and run_forecast_loop.py if running 
the Python wrapper, and in the initHotspotAdapter.xml file if using FEWS. The following are the 
script’s arguments:
    - regionHome: The path to the Region Home directory
    - systemTime: The system time for the forecast/hindcast, in the format: “YYYYMMDD_HHMM”
    - siteName: The name of the site. This will either be “Narrabeen” or “Mandurah”, and it is 
    designated in hotspotLocations.csv
    - workDir: Working directory. This should be the Module directory ([Region Home]\Modules\initFEWSForecast).


KEY INPUTS
    - diagOpen.txt: A template file that FEWS populates and uses as a log file
    - spinUpWindow (set in fewsForecast.py, class hotspotForecast): The number of 
    hours that XBeach will spin-up. Currently, it is set to a default value of 12 
    hours. 
    - forecastHorizon (set in fewsForecast.py, class hotspotForecast): This is where 
    the forecast horizon is set. Currently, it is set to a default value of 7 days.
    - tintm (set in fewsForecast.py, class hotspotForecast): This is where the 
    time-averaged XBeach output timestep is set, and it corresponds to “tintm” in the 
    params.txt file. Currently, it is set to a default value of 900 s. 
    - tintg (set in fewsForecast.py, class hotspotForecast): Instantaneous spatial 
    output timestep for XBeach, and it corresponds to the “tintg” parameter in 
    params.txt file. Currently, it is set to a default value of 900 s.

KEY OUTPUT
    - diag.xml: The resulting diagnostic file that FEWS populates and uses (i.e. 
    prints to its console) 
    - forecast_hotspot.pkl: The output pickle file that stores all the attributes of 
    the newly-created instance of the fewsForecast class


COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
python [path to this script] [path to Region Home] [System time in format YYYYMMDD_HHMM] [Site ID] [working directory, i.e. the path to the folder containing this script]
e.g.
python C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initializeHotspot.py C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus 20210830_0000 Narrabeen C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\initFEWSForecast
"""

############ Modules ############
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
    # Site Name
    siteName = str(args[2])
    # Work dir
    workDir = str(args[3])


    ############ Modules ############
    from xbfewsTools import fewsForecast
    from xbfewsTools import fewsUtils
    import pickle


    ############ Paths ############ 
    diagFile = os.path.join(workDir,"diagOpen.txt")


    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTimeStr)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Load FEWS forecast object ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))


    #============== Initialize hotspot forecast ==============#
    fcstHotspot = fewsForecast.hotspotForecast(fcst, siteName)
    # Isolates and loads up relevant row from df containing hotspot info (a loaded location set in MapLayerFiles)
    fcstHotspot.init_hotspotInfo()
    # Make the hotspot forecast directory if it doesn't exist
    fcstHotspot.init_directory()

    #============== Write out pickle for hotspot forecast ==============#
    with open(os.path.join(fcstHotspot.forecastDir,"forecast_%s.pkl" % fcstHotspot.type), "wb") as output:
            pickle.dump(fcstHotspot, output, pickle.HIGHEST_PROTOCOL)


    #============== Generate diagnostics file ==============#
    diagBlankFile = fcst.blankDiagFilePath
    diagFile = os.path.join(fcstHotspot.forecastDir, "diag.xml")
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    # Write to diagnostic file
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Hotspot forecast for %s site initiated" % siteName ))
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
