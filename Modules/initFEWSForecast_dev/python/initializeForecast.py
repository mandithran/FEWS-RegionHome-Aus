############ Modules ############
from xbfewsTools import fewsForecast
from xbfewsTools import fewsUtils
import traceback
import sys
import os
import shutil
import pickle

# Commands for debugging
# python C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initializeForecast.py c:/Users/z3531278/Documents/01_FEWS-RegionHome-Aus 20210620_0100 NSW C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev

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



    ############### Generate diagnostics file ###############
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