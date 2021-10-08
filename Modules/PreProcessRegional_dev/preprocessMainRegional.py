# preprocessMainRegional.py
# Author: Mandi Thran
# Date: 30/09/2021

# DESCRIPTION
# This script loads the regional-scale profiles and pre-processes BoM water 
# level forecasts as input to generate the forecast. The script is not yet 
# complete. At the time of writing, this script more specifically does the 
# following:
#     - Determines the current running forecast/hindcasts
#     - Loads the relevant pickle file containing the object instance of the 
#     fewsForecast class
#     - Loads the relevant pickle file containing the object instance of the 
#     regionalForecast class
#     - Loads CoastSat profiles (see Section 4.1.4.1)
#     - Pre-processes the astronomical tide predictions
#     - Pre-processes the water level time series for each of the profiles, 
#     according to their assigned nodes on the water level forecast mesh
#     - Writes out diagnostics

# ARGUMENTS FOR THIS SCRIPT:
# Arguments for this script are set in run_forecast_loop*.bat and 
# run_forecast_loop.py if running the Python wrapper, and in the 
# PreProcessRegionalAdapter.xml file if using FEWS. The following are the 
# script’s arguments:
#     - regionHome: The path to the Region Home directory
#     - systemTimeStr: The system time for the forecast/hindcast, in the 
#     format: “YYYYMMDD_HHMM”
#     - regionName: The name of the region. This will either be “NSW” or 
#     “WA”, and it is designated in ausStates.csv
#     - workDir: Working directory. This should be the Module directory 
#     ([Region Home]\Modules\PreProcessRegional).

# KEY VARIABLES/INPUTS/PARAMETERS:
#     - forecast.pkl: The pickle file that stores all the attributes of the 
#     instance of the fewsForecast class
#     - diagOpen.txt: A template file that FEWS populates and uses as a log 
#     file
#     - regionalTransects_[region].shp: The process CoastSat profiles
#     - [city]TidesGmt.csv: The process astronomical tides for a given city, 
#     in GMT (see Section 4.1.3)
#     - IDZ00154_StormSurge_national_YYMMDDHH.nc: The BoM forecast that gets 
#     fetched by the NSSDownload module. 

# KEY OUTPUTS:
#     - diag.xml: The resulting diagnostic file that FEWS populates and uses 
#     (i.e. prints to its console)
#     - [profile id]_wlFor.csv: Each of the individual water level forecast 
#     files that correspond to each of the CoastSat profiles.  

# COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
# python [path to this script] [path to Region Home] [System time in format YYYYMMDD_HHMM] [region name] [working directory, i.e. the path to the folder containing this script]
# e.g.,
# python C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PreProcessRegional_dev\preprocessMainRegional.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus 20200208_0000 NSW C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PreProcessRegional_dev



# Modules
import os
import sys
import traceback
import shutil


