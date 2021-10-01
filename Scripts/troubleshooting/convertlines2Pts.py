"""
convertlines2Pts.py
Author: Mandi Thran
Date: 01/10/21

DESCRIPTION:
This script converts the extreme water line and erosion scarp line shapefiles to points. 
"""

#=========== Modules ===========#
import os
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point


#=========== Paths ===========#
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
forecastsDir = os.path.join(regionHome,"Forecasts")


#=========== Variables ===========#
regionName = "NSW"
siteName = "Narrabeen"
epsg = int(28356)
start = np.datetime64("2020-02-12 00:00")
end = np.datetime64("2020-02-29 12:00")
deltat = np.timedelta64(12, "h")
series = np.arange(start,end+deltat,deltat)

def linestring_to_points(feature,line):
    return {feature:line.coords}

def line_to_points(gdf,epsg):
    gdf['points'] = gdf.apply(lambda x: [y for y in x['geometry'].coords], axis=1)
    gdf_d = gdf.to_dict('records')
    points = [Point(pt[0], pt[1]) for pt in gdf_d[0]['points']]
    gdf_out = gpd.GeoSeries(points)
    gdf_out = gdf_out.set_crs(epsg=epsg)
    return gdf_out


#================== Loop through each  of the forecasts ==================#
for dt in series:
    print(dt)
    dtpy = pd.to_datetime(str(dt)) 
    dt_str = dtpy.strftime("%Y%m%d_%H%M")
    xbDir = os.path.join(forecastsDir, dt_str, regionName, "hotspot", siteName, "XBeach")
    postprocDir = os.path.join(xbDir, "postProcess")
    gaugesDir = os.path.join(postprocDir,"gauges")
    gaugesLineDir = os.path.join(gaugesDir,"lines")
    gaugesPointsDir = os.path.join(gaugesDir,"points")
    if not os.path.exists(gaugesPointsDir):
        os.makedirs(gaugesPointsDir)
    #=================== EWL ===================#
    print("Processing extreme water lines...")
    # Time-dependent shapefiles
    for ifile in os.listdir(gaugesLineDir):
        if ".shp" in ifile:
            fileTime = ifile.split("_")[1].split("h")[0]
            if float(fileTime) % 10 == 0:
                print(ifile)
            gdf = gpd.read_file(os.path.join(gaugesLineDir,ifile))
            gdf_out = line_to_points(gdf,epsg)
            gdf_out.to_file(os.path.join(gaugesPointsDir,"gauges_%shrs_points.shp" % fileTime))
    # Overall forecast EWL
    ewlOverall = os.path.join(postprocDir,"ewl_XBeach.shp")
    gdf = gpd.read_file(ewlOverall)
    gdf_out = line_to_points(gdf,epsg)
    gdf_out.to_file(os.path.join(postprocDir,"ewl_XBeach_points.shp"))
    #=================== Scarp ===================#
    try:
        scarpDir = os.path.join(postprocDir,"scarp")
        scarpPointsDir = os.path.join(scarpDir,'points')
        if not os.path.exists(scarpPointsDir):
            os.makedirs(scarpPointsDir)
        print("Processing scarp lines...")
        # Time-dependent shapefiles
        for ifile in os.listdir(scarpDir):
            if ".shp" in ifile:
                fileTime = ifile.split("_")[1].split("h")[0]
                if float(fileTime) % 10 == 0:
                    print(ifile)
                gdf = gpd.read_file(os.path.join(scarpDir,ifile))
                gdf_out = line_to_points(gdf,epsg)
                gdf_out.to_file(os.path.join(scarpPointsDir,"scarp_%shrs_points.shp" % fileTime))
        # Overall forecast EWL
        scarpOverall = os.path.join(postprocDir,"maxEroScarp.shp")
        gdf = gpd.read_file(scarpOverall)
        gdf_out = line_to_points(gdf,epsg)
        gdf_out.to_file(os.path.join(postprocDir,"maxEroScarp_points.shp"))
    except:
        pass