#====================================================================================
# run_forecast_loopy.py
# Author: Mandi Thran
# Date: 24/09/2021

# The main script used to conduct a series of forecasts. Basically acts like
# FEWS in headless mode; it calls each of the modules that FEWS does.
# This script should mainly be used to run hindcasts in succession. 
# It also provides a decent overview of what FEWS and python are actually doing
# under the hood.

# ARGUMENTS:
# Arguments are set in run_forecast_loop.bat. They are parsed in the "Arguments from 
# run_forecast_loop*.bat file" code block. The arguments are:
#  - The path to the region home directory
#  - System Start Date (which the forecast will start looping through)
#  - System Start Time 
#  - System End Date (which the forecast will stop on when looping)
#  - System End Time
#  - The path to the BoM storm surge forecasts
#  - The path to the BoM nearshore wave forecasts
# For more on these arguments, see the run_forecast_loop.bat file. 

# KEY INPUTS:
#     - forecastInt: Forecast interval, currently set to 12 hours
#     - modules: Full list of external modules to run
#     - initFEWSForecast_flag: Set to "True" if you want the initFEWSForecast module
#     to run, set to "False" if you don't. 
#     - initRegionalForecast_flag: "True" to run module, "False" to not.
#     - initHotspotForecast_flag: "True" to run module, "False" to not.
#     - NSSDownload_flag: "True" to run module, "False" to not.
#     - WaveDownload_flag: "True" to run module, "False" to not.
#     - PreProcessRegional_flag: "True" to run module, "False" to not.
#     - PreProcessXBeach_flag: "True" to run module, "False" to not.
#     - runXBeach_flag: "True" to run module, "False" to not.
#     - PostProcessXBeach_flag: "True" to run module, "False" to not.
#     - IndicatorsXBeach_flag: "True" to run module, "False" to not.
#     - WipeForecast_flag: "True" to run module, "False" to not.

# For inputs pertaining to the individual modules, see their relevant code blocks. 



#============================== Modules ==============================#
import os
from datetime import datetime,timedelta
from shutil import copyfile
import zipfile
import sys
import traceback
import subprocess

