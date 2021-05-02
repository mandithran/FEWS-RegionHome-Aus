#https://docs.dea.ga.gov.au/notebooks/Frequently_used_code/Working_with_time.html
import xarray as xr
import os
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString, shape
from xbfewsTools import postProcTools

################ Paths ################

regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
xbWorkDir = os.path.join(regionHome, "Modules\\XBeach\\Narrabeen\\runs\\latest\\workDir")
ncOut = os.path.join(xbWorkDir, "xboutput.nc")
postProcessDir = os.path.join(xbWorkDir,"postProcess")
gaugesDir = os.path.join(postProcessDir,"gauges")
gaugesDirPts = os.path.join(gaugesDir, "points")
gaugesDirLines = os.path.join(gaugesDir, "lines")


################ Variables ################
epsg = int(28356) # EPSG:28356

# Make directories if they don't exist
if not os.path.exists(postProcessDir):
    os.makedirs(postProcessDir)
if not os.path.exists(gaugesDir):
    os.makedirs(gaugesDir)
if not os.path.exists(gaugesDirPts):
    os.makedirs(gaugesDirPts)
if not os.path.exists(gaugesDirLines):
    os.makedirs(gaugesDirLines)


################ Load Output ################
ds = xr.open_dataset(ncOut)
# Just gauges for now
#ds = ds[['point_xz', 'point_yz', 'point_zs']]


################ Remove dummy point from gauges output ################
# Dummy point needed for XBeach to register that there are gauges
# Set with "npoints" parameter in params.txt
paramsFile = os.path.join(xbWorkDir,"params.txt")
# Return line number with desired point
lineNumber = postProcTools.search_string_in_file(paramsFile,"npoints")
lineNumber = lineNumber[0][0] + 1 # We want the line number directly below where "npoints" appears
dummyPt = postProcTools.search_by_line_num(paramsFile,lineNumber)
# Convert dummy pt to point geometry
dummyPt = dummyPt.split()
dummyPt = Point(int(dummyPt[0]),int(dummyPt[1]))
# Convert xarray ds to geodataframe to do point searching
dsSearch = ds[['point_xz', 'point_yz', 'point_zs']]
xbgdf = dsSearch.to_dataframe()
xbgdf = gpd.GeoDataFrame(xbgdf, geometry=gpd.points_from_xy(xbgdf.point_xz,xbgdf.point_yz))
xbgdf.set_crs(epsg)
# unary union of the geomtries 
pts = xbgdf.geometry.unary_union
ptIndex = postProcTools.nearGeom(dummyPt, pts=pts, gdfIn=xbgdf, outVar="index")[0]
# Remove dummy pt from dataset
ds = ds.drop_sel(points=0)


################ Loop through, export points and lines for Extreme water line ################
for d in np.arange(0,ds["pointtime"].sizes["pointtime"],1):
    print("Processing time step %s" % d)
    time= ds["pointtime"][d].values
    time_str = str(int(time)/3600).zfill(4)
    ds_sub = ds.isel({"pointtime":d})
    xx = ds_sub["point_xz"][:].values.flatten()
    yy = ds_sub["point_yz"][:].values.flatten()
    zz = ds_sub["point_zs"][:].values.flatten()
    df = pd.DataFrame({"x":xx,
                        "y":yy,
                        "z":zz})
    # Export point shapefile
    if time % 3600 == 0:
        geometry = [Point(xy) for xy in zip (xx,yy)]
        gdf = gpd.GeoDataFrame(df, geometry=geometry,crs=epsg)
        gdf.to_file(os.path.join(gaugesDirPts,"gauges_%shrs.shp" % time_str))
        # Export line shapefile
        gdf2 = gpd.GeoSeries(LineString(gdf.geometry.tolist()),crs=epsg)
        gdf2.to_file(os.path.join(gaugesDirLines,"gauges_%shrs_lines.shp" % time_str))



################ Determine extreme water line from XBeach output ################

colIndeces = []
for t in np.arange(0,ds["pointtime"].sizes["pointtime"],1):
    yind = 0
    colIndex = []
    ds_sub = ds.isel({"pointtime":t})
    for searchX in ds_sub['point_xz'].values:
        xx = ds.globalx[yind,:].values
        # Find point that is closest to gauge's x value
        landwardx = min(xx, key= lambda x:abs(x-searchX))
        # Return x index of this point
        landwardColInd = np.where(xx==landwardx)[0][0]
        colIndex.append(landwardColInd)
        yind += 1
    colIndeces.append(colIndex)

dff = pd.DataFrame(colIndeces)
# Return maximum value for each column
colIndeces = dff.max().values

# Loop through these values and return the x and y locations as shapely points
maxWaterLine = []
yind = 0
for searchI in colIndeces:
    xpt = ds.globalx[yind,:][searchI]
    ypt = ds.globaly[:,searchI][yind]
    point = Point(xpt,ypt)
    maxWaterLine.append(point)
    yind += 1

# Export max water line as GeoSeries, convert a line shapefile
gdf3 = gpd.GeoSeries(LineString(maxWaterLine),crs=epsg)
gdf3.to_file(os.path.join(postProcessDir,"ewl_XBeach.shp"))


