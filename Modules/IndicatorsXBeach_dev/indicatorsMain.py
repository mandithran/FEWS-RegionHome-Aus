# ==========================================================================================
# indicatorsMain.py
# Author: Mandi Thran
# Date: 30/09/21

# DESCRIPTION:
# This script computes the storm impact indicators from XBeach model output. It computes two 
# indicators: the safe corridor width, and the "building-scarp distance". Locations of 
# interest (in this version, the dune toes) are imported for each row along the XBeach grid.   

# Safe corridor width procedure: the distances between these dune toes and the extreme  water 
# lines are calculated. Depending on how close the extreme water line comes to the dune toe, 
# a Safe Corridor Width indicator of either "Low", "Medium", or "High" is assigned. The 
# closer the extreme water line, the higher the indicator. Indicators are exported at each 
# time step.  

# Building-scarp distance procedure: the distances between the dune toes and the simulated 
# scarp location (i.e. the landward most extent of the erosion) are calculated. Depending on 
# how close the scarp comes to the dune toe, a "Building- scarp distance" indicator is 
# assigned either a "Low", "Medium', or "High." The closer the scarp, the higher the 
# indicator. 

# Indicators are exported at each time step.  Note that the script initially was written 
# such that the locations of interest were buildings, hence the name of the indicator. Then, 
# property boundaries (plots) were used. Finally, it was determined that the dune toe would 
# be more appropriate to use in order to compute the indicator. This created a lack of 
# consistency with some of the syntax.

# ARGUMENTS FOR THE SCRIPT:
# Arguments for this script are set in run_forecast_loop*.bat and run_forecast_loop.py if 
# running the Python wrapper, and in the IndicatorsXBeachAdapter.xml file if using FEWS. 
# The following are the script’s arguments:
#     - regionHome: The path to the Region Home directory
#     - systemTimeStr: The system time for the forecast/hindcast, in the format: “YYYYMMDDHH”
#     - siteName: The name of the region. This will either be “Narrabeen” or “Mandurah”, and 
#     it is designated in hotspotLocations.csv
#     - workDir: Working directory. This should be the Module directory 
#     ([Region Home]\Modules\IndicatorsXBeach).

# KEY VARIABLES/INPUTS/PARAMETERS:
#     - diagOpen.txt: A template file that FEWS populates and uses as a log file
#     - forecast.pkl: The pickle file that stores all the attributes of the instance of the 
#     fewsForecast class
#     - forecast_hotspot.pkl: The pickle file that stores all the attributes of the instance 
#     of the hotspotForecast class
#     - corridor_pts_50m.shp: Positions of the dune toes along each cross-shore profile of 
#     the XBeach mesh (see Section 4.1.5.6)
#     - gauges\points: Folder containing positions of the extreme water line at each timestep, 
#     given both as point and line shapefiles.
#     - scarp\points: Folder containing positions of the maximum landward extent of erosion 
#     (i.e. the erosion scarp), given as point and line shapefiles
#     - ewl_XBeach_points.shp: Maximum extreme water line over the course of the entire 
#     XBeach simulation, in points
#     - maxEroScarp_points.shp: Maximum landward extent of erosion (scarp) over the entire 
#     XBeach simulation, in points
#     - dune toe-scarp distance indicator thresholds (defined in postProcTools.py, 
#     compute_bsd function): Thresholds that define the “Low”, “Medium”, and “High” indicators 
#     for the distance between the dune toe (or other point of interest) and the computed 
#     scarp. At the moment, these are set to default values of: 
#         - Low: distance > 20 m
#         - Medium: 10 m < distance <= 20 m
#         - High: distance <= 10 m
#     - Safe corridor width indicator thresholds (defined in postProcTools.py, compute_scw 
#     function): Thresholds that define the “Low”, “Medium”, and “High” indicators for the 
#     distance between the dune toe (or other point of interest) and the extreme water line. 
#     At the moment, these are set to default values of: 
#         - Low: distance > 10 m
#         - Medium: 5 m < distance <= 10 m
#         - High: distance <= 5 m