# Full script resides in this "main" function so that
# the script can receive command-line arguments from 
# FEWS/Python wrapper and error log. 
def main(args=None):

    # Module Flags
    # Set as True if you want to run a given module, set as False if you don't
    # These flag names correspond to the module folders
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
    WipeForecast_flag = False


    #============== Arguments from run_forecast_loop*.bat file =============#
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments  ==============#
    # Path to Region Home
    # When using Python wrapper, this is defined in run_forecast_loop*.bat
    regionHomeDir = str(args[0])
    # Start/end date/time for the hindcast times you want to loop through
    # Format should be: "YYYY-MM-DD HH:MM", assumes UTC/GMT
    # Arguments et in run_forecast_loop*.bat
    startSystemDate = str(args[1])
    startSystemTime = str(args[2])
    endSystemDate = str(args[3])
    endSystemTime = str(args[4])
    # Locations of BoM forecasts, set in run_forecast_loop*.bat
    surgeLocation = str(args[5])
    wavesLocation = str(args[6])


    #===================== Modules ======================#
    import numpy as np
    import pandas as pd

    
    #============================== Variables ==============================#
    # Forecast interval, runs once per 12-hour period
    forecastInt = timedelta(hours=12)
    # The list of all the modules. Should correspond to the names of 
    # any zipped folders in the [Region Home]\Config\ModuleDataSetFiles
    modules=["initFEWSForecast","NSSDownload",
             "WaveDownload","PreProcessXBeach","PostProcessXBeach",
             "IndicatorsXBeach","WipeForecast",
             "PreProcessRegional"]


    #============================== Paths ==============================#
    # Current working directory
    workDir = os.path.join(regionHomeDir,"Scripts\\runForecast")
    # These are the paths/files where location sets are defined for FEWS
    # The Python wrapper makes use of them, too. 
    mapLayersDir = os.path.join(regionHomeDir,"Config\\MapLayerFiles")
    # Regional location set (Australian states)
    ausStates = os.path.join(mapLayersDir,"ausStates.csv")
    # Hotspot location set (Beach sites)
    hotspots = os.path.join(mapLayersDir,"hotspotLocations.csv")
    # Directory where FEWS external modules are exported to from ModuleDataSetFiles
    moduleDir = os.path.join(regionHomeDir,"Modules")
    # ModuleDataSetFiles, where scripts for each of the modules (one module per zip file)
    # Are unzipped when the module is called in FEWS. This script mimics this unzipping
    # and execution of the external module that FEWS does. 
    moduleDataSetDir = os.path.join(regionHomeDir,"Config\\ModuleDataSetFiles")
    # Any python-related errors dumped here
    logf = open(os.path.join(workDir,"exceptions_forecastLoop.log"), "w")



    #============================== Local functions ==============================#
    def unzipModule(moduleDataSet=None):
        """
        Description: In order to run an external module, FEWS has to unzip 
        it from the ModuleDataSetFiles directory. This function mimics 
        that process; it moves the zipped folder from [Region Home]\Config
        \ModuleDataSetFiles, copies it to [Region Home]\Modules, and unzips it.
        
        Input: moduleDataSet: Precise name of the module data set. Should match the 
        name of the zipped folder in [Region Home]\Config\ModuleDataSetFiles
        
        """

        # Copy zipped module dataset to Module directory
        zipName = "%s.zip" % moduleDataSet
        srcPath = os.path.join(moduleDataSetDir,zipName)
        destPath = os.path.join(moduleDir,zipName)
        copyfile(srcPath, destPath)

        # Unzip file in its current location (Modules directory in regionHome, designated above)
        with zipfile.ZipFile(destPath, 'r') as zip_ref:
            zip_ref.extractall(moduleDir)

        # Remove the original .zip file once unzipped (in [Region Home\Modules])
        os.remove(destPath)


    def runModule(script=None, args=None):
        """
        Description: Mimics the way FEWS runs external modules (meaing that it basically
        runs a Python script.) Throws an error if there are any errors raised in the
        relevant python scripts.

        Inputs:
           - script: the Python script to run
           - args: the specific arguments the above script takes
        """ 
        try:
            # Each external FEWS module takes on its own individual arguments
            arguments = " ".join(args)
            command = "python %s %s" % (script, arguments)
            #subprocess.check_output(command,shell=True,stderr=subprocess.STDOUT)
            subprocess.run(command, check=True, shell=True)
        # If there is an error, send it to the log file. We want each module to be run
        # each time. 
        except subprocess.CalledProcessError as e:
            logf.write("Failed. {0}\n".format(str(e)))
            logf.write('Recorded at %s.\n' % (datetime.now()))
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


    #============================== Load location sets ==============================#
    # Mimics what FEWS does, which is that it loops through Location Sets
    # Two location sets are relevant here: the regional location set, which consists
    # of Australian states; and the hotspot location sets, which contains hotspot
    # sites.
    # Regional location set
    ausStates_df = pd.read_csv(ausStates)
    regions = ausStates_df['ID'].unique()
    # Hotspot location set
    hotspots_df = pd.read_csv(hotspots)


    #==================== Unzip module datasets ====================#
    # Call the unzipModule functin defined above
    for module in modules:
        unzipModule(module)



    #======================================== Main forecast loop ========================================#
    # Format hindcast times to loop through. Assumes UTC.
    # Combines date and time into a full datetime string
    startSystemTime = str(startSystemDate+' '+startSystemTime)
    endSystemTime = str(endSystemDate+' '+endSystemTime)
    # Construct the series of times to hindcast for. The forecast loop will loop through these times.
    # Parse start time
    startSystemTime = datetime.strptime(startSystemTime, '%Y-%m-%d %H:%M')
    # Parse end time
    endSystemTime = datetime.strptime(endSystemTime, '%Y-%m-%d %H:%M')
    # Array of times based on start and end time, and the forecast interval of 12 hours.
    forecastTimes = np.arange(startSystemTime,endSystemTime+forecastInt,forecastInt)
    # Format these into strings that FEWS sends to the python scripts as arguments
    forecastTimes_str = [pd.to_datetime(str(date_obj)) for date_obj in forecastTimes]
    forecastTimes_str = [date_obj.strftime('%Y%m%d_%H%M') for date_obj in forecastTimes_str]

    # Loop through hindcast times
    for systemTime in forecastTimes_str:
        # Loop through regions (specified in ausStates.csv location set file, regions are Australian states)
        for region in regions:

            # ================================ Initialize Forecast Module ================================#
            # Calls the script that initializes the entire forecast (initializeForecast.py). Essentially 
            # does what the WF_InitializeForecast.xml workflow and the InitForecastAdapter.xml Module Adapter
            # do. Arguments are regionHomeDir, the system time, the region, and the working directory of 
            # the python script being called. See InitForecastAdapter.xml
            
            # Date/time of current hindcast being looped through. 
            sysTime_dt = datetime.strptime(systemTime, '%Y%m%d_%H%M')
            # Only run if flag is set to True
            if initFEWSForecast_flag:
                # Inform user which module is being run.
                print("**********************Running initialization module for time: %s GMT **********************" % sysTime_dt)
                # Working directory, location of below python script
                workDir_initializeForecastPy = os.path.join(moduleDir,"initFEWSForecast")
                # Python script being called for this module
                initializeForecastPy = os.path.join(workDir_initializeForecastPy,"python\\initializeForecast.py")
                # Arguments for the above Python script
                arguments = [regionHomeDir,systemTime,region,workDir_initializeForecastPy]
                # Run the module (i.e. run the python script), calling the function runModule defined 
                # above
                runModule(script=initializeForecastPy,args=arguments)


            # =========================== Initialize Regional Forecast Module ===========================#
            # Calls the script that initializes the regional forecast (initializeRegional.py). Essentially 
            # does what the WF_InitializeForecast.xml workflow and the InitRegionalAdapter.xml Module Adapter
            # do. Arguments are regionHomeDir, the system time, the region, and the working directory of 
            # the python script being called. See InitRegionalAdapter.xml

            # Grabs the relevant hotspots within the region (state) of interest
            hotspots_subset = hotspots_df[hotspots_df['Region']==region]
            # List of all unique hotspots within the region (state)
            hotspotIDs = hotspots_subset['ID'].unique()
            # Only run if flag is set to True
            if initRegionalForecast_flag:
                # Inform user which module is being run.
                print("**************** Initializing regional forecast for time: %s GMT ****************" % sysTime_dt)
                # Working directory, location of below python script
                workDir_initializeForecastPy = os.path.join(moduleDir,"initFEWSForecast")
                # Python script being called for this module
                initializeRegionalPy = os.path.join(workDir_initializeForecastPy,"python\\initializeRegional.py")
                # Arguments for the above Python script
                arguments = [regionHomeDir,systemTime,region,workDir_initializeForecastPy]
                # Run the module (i.e. run the python script), calling the function runModule defined 
                # above
                runModule(script=initializeRegionalPy,args=arguments)


                
                # ========================== Initialize Hotspot Forecasts Module ==========================#
                # Calls the script that initializes the hotspot forecast (initializeHotspot.py). Essentially 
                # does what the WF_InitializeForecast.xml workflow and the InitHotspotAdapter.xml Module Adapter
                # do. Arguments are regionHomeDir, the system time, the hotspot name (ID), and the working 
                # directory of the python script being called. See InitHotspotAdapter.xml.

                # Only run if flag is set to True
                if initHotspotForecast_flag:
                    # Loop through hotspots in a given region (state)
                    for hotspotName in hotspotIDs:
                        # Inform user which module is being run. 
                        print("*********** Initializing hotspot forecast for %s site in %s... ***********" %(hotspotName,region))
                        # Working directory, location of below python script
                        workDir_initializeHotspotPy = os.path.join(moduleDir,"initFEWSForecast")
                        # Python script being called for this module
                        initializeHotspotPy = os.path.join(workDir_initializeForecastPy,"python\\initializeHotspot.py")
                        # Arguments for the above Python script
                        arguments = [regionHomeDir,systemTime,hotspotName,workDir_initializeHotspotPy]
                        # Run the module (i.e. run the python script), calling the function runModule defined 
                        # above
                        runModule(script=initializeHotspotPy,args=arguments)




            # ================== Retrieve National Storm Surge System Forecasts ==================#
            # Calls the script that fetches the BoM storm surge forecasts (retrieveNSS.py). Does
            # what the WF_ImportAusSurge.xml workflow and the RetrieveAusSurgeAdapter.xml Module
            # Adapter do. Arguments are the Region Home Directory, the system time, the working
            # directory (i.e. the location of the Python script), and the location where the
            # BoM storm surge forecasts are being pulled from. This could be WRL1 or a local directory.
            # If running a forecast, the code will automatically pull it from the BoM's servers.
            # See RetrieveNSSAdapter.xml
            
            # Only run if flag is set to True
            if NSSDownload_flag:
                # Inform user which module is being run. 
                print("*********Running NSSDownload module for time: %s GMT *********" % sysTime_dt)
                # Working directory, location of below python script
                workDir_RetrieveNSS = os.path.join(moduleDir,"NSSDownload")
                # Python script being called for this module
                retrieveNSSPy = os.path.join(workDir_RetrieveNSS,"python\\retrieveNSS.py")
                # Location of the forecasts, which is an argument for this script
                # This argument is set in run_forecast_loop*.bat
                serverLoc = surgeLocation
                # Arguments for the above Python script
                arguments = [regionHomeDir, systemTime, workDir_RetrieveNSS, serverLoc]
                # Run the module (i.e. run the python script), calling the function runModule defined 
                # above
                runModule(script=retrieveNSSPy,args=arguments)



            # ============================ Retrieve Wave Forecasts ===========================#
            # Calls the script that fetches the BoM wave forecasts (retrieveAusWaves.py). Does
            # what the WF_ImportAusWaves.xml workflow and the RetrieveAusWavesAdapter.xml Module
            # Adapter do. Arguments are the Region Home Directory, the system time, the working
            # directory (i.e. the location of the Python script), and the location where the
            # BoM wave forecasts are being pulled from. This could be WRL1 or a local directory.
            # If running a forecast, the code will automatically pull it from the BoM's servers.
            # See RetrieveAusWavesAdapter.xml            
            
            # Only run if flag is set to True
            if WaveDownload_flag:
                # Inform user which module is being run. 
                print("*********Running WaveDownload module for time: %s GMT *********" % sysTime_dt)
                # Working directory, location of below python script
                workDir_RetrieveAusWaves = os.path.join(moduleDir,"WaveDownload")
                # Python script being called for this module
                retrieveAusWavesPy = os.path.join(workDir_RetrieveAusWaves,"python\\retrieveAusWaves.py")
                # Location of the forecasts, which is an argument for this script
                # This argument is set in run_forecast_loop*.bat
                serverLoc = wavesLocation
                # Arguments for the above Python script
                arguments = [regionHomeDir,systemTime,workDir_RetrieveAusWaves, serverLoc]
                # Run the module (i.e. run the python script), calling the function runModule defined 
                # above
                runModule(script=retrieveAusWavesPy,args=arguments)



            # ===================== Pre-process Regional Forecast Module =====================#
            # Calls the script that pre-processes the regional forecast
            # (preprocessMainRegional.py). Does what the WF_PreProcessRegional.xml workflow
            # and the PreProcessRegionalAdapter.xml Module Adapter do. Arguments are the Region 
            # Home Directory, the system time, the region (i.e. Australian state), and the 
            # working directory (i.e. the location of the Python script).
            # See PreProcessRegionalAdapter.xml             
            
            # Only run if flag is set to True
            if PreProcessRegional_flag:
                # Inform user which module is being run. 
                print("*********Running PreProcessRegional module for time: %s GMT *********" % sysTime_dt)
                # Working directory, location of below python script
                workDir_preProcessRegionalPy = os.path.join(moduleDir,"PreProcessRegional")
                # Python script being called for this module
                preProcessRegionalPy = os.path.join(workDir_preProcessRegionalPy,"preprocessMainRegional.py")
                # Arguments for the above Python script
                arguments = [regionHomeDir,systemTime,region,workDir_preProcessRegionalPy]
                # Run the module (i.e. run the python script), calling the function runModule defined 
                # above
                runModule(script=preProcessRegionalPy,args=arguments)
            



            # Loop through hotspots in a particular region
            for hotspotName in hotspotIDs:

                # =========================== Pre-process XBeach ===========================#
                # Calls the script that pre-processes the hotspot forecast (XBeach run - 
                # preprocessMain.py). Does what the WF_PreProcessXBeach.xml workflow and the
                # PreProcessXBeachAdapter.xml Module Adapter do. Arguments are the Region 
                # Home Directory, the system time, the hotspot name (ID), and the working 
                # directory (i.e. the location of the Python script). See 
                # PreProcessXBeachAdapter.xml 

                # Only run if flag is set to True
                if PreProcessXBeach_flag:
                    # Inform user which module is being run. 
                    print("*********Running PreProcessXBeach module for time: %s GMT *********" % sysTime_dt)
                    # Working directory, location of below python script
                    workDir_PreProcessXBeach = os.path.join(moduleDir,"PreProcessXBeach")
                    # Python script being called for this module
                    preProcessXBeachPy = os.path.join(workDir_PreProcessXBeach,"preprocessMain.py")
                    # Arguments for the above Python script
                    arguments = [regionHomeDir,systemTime,hotspotName,workDir_PreProcessXBeach]
                    # Run the module (i.e. run the python script), calling the function runModule defined 
                    # above
                    runModule(script=preProcessXBeachPy,args=arguments)



                # =============================== Run XBeach ===============================#
                # Runs XBeach.exe after the run folder has been prepped by the above module.
                # Does what the WF_runXBeach.xml workflow and the XBeachAdapter.xml Module
                # Adapter do. No arguments, just runs the executable. The XBeach simulations
                # are run in the directory: [Region Home]\Modules\xbeach. 
                # See XBeachAdapter.xml
                
                # Only run if flag is set to True
                if runXBeach_flag:
                    print("*********Running PreProcessXBeach module for time: %s GMT *********" % sysTime_dt)
                    #Reforamt system time string to get the correct path
                    systemTime_str = sysTime_dt.strftime('%Y%m%d%H')
                    # Working directory - i.e. the directory where xbeach.exe is located for the
                    # given run
                    workDir_runXBeachName = "%sSystemTime-%s" % (systemTime_str,hotspotName)
                    workDir_runXBeach = os.path.join(moduleDir,"XBeach",hotspotName,workDir_runXBeachName)
                    # Location of xbeach.exe
                    xbeach_exe = os.path.join(workDir_runXBeach,"xbeach.exe")
                    # Try, except logic here - we want XBeach to run when this module is 
                    # called
                    try:
                        # Change the directory to the same directory xbeach.exe is in, or else
                        # Xbeach doens't know what to do.
                        os.chdir(workDir_runXBeach)
                        #subprocess.check_output(xbeach_exe,shell=True,stderr=subprocess.STDOUT)
                        # Run xbeach.exe
                        subprocess.run(xbeach_exe, check=True, shell=True)
                        # Change the directory back to the Region Home
                        os.chdir(regionHomeDir)
                    # Throw an error if it doesn't run
                    except subprocess.CalledProcessError as e:  # most generic exception you can catch
                        logf.write("Failed. {0}\n".format(str(e)))
                        logf.write('Recorded at %s.\n' % (datetime.now()))
                        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


                # =============================== Post-process XBeach ===============================#
                # Calls the script that post-processes the hotspot forecast (XBeach run - 
                # postprocessMain.py). Does what the WF_PostProcessXBeach.xml workflow and the
                # PostProcessXBeachAdapter.xml Module Adapter do. Arguments are the Region Home 
                # Directory, the system time, the hotspot name (ID), and the working directory (i.e. 
                # the location of the Python script). See PostProcessXBeachAdapter.xml 

                # Only run if flag is set to True
                if PostProcessXBeach_flag:
                    # Inform user which module is being run. 
                    print("*********Running PostProcessXBeach module for time: %s GMT *********" % sysTime_dt)
                    # Working directory, location of below python script
                    workDir_PostProcessXBeach = os.path.join(moduleDir,"PostProcessXBeach")
                    # Python script being called for this module
                    postProcessXBeachPy = os.path.join(workDir_PostProcessXBeach,"postprocessMain.py")
                    # Formatted system time string
                    systemTime_str = sysTime_dt.strftime('%Y%m%d%H')
                    # Arguments for the above Python script
                    arguments = [regionHomeDir,systemTime_str,hotspotName,workDir_PostProcessXBeach]
                    # Run the module (i.e. run the python script), calling the function runModule defined 
                    # above
                    runModule(script=postProcessXBeachPy,args=arguments)


                # ============================ Storm Impact Indicators XBeach ===========================#
                # Calls the script that processes the storm impact indicators from the XBeach run 
                # (indicatorsMain.py). Does what the WF_IndicatorsXBeach.xml workflow and the
                # IndicatorsXBeachAdapter.xml Module Adapter do. Arguments are the Region Home 
                # Directory, the system time, the hotspot name (ID), and the working directory (i.e. 
                # the location of the Python script). See IndicatorsXBeachAdapter.xml 

                # Only run if flag is set to True
                if IndicatorsXBeach_flag:
                    # Inform user which module is being run. 
                    print("*********Running IndicatorsXBeach module for time: %s GMT *********" % sysTime_dt)
                    # Working directory, location of below python script
                    workDir_IndicatorsXBeach = os.path.join(moduleDir,"IndicatorsXBeach")
                    # Python script being called for this module
                    indicatorsXBeachPy = os.path.join(workDir_IndicatorsXBeach,"indicatorsMain.py")
                    # Arguments for the above Python script
                    arguments = [regionHomeDir,systemTime,hotspotName,workDir_IndicatorsXBeach]
                    # Run the module (i.e. run the python script), calling the function runModule defined 
                    # above
                    runModule(script=indicatorsXBeachPy,args=arguments)


                # ======================== Wipe Extra Files from Forecast for Space =========================#
                # Calls the script that wipes the larger forecast-related files that are no longer needed
                # (i.e., the XBeach output netcdf file, other XBeach output files, and the BoM forecasts).
                # Does what the WF_WipeForecast.xml workflow and the WipeForecastAdapter.xml Module Adapter
                # do. Arugments are the Region Home Directory, the system time, the hotspot name (ID), and the 
                # working directory (i.e. the location of the Python script). See WipeForecastAdapter.xml 

                # Only run if flag is set to True
                if WipeForecast_flag:
                    # Inform user which module is being run. 
                    print("*********Running WipeForecast module for time: %s GMT *********" % sysTime_dt)
                    # Working directory, location of below python script
                    workDir_WipeForecast = os.path.join(moduleDir,"WipeForecast")
                    # Python script being called for this module
                    wipeForecastPy = os.path.join(workDir_WipeForecast,"wipeForecast.py")
                    # Arguments for the above Python script
                    arguments = [regionHomeDir,systemTime,hotspotName,workDir_WipeForecast]
                    # Run the module (i.e. run the python script), calling the function runModule defined 
                    # above
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
