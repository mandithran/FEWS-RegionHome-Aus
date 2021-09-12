# Modules
import traceback
import sys
import os
import shutil
import pickle
from xbfewsTools import fewsUtils
from xbfewsTools import fewsForecast


def main(args=None):

    # For debugging:
    # python C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initializeRegional.py C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus 20210910_0000 NSW C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\initFEWSForecast

    ############ Arguments ############ 
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # Path to Region Home, defined in global properties file
    regionHome = str(args[0])
    # System time according to FEWS
    sysTimeStr = str(args[1])
    # Site Name
    regionName = str(args[2])
    # Work dir
    workDir = str(args[3])

    with open(os.path.join(workDir,'test.txt'), 'w') as f:
        f.write('here')

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


    #============== Write out pickle for hotspot forecast ==============#
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