# KEY OUTPUTS:
#     - indicators\bsd: Folder containing the time-dependent building-scarp distance 
#     indicators (which are actually the dune toe-scarp distance indicators), expressed as 
#     points. 
#     - indicators\scw: Folder containing the time-dependent safe corridor width indicators, 
#     expressed as points.
#     - building-scarpDistOverall_pts.shp: Building-scarp distance indicators (i.e., dune 
#     toe-scarp distance indicators) representing the highest indicator levels over the entire 
#     forecast window. 
#     - safe-corridorOverall_pts.shp: Safe corridor width indicators representing the highest 
#     indicator levels over the entire forecast window
#     - diag.xml: The resulting diagnostic file that FEWS populates and uses (i.e. prints to 
#     its console) 
#     - forecast_hotspot.pkl: The updated pickle file that stores all the attributes of the 
#     hotspotForecast instance

# COMMAND TO DE-BUG AND MODIFY THIS SCRIPT INDIVIDUALLY:
# python [path to this script] [path to Region Home] [System time in format YYYYMMDDHH] [site name] [working directory, i.e. the path to the folder containing this script]
# e.g.,
# python C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\IndicatorsXBeach_dev/indicatorsMain.py C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus 20200208_0000 Narrabeen C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Modules\IndicatorsXBeach_dev
#
# ==========================================================================================


# Modules
import traceback
import os
import sys
import traceback
import shutil