def main(args=None):

    # More Modules
    import pandas as pd
    import geopandas as gpd
    import pickle
    from xbfewsTools import preProcWatLevs
    from xbfewsTools import preProcWaves
    from xbfewsTools import fewsUtils
    from shapely.ops import nearest_points
    from shapely.geometry import Point
    import xarray as xr


    # Arguments for this script
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # Path to Region Home
    regionHome = str(args[0])
    # System time according to FEWS
    sysTime = str(args[1])
    # Region name, either WA or NSW
    regionName = str(args[2])
    # The folder location of the BoM NSS (wave) forecasts
    workDir = str(args[3])


    #======================== Paths ========================#
    # Diagnostics file that FEWS uses
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    # Path to data files
    dataPath = os.path.join(regionHome, "Data")
    # Path to the main directory that has the external 
    # modules
    modulePath = os.path.join(regionHome,"Modules")


    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write("</Diag>")


    #============== Parse system time and find directory of current forecast ==============#
    # Parse system time, converts string to datetime object
    systemTime = fewsUtils.parseFEWSTime(sysTime)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    # Rounded time expressed as a string, so that script can locate the active forecast 
    # directory
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Load fewsForecast object instance ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))


    #============== Load regional forecast object ==============#
    regionalForecastDir = os.path.join(forecastDir, regionName,"regional")
    regionalFcst = pickle.load(open(os.path.join(regionalForecastDir,"forecast_regional.pkl"),"rb"))


    #==================== Load CoastSat profiles ====================#
    # These CoastSat profiles have NSS and Wave Forecast mesh points
    # manually assigned to them
    gdf = gpd.read_file(os.path.join(dataPath,"CoastSat", regionName, "regionalTransects_%s.shp" % regionName))
    # TODO: REMMOVE BELOW LINE:
    gdf = gdf[0:3]
    # Save the geodataframe as an attribute of the regional forecast
    # object
    regionalFcst.profiles_gdf = gdf


    #============== Initial pre-processing for water level forecasts ==============#

    # Inform user through FEWS
    fewsUtils.clearDiagLastLine(diagFile)
    # Write to diagnostics file
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "Pre-processing water levels for regional forecast..."))
        fileObj.write("</Diag>")

    # Generate time series dataframe in GMT/UTC
    wlTimeSeries = preProcWatLevs.generateTimeSeries(forecast=regionalFcst)

                #   ===     Tides   ===     #
    # Copy tide predictions to pre-processing working directory
    # Tides must be in GMT
    tidesPath = os.path.join(dataPath,"Tides//%s//processed" % regionalFcst.tideLocation)
    shutil.copy(os.path.join(tidesPath,"%sTidesGMT.csv" % regionalFcst.tideLocation), workDir)
    #  Path to the tides input file
    tideFile = os.path.join(workDir,"%sTidesGMT.csv" % regionalFcst.tideLocation)
    # Load tide predictions, chop tide time series at start and end time
    tideSeries = preProcWatLevs.loadTideData(ifile=tideFile,
                                             forecast=regionalFcst)
    # Interpolate tide time series at specified deltat (regionalFcst object 
    # attribute), set when forecast object was initialized
    tidesInterp = preProcWatLevs.interpSeries(series=tideSeries, forecast=regionalFcst)
    # Join tides with interpolated time series
    watlevSeries = wlTimeSeries.merge(tidesInterp, left_index=True, right_index=True)
                #   ===     Surge   ===     #
    # Determine BoM storm surge file to be processed
    surgeDirNC = os.path.join(modulePath,"NSSDownload/ncFiles")
    # Parse BOM file name
    bomDT = str(str(regionalFcst.roundedTime.year)+
            str(regionalFcst.roundedTime.month).zfill(2)+
            str(regionalFcst.roundedTime.day).zfill(2)+
            str(regionalFcst.roundedTime.hour).zfill(2))
    fname = "IDZ00154_StormSurge_national_" + bomDT + ".nc"
    # Full path of storm surge forecast file to be loaded
    ifile = os.path.join(surgeDirNC,fname)
    # Load netCDF file as xarray dataset
    surge_ds = xr.open_dataset(ifile)
    # Convert xarray dataset to pandas dataframe
    surge_df = pd.DataFrame({"Lon":surge_ds.coords['lon'].values,"Lat":surge_ds.coords['lat'].values})
    # Get datasets into correct geodataframe format. This is so that
    # the correct points on water level forecast mesh can be found. 
    gdfPts = gpd.GeoDataFrame(surge_df, geometry=gpd.points_from_xy(surge_df.Lon,surge_df.Lat))
    gdfPts.set_crs(epsg=int(regionalFcst.epsgWL))
    # unary union of the geomtries 
    pts = gdfPts.geometry.unary_union
    # Make output folder if it doesn't exist
    regionalFcst.inputsDir = os.path.join(forecastDir, regionName,'regional','inputs')
    regionalFcst.wlForecastDir = os.path.join(regionalFcst.inputsDir,"wlForecasts")
    if not os.path.exists(regionalFcst.wlForecastDir):
        os.makedirs(regionalFcst.wlForecastDir)


    #============== Initial pre-processing for wave forecasts ==============#




    # Iterate over the CoastSat profiles
    for index, row in gdf.iterrows():
        # Find the nearest point on the BoM National Storm Surge forecast
        # mesh to the point location that was manually assigned in the CoastSat 
        # profile dataset file ("regionalTransects_*.shp"). This will ensure 
        # that the surge signal is being extracted from the correct location 
        # for each profile. It's not a direct look-up of a perfectly matching 
        # point because sometimes the BoM water level forecast mesh changes. 
        searchPt = Point(row['nss_lon'],row['nss_lat'])
        # Returns the closest point on the BoM National Storm Surge forecast
        # mesh to the CoastSat profile point that was previously assigned
        # (while examining the mesh and profiles in QGIS)
        closestPt = preProcWaves.nearGeom(searchPt, pts=pts,
                                    gdfIn=gdfPts, outVar='geometries')
        # Extract storm surge forecast at all profiles
        surgeSeries = preProcWatLevs.extractNSS(forecast=regionalFcst,ds=surge_ds,
                                  nss_lat=closestPt.y, nss_lon=closestPt.x)
        # Interpolate surge time series at specified deltat (attirbute of the forecast object)
        surgeInterp = preProcWatLevs.interpSeries(series=surgeSeries, forecast=regionalFcst)
        # Combine storm surge and astronomical tide to get offshore water level
        watlevSeries = watlevSeries.merge(surgeSeries,how='inner',left_index=True,right_index=True)
        watlevSeries['wl_m'] = (watlevSeries['tide_m'] + watlevSeries['surge (m)']).round(2)
        # Export water level forecasts as csv files, one for each CoastSat Profile
        ofileName = '%s_wlFor.csv' % row['id']
        watlevSeries.to_csv(os.path.join(regionalFcst.wlForecastDir, ofileName),
                            columns=['wl_m'])
        watlevSeries = watlevSeries.drop(columns=['surge (m)'], axis=1)


    # Inform user through FEWS, via the diagnostic file
    fewsUtils.clearDiagLastLine(diagFile)
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "Water levels successfully pre-processed."))
        fileObj.write("</Diag>")



# If Python throws an error, send to exceptions.log file to module directory
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise