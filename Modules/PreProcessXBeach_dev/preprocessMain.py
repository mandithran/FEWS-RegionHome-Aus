#============================================================================================
# preprocessMain.py
# Author: Mandi Thran
# Date: 30/09/2021

# DESCRIPTION:
# This script does all the essential pre-processing of XBeach inputs in preparation for the 
# XBeach model run. More specifically, this script does the following:
#     - Determines the current running forecast/hindcasts
#     - Loads the relevant pickle file containing the object instance of the fewsForecast 
#     class
#     - Loads the relevant pickle file containing the object instance of the hotspotForecast 
#     class
#     - Set some parameters for the hotspotForecast instance
#     - Copies prepped XBeach grids, executable into an XBeach run folder
#     - Generates run-up gauges according to the input XBeach grids
#     - Pre-processes the astronomical tide and storm surge predictions to produce a water 
#     level boundary condition for XBeach
#     - Pre-processes wave forecasts to provide boundary condition for XBeach
#     - Determines when to turn morstart on depending on when storm conditions are detected 
#     in the offshore forecast
#     - Populates XBeach params.txt file 
#     - Updates pickle file with hotspotForecast instance
#     - Writes out diagnostics

# ARGUMENTS FOR THE SCRIPT:
# Arguments for this script are set in run_forecast_loop*.bat and run_forecast_loop.py if 
# running the Python wrapper, and in the PreProcessXBeachAdapter.xml file if using FEWS. 
# The following are the script’s arguments:
#     - regionHome: The path to the Region Home directory
#     - systemTimeStr: The system time for the forecast/hindcast, in the format: 
#     “YYYYMMDD_HHMM”
#     - siteName: The name of the region. This will either be “Narrabeen” or “Mandurah”, and 
#     it is designated in hotspotLocations.csv
#     - workDir: Working directory. This should be the Module directory 
#     ([Region Home]\Modules\PreProcessXBeach).

# KEY VARIABLES/INPUTS/PARAMETERS:
#     - xbFilesPath: Path to the below four XBeach grids 
#     - xgrd: The prepped XBeach grid containing x locations of the mesh. The file has the 
#     same dimensions as the mesh. For more information, see the XBeach documentation. 
#     - ygrd: The prepped XBeach grid containing y locations of the mesh. The file has the 
#     same dimensions as the mesh. 
#     - zgrd: The prepped XBeach grid containing  locations of the mesh. The file has the 
#     same dimensions as the mesh. 
#     ne_layer: The prepped XBeach non-erodible layer. The file has the same dimensions as 
#     the mesh. 
#     - deltat_str: The input time series resolution that will be set for XBeach inputs  
#     - diagOpen.txt: A template file that FEWS populates and uses as a log file
#     - forecast.pkl: The pickle file that stores all the attributes of the instance of the 
#     fewsForecast class
#     - forecast_hotspot.pkl: The pickle file that stores all the attributes of the instance 
#     of the hotspotForecast class
#     - [city]TidesGmt.csv: The process astronomical tides for a given city, in GMT (see 
#     Section 4.1.3)
#     - IDZ00154_StormSurge_national_YYMMDDHH.nc: The BoM surge forecast that gets fetched by 
#     the NSSDownload module. 
#     - [citycode].msh.YYYYMMDDTHHMMZ.nc: The BoM nearshore wave forecast that gets fetched 
#     by the WaveDownload module. 
#     - auswaveOutPts_[site name].csv: Csv file that lists the points on the BoM wave 
#     forecast mesh that are closest to the XBeach grid boundary points (see Section 4.1.5.3).
#     - JONSWAP parameters (set in preProcWaves.py, function generateWaveFiles): Several 
#     JONSWAP parameters that XBeach uses to generate the wave spectra from the forecast 
#     input. 
#     - Significant wave height threshold that determines storm (set in preProcWaves.py, 
#     function determineStormPeriods): The Hsig threshold used to determine whether there are 
#     storm conditions forecasted. It has a current default value of 3 m. 
#     - Length of a storm period (set in preProcWaves.py, function determineStormPeriods): 
#     The length, in hours, of a full storm period. Currently, a “storm” is classified as a 
#     period of Hsig >=3 for 6 hours or more.
#     - Length of the “quiet” time interval needed to separate storms (set in preProcWaves.py, 
#     function determineStormPeriods): Currently, if there is a quiet period that last more 
#     than 48 hours between storm conditions, these two storm events are considered to be 
#     separate. If storm conditions subside for a period of less than 48 hours, but then 
#     worsen again, this is considered to be a single storm event. 