def main(args=None):

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    regionHome = str(args[0])
    sysTime = str(args[1])
    siteName = str(args[2])
    workDir = str(args[3])


    #============== Modules ==============#
    import pickle
    from xbfewsTools import fewsUtils
    from xbfewsTools import postProcTools
    import geopandas as gpd
    import pandas as pd
    import numpy as np
    from shapely import geometry
    from xbfewsTools import fewsUtils
    

    #============== Parse system time and find directory of current forecast ==============#
    systemTime = fewsUtils.parseFEWSTime(sysTime)
    roundedTime = fewsUtils.round_hours(systemTime, 12)
    roundedTimeStr = roundedTime.strftime("%Y%m%d_%H%M") 
    forecastDir = os.path.join(regionHome,"Forecasts",roundedTimeStr)


    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    indicatorDir = os.path.join(regionHome,"Data\\Indicators\\Hotspot\\%s" % siteName)

    #============== Load FEWS forecast object ==============#
    fcst = pickle.load(open(os.path.join(forecastDir,"forecast.pkl"),"rb"))


    #============== Load hotspot forecast object ==============#
    regionName = fcst.hotspotDF.loc[fcst.hotspotDF['ID']==siteName]['Region'][0]
    hotspotForecastDir = os.path.join(forecastDir, regionName,"hotspot",siteName)
    hotspotFcst = pickle.load(open(os.path.join(hotspotForecastDir,"forecast_hotspot.pkl"),"rb"))
    epsg = int(hotspotFcst.xbeachEPSG)

    hotspotFcst.indicatorResultsDir = os.path.join(hotspotFcst.postProcessDir,"indicators")
    if not os.path.exists(hotspotFcst.indicatorResultsDir):
        os.makedirs(hotspotFcst.indicatorResultsDir)
    scwDir = os.path.join(hotspotFcst.indicatorResultsDir,"scw")
    scwDirPts = os.path.join(scwDir,"points")
    bsdDir = os.path.join(hotspotFcst.indicatorResultsDir, "bsd")
    bsdDirPts = os.path.join(bsdDir,'points')
    if not os.path.exists(scwDir):
        os.makedirs(scwDir)
    if not os.path.exists(scwDirPts):
        os.makedirs(scwDirPts)
    if not os.path.exists(bsdDir):
        os.makedirs(bsdDir)
    if not os.path.exists(bsdDirPts):
        os.makedirs(bsdDirPts)
    #plotsShp = os.path.join(indicatorDir,"lotsEPSG%s.shp" % hotspotFcst.xbeachEPSG)
    #corridorsShp = os.path.join(indicatorDir,"corridors50m.shp")
    plotsShp = os.path.join(indicatorDir,"corridor_pts_50m.shp")
    corridorsShp = os.path.join(indicatorDir,"corridor_pts_50m.shp")

    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write("</Diag>")


    #============== More Paths ==============#
    gaugesDir = os.path.join(hotspotFcst.postProcessDir,"gauges\\points")
    scarpDir = os.path.join(hotspotFcst.postProcessDir,"scarp\\points")


    #============== Load key files ==============#
    # Load plots shapefile as geopandas df
    plots_gdf = gpd.read_file(plotsShp)
    corridors_gdf = gpd.read_file(corridorsShp)
    ewlOverall = os.path.join(hotspotFcst.postProcessDir,"ewl_XBeach_points.shp")
    scarpOverall = os.path.join(hotspotFcst.postProcessDir,"maxEroScarp_points.shp")
    # Load these as geoseries
    ewlOverall = gpd.read_file(ewlOverall)
    if os.path.exists(scarpOverall):
        scarpOverall_gdf = gpd.read_file(scarpOverall)
    else:
        scarpOverall_gdf = None


    #========= Add key fields to plots_gdf and corridors_gdf =========#
    # Add the row index to the plots_gdf and corridors_gdf The dataframes
    # will then be merged on this value. This is an important step.
    # Otherwise, the storm impact indicators won't be computed 
    # correctly. 
    
    # Sort values by name. This will put them in north-to-south order.
    # The names were determined manually (this naming convention is)
    # deliberately north-south.
    plots_gdf = plots_gdf.sort_values('ID')
    plots_gdf = plots_gdf.reset_index(drop=True)
    # Assign a new field based on the index
    plots_gdf['rowInd'] = plots_gdf.index
    # Repeat the process for the corridors_gdf
    corridors_gdf = corridors_gdf.sort_values('ID')
    corridors_gdf = corridors_gdf.reset_index(drop=True)
    # Assign a new field based on the index
    corridors_gdf['rowInd'] = corridors_gdf.index

    #============== Error-handling ==============#
    # Check to make sure there are the same number of plots and corridors
    # as there are ewl and scarp points. Difference in the number of points
    # implies different longshore resolutions. plotsShp and corridorsShp
    # need to be manually created for each different grid used, or else
    # the indicator module will not work properly.
    if len(ewlOverall) != len(corridors_gdf):
        raise ValueError("Corridors shapefile does not have the same number of rows used in the XBeach model.")

    # Construct time series to iterate through
    # Numpy timedelta64 objects are easier to deal with
    tstep = np.timedelta64(hotspotFcst.tintg,'s')
    t_total = hotspotFcst.endTime - hotspotFcst.startTime
    # In seconds
    t_total = t_total.days*24.*60.*60 + t_total.seconds
    t_total = np.timedelta64(int(t_total),'s')
    tseries = np.arange(0, t_total+tstep, tstep)
    tseries = np.array(tseries, dtype=float)
    # Then express as hours because time is expressed as hours in files
    tseries_hrs = np.divide(tseries,3600.)

    ############################### Compute the building-scarp distance indicator ###############################
    # Timestep in hours
    for t_step in tseries_hrs:
        tstep_hrs_str = f'{(t_step):.2f}'.zfill(6)
        if t_step % 5 == 0:
            print("Processing BSD for time: %s hrs" % t_step)
        fname = "scarp_%shrs_points.shp" % tstep_hrs_str
        fPath = os.path.join(scarpDir,fname)
        # Be careful here - the "try" logic here could conceal bugs
        # This could potentially just assign everything as being "Low" risk
        try:
            scarp_gdf = gpd.read_file(fPath)
            # Merge the scarp_gdf with the plots_gdf
            # This ensures the correct points are being compared with one another
            scarp_gdf = scarp_gdf.merge(plots_gdf, how="inner", on="rowInd")
            # Re-name geometry columns
            # Regular "geometry" column contain the scarp locations
            # "geometry_plots" contains locations of where the indicator is being
            # measured from. Before, it was the locations of plots of land.
            # In this version, it is from the dune toe. So in this version, 
            # "geometry_plots" contains the dune toe geometries at every row in
            # the XBeach grid.
            scarp_gdf = scarp_gdf.rename(columns={"geometry_x":"geometry",
                                                  "geometry_y":"geometry_plots"})
            scarp_gdf = gpd.GeoDataFrame(scarp_gdf, geometry=scarp_gdf.geometry)
            scarp_gdf['bsd_dist'] = scarp_gdf.geometry_plots.apply(lambda g: scarp_gdf.distance(g).min())
            scarp_gdf['BSD'] = postProcTools.compute_bsd(scarp_gdf['bsd_dist'])
            # Remove the "geometry_plots" field so file can be exported
            scarp_gdf = scarp_gdf.drop(columns='geometry_plots',axis=1)
            scarp_gdf = scarp_gdf.set_crs(epsg=epsg)
        except:
            pass

        # Export these as points
        ofileName = "bsd_%shrs.shp" % tstep_hrs_str
        try:
            scarp_gdf.to_file(os.path.join(bsdDirPts,ofileName))
        except:
            pass
    
    # Compute overall BSD indicator for the entire forecast
    if scarpOverall_gdf is not None: # A scarp might not be detected
        # Convert column to integer
        scarpOverall_gdf = scarpOverall_gdf.astype({"rowInd": int})
        # Compute distance between each building plot and the scarp line
        scarpOverall_gdf= scarpOverall_gdf.merge(plots_gdf, how="inner", on="rowInd")
        scarpOverall_gdf = scarpOverall_gdf.rename(columns={"geometry_x":"geometry",
                                                  "geometry_y":"geometry_plots"})
        scarpOverall_gdf = gpd.GeoDataFrame(scarpOverall_gdf, geometry=scarpOverall_gdf.geometry)
        scarpOverall_gdf['bsd_dist'] = scarpOverall_gdf.geometry_plots.apply(lambda g: scarpOverall_gdf.distance(g).min())
        scarpOverall_gdf['BSD'] = postProcTools.compute_bsd(scarpOverall_gdf['bsd_dist'])
        scarpOverall_gdf = scarpOverall_gdf.drop(columns="geometry_plots", axis=1)
    else:
        plots_gdf["BSD"] = "Low"
        scarpOverall_gdf = plots_gdf
    scarpOverall_gdf.to_file(os.path.join(hotspotFcst.indicatorResultsDir, "building-scarpDistOverall_pts.shp"))

    ############################### Compute the safe corridor width indicator ###############################
    for t_step in tseries_hrs:
        tstep_hrs_str = f'{(t_step):.2f}'.zfill(6)
        if t_step % 5 == 0:
            print("Processing SCW for time: %s hrs" % t_step)
        fname = "gauges_%shrs_points.shp" % tstep_hrs_str
        fPath = os.path.join(gaugesDir,fname)
        ewl_gdf = gpd.read_file(fPath)
        # Compute distances between ewl and corridors at timestep
        ewl_gdf['ewl_dist'] = corridors_gdf.geometry.apply(lambda g: ewl_gdf.distance(g).min())
        ewl_gdf['SCW'] = postProcTools.compute_scw(ewlDistSeries=ewl_gdf['ewl_dist'])
        # export to a file
        ewl_gdf.to_file(os.path.join(scwDirPts,"scw_%shrs.shp" % (tstep_hrs_str)))

    # Compute the distance between each corridor section and the extreme water line
    ewlOverall['ewl_dist'] = ewlOverall.geometry.apply(lambda g: corridors_gdf.distance(g).min())
    ewlOverall['SCW'] = postProcTools.compute_scw(ewlOverall['ewl_dist'])
    ewlOverall.to_file(os.path.join(hotspotFcst.indicatorResultsDir, "safe-corridorOverall_pts.shp"))

## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise