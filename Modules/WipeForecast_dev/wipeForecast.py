"""
wipeForecast.py
Author: Mandi Thran
Date: 30/09/21

DESCRIPTION:
This script wipes all the larger files associated with the forecast. More specifically, 
this script:
    - Determines the current running forecast/hindcast
    - Loads the relevant pickle file containing the object instance of the fewsForecast 
    class
    - Loads the relevant pickle file containing the object instance of the hotspotForecast 
    class
    - Remove xboutput.nc and the *bcf files
    - Removes the directory where the XBeach run was executed ([Region Home]\Modules\XBeach)
    - Removes the BoM wave and water level forecasts from their local module directories:
        - [Region Home]\Modules\WaveDownload\ncFiles
        - [Region Home]\Modules\NSSDownload\ncFiles
        - NOTE: This doesn’t (and isn’t supposed to) remove the forecasts from the original 
        locations they were downloaded from. 
    - Writes out diagnostics

Arguments for the Script
Arguments for this script are set in run_forecast_loop*.bat and run_forecast_loop.py if 
running the Python wrapper, and in the WipeForecastAdapter.xml file if using FEWS. The 
following are the script’s arguments:
    - regionHome: The path to the Region Home directory
    - systemTimeStr: The system time for the forecast/hindcast, in the format: “YYYYMMDDHH”
    - siteName: The name of the region. This will either be “Narrabeen” or “Mandurah”, and 
    it is designated in hotspotLocations.csv
    - workDir: Working directory. This should be the Module directory 
    ([Region Home]\Modules\WipeForecast).

Key Variables/Inputs/Parameters
    - diagOpen.txt: A template file that FEWS populates and uses as a log file
    - forecast.pkl: The pickle file that stores all the attributes of the instance of the 
    fewsForecast class
    - forecast_hotspot.pkl: The pickle file that stores all the attributes of the instance 
    of the hotspotForecast class
    - xboutput.nc: XBeach output netCDF file. 
    - *.bcf: XBeach .bcf output files
    - IDZ00154_StormSurge_national_YYMMDDHH.nc:	The BoM National Storm Surge System 
    forecast, stored as a netCDF file.
    - [city code].msh.YYYYMMDDTHHMMZ.nc: The BoM nearshore wave forecast, fetched from the 
    WaveDownload module.

Key Outputs
    - diag.xml: The resulting diagnostic file that FEWS populates and uses (i.e. prints to 
    its console) 

COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
python [path to this script] [path to Region Home] [System time in format YYYYMMDDHH] [site name] [working directory, i.e. the path to the folder containing this script]
e.g.,
# python C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\wipeForecast_dev/wipeForecast.py C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus 20200208_0000 Narrabeen C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\WipeForecast_dev


"""

# Modules
import os
import traceback
import shutil
import sys

def main(args=None):

    # Modules
    import pickle
    from xbfewsTools import fewsUtils
    from xbfewsTools import postProcTools


    #============== Parse arguments from FEWS ==============#
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    # Region home
    regionHome = str(args[0])
    # System time according to FEWS
    sysTimeStr = str(args[1])
    # Site Name
    siteName = str(args[2])
    # Path to Region Home, defined in global properties file
    workDir = str(args[3])


    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTimeStr)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    indicatorDir = os.path.join(regionHome,"Data\\Indicators\\Hotspot\\Narrabeen")
    modulePath = os.path.join(regionHome,"Modules")

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
    postProcTools.delete_files(hotspotFcst.xbWorkDir,"xboutput.nc")
    postProcTools.delete_files(hotspotFcst.xbWorkDir,"*.bcf")


    ############ Remove Module Directory where original run took place #############
    if os.path.exists(hotspotFcst.moduleDir):
        shutil.rmtree(hotspotFcst.moduleDir)


    ############ Remove any wave and water level forecasts from local directory #############
    # Storm surge already processed for import into FEWS, by ProcessAusSurgeAdapter
    surgeDirNC = os.path.join(modulePath,"NSSDownload/ncFiles")
    # Parse BOM file name
    bomDT = str(str(hotspotFcst.roundedTime.year)+
            str(hotspotFcst.roundedTime.month).zfill(2)+
            str(hotspotFcst.roundedTime.day).zfill(2)+
            str(hotspotFcst.roundedTime.hour).zfill(2))
    fname = "IDZ00154_StormSurge_national_" + bomDT + ".nc"
    surgeFile = os.path.join(surgeDirNC,fname)
    if os.path.exists(surgeFile):
        os.remove(surgeFile)

    # Remove wave forecasts
    waveDirNC = os.path.join(modulePath,"WaveDownload/ncFiles")
    # Parse wave filename
    # Parse date to match Auswave output naming convention
    bomDate = str(str(hotspotFcst.roundedTime.year)+
            str(hotspotFcst.roundedTime.month).zfill(2)+
            str(hotspotFcst.roundedTime.day).zfill(2))
    bomTime = str(str(hotspotFcst.roundedTime.hour).zfill(2)+
            str(hotspotFcst.roundedTime.minute).zfill(2))
    bomDT = str(bomDate+"T"+bomTime+"Z")
    cityCode = hotspotFcst.waveCode
    fname = "%s.msh.%s.nc" % (cityCode,bomDT)
    ausWaveFile = os.path.join(waveDirNC, fname)
    if os.path.exists(ausWaveFile):
        os.remove(ausWaveFile)



## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise