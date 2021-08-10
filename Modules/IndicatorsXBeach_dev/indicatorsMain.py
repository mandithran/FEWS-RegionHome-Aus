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
    plotsShp = os.path.join(indicatorDir,"lotsEPSG%s.shp" % hotspotFcst.xbeachEPSG)
    corridorsShp = os.path.join(indicatorDir,"corridors100m.shp")

    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write("</Diag>")

    #============== Load key files ==============#
    ewlOverall = os.path.join(hotspotFcst.xbWorkDir,"postProcess","ewl_XBeach.shp")
    scarpOverall = os.path.join(hotspotFcst.xbWorkDir,"postProcess","maxEroScarp.shp")
    # Load these as geoseries
    ewlOverall = gpd.read_file(ewlOverall)
    try:
        scarpOverall = gpd.read_file(scarpOverall)
    except:
        pass

    ############################### Compute the building-scarp distance indicator ###############################
    # Load plots shapefile as geopandas df
    plots_df = gpd.read_file(plotsShp)
    # Drop the fields you don't need
    fields2keep = ['cadid','geometry']
    plots_df = plots_df[fields2keep]
    try: # A scarp might not be detected
        # Compute distance between each building plot and the scarp line
        plots_df['scarp_dist'] = plots_df.geometry.apply(lambda g: scarpOverall.distance(g).min())
        #============== Thresholding ==============#
        thresholdsBSD = [{"lower": 0, "upper": 10, "level": "High"},
            {"lower": 10, "upper": 20, "level": "Medium"},
            {"lower": 20, "upper": 10000, "level": "Low"}]
        thresholdsBSD_df = pd.DataFrame(thresholdsBSD)
        #create bins
        bins = list(thresholdsBSD_df["upper"])
        bins.insert(0,0)
        plots_df["BSD"] = pd.cut(plots_df["scarp_dist"], bins, labels = thresholdsBSD_df["level"]).astype(str)
        #============== Label instances where lines intersect bounds ==============#
        # If they intersect, algorithm above throws a "nan"
        plots_df = plots_df.replace({'BSD':'nan'},"High")
    except:
        plots_df["BSD"] = "Low"
    plots_df.to_file(os.path.join(hotspotFcst.indicatorResultsDir, "building-scarpDistOverall.shp"))
    

    ############################### Compute the safe corridor width indicator ###############################
    corridors_df = gpd.read_file(corridorsShp)
    # Compute the distance between each corridor section and the scarp line
    corridors_df['ewl_dist'] = corridors_df.geometry.apply(lambda g: ewlOverall.distance(g).min())
    thresholdsSCW = [{"lower": 0, "upper": 5, "level": "High"},
        {"lower": 5, "upper": 10, "level": "Medium"},
        {"lower": 10, "upper": 10000, "level": "Low"}]
    thresholdsSCW_df = pd.DataFrame(thresholdsSCW)
    #create bins
    bins = list(thresholdsSCW_df["upper"])
    bins.insert(0,0)
    corridors_df["SCW"] = pd.cut(corridors_df["ewl_dist"], bins, labels = thresholdsSCW_df["level"]).astype(str)
    #============== Label instances where lines intersect bounds ==============#
    # If they intersect, algorithm above throws a "nan"
    corridors_df = corridors_df.replace({'SCW':'nan'},"High")
    #print(postProcessDir)
    corridors_df.to_file(os.path.join(hotspotFcst.indicatorResultsDir, "safe-corridorOverall.shp"))
    # Copy and rename diagOpen.txt
    fewsUtils.clearDiagLastLine(diagFile)
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3,"No erosion scarp detected"))
        fileObj.write("</Diag>")



## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise