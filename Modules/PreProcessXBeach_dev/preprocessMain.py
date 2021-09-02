# Modules
import os
import sys
import traceback
import shutil
import pandas as pd
from xbfewsTools import fewsUtils
from xbfewsTools import xBeachModel
from xbfewsTools import preProcWatLevs
from xbfewsTools import preProcWaves
from datetime import datetime, timezone, timedelta
import fileinput
import pickle
import numpy as np
import geopandas as gpd

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Debugging
# Forecast:
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PreProcessXBeach_dev/preprocessMain.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PreProcessXBeach_dev 20200713_0000 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus Narrabeen 3
# Hindcast:
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PreProcessXBeach_dev/preprocessMain.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PreProcessXBeach_dev 20200713_0000 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus Narrabeen 3


def main(args=None):

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    workDir = str(args[0])
    sysTime = str(args[1])
    regionHome = str(args[2])
    siteName = str(args[3])
    #spinUpWindow = str(args[4]) # in hours
    #forecastHorizon = str(args[4]) # in days
    #deltat_str =  str(args[5]) 
    #locSetFilename = str(args[7])


    #============== Grid parameters ==============#
    # Testing Grid:
    """
    xgrd = os.path.join(regionHomeDir,"Data\\Grids\\%s\\xb-ready-files\\lowres-testing\\x_testing.grd" % siteName)
    ygrd = os.path.join(regionHomeDir,"Data\\Grids\\%s\\xb-ready-files\\lowres-testing\\y_testing.grd" % siteName)
    zgrd = os.path.join(regionHomeDir,"Data\\TopoBathy\\%s\\prep\\xb-ready-files\\lowres-testing\\bed_testing.DEP" % siteName)
    """
    xbFilesPath = os.path.join(regionHome,"Data\\xbeach\\%s\\grd\\2020_02_09\\pre-storm\\25mAlongshore" % siteName)
    xgrd = os.path.join(xbFilesPath,"x.grd")
    ygrd = os.path.join(xbFilesPath,"y.grd")
    zgrd = os.path.join(xbFilesPath,"z.grd")
    ne_layer = os.path.join(xbFilesPath,'ne_layer.grd')


    #============== Other Parameters ==============#
    deltat_str = 10 # input time series resolution, in minutes


    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    modulePath = os.path.join(regionHome,"Modules")
    dataPath = os.path.join(regionHome, "Data")
    gridsPath = os.path.join(dataPath, "Grids", siteName)
    depPath = os.path.join(dataPath,"TopoBathy", siteName)
    paramsTemplate = os.path.join(dataPath,"xbeach/%s/params_template.txt" % siteName)
    execTemplate = os.path.join(dataPath,"xbeach/xbeach.exe")


    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTime)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


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
        fileObj.write("</Diag>")


    #============== Set more parameters for hotspot forecast instance ==============#
    runName = "%s-%s" % (roundedTimeStr,siteName)
    hotspotFcst.runName = runName
    xbWorkDir = os.path.join(hotspotForecastDir,"XBeach")
    if not os.path.exists(xbWorkDir):
        os.makedirs(xbWorkDir)
    hotspotFcst.xbWorkDir = xbWorkDir
    hotspotFcst.deltat = timedelta(minutes=int(deltat_str))
    hotspotFcst.init_runInfo()
    hotspotFcst.inputGridsDir = xbFilesPath

    # Write some of this info to diag file
    # Remove </Diag> line since you are appending more lines
    fewsUtils.clearDiagLastLine(diagFile)
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "XBeach Working Directory: % s" % hotspotFcst.xbWorkDir))
        fileObj.write(fewsUtils.write2DiagFile(3, "System time (from FEWS): %s" % hotspotFcst.systemTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Rounded time: %s" % hotspotFcst.roundedTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Spin-up window : %s" % hotspotFcst.spinUpWindow))
        fileObj.write(fewsUtils.write2DiagFile(3, "Forecast horizon : %s" % hotspotFcst.forecastHorizon))
        fileObj.write(fewsUtils.write2DiagFile(3, "XBeach model start time: %s" % hotspotFcst.startTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "XBeach model end time: %s" % hotspotFcst.endTime))
        fileObj.write("</Diag>")


    #============== Copy Ready-made input files ==============#
    # Transfer pre-made x.grd, y.grd, bed.DEP to working directory
    # Generated with 01preprocess-morpho.py script
    # Copy grids over
    shutil.copy(xgrd, hotspotFcst.xbWorkDir)
    shutil.copy(ygrd, hotspotFcst.xbWorkDir)
    shutil.copy(zgrd, hotspotFcst.xbWorkDir)
    shutil.copy(ne_layer, hotspotFcst.xbWorkDir)
    hotspotFcst.xgrdPath = xgrd
    hotspotFcst.ygrdPath = ygrd
    hotspotFcst.zgrdPath = zgrd
    hotspotFcst.ne_layerPath = zgrd
    

    #============== Generate list of run-up gauges ==============#
    # Command to run script manually:
    # Read xgrd, left most cells contain seaward boundary
    hotspotFcst.dfGauges = pd.read_csv(hotspotFcst.xgrdPath, delim_whitespace=True, header=None, prefix='x', usecols=[0])
    # Read ygrd and add as a column (the correct way), left most cells contain seaward boundary
    hotspotFcst.dfGauges.loc[:,'y0'] = pd.read_csv(hotspotFcst.ygrdPath, delim_whitespace=True, header=None, prefix='y', usecols=[0])


    #============== Pre-process water levels ==============#
    # Inform user through FEWS
    fewsUtils.clearDiagLastLine(diagFile)
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "Pre-processing water levels..."))
        fileObj.write("</Diag>")


    # Generate time series dataframe in GMT
    hotspotFcst.inTimeSeries = preProcWatLevs.generateTimeSeries(forecast=hotspotFcst)
    
    

                #   ===     Tides   ===     #
    # Copy tide dataset to pre-processing working directory
    # Tides must be in GMT
    tidesPath = os.path.join(dataPath,"Tides//%s//processed" % hotspotFcst.city)
    shutil.copy(os.path.join(tidesPath,"%sTidesGMT.csv" % hotspotFcst.city), workDir)
    # Load tide date, chop at start and end time (inherited in xBeachModel class)
    tideFile = os.path.join(workDir,"%sTidesGMT.csv" % hotspotFcst.city)
    tideSeries = preProcWatLevs.loadTideData(ifile=tideFile,
                                             forecast=hotspotFcst)
    # Interpolate tide time series at specified deltat
    tidesInterp = preProcWatLevs.interpSeries(series=tideSeries, forecast=hotspotFcst)

    # Join tides with timeseries
    hotspotFcst.watlevSeries = hotspotFcst.inTimeSeries.merge(tidesInterp, left_index=True, right_index=True)

                #   ===     Surge   ===     #
    # Determine surge file to be processed
    # Assign this as an attribute for easy reference
    # Storm surge already processed for import into FEWS, by ProcessAusSurgeAdapter
    surgeDirNC = os.path.join(modulePath,"NSSDownload/ncFiles")
    # Parse BOM file name
    bomDT = str(str(hotspotFcst.roundedTime.year)+
            str(hotspotFcst.roundedTime.month).zfill(2)+
            str(hotspotFcst.roundedTime.day).zfill(2)+
            str(hotspotFcst.roundedTime.hour).zfill(2))
    fname = "IDZ00154_StormSurge_national_" + bomDT + ".nc"

    #============== Process surge at site ==============#
    # Extract surge from netCDF file
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
    # "Try" this, because there might not be any storm periods in the forecast.
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
    # The old way of checking for storm conditions - using the model forcing    
    """hs_ds = wavesDs[['hs']]
    # If we find values that are >= 3 m, just set the minIndex to be the last index
    # So there is something to compare to
    minIndex = len(hs_ds.time.values)
    for index in np.arange(0,hs_ds.sizes['node']):
        hvals = hs_ds.hs[:,index].values
        boolArr = np.greater_equal(hvals,3.)
        idx_values = np.where(boolArr==True)
        if np.any(boolArr):
            minTest = np.amin(idx_values)
            if minTest < minIndex:
                minIndex = minTest
            print(hvals)
        else:
            # Otherwise just pass
            pass  
    # Determine when to turn on morpho based on spin-up time
    spinup_s = hotspotFcst.spinUpWindow.total_seconds()
    waveforecastTs = hs_ds.time.values
    waveStep = waveforecastTs[1]-waveforecastTs[0]
    # Convert from numpy timedelta64 nanoseconds to seconds (as an integer)
    waveStep = waveStep.item() / 1000000000
    hotspotFcst.morstart = spinup_s + (waveStep*(minIndex-1))"""

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