# KEY OUTPUTS
#     - diag.xml: The resulting diagnostic file that FEWS populates and uses (i.e. prints to 
#     its console) 
#     - XBeach output directory: Includes params.txt, tide.txt, wave files, loclist.txt, 
#     x.grd, y.grd, z.grd, ne_layer.grd, XBeach executable
#     - forecast_hotspot.pkl: The updated pickle file that stores all the attributes of the 
#     hotspotForecast instance

# COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
# python [path to this script] [path to Region Home] [System time in format YYYYMMDD_HHMM] [site name] [working directory, i.e. the path to the folder containing this script]
# e.g.,
# python C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\PreProcessXBeach_dev/preprocessMain.py C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus 20210910_0000 Narrabeen C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\PreProcessXBeach_dev
#============================================================================================


# Python Modules
import os
import sys
import traceback
import shutil
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


def main(args=None):


    #============== Arguments for this script ==============#
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments ==============#
    # Arguments parsed from PreProcessXBeachAdapter.xml if using FEWS
    # Arguments parsed from run_forecast_loop*.py if using Python wrapper
    # Path to Region Home
    regionHome = str(args[0])
    # System time according to FEWS
    sysTime = str(args[1])
    # Site Name (Narrabeen/Mandurah)
    siteName = str(args[2])
    # Work directory - the current module directory
    workDir = str(args[3])


    #============== Python Modules ==============#
    import pandas as pd
    from xbfewsTools import fewsUtils
    from xbfewsTools import preProcWatLevs
    from xbfewsTools import preProcWaves
    from datetime import datetime, timezone, timedelta
    import fileinput
    import pickle
    import numpy as np
    import geopandas as gpd


    #============== Grid parameters ==============#
    # Low resolution grid for testing:
    # xgrd = os.path.join(regionHomeDir,"Data\\Grids\\%s\\xb-ready-files\\lowres-testing\\x_testing.grd" % siteName)
    # ygrd = os.path.join(regionHomeDir,"Data\\Grids\\%s\\xb-ready-files\\lowres-testing\\y_testing.grd" % siteName)
    # zgrd = os.path.join(regionHomeDir,"Data\\TopoBathy\\%s\\prep\\xb-ready-files\\lowres-testing\\bed_testing.DEP" % siteName)

    xbFilesPath = os.path.join(regionHome,"Data\\xbeach\\%s\\grd\\2020_02_09\\pre-storm\\50mAlongshore" % siteName)
    xgrd = os.path.join(xbFilesPath,"x.grd")
    ygrd = os.path.join(xbFilesPath,"y.grd")
    zgrd = os.path.join(xbFilesPath,"z.grd")
    ne_layer = os.path.join(xbFilesPath,'ne_layer.grd')


    #=================== Other Parameters ===================#
    # time series resolution that XBeach will use, in minutes
    deltat_str = 10 


    #============================== Paths ==============================#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    modulePath = os.path.join(regionHome,"Modules")
    dataPath = os.path.join(regionHome, "Data")
    gridsPath = os.path.join(dataPath, "Grids", siteName)
    depPath = os.path.join(dataPath,"TopoBathy", siteName)
    paramsTemplate = os.path.join(dataPath,"xbeach/%s/params_template.txt" % siteName)
    execTemplate = os.path.join(dataPath,"xbeach/xbeach.exe")


    #============== Parse system time and find directory of current forecast ==============#
    # Parse system time, converts string to datetime object
    systemTime = fewsUtils.parseFEWSTime(sysTime)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    # Rounded time expressed as a string, so that script can locate the active forecast 
    # directory
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Load fewsForecast instance ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))


    #============== Load hotspotForecast instance ==============#
    # Find the region of the given hotspot (NSW or WA)
    regionName = fcst.hotspotDF.loc[fcst.hotspotDF['ID']==siteName]['Region'][0]
    hotspotForecastDir = os.path.join(forecastDir, regionName,"hotspot",siteName)
    # Load pickle file
    hotspotFcst = pickle.load(open(os.path.join(hotspotForecastDir,"forecast_hotspot.pkl"),"rb"))



    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    # Write to diagnostics file
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write("</Diag>")


    #============== Set more parameters for hotspot forecast instance ==============#
    # Name of the XBeach run
    runName = "%s-%s" % (roundedTimeStr,siteName)
    hotspotFcst.runName = runName
    # Path to the XBeach work directory
    xbWorkDir = os.path.join(hotspotForecastDir,"XBeach")
    # Make XBeach work directory if it doesn't exist
    if not os.path.exists(xbWorkDir):
        os.makedirs(xbWorkDir)
    # Path to XBeach work directory
    hotspotFcst.xbWorkDir = xbWorkDir
    # Timestep of the inputs XBeach will ingest
    hotspotFcst.deltat = timedelta(minutes=int(deltat_str))
    # Sets the start and end time of the XBeach run given a spin-up window, and sets
    # a few more attributes
    hotspotFcst.init_runInfo()
    # Path of the XBeach grids, for future reference and record-keeping
    hotspotFcst.inputGridsDir = xbFilesPath

    # Write some of this info to diag file
    # Remove </Diag> line since more lines are being appended
    fewsUtils.clearDiagLastLine(diagFile)
    # Write to diagnostics file 
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "XBeach Working Directory: % s" % hotspotFcst.xbWorkDir))
        fileObj.write(fewsUtils.write2DiagFile(3, "System time (from FEWS): %s" % hotspotFcst.systemTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Rounded time: %s" % hotspotFcst.roundedTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Spin-up window : %s" % hotspotFcst.spinUpWindow))
        fileObj.write(fewsUtils.write2DiagFile(3, "Forecast horizon : %s" % hotspotFcst.forecastHorizon))
        fileObj.write(fewsUtils.write2DiagFile(3, "XBeach model start time: %s" % hotspotFcst.startTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "XBeach model end time: %s" % hotspotFcst.endTime))
        fileObj.write("</Diag>")


    #================= Copy Ready-made input files =================#
    # Transfer pre-made x.grd, y.grd, bed.DEP to working directory
    # (XBeach work directory inside the Forecast directory)
    # Generated with 01preprocess-morpho.py script
    # Copy grids over
    shutil.copy(xgrd, hotspotFcst.xbWorkDir)
    shutil.copy(ygrd, hotspotFcst.xbWorkDir)
    shutil.copy(zgrd, hotspotFcst.xbWorkDir)
    shutil.copy(ne_layer, hotspotFcst.xbWorkDir)
    hotspotFcst.xgrdPath = xgrd
    hotspotFcst.ygrdPath = ygrd
    hotspotFcst.zgrdPath = zgrd
    hotspotFcst.ne_layerPath = ne_layer
    

    #============== Generate list of run-up gauges for XBeach output ==============#
    # Read xgrd, left-most cells contain seaward boundary, this is where run-up
    # gauges will be placed at the start of the simulation
    hotspotFcst.dfGauges = pd.read_csv(hotspotFcst.xgrdPath, delim_whitespace=True, header=None, prefix='x', usecols=[0])
    # Read ygrd and add as a column (the correct way), left most cells contain seaward boundary
    hotspotFcst.dfGauges.loc[:,'y0'] = pd.read_csv(hotspotFcst.ygrdPath, delim_whitespace=True, header=None, prefix='y', usecols=[0])


    #============== Pre-process water levels ==============#
    # Inform user through FEWS
    fewsUtils.clearDiagLastLine(diagFile)
    # Write to diagnostics file
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "Pre-processing water levels..."))
        fileObj.write("</Diag>")


    # Generate time series dataframe in GMT/UTC
    hotspotFcst.inTimeSeries = preProcWatLevs.generateTimeSeries(forecast=hotspotFcst)
    
    

                #   ===     Tides   ===     #
    # Copy tide predictions to pre-processing working directory
    # Tides must be in GMT/UTC
    tidesPath = os.path.join(dataPath,"Tides//%s//processed" % hotspotFcst.city)
    shutil.copy(os.path.join(tidesPath,"%sTidesGMT.csv" % hotspotFcst.city), workDir)
    # Load tide predictions, chop time series at start and end time to get
    # tides over the forecast window
    tideFile = os.path.join(workDir,"%sTidesGMT.csv" % hotspotFcst.city)
    tideSeries = preProcWatLevs.loadTideData(ifile=tideFile,
                                             forecast=hotspotFcst)
    # Interpolate tide time series at specified deltat (hotspotFcst attribute)
    tidesInterp = preProcWatLevs.interpSeries(series=tideSeries, forecast=hotspotFcst)

    # Join tides with time series - this becomes the basis for the 
    # water level forcing for XBeach. 
    hotspotFcst.watlevSeries = hotspotFcst.inTimeSeries.merge(tidesInterp, left_index=True, right_index=True)

                #   ===     Surge   ===     #
    # Determine BoM surge file to be processed
    # Assign this as an attribute for easy reference
    surgeDirNC = os.path.join(modulePath,"NSSDownload/ncFiles")
    # Parse BOM file name based on the rounded time
    bomDT = str(str(hotspotFcst.roundedTime.year)+
            str(hotspotFcst.roundedTime.month).zfill(2)+
            str(hotspotFcst.roundedTime.day).zfill(2)+
            str(hotspotFcst.roundedTime.hour).zfill(2))
    fname = "IDZ00154_StormSurge_national_" + bomDT + ".nc"

    #============== Process surge at hotspot site ==============#
    # Extract surge from netCDF file at correct point
    surgeSeries = preProcWatLevs.processNSS_nc(forecast=hotspotFcst,
                                           nssDir=surgeDirNC,
                                           fname=fname)
    # Duplicated index in there for some reason (shouldn't be a DST issue)
    # Maybe because of the merge in processNSS_nc?
    surgeSeries = surgeSeries[~surgeSeries.index.duplicated()]
    # Interpolate surge data to ensure it is robust
    surgeInterp = preProcWatLevs.interpSeries(series=surgeSeries, forecast=hotspotFcst)
    # Make a new surge series and assign hotspot forecast object
    hotspotFcst.watlevSeries = hotspotFcst.watlevSeries.merge(surgeInterp, left_index=True, right_index=True)
    # Add surge to tide to get total water level forcing
    hotspotFcst.watlevSeries['waterlev_m'] = (hotspotFcst.watlevSeries['tide_m'] + 
                                          hotspotFcst.watlevSeries['surge (m)']).round(2)
    # Convert time series index to number of seconds from time0 (xbModel.startTime) 
    # This is the format needed by XBeach
    hotspotFcst.watlevSeries.index = (hotspotFcst.watlevSeries.index -
                                  hotspotFcst.watlevSeries.index[0]).total_seconds().astype(int)
    # Grab total time - set as attribute
    hotspotFcst.totalTime = max(hotspotFcst.watlevSeries.index)
    # Export water level time series to XBeach model working directory
    hotspotFcst.watlevSeries.to_csv(os.path.join(hotspotFcst.xbWorkDir,'tide.txt'), 
                                columns=['waterlev_m'], 
                                sep='\t', header=False, index=True)


    # Inform user through FEWS
    fewsUtils.clearDiagLastLine(diagFile)
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "Water levels successfully pre-processed."))
        fileObj.write("</Diag>")



    #============== Pre-process waves ==============#
    # Inform user through FEWS
    fewsUtils.clearDiagLastLine(diagFile)
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "Pre-processing waves..."))
        fileObj.write("</Diag>")
    # Load locations of mesh points on Auswave output
    meshPts = os.path.join(dataPath,"Waves\\%s\\auswave" % hotspotFcst.city,"auswaveOutPts_%s.csv" % hotspotFcst.siteName)
    # Auswave epsg is 4939
    meshPts = preProcWaves.loadMeshPts(meshPts=meshPts, epsg=hotspotFcst.auswaveEPSG)
    # Load Auswave output
    wavesDir= os.path.join(modulePath,"WaveDownload/ncFiles")
    # Netcdf file as xarray dataset
    wavesDs = preProcWaves.loadAuswave(forecast=hotspotFcst, wavesDir=wavesDir)
    # Slice it to the forecast window
    wavesDs = wavesDs.sel(time=slice(hotspotFcst.roundedTime,hotspotFcst.endTime))
    # Extract the point that is close to the offshore buoy
    offshore_df = pd.DataFrame({"lat":hotspotFcst.offshoreWaveLat,
                                "lon":hotspotFcst.offshoreWaveLon},
                                index=[0])
    offshore_gdf = gpd.GeoDataFrame(offshore_df,geometry=gpd.points_from_xy(offshore_df.lon,offshore_df.lat))
    offshore_gdf.set_crs(epsg=hotspotFcst.auswaveEPSG)
    wavesOffshoreDs = preProcWaves.extractAusWavePts(ds=wavesDs,meshPts=offshore_gdf,epsg=hotspotFcst.auswaveEPSG)
    wavesOffshoreDs = wavesOffshoreDs[['hs']]
    # Extract Auswave points that will force the XBeach model
    # Looking for an exact "point look-up" match doesn't work
    # This code looks at the mesh points, and returns the 
    #    Auswave time series points that are closest to those
    #    points. These are then set along the XBeach seaward 
    #    boundary as forcing.
    wavesDs = preProcWaves.extractAusWavePts(ds=wavesDs, meshPts=meshPts, epsg=hotspotFcst.auswaveEPSG)
    # Loop through mesh points and generate wavefile.txt input files for XBeach
    preProcWaves.generateWaveFiles(ds=wavesDs,forecast=hotspotFcst)
    # Add wavefile name as gdf entry
    meshPts["ind"] = meshPts.index.astype(int)
    meshPts["wavefile"] = [f"wavefile{i+1}.txt" for i in meshPts.index]
    # Place these wave time series on the seaward boundary of the XBeach mesh
    wavesDf, hotspotFcst.ncols, hotspotFcst.nrows = preProcWaves.moveWavestoBoundary(meshPts=meshPts,
                                                                                     forecast=hotspotFcst)
    # Export the locations of the wave time series 
    # forcing to XBeach-friendly input file
    with open(os.path.join(hotspotFcst.xbWorkDir, "loclist.txt"), 'w') as fp:
        fp.write('LOCLIST\n')
        fp.write(wavesDf.to_csv(index=False, columns=["xtarget","ytarget","wavefile"],
            header=False,sep=' ',line_terminator='\n'))


    #============== Morstart - Hsig condition to turn it on/off =================#
    # Determine storm periods from location in wave forecasts that is near offshore
    # buoy
    # IMPORTANT: Assumes wave forecast timestep of one hour.
    offshore_df = wavesOffshoreDs.to_dataframe()
    # Set these flags to None, there may not be a storm in the current forecast
    # and this assists with the code logic below
    morstart_ = None
    morstop_ = None
    hotspotFcst.stormPeriods = preProcWaves.determineStormPeriods(df=offshore_df)
    # Warn the user through FEWS if there is more than one storm period detected
    # in forecast
    if len(hotspotFcst.stormPeriods) > 1:
        # Inform user through FEWS
        fewsUtils.clearDiagLastLine(diagFile)
        with open(diagFile, "a") as fileObj:
            fileObj.write(fewsUtils.write2DiagFile(2, "Warning: more than one storm period detected."))
            fileObj.write("</Diag>")
    if len(hotspotFcst.stormPeriods) >= 1:
        # If there's more than one storm period detected, turn on morphology
        # when the first storm starts, then turn it off when the last storm ends
        stormStart = hotspotFcst.stormPeriods.iloc[0]['storm_start'].tz_localize(timezone.utc).to_pydatetime()
        stormEnd = hotspotFcst.stormPeriods.iloc[-1]['storm_end'].tz_localize(timezone.utc).to_pydatetime()
        # Compute the time that morpho would have to start, including spin-up
        stormStart_spinup = stormStart - timedelta(hours=12)
        stormEnd_spinup = stormEnd + timedelta(hours=12)
        # Compute what morstart would be in this scenario
        morstart_ = (stormStart_spinup-hotspotFcst.startTime).total_seconds()
        morstop_ = (stormEnd_spinup-hotspotFcst.startTime).total_seconds()
    # Check if morstart_, with is own spinup, is shorter than the spinup time the model actually needs
    # at the start of the run. If it's shorter, then set morstart to the model spin-up time of 
    # 12-hours. The waves still need this spin-up so that they reach the coast before the morphology
    # module is turned on in XBeach.
    runTime_sec = (hotspotFcst.endTime-hotspotFcst.startTime).total_seconds()
    if morstart_ is not None and morstart_ <= hotspotFcst.spinUpWindow.total_seconds():
        hotspotFcst.morstart = hotspotFcst.spinUpWindow.total_seconds()
    elif morstart_ is not None and morstart_ > hotspotFcst.spinUpWindow.total_seconds():
        hotspotFcst.morstart = morstart_
    else:
        # This should happen when morstart_ = None, i.e. when there are no storms found
        # Set it to one second less than the run time so XBeach doesn't complain
        hotspotFcst.morstart = runTime_sec-1
    # Similarly, check if morstop happens after the model end time, and if it does, then set morstop 
    # to the total run time in seconds
    if morstop_ is not None and morstop_ >= runTime_sec:
        hotspotFcst.morstop = runTime_sec
    elif morstop_ is not None and morstop_ < runTime_sec:
        hotspotFcst.morstop = morstop_
    else:
        # This should happen when morstop_ = None, i.e. when there are no storms found
        hotspotFcst.morstop = runTime_sec

    #============== Format gauges for params.txt file =================#
    gauges = hotspotFcst.dfGauges.to_csv(index=False, sep=" ", header=False)
    #============== Generate params.txt file ==============#
    paramsFile = os.path.join(hotspotFcst.xbWorkDir, "params.txt")
    # String for dummy pt
    dummyPtStr = "%s %s" % (hotspotFcst.dummyPtX,hotspotFcst.dummyPtY)
    params2replace = {'nx':hotspotFcst.ncols-1,
                      'ny':hotspotFcst.nrows-1,
                      'tstop':hotspotFcst.totalTime,
                      'nrugauge':str(str(len(hotspotFcst.dfGauges))+"\n"+gauges),
                      'morstart':hotspotFcst.morstart,
                      'morstop':hotspotFcst.morstop,
                      'npoints':"1"+"\n"+dummyPtStr,
                      'tintg':hotspotFcst.tintg,
                      'tintm':hotspotFcst.tintm}
    # Replace lines in params.txt template file, write a new params.txt file to working dir
    with open(paramsTemplate) as data:
        with open(paramsFile, "w", newline='') as new_data:
            for line in data:
                for key in params2replace:
                    text2search = "%s = XX" % key
                    if text2search in line:
                        text2replace = "%s = %s" % (key,params2replace[key])
                        line = line.replace(text2search, text2replace)
                new_data.write(line)

    #============== Copy over executable ==============#
    shutil.copy(execTemplate,hotspotFcst.xbWorkDir)

    # Set pre-processing status in model class to "True"
    hotspotFcst.preProcessed = True

    # Set the module run folder
    # This should contain the FEWS system time so that FEWS can find it...
    # Sets self.systemTimeStr
    hotspotFcst.formatSystemTimeStr()
    hotspotFcst.moduleDir = os.path.join(hotspotFcst.regionHome, "Modules\\XBeach\\%s\\%sSystemTime-%s" \
                                                      % (hotspotFcst.siteName,
                                                         hotspotFcst.systemTimeStr,
                                                         hotspotFcst.siteName))

    # Use pickle to save xbeach model object info
    picklePath = os.path.join(hotspotFcst.forecastDir,"forecast_hotspot.pkl")
    with open(picklePath, "wb") as output:
        pickle.dump(hotspotFcst, output, pickle.HIGHEST_PROTOCOL)


    #============== Copy the contents of the xBeach work dir to XBeach module folder ==============#
    # Make sure module directory is made if it doesn't exist
    if not os.path.exists(hotspotFcst.moduleDir):
        os.makedirs(hotspotFcst.moduleDir)
    else:
        # Wipe the contents of the directory if it already exists
        shutil.rmtree(hotspotFcst.moduleDir)
    # Copy contents of xbWorkDir into moduleDir
    from distutils.dir_util import copy_tree
    copy_tree(hotspotFcst.xbWorkDir, hotspotFcst.moduleDir)
    # Copy over the pickle file too
    shutil.copy(picklePath,hotspotFcst.moduleDir)


## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise