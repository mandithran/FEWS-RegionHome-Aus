#============================================================================#
# The main script used to conduct a series of forecasts. Basically acts like
# FEWS in headless mode; it calls each of the modules that FEWS does.
# This script should mainly be used to run hindcasts in succession. 
# It also provides a decent overview of what FEWS and python are actually doing
# under the hood.
#============================================================================#


#============================== Modules ==============================#
import os
from datetime import datetime,timedelta
from shutil import copyfile
import zipfile
import sys
import traceback
import subprocess


def main(args=None):

    # Module Flags
    # Set as True if you want to run it, set as False if you don't
    initFEWSForecast_flag = True
    initRegionalForecast_flag = True
    initHotspotForecast_flag = True
    NSSDownload_flag = True
    WaveDownload_flag = True
    PreProcessRegional_flag = True
    PreProcessXBeach_flag = True
    runXBeach_flag = True
    PostProcessXBeach_flag = True
    IndicatorsXBeach_flag = True
    WipeForecast_flag = True


    #============================== Scripts that FEWS Runs ==============================#
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from run_forecast_loop.bat file ==============#
    # Path to Region Home, defined in global properties file in main FEWS directory
    regionHomeDir = str(args[0])
    # Start/end date/time for the hindcast times you want to loop through, format should be: "YYYY-MM-DD HH:MM"
    # Assumes UTC
    startSystemDate = str(args[1])
    startSystemTime = str(args[2])
    endSystemDate = str(args[3])
    endSystemTime = str(args[4])
    surgeLocation = str(args[5])
    wavesLocation = str(args[6])


    #============================== Modules ==============================#
    import numpy as np
    import pandas as pd

    #============================== Paths ==============================#
    # Current working directory
    workDir = os.path.join(regionHomeDir,"Scripts\\runForecast")
    # These are the paths/files where location sets are defined for FEWS
    mapLayersDir = os.path.join(regionHomeDir,"Config\\MapLayerFiles")
    ausStates = os.path.join(mapLayersDir,"ausStates.csv")
    hotspots = os.path.join(mapLayersDir,"hotspotLocations.csv")
    # Directory where FEWS external modules are exported to from ModuleDataSetFiles
    moduleDir = os.path.join(regionHomeDir,"Modules")
    # ModuleDataSetFiles, where scripts for each of the modules (one module per zip file)
    # Are unzipped when the module is called in FEWS. This scripts mimics this unzipping
    # and execution of the external module.
    moduleDataSetDir = os.path.join(regionHomeDir,"Config\\ModuleDataSetFiles")
    # Any python-related errors dumped here
    logf = open(os.path.join(workDir,"exceptions_forecastLoop.log"), "w")


    #============================== Variables ==============================#
    # Format hindcast times to loop through. Assumes UTC.
    startSystemTime = str(startSystemDate+' '+startSystemTime)
    endSystemTime = str(endSystemDate+' '+endSystemTime)
    forecastInt = timedelta(hours=12)


    #============================== Local functions ==============================#
    def unzipModule(moduleDataSet=None):

        # In order to run an external module, FEWS has to unzip it from the ModuleDataSetFiles
        # directory. This function mimics that process

        # Copy zipped module dataset to Module directory
        zipName = "%s.zip" % moduleDataSet
        srcPath = os.path.join(moduleDataSetDir,zipName)
        destPath = os.path.join(moduleDir,zipName)
        copyfile(srcPath, destPath)

        # Unzip file in its current location (Modules directory in regionHome, designated above)
        with zipfile.ZipFile(destPath, 'r') as zip_ref:
            zip_ref.extractall(moduleDir)

        # Remove the original .zip file once unzipped
        os.remove(destPath)


    def runModule(script=None, args=None):
        # Mimics the way FEWS runs external modules
        # Throws an error if there are any errors raised in relevant
        # python scripts
        try:
            # Each external FEWS module takes on its own individual arguments
            arguments = " ".join(args)
            command = "python %s %s" % (script, arguments)
            #subprocess.check_output(command,shell=True,stderr=subprocess.STDOUT)
            subprocess.run(command, check=True, shell=True)
        except subprocess.CalledProcessError as e:  # most generic exception you can catch
            logf.write("Failed. {0}\n".format(str(e)))
            logf.write('Recorded at %s.\n' % (datetime.now()))
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


    #============================== Load location sets ==============================#
    # Mimics what FEWS does
    ausStates_df = pd.read_csv(ausStates)
    regions = ausStates_df['ID'].unique()
    hotspots_df = pd.read_csv(hotspots)


    #============================== Unzip module datasets ==============================#
    modules=["initFEWSForecast","NSSDownload",
             "WaveDownload","PreProcessXBeach","PostProcessXBeach",
             "IndicatorsXBeach","WipeForecast",
             "PreProcessRegional"]
    for module in modules:
        unzipModule(module)



    #============================== Main forecast loop ==============================#

    # Main Coastal Forecast loop
    # Construct the series of times to hindcast for
    startSystemTime = datetime.strptime(startSystemTime, '%Y-%m-%d %H:%M')
    endSystemTime = datetime.strptime(endSystemTime, '%Y-%m-%d %H:%M')
    forecastTimes = np.arange(startSystemTime,endSystemTime+forecastInt,forecastInt)
    # Format these into strings that FEWS sends to the python scripts
    forecastTimes_str = [pd.to_datetime(str(date_obj)) for date_obj in forecastTimes]
    forecastTimes_str = [date_obj.strftime('%Y%m%d_%H%M') for date_obj in forecastTimes_str]

    # Loop through hindcast times
    for systemTime in forecastTimes_str:
        # Loop through regions (specified in ausStates.csv location set file, regions are Australian states)
        for region in regions:

            # ================================ Initialize Forecast Module ================================#
            # Initialize forecast. Essentially does what WF_InitializeForecast.xml workflow does
            # FEWS Module adapters InitForecastAdapter.xml and InitHotspotAdapter.xml are contained within
            # this worklfow.
            # Arguments are regionHomeDir, the system time, the region, and the working directory of
            # the python script being called
            # See InitForecastAdapter.xml
            sysTime_dt = datetime.strptime(systemTime, '%Y%m%d_%H%M')
            if initFEWSForecast_flag:
                print("**********************Running initialization module for time: %s GMT **********************" % sysTime_dt)
                workDir_initializeForecastPy = os.path.join(moduleDir,"initFEWSForecast")
                initializeForecastPy = os.path.join(workDir_initializeForecastPy,"python\\initializeForecast.py")
                arguments = [regionHomeDir,systemTime,region,workDir_initializeForecastPy]
                runModule(script=initializeForecastPy,args=arguments)


            # ================================ Initialize Regional Forecast Module ================================#
            # Initialize regional forecast. Also within WF_InitializeForecast.xml workflow
            # Arguments are regionHomeDir, the system time, the region, and the working directory of
            # the python script being called
            # See InitRegionalAdapter.xml
            hotspots_subset = hotspots_df[hotspots_df['Region']==region]
            hotspotIDs = hotspots_subset['ID'].unique()
            if initRegionalForecast_flag:
                print("**************** Initializing regional forecast for time: %s GMT ****************" % sysTime_dt)
                workDir_initializeForecastPy = os.path.join(moduleDir,"initFEWSForecast")
                initializeRegionalPy = os.path.join(workDir_initializeForecastPy,"python\\initializeRegional.py")
                arguments = [regionHomeDir,systemTime,region,workDir_initializeForecastPy]
                runModule(script=initializeRegionalPy,args=arguments)

                
                # ========================== Initialize Hotspot Forecasts Module ==========================#
                # Initialize the hotspot forecasts. Also within WF_InitializeForecast.xml
                # Arguments are region home, system time, location ID for the hotspot, and
                # the working directory of the python script being called
                # See InitHotspotAdapter.xml for FEWS Module Adapter, this code block
                # basically mimics this
                # Load hotspot locations for the respective state
                if initHotspotForecast_flag:
                    # Loop through hotspots
                    for hotspotName in hotspotIDs:
                        print("*********** Initializing hotspot forecast for %s site in %s... ***********" %(hotspotName,region))
                        # Arguments
                        workDir_initializeHotspotPy = os.path.join(moduleDir,"initFEWSForecast")
                        initializeHotspotPy = os.path.join(workDir_initializeForecastPy,"python\\initializeHotspot.py")
                        arguments = [regionHomeDir,systemTime,hotspotName,workDir_initializeHotspotPy]
                        runModule(script=initializeHotspotPy,args=arguments)




            # ============= Retrieve National Storm Surge System Forecasts =============#
            # This is contained within the WF_ImportAusSurge.xml workflow, and basically
            # does what the RetrieveNSSAdapter.xml FEWS Module adapter does
            if NSSDownload_flag:
                print("*********Running NSSDownload module for time: %s GMT *********" % sysTime_dt)
                workDir_RetrieveNSS = os.path.join(moduleDir,"NSSDownload")
                retrieveNSSPy = os.path.join(workDir_RetrieveNSS,"python\\retrieveNSS.py")
                serverLoc = surgeLocation
                arguments = [regionHomeDir, systemTime, workDir_RetrieveNSS, serverLoc]
                runModule(script=retrieveNSSPy,args=arguments)



            # ========================= Retrieve Wave Forecasts ========================#
            # This is contained within the WF_ImportAusWaves.xml workflow, and basically
            # does what the RetrieveAusWavesAdapter.xml FEWS Module adapter does
            if WaveDownload_flag:
                print("*********Running WaveDownload module for time: %s GMT *********" % sysTime_dt)
                workDir_RetrieveAusWaves = os.path.join(moduleDir,"WaveDownload")
                retrieveAusWavesPy = os.path.join(workDir_RetrieveAusWaves,"python\\retrieveAusWaves.py")
                serverLoc = wavesLocation
                arguments = [regionHomeDir,systemTime,workDir_RetrieveAusWaves, serverLoc]
                runModule(script=retrieveAusWavesPy,args=arguments)



            # ======================== Pre-process Regional Forecast Module ========================#
            # Pre-processing for regional forecast. Contained within WF_PreProcessRegional.xml workflow.
            # Basically does wihat PreProcessRegionalAdapter.xml FEWS Module adapter does
            # Arguments are regionHomeDir, the system time, the region, and the working directory of
            # the python script being called
            # See PreProcessRegionalAdapter.xml
            if PreProcessRegional_flag:
                print("*********Running PreProcessRegional module for time: %s GMT *********" % sysTime_dt)
                workDir_preProcessRegionalPy = os.path.join(moduleDir,"PreProcessRegional")
                preProcessRegionalPy = os.path.join(workDir_preProcessRegionalPy,"preprocessMainRegional.py")
                arguments = [regionHomeDir,systemTime,region,workDir_preProcessRegionalPy]
                runModule(script=preProcessRegionalPy,args=arguments)
            



            # Loop through hotspots
            for hotspotName in hotspotIDs:
                # =========================== Pre-process XBeach ===========================#
                # This is contained within the WF_PreProcessXBeach.xml workflow, and basically
                # does what the PreProcessXBeachAdapter.xml FEWS Module adapter does
                if PreProcessXBeach_flag:
                    print("*********Running PreProcessXBeach module for time: %s GMT *********" % sysTime_dt)
                    workDir_PreProcessXBeach = os.path.join(moduleDir,"PreProcessXBeach")
                    preProcessXBeachPy = os.path.join(workDir_PreProcessXBeach,"preprocessMain.py")
                    arguments = [regionHomeDir,systemTime,hotspotName,workDir_PreProcessXBeach]
                    runModule(script=preProcessXBeachPy,args=arguments)


                # =============================== Run XBeach ===============================#
                # Mimics the XBeachAdapter.xml module in FEWS
                if runXBeach_flag:
                    print("*********Running PreProcessXBeach module for time: %s GMT *********" % sysTime_dt)
                    #Reforamt system time string to get the path
                    systemTime_str = sysTime_dt.strftime('%Y%m%d%H')
                    workDir_runXBeachName = "%sSystemTime-%s" % (systemTime_str,hotspotName)
                    workDir_runXBeach = os.path.join(moduleDir,"XBeach",hotspotName,workDir_runXBeachName)
                    xbeach_exe = os.path.join(workDir_runXBeach,"xbeach.exe")
                    try:
                        os.chdir(workDir_runXBeach)
                        #subprocess.check_output(xbeach_exe,shell=True,stderr=subprocess.STDOUT)
                        subprocess.run(xbeach_exe, check=True, shell=True)
                        os.chdir(regionHomeDir)
                    except subprocess.CalledProcessError as e:  # most generic exception you can catch
                        logf.write("Failed. {0}\n".format(str(e)))
                        logf.write('Recorded at %s.\n' % (datetime.now()))
                        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


                # =============================== Post-process XBeach ===============================#
                # Mimics the PostProcessXbeachAdapter.xml module in FEWS
                if PostProcessXBeach_flag:
                    print("*********Running PostProcessXBeach module for time: %s GMT *********" % sysTime_dt)
                    workDir_PostProcessXBeach = os.path.join(moduleDir,"PostProcessXBeach")
                    postProcessXBeachPy = os.path.join(workDir_PostProcessXBeach,"postprocessMain.py")
                    systemTime_str = sysTime_dt.strftime('%Y%m%d%H')
                    arguments = [regionHomeDir,systemTime_str,hotspotName,workDir_PostProcessXBeach]
                    runModule(script=postProcessXBeachPy,args=arguments)


                # =============================== Storm Impact Indicators XBeach ===============================#
                # Mimics the IndicatorsXbeachAdapter.xml module in FEWS
                if IndicatorsXBeach_flag:
                    print("*********Running IndicatorsXBeach module for time: %s GMT *********" % sysTime_dt)
                    workDir_IndicatorsXBeach = os.path.join(moduleDir,"IndicatorsXBeach")
                    indicatorsXBeachPy = os.path.join(workDir_IndicatorsXBeach,"indicatorsMain.py")
                    arguments = [regionHomeDir,systemTime,hotspotName,workDir_IndicatorsXBeach]
                    runModule(script=indicatorsXBeachPy,args=arguments)


                # =============================== Wipe Extra Files from Forecast for Space ===============================#
                # Mimics the WipeForecastAdapter.xml module in FEWS
                if WipeForecast_flag:
                    print("*********Running WipeForecast module for time: %s GMT *********" % sysTime_dt)
                    workDir_WipeForecast = os.path.join(moduleDir,"WipeForecast")
                    wipeForecastPy = os.path.join(workDir_WipeForecast,"wipeForecast.py")
                    arguments = [regionHomeDir,systemTime,hotspotName,workDir_WipeForecast]
                    runModule(script=wipeForecastPy,args=arguments)



## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise
