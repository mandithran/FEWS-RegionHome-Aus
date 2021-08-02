import os
import traceback
import shutil
import pickle
from xbfewsTools import fewsUtils
from xbfewsTools import postProcTools
import sys

#Debug
#C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\wipeForecast_dev/wipeForecast.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\WipeForecast_dev 20200208_0000 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus Narrabeen


def main(args=None):

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # Path to Region Home, defined in global properties file
    workDir = str(args[0])
    # System time according to FEWS
    sysTimeStr = str(args[1])
    # Region home
    regionHome = str(args[2])
    # Site Name
    siteName = str(args[3])


    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTimeStr)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    indicatorDir = os.path.join(regionHome,"Data\\Indicators\\Hotspot\\Narrabeen")

    #============== Load FEWS forecast object ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))


    #============== Load hotspot forecast object ==============#
    regionName = fcst.hotspotDF.loc[fcst.hotspotDF['ID']==siteName]['Region'][0]
    hotspotForecastDir = os.path.join(forecastDir, regionName,"hotspot",siteName)
    hotspotFcst = pickle.load(open(os.path.join(hotspotForecastDir,"forecast_hotspot.pkl"),"rb"))


    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3, "Wiping hotspot run: %s" % hotspotFcst.runName))
        fileObj.write(fewsUtils.write2DiagFile(3, "Forecast for time period starting at: %s" % hotspotFcst.roundedTime))
        fileObj.write("</Diag>")

    
    ############ Remove Excess XBeach output to save space ################
    postProcTools.delete_files(hotspotFcst.xbWorkDir,"*.nc")
    postProcTools.delete_files(hotspotFcst.xbWorkDir,"*.bcf")

    ############ Remove Module Directory where original run took place #############
    shutil.rmtree(hotspotFcst.moduleDir)


## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise