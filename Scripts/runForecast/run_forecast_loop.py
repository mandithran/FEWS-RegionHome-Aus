#============================================================================#

#============================================================================#


# TODO: uncomment out
#try:

#============================== Modules ==============================#
import os
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
from shutil import copyfile
import zipfile
import sys
import traceback
import subprocess


def main(args=None):


    #============================== Scripts that FEWS Runs ==============================#
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # Path to Region Home, defined in global properties file
    regionHomeDir = str(args[0])
    # Start time for the forecasts, format should be: "YYYY-MM-DD HH:MM"
    # Assumes UTC
    startSystemDate = str(args[1])
    startSystemTime = str(args[2])
    endSystemDate = str(args[3])
    endSystemTime = str(args[4])

    #============================== Paths ==============================#
    # TODO: get it to accept region home and system time as arguments
    workDir = os.path.join(regionHomeDir,"Scripts\\runForecast")
    mapLayersDir = os.path.join(regionHomeDir,"Config\\MapLayerFiles")
    ausStates = os.path.join(mapLayersDir,"ausStates.csv")
    hotspots = os.path.join(mapLayersDir,"hotspotLocations.csv")
    moduleDir = os.path.join(regionHomeDir,"Modules")
    moduleDataSetDir = os.path.join(regionHomeDir,"Config\\ModuleDataSetFiles")
    logf = open(os.path.join(workDir,"exceptions_forecastLoop.log"), "w")


    #============================== Variables ==============================#
    # Times. Assumes UTC.
    startSystemTime = str(startSystemDate+' '+startSystemTime)
    endSystemTime = str(endSystemDate+' '+endSystemTime)
    forecastInt = timedelta(hours=12)

    #============================== Local functions ==============================#
    def unzipModule(moduleDataSet=None):
        # Copy zipped module dataset to Module directory
        zipName = "%s.zip" % moduleDataSet
        srcPath = os.path.join(moduleDataSetDir,zipName)
        destPath = os.path.join(moduleDir,zipName)
        copyfile(srcPath, destPath)
        # Unzip file in its current location (Modules directory in Region Home)
        with zipfile.ZipFile(destPath, 'r') as zip_ref:
            zip_ref.extractall(moduleDir)
        # Remove the zip file
        os.remove(destPath)


    def runModule(script=None, args=None):
        try:
            arguments = " ".join(args)
            command = "python %s %s" % (script, arguments)
            subprocess.check_output(command,shell=True,stderr=subprocess.STDOUT)
            subprocess.run(command, check=True, shell=True)
            #os.system('python %s %s %s %s' % (script,systemTime,region,workDir_initializeForecastPy))
        except subprocess.CalledProcessError as e:  # most generic exception you can catch
            logf.write("Failed. {0}\n".format(str(e)))
            logf.write('Recorded at %s.\n' % (datetime.now()))
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


    #============================== Load location sets ==============================#
    ausStates_df = pd.read_csv(ausStates)
    regions = ausStates_df['ID'].unique()
    hotspots_df = pd.read_csv(hotspots)


    #============================== Unzip module datasets ==============================#
    # TODO: unzip module dataset in correct location
    modules=["initFEWSForecast","AstroTides","NSSDownload",
             "WaveDownload","PreProcessXBeach","PostProcessXBeach",
             "IndicatorsXBeach","WipeForecast"]
    for module in modules:
        unzipModule(module)



    #============================== Main forecast loop ==============================#

    # Main Coastal Forecast loop
    # Construct the series of times to hindcast for
    startSystemTime = datetime.strptime(startSystemTime, '%Y-%m-%d %H:%M')
    endSystemTime = datetime.strptime(endSystemTime, '%Y-%m-%d %H:%M')
    forecastTimes = np.arange(startSystemTime,endSystemTime+forecastInt,forecastInt)
    # Format these into strings that FEWS sent to the python scripts
    forecastTimes_str = [pd.to_datetime(str(date_obj)) for date_obj in forecastTimes]
    forecastTimes_str = [date_obj.strftime('%Y%m%d_%H%M') for date_obj in forecastTimes_str]

    # Loop through times
    for systemTime in forecastTimes_str:
        for region in regions:

            # ================================ Initialize Forecast Module ================================#
            # Initialize forecast. Essentially does what WF_InitializeForecast.xml workflow does
            # FEWS Module adapters InitForecastAdapter.xml and InitHotspotAdapter.xml are contained within
            # this worklfow.
            # Arguments are regionHomeDir, the system time, the region, and the working directory of
            # the python script being called
            # See InitForecastAdapter.xml
            sysTime_dt = datetime.strptime(systemTime, '%Y%m%d_%H%M')
            print("********************** Initializing the forecast for time: %s GMT **********************" % sysTime_dt)
            workDir_initializeForecastPy = os.path.join(moduleDir,"initFEWSForecast")
            initializeForecastPy = os.path.join(workDir_initializeForecastPy,"python\\initializeForecast.py")
            arguments = [regionHomeDir,systemTime,region,workDir_initializeForecastPy]
            runModule(script=initializeForecastPy,args=arguments)

            
            # ========================== Initialize Hotspot Forecasts Module ==========================#
            # Initialize the hotspot forecasts. Also within WF_InitializeForecast.xml
            # Arguments are region home, system time, location ID for the hotspot, and
            # the working directory of the python script being called
            # See InitHotspotAdapter.xml for FEWS Module Adapter, this code block
            # basically mimics this
            # Load hotspot locations for the respective state
            hotspots_subset = hotspots_df[hotspots_df['Region']==region]
            hotspotIDs = hotspots_subset['ID'].unique()
            # Loop through hotspots
            for hotspotName in hotspotIDs:
                print("*********** Initializing hotspot forecast for %s site in %s... ***********" %(hotspotName,region))
                # Arguments
                workDir_initializeHotspotPy = os.path.join(moduleDir,"initFEWSForecast")
                initializeHotspotPy = os.path.join(workDir_initializeForecastPy,"python\\initializeHotspot.py")
                arguments = [regionHomeDir,systemTime,hotspotName,workDir_initializeHotspotPy]
                runModule(script=initializeHotspotPy,args=arguments)


            
            # ============================= Retrieve Tides =============================#
            # This just involves unzipping the tide predictions from the module dataset
            # See RetrieveAstroTideAdapter.xml
            # This is done above in the "Unzip Module Datasets" code block
            pass


            # ============= Retrieve National Storm Surge System Forecasts =============#
            # This is contained within the WF_ImportAusSurge.xml workflow, and basically
            # does what the RetrieveNSSAdapter.xml FEWS Module adapter does
            print("Retrieving BOM National Storm Surge forecasts...")
            workDir_RetrieveNSS = os.path.join(moduleDir,"NSSDownload")
            retrieveNSSPy = os.path.join(workDir_RetrieveNSS,"python\\retrieveNSS.py")
            arguments = [workDir_RetrieveNSS,systemTime,regionHomeDir]
            runModule(script=retrieveNSSPy,args=arguments)



            # ========================= Retrieve Wave Forecasts ========================#
            # This is contained within the WF_ImportAusWaves.xml workflow, and basically
            # does what the RetrieveAusWavesAdapter.xml FEWS Module adapter does
            print("Retrieving BOM Wave Forecast...")
            workDir_RetrieveAusWaves = os.path.join(moduleDir,"WaveDownload")
            retrieveAusWavesPy = os.path.join(workDir_RetrieveAusWaves,"python\\retrieveAusWaves.py")
            arguments = [workDir_RetrieveAusWaves,systemTime,regionHomeDir]
            runModule(script=retrieveAusWavesPy,args=arguments)


            # Loop through hotspots
            for hotspotName in hotspotIDs:
                # =========================== Pre-process XBeach ===========================#
                # This is contained within the WF_PreProcessXBeach.xml workflow, and basically
                # does what the PreProcessXBeachAdapter.xml FEWS Module adapter does
                print("Pre-processing XBeach Run...")
                workDir_PreProcessXBeach = os.path.join(moduleDir,"PreProcessXBeach")
                preProcessXBeachPy = os.path.join(workDir_PreProcessXBeach,"preprocessMain.py")
                arguments = [workDir_PreProcessXBeach,systemTime,regionHomeDir,hotspotName]
                runModule(script=preProcessXBeachPy,args=arguments)


                # =============================== Run XBeach ===============================#
                # Mimics the XBeachAdapter.xml module in FEWS
                print("Running XBeach...")
                #Reforamt system time string to get the path
                systemTime_str = sysTime_dt.strftime('%Y%m%d%H')
                workDir_runXBeachName = "%sSystemTime-%s" % (systemTime_str,hotspotName)
                workDir_runXBeach = os.path.join(moduleDir,"XBeach",hotspotName,workDir_runXBeachName)
                xbeach_exe = os.path.join(workDir_runXBeach,"xbeach.exe")
                try:
                    os.chdir(workDir_runXBeach)
                    subprocess.check_output(xbeach_exe,shell=True,stderr=subprocess.STDOUT)
                    subprocess.run(xbeach_exe, check=True, shell=True)
                    os.chdir(regionHomeDir)
                except subprocess.CalledProcessError as e:  # most generic exception you can catch
                    logf.write("Failed. {0}\n".format(str(e)))
                    logf.write('Recorded at %s.\n' % (datetime.now()))
                    raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


                # =============================== Post-process XBeach ===============================#
                # Mimics the PostProcessXbeachAdapter.xml module in FEWS
                print("Post-processing XBeach run...")
                workDir_PostProcessXBeach = os.path.join(moduleDir,"PostProcessXBeach")
                postProcessXBeachPy = os.path.join(workDir_PostProcessXBeach,"postprocessMain.py")
                systemTime_str = sysTime_dt.strftime('%Y%m%d%H')
                arguments = [workDir_PostProcessXBeach,systemTime_str,regionHomeDir,hotspotName]
                runModule(script=postProcessXBeachPy,args=arguments)


                # =============================== Storm Impact Indicators XBeach ===============================#
                # Mimics the PostProcessXbeachAdapter.xml module in FEWS
                print("Computing Storm Impact Indicators from XBeach run...")
                workDir_IndicatorsXBeach = os.path.join(moduleDir,"IndicatorsXBeach")
                indicatorsXBeachPy = os.path.join(workDir_IndicatorsXBeach,"indicatorsMain.py")
                arguments = [workDir_IndicatorsXBeach,systemTime,regionHomeDir,hotspotName]
                runModule(script=indicatorsXBeachPy,args=arguments)


                # =============================== Wipe Extra Files from Forecast for Space ===============================#
                # Mimics the WipeForecastAdapter.xml module in FEWS
                print("Wiping files from forecast...")
                workDir_WipeForecast = os.path.join(moduleDir,"WipeForecast")
                wipeForecastPy = os.path.join(workDir_WipeForecast,"wipeForecast.py")
                arguments = [workDir_WipeForecast,systemTime,regionHomeDir,hotspotName]
                runModule(script=wipeForecastPy,args=arguments)


                # =========================== TODO: write information to log file ===========================#



## If Python throws an error, send to exceptions.log file

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise