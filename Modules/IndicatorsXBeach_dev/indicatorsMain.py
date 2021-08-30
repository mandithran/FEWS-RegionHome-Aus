# Modules
import traceback
from xbfewsTools import fewsUtils
import os
import sys
import traceback
import shutil
import pickle
from xbfewsTools import fewsUtils
from xbfewsTools import postProcTools
import geopandas as gpd
import pandas as pd
import numpy as np
import glob
import ntpath
from datetime import datetime, timedelta
from shapely.geometry import Point, LineString, shape


# Debugging
# Forecast:
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\IndicatorsXBeach_dev/indicatorsMain.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\IndicatorsXBeach_dev 20200713_0000 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus Narrabeen


def main(args=None):

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    workDir = str(args[0])
    sysTime = str(args[1])
    regionHome = str(args[2])
    siteName = str(args[3])
    #workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\IndicatorsXBeach_dev"
    #sysTime = "20200203_0000"
    #regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
    #siteName = "Narrabeen"

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
    #corridorsShp = os.path.join(indicatorDir,"corridors100m.shp")
    plotsShp = os.path.join(indicatorDir,"corridor_pts_100m.shp")
    corridorsShp = os.path.join(indicatorDir,"corridor_pts_100m.shp")

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
    plots_df = gpd.read_file(plotsShp)
    corridors_df = gpd.read_file(corridorsShp)
    ewlOverall = os.path.join(hotspotFcst.postProcessDir,"ewl_XBeach_points.shp")
    scarpOverall = os.path.join(hotspotFcst.postProcessDir,"maxEroScarp_points.shp")
    # Load these as geoseries
    ewlOverall = gpd.read_file(ewlOverall)
    try:
        scarpOverall = gpd.read_file(scarpOverall)
    except:
        pass

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
        # And just assign everything as being "Low"
        try:
            scarp_gdf = gpd.read_file(fPath)
            scarp_gdf['bsd_dist'] = plots_df.geometry.apply(lambda g: scarp_gdf.distance(g).min())
            scarp_gdf['BSD'] = postProcTools.compute_bsd(scarp_gdf['bsd_dist'])
        except:
            pass
            #scarp_gdf["BSD"] = "Low"
        # Export these as points
        ofileName = "bsd_%shrs.shp" % tstep_hrs_str
        try:
            scarp_gdf.to_file(os.path.join(bsdDirPts,ofileName))
        except:
            pass

    # Compute overall BSD indicator for the entire forecast
    try: # A scarp might not be detected
        # Compute distance between each building plot and the scarp line
        scarpOverall['bsd_dist'] = plots_df.geometry.apply(lambda g: scarpOverall.distance(g).min())
        scarpOverall['BSD'] = postProcTools.compute_bsd(scarpOverall['bsd_dist'])
    except:
        plots_df["BSD"] = "Low"
    scarpOverall.to_file(os.path.join(hotspotFcst.indicatorResultsDir, "building-scarpDistOverall_pts.shp"))
    

    ############################### Compute the safe corridor width indicator ###############################
    for t_step in tseries_hrs:
        tstep_hrs_str = f'{(t_step):.2f}'.zfill(6)
        if t_step % 5 == 0:
            print("Processing SCW for time: %s hrs" % t_step)
        fname = "gauges_%shrs_points.shp" % tstep_hrs_str
        fPath = os.path.join(gaugesDir,fname)
        ewl_gdf = gpd.read_file(fPath)
        # Compute distances between ewl and corridors at timestep
        ewl_gdf['ewl_dist'] = corridors_df.geometry.apply(lambda g: ewl_gdf.distance(g).min())
        ewl_gdf['SCW'] = postProcTools.compute_scw(ewlDistSeries=ewl_gdf['ewl_dist'])
        # export to a file
        ewl_gdf.to_file(os.path.join(scwDirPts,"scw_%shrs.shp" % (tstep_hrs_str)))

        # OLD WAY WHERE INDICATORS ASSIGNED TO FIXED DUNE TOE POINTS RATHER THAN MOVING EWL POINTS
        #corridors_df_copy = corridors_df.copy()
        #corridors_df_copy['ewl_dist'] = ewl_gdf.geometry.apply(lambda g: corridors_df_copy.distance(g).min())
        #corridors_df_copy['SCW'] = postProcTools.compute_scw(ewlDistSeries=corridors_df_copy['ewl_dist'])
        # export to a file
        #corridors_df_copy.to_file(os.path.join(scwDir,"scw_%shrs.shp" % (tstep_hrs_str)))

    # Compute the distance between each corridor section and the extreme water line
    ewlOverall['ewl_dist'] = ewlOverall.geometry.apply(lambda g: corridors_df.distance(g).min())
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