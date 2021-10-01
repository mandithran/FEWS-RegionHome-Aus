# ====================================================================================================
# initializeForecast.py
# Author: Mandi Thran
# Date: 27/09/2021
#
# DESCRIPTION
# This script initializes the forecast, setting key parameters and generating key folders/files that 
# are relevant for the overall forecast (regional scale + hotspot scale). When initializing, it is 
# designed to loop through forecast/hindcast times at 12-hour intervals. For each forecast interval 
# of interest, the script does the following:
# - Creates an instance of what is known as a fewsForecast class (defined in xbfewsTools)
# - Sets several key attributes
# - Determines whether the run is in forecast/hindcast mode
# - Generates the directory where all outputs will be held for a given forecast time, across all 
# regions and hotspot areas. This folder takes on the naming convention “YYYYMMDD_HHMM”
# - Writes out a “pickle” file for the forecast (so that the instance of the fewsForecast class 
# can be loaded across scripts, and attributes can be easily access).


# ARGUMENTS FOR THE SCRIPT:
# Arguments for this script are set in run_forecast_loop*.bat and run_forecast_loop.py if running the 
# Python wrapper, and in the initForecastAdapter.xml file if using FEWS. The following are the 
# script’s arguments:
#     - regionHome: The path to the Region Home directory
#     - systemTime: The system time for the forecast/hindcast, in the format: “YYYYMMDD_HHMM”
#     - region: The ID of the region. This will either be “NSW” or “WA”, and it is designated in 
#     ausStates.csv
#     - workDir: Working directory. This should be the Module directory 
#     ([Region Home]\Modules\initFEWSForecast).


# KEY INPUTS:
# - diagOpen.txt: A template file that FEWS populates and uses as a log file. 
# - fcst.roundedTime: Here is where you set how the System Time is rounded down. Right now, the module 
# takes the System Time and rounds it down to the nearest 12-hour interval (this is compatible with 
# twice-daily forecasts). Note: be careful changing this parameter – if you round down to a different 
# time, you’ll have to do a search for “round_hours” throughout the entire Region Home to ensure that 
# that function is rounding down to the nearest desired interval.
# - Regions Location Set (set by ausStates.csv): These are where the different regional locations (for 
# the regional-scale forecasts) are set.
# - Hotspot Location Set (set by hotspotLocations.csv): These are where the different hotspot 
# locations (for the hotspot-scale forecasts) are set. 


# KEY OUTPUTS:
# - diag.xml: The resulting diagnostic file that FEWS populates and uses (i.e. prints to its console)
# - forecast.pkl: The output pickle file that stores all the attributes of the newly-created instance 
# of the fewsForecast classs


# COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
# python [path to this script] [path to Region Home] [System time in format YYYYMMDD_HHMM] [Region ID] [working directory, i.e. the path to the folder containing this script]
# e.g.
# python C:\Users\mandiruns\Documents\\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initializeForecast.py c:/Users/mandiruns/Documents/01_FEWS-RegionHome-Aus 20210620_0100 NSW C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev
# ====================================================================================================



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
    systemTime = str(args[1]) 
    # Region
    region = str(args[2])
    # Work dir
    workDir = str(args[3])


    ############ More modules ############
    from xbfewsTools import fewsForecast
    from xbfewsTools import fewsUtils
    import pickle

    
    ############ Paths ############ 
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")


    ############ Initialize forecast instance of fewsForecast class ############ 
    fcst = fewsForecast.fewsForecast()
    # System time
    fcst.systemTime = fewsUtils.parseFEWSTime(systemTime)
    # Rounded time
    fcst.roundedTime = fewsUtils.round_hours(fcst.systemTime,12)
    # Region home
    fcst.regionHome = regionHome
    # Path to blank diagnostics file
    fcst.blankDiagFilePath = diagBlankFile


    ############ Make a new directory based on rounded time ############
    roundedTimeStr = fcst.roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)
    fcst.forecastDir = forecastDir
    fcst.roundedTimeStr = roundedTimeStr
    # Region sub directories within forecast directory (FEWS loops through Aus states)
    regionDir = os.path.join(forecastDir,region)


    ############ Determine if Forecast v hindcast mode ############ 
    fcst.determineMode()


    ############ Load hotspot location set ############
    fcst.load_regions()
    fcst.load_hotspots()


    ############ Write out pickle for this forecast, separate folder ############ 
    # Make working directory if it doesn't exist
    if not os.path.exists(fcst.forecastDir):
        os.makedirs(fcst.forecastDir)
    # Use pickle to save fewsForecast object info
    with open(os.path.join(fcst.forecastDir,"forecast.pkl"), "wb") as output:
        pickle.dump(fcst, output, pickle.HIGHEST_PROTOCOL)

    ####### Make new directories within forecast directory for the different states (NSW/WA) #######
    # Make region directory if it doesn't exist
    if not os.path.exists(regionDir):
        os.makedirs(regionDir)



    ############### Generate diagnostics file for FEWS ###############
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)

    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Forecast initiated" ))
        fileObj.write(fewsUtils.write2DiagFile(3,"If Python error exit code 1 is triggered, see exceptions.log file in Module directory."))
        fileObj.write("</Diag>")


## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error")
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise