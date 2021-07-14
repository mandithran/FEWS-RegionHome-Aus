# Note: there's some extraneous code in here that processes the maximum water line (total water level)
# from time-averaged outputs. Virtual run-up gauges have turned out to be the preferred option.
# Leaving in the extra code for now, though

################ Modules ################
import xarray as xr
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, shape
from xbfewsTools import postProcTools

################ Variables ################
epsg = int(28356)

################ Paths ################
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
# TODO: CHANGE DIRECTORY BACK
xbWorkDir = os.path.join(regionHome, "Modules\\XBeach\\Narrabeen\\runs\\latest\\workDir")
postProcessDir = os.path.join(xbWorkDir,"postProcess")
#mwlDir = os.path.join(postProcessDir,"mwl")
scarpDir = os.path.join(postProcessDir,"scarp")
ncOut = os.path.join(xbWorkDir, "xboutput.nc")

# Make directories if they don't exist
if not os.path.exists(postProcessDir):
    os.makedirs(postProcessDir)
#if not os.path.exists(mwlDir):
#    os.makedirs(mwlDir)
if not os.path.exists(scarpDir):
    os.makedirs(scarpDir)


################ TODO: replace with pickle ################
# Read information about model run
paramsFile = os.path.join(xbWorkDir,"params.txt")
# Return line number with desired point
line = postProcTools.search_string_in_file(paramsFile,"tintm")
line = str(line[0])
tint = int(line.split(" ")[3].split("'")[0]) # in seconds


################ Load Output ################
ds = xr.open_dataset(ncOut)
# Isolate dataset at initial time step to get initial elevation zb
# Goes to next timestep because of initial slumping 
# TODO: modify this to spin-up window
ds_zbi = ds.isel({"globaltime":13})


################ Determine water line and erosion scarp at each time step ################
# Iterate over all rows
# globaly[ny,nx] -> ds.globaly[:,0] grabs the first nx (column) and all rows (ny)
# Initialize dataframe
df = pd.DataFrame(columns=["timeStepMins","xWater","yWater",
                            "xScarp", "yScarp","rowInd", "colIndWater"
                            "colIndexScarp"])

