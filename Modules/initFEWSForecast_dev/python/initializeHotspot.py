############ Modules ############
import traceback
import sys
import os
import shutil
import pickle


def main(args=None):

    # For debugging:
    # python C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initializeHotspot.py C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus 20210830_0000 Narrabeen C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\initFEWSForecast

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