# Starts at timestep 2 because of initial slumping creating artefacts in erosion scarp line
for timestep in np.arange(15,ds["meantime"].sizes["meantime"],1):

    print("Processing time step %s" % timestep)
    # Make string for timestep in number of minutes
    tstep_hrs = int((timestep*tint)/3600)
    tstring = str(tstep_hrs).zfill(4)
    # Initialize timestep dataframe
    dftstep = pd.DataFrame(columns=["xWater","yWater",
                                "xScarp", "yScarp"])
    # Isolate at timestep
    dsstep = ds.isel({"meantime":timestep})
    dsstep = dsstep.isel({"globaltime":timestep+1}) # global time and mean time not the same

    #print(timestep)
    #print(ds.meantime)
    #print(ds.globaltime)
    
    for index in np.arange(0,len(ds.globaly[:,0]),1):

        """############# Find maximum water level line in each cross-shore transect #############
        # Access water depth at each row
        # TODO: evaluate whether hh_max or hh better
        #depths = dsstep.hh_max[index,:].values
        watlevs = dsstep.zs_max[index,:].values
        bedlevs = dsstep.zb[index,:].values
        depths = watlevs-bedlevs
        # Evaluate whether water depth is >= 0.05 m (5 cm)
        depth_bool = depths>0.05
        # Determine highest x index of those points (i.e. the landward-most index)
        maxIndex = np.max(np.where(depth_bool))
        # Get point x,y point locations for the water line in each row
        xWater = dsstep.globalx[index,maxIndex].values
        yWater = dsstep.globaly[index,maxIndex].values"""

        ############# Find erosion scarp #############
        # Access initial elevation at each row
        elev_i = ds_zbi.zb[index,:].values
        # Access elevation at each row (cross-shore, x points)
        elevations = dsstep.zb[index,:].values
        # Compute the change in elevation from the start of simulation
        deltaz = elev_i - elevations
        # Evalute whether change in elevation surpasses 0.5 m 
        elev_bool = deltaz > 0.05
        # TODO: figure out what to do if it can't find a scarp... and if no morpho is actually run. Pickle?? YAS!
        # Determine highest x index of those points (i.e. the landward-most index)
        try:
            maxIndex2 = np.max(np.where(elev_bool))
            # Get point x,y point locations for the erosion scarp in each row
            xScarp = dsstep.globalx[index,maxIndex2].values
            yScarp = dsstep.globaly[index,maxIndex2].values
            
            ######### Append information to main dataframe######### 
            """data = {"timeStepHrs":[tstep_hrs],"xWater":[xWater],"yWater":[yWater],
                    "xScarp":[xScarp],"yScarp":[yScarp],
                    "rowInd":[index],"colIndWater":[maxIndex],
                    "colIndexScarp":[maxIndex2]}"""
            data = {"timeStepHrs":[tstep_hrs],
                    "xScarp":[xScarp],"yScarp":[yScarp],
                    "rowInd":[index],
                    "colIndexScarp":[maxIndex2]}
            dftmp = pd.DataFrame(data)
            df = df.append(dftmp)

            ######### Append information to time step's dataframe ######### 
            dftstep = dftstep.append(dftmp)

            # Export line shapefile for maximum water line (mwl)
            """gdf = gpd.GeoDataFrame(dftstep, geometry=gpd.points_from_xy(dftstep.xWater, dftstep.yWater), 
                                crs=epsg)
            gdf = gdf[["geometry"]]
            gdf = gpd.GeoSeries(LineString(gdf.geometry.tolist()),crs=epsg)
            gdf.to_file(os.path.join(mwlDir,"mwl_%shrs.shp" % tstring))"""
            # Export line shapefile for erosion scarp 
            gdf2 = gpd.GeoDataFrame(dftstep, geometry=gpd.points_from_xy(dftstep.xScarp, dftstep.yScarp), crs=epsg)
            gdf2 = gdf2[["geometry"]]
            gdf2 = gpd.GeoSeries(LineString(gdf2.geometry.tolist()),crs=epsg)
            gdf2.to_file(os.path.join(scarpDir,"scarp_%shrs.shp" % tstring))
        except:
            pass
    


################ Determine maximum water line from XBeach output ################
# Group by row index
# Of these groups, find the max x index 
"""gdf_wl = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.xWater, df.yWater), 
                           crs=epsg)
df_mwl = gdf_wl.groupby(['rowInd'])['colIndWater'].agg(
        [('colIndWaterMax', 'max')])
# Merge dataframes to get the geometry
df_mwl = pd.merge(gdf_wl[["rowInd","geometry","colIndWater"]],
                  df_mwl,
                   left_on = ["rowInd","colIndWater"],
                   right_on = ["rowInd","colIndWaterMax"],
                   how = "right")

# Drop duplicates
df_mwl = df_mwl.drop_duplicates()

# Export extreme water line 
gdf = gpd.GeoDataFrame(df_mwl, geometry="geometry", 
                           crs=epsg)
gdf = gdf[["geometry"]]
gdf = gpd.GeoSeries(LineString(gdf.geometry.tolist()),crs=epsg)
gdf.to_file(os.path.join(postProcessDir,"mwl.shp"))"""


################ Determine maximum erosion scarp from XBeach output ################
gdf_es = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.xScarp, df.yScarp), 
                           crs=epsg)
df_es = gdf_es.groupby(['rowInd'])['colIndexScarp'].agg(
        [('colIndexScarpMax', 'max')])
# Merge dataframes to get the geometry
df_es = pd.merge(gdf_es[["rowInd","geometry","colIndexScarp"]],
                  df_es,
                   left_on = ["rowInd","colIndexScarp"],
                   right_on = ["rowInd","colIndexScarpMax"],
                   how = "right")
# Drop duplicates
df_es = df_es.drop_duplicates()
# Export max erosion scarp line 
gdf = gpd.GeoDataFrame(df_es, geometry="geometry", 
                           crs=epsg)
gdf = gdf[["geometry"]]
gdf = gpd.GeoSeries(LineString(gdf.geometry.tolist()),crs=epsg)
gdf.to_file(os.path.join(postProcessDir,"maxEroScarp.shp"))