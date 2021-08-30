# Modules
import os
import sys
import traceback
import shutil
import pickle
from xbfewsTools import fewsUtils
import geopandas as gpd
from shapely.geometry import Point, LineString, shape
import xarray as xr
from xbfewsTools import postProcTools
import numpy as np
import pandas as pd

# For debugging:
# Forecast:
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PostProcessXBeach_dev/postprocessMain.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PostProcessXBeach_dev 2020030100 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus Narrabeen
# Hindcast
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PostProcessXBeach_dev/postprocessMain.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PostProcessXBeach_dev 2020020300 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus Narrabeen

def main(args=None):

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # Path to Region Home, defined in global properties file
    workDir = str(args[0])
    # System time according to FEWS
    sysTimeStr = str(args[1])
    # Region home
    regionHome = str(args[2])
    # Site Name
    siteName = str(args[3])

    #============== Determine appropriate forecast directory ==============#
    # This is based on system time given from FEWS
    modelRunDir = os.path.join(regionHome,"Modules\\XBeach",siteName,
                               "%sSystemTime-%s" %(sysTimeStr,siteName))
    
    
    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    hotspotLocSet = os.path.join(regionHome,"Config\\MapLayerFiles\\hotspotLocations.csv")


    #============== Load hotspot location set ==============#
    hotspotLocSet = pd.read_csv(hotspotLocSet)
    regionName = hotspotLocSet.loc[hotspotLocSet['ID']==siteName]['Region'][0]


    #============== Load hotspot forecast object with pickle ==============#
    # C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Forecasts\20200201_0000\NSW\hotspot\Narrabeen
    t_str = sysTimeStr[0:8] + '_' + sysTimeStr[8:] + '00'
    fcstHotspot = os.path.join(regionHome,"Forecasts",t_str,regionName,"hotspot",siteName,"forecast_hotspot.pkl")
    fcstHotspot = pickle.load(open(fcstHotspot, "rb"))
    

    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3, "Post-processing hotspot run: %s" % fcstHotspot.runName))
        fileObj.write(fewsUtils.write2DiagFile(3, "Forecast for time period starting at: %s" % fcstHotspot.roundedTime))
        fileObj.write("</Diag>")


    #============== Copy over contents of run directory for post-processing ==============#
    from distutils.dir_util import copy_tree
    copy_tree(fcstHotspot.moduleDir,fcstHotspot.xbWorkDir)


    #============== Create and designate some new paths ==============#
    ncOut = os.path.join(fcstHotspot.xbWorkDir, "xboutput.nc")
    postProcessDir = os.path.join(fcstHotspot.xbWorkDir,"postProcess")
    gaugesDir = os.path.join(postProcessDir,"gauges")
    gaugesDirPts = os.path.join(gaugesDir, "points")
    gaugesDirLines = os.path.join(gaugesDir, "lines")
    scarpDir = os.path.join(postProcessDir,"scarp")
    scarpDirPts = os.path.join(scarpDir, "points")
    scarpDirLines = os.path.join(scarpDir, "lines")
    ncOut = os.path.join(fcstHotspot.xbWorkDir, "xboutput.nc")
    # Make directories if they don't exist
    if not os.path.exists(postProcessDir):
        os.makedirs(postProcessDir)
    if not os.path.exists(gaugesDir):
        os.makedirs(gaugesDir)
    if not os.path.exists(gaugesDirPts):
        os.makedirs(gaugesDirPts)
    if not os.path.exists(gaugesDirLines):
        os.makedirs(gaugesDirLines)
    if not os.path.exists(scarpDir):
        os.makedirs(scarpDir)
    if not os.path.exists(scarpDirPts):
        os.makedirs(scarpDirPts)
    if not os.path.exists(scarpDirLines):
        os.makedirs(scarpDirLines)


    ################ Load Output ################
    ds = xr.open_dataset(ncOut)


    #============== Re-load hotspot forecast object with pickle ==============#
    # Read it now from original forecast directory
    fcstHotspot = pickle.load(open(os.path.join(fcstHotspot.forecastDir,"forecast_hotspot.pkl"), "rb"))
    # Caluclate the total run time, including spin-up time
    fcstHotspot.totalRunTime = fcstHotspot.endTime - fcstHotspot.startTime
    epsg = int(fcstHotspot.xbeachEPSG)
    fcstHotspot.postProcessDir = os.path.join(fcstHotspot.xbWorkDir,"postProcess")
    

    #print(fcstHotspot.postProcessDir)
    #fcstHotspot.postProcessDir = 43200.0
    #with open(os.path.join(fcstHotspot.forecastDir,"forecast_%s.pkl" % fcstHotspot.type), "wb") as output:
    #        pickle.dump(fcstHotspot, output, pickle.HIGHEST_PROTOCOL)

    ################################# Process extreme water line #################################
    #========== Remove dummy point from gauges output ==========#
    dummyPt = Point(fcstHotspot.dummyPtX,fcstHotspot.dummyPtY)
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
    #========== Loop through, export points and lines for Extreme water line ==========#
    colIndecesTotalRun = []
    colIndeces = []
    for d in np.arange(0,ds["pointtime"].sizes["pointtime"],1):
        if d % 100 == 0:    
            print("Processing time step %s" % d)
        time= ds["pointtime"][d].values
        time_str = f'{(time/3600):.2f}'.zfill(6)
        # Subset the dataset by point time step
        ds_sub = ds.isel({"pointtime":d})
        colIndex = []
        yind = 0
        # For each time step slice, loop through each row
        # And locate the x index of the point that is neareest to where the gauge it
        for searchX in ds_sub['point_xz'].values:
            xx = ds.globalx[yind,:].values
            # Find point that is closest to gauge's x value
            landwardx = min(xx, key= lambda x:abs(x-searchX))
            # Return x index of this point
            landwardColInd = np.where(xx==landwardx)[0][0]
            # Append this point to the collection of points specific to the time step
            colIndex.append(landwardColInd)
            yind += 1
        colIndeces.append(colIndex)
        colIndecesTotalRun.append(colIndex)
        if time % 900 == 0: # Exports every 15 min (900 sec)
            dff = pd.DataFrame(colIndeces)
            # Return maximum value for each column over the 15 min interval
            colIndeces = dff.max().values
            # Loop through these values and return the x and y locations as shapely points
            maxWaterLine = []
            yind = 0
            # Find the relevant x and y values for these max landward gauge points
            for searchI in colIndeces:
                xpt = ds.globalx[yind,:][searchI]
                ypt = ds.globaly[:,searchI][yind]
                point = Point(xpt,ypt)
                maxWaterLine.append(point)
                yind += 1
            # Export max water line as GeoSeries, convert a line shapefile
            gdf1 = gpd.GeoSeries(maxWaterLine,crs=epsg)
            gdf1.to_file(os.path.join(gaugesDirPts,"gauges_%shrs_points.shp" % time_str))
            gdf2 = gpd.GeoSeries(LineString(maxWaterLine),crs=epsg)
            gdf2.to_file(os.path.join(gaugesDirLines,"gauges_%shrs_lines.shp" % time_str))
            # Reset the column indeces for the next 15 minute interval
            colIndeces = []
    #========== Determine extreme water line from XBeach output ==========#
    dff = pd.DataFrame(colIndecesTotalRun)
    # Return maximum value for each column
    colIndecesTotalRun = dff.max().values
    # Loop through these values and return the x and y locations as shapely points
    maxWaterLine = []
    yind = 0
    for searchI in colIndecesTotalRun:
        xpt = ds.globalx[yind,:][searchI]
        ypt = ds.globaly[:,searchI][yind]
        point = Point(xpt,ypt)
        maxWaterLine.append(point)
        yind += 1
    # Export max water line as GeoSeries, convert a line shapefile
    gdf3 = gpd.GeoSeries(maxWaterLine,crs=epsg)
    gdf3.to_file(os.path.join(fcstHotspot.postProcessDir,"ewl_XBeach_points.shp"))
    gdf4 = gpd.GeoSeries(LineString(maxWaterLine),crs=epsg)
    gdf4.to_file(os.path.join(fcstHotspot.postProcessDir,"ewl_XBeach.shp"))

    ################################# Process erosion scarp #################################
    # Check to see that morstart isn't equal to the total run time
    # This indicates that morphology was turned on before the run ended
    # If this condition is satisfied, the erosion line is calculated
    if fcstHotspot.morstart < fcstHotspot.totalRunTime.total_seconds():
        # We want to return the morphology at a time that is a little after the "rounded time"
        # This is right when morphology is meant to be switched on, and it's also after the first
        # couple time steps, where subaerial slumping can mess up the position of the computed
        # erosion scarp. Correct index is the spinUp interval divided by the timestep 
        # Starts one of the first timesteps after the rounded time because of initial slumping creating artefacts in erosion scarp lines
        roundedTimeIndex = int((fcstHotspot.roundedTime - fcstHotspot.startTime).seconds/fcstHotspot.tintm)
        dtout = (ds.meantime[1]-ds.meantime[0]).values
        eroStartIndex = int(fcstHotspot.morstart/dtout)+1
        ds_zbi = ds.isel({"globaltime":eroStartIndex})
        # Initialize dataframe
        df = pd.DataFrame(columns=["timeStepMins","xScarp", 
                                "yScarp","rowInd",
                                "colIndexScarp"])
        #for timestep in np.arange(eroStartIndex+2,ds["meantime"].sizes["meantime"],1):
        for timestep in np.arange(eroStartIndex+2,ds["globaltime"].sizes["globaltime"],1):
            if timestep == roundedTimeIndex:
                print("Starting at timestep %s " % roundedTimeIndex)
            if timestep % 10 == 0: 
                print("Processing time step %s" % timestep)
            tstep_hrs = round((timestep*fcstHotspot.tintm),2)/3600
            tstring = f'{tstep_hrs:.2f}'.zfill(6)
            # Initialize timestep dataframe
            dftstep = pd.DataFrame(columns=["xWater","yWater",
                                        "xScarp", "yScarp"])
            # Splice the dataset at the given timestep
            #if timestep % 10 == 0:
                #print(ds.globaltime,ds.meantime)
            #dsstep = ds.isel({"meantime":timestep})
            #if timestep % 10 == 0:
                #print(dsstep)
            #dsstep = dsstep.isel({"globaltime":timestep+1})
            #dsstep = dsstep.isel({"globaltime":timestep})
            dsstep = ds.isel({"globaltime":timestep}) # global time and mean time not the same
            print(timestep,tstring)
            #if timestep % 10 == 0:
                #print(dsstep)
            # Find the erosion scarp at each time step
            for index in np.arange(0,len(ds.globaly[:,0]),1):
                # Access initial elevation at each row
                elev_i = ds_zbi.zb[index,:].values
                # Access elevation at each row (cross-shore, x points)
                elevations = dsstep.zb[index,:].values
                # Compute the change in elevation from the start of simulation
                deltaz = elev_i - elevations
                # Evalute whether change in elevation surpasses 0.1 m 
                elev_bool = deltaz > 0.5
                # Sometimes we won't get a scarp and that's fine
                try:
                    maxIndex2 = np.max(np.where(elev_bool))
                    # Get point x,y point locations for the erosion scarp in each row
                    xScarp = dsstep.globalx[index,maxIndex2].values
                    yScarp = dsstep.globaly[index,maxIndex2].values               
                    ######### Append information to main dataframe######### 
                    data = {"timeStepHrs":[tstep_hrs],
                            "xScarp":[xScarp],"yScarp":[yScarp],
                            "rowInd":[index],
                            "colIndexScarp":[maxIndex2]}
                    dftmp = pd.DataFrame(data)
                    df = df.append(dftmp)
                    ######### Append information to time step's dataframe ######### 
                    dftstep = dftstep.append(dftmp)
                    # Export point shapefile for erosion scarp
                    gdf1 = gpd.GeoDataFrame(dftstep, geometry=gpd.points_from_xy(dftstep.xScarp, dftstep.yScarp), crs=epsg)
                    gdf1 = gdf1[["geometry"]]
                    gdf1 = gpd.GeoSeries(gdf1.geometry.tolist(),crs=epsg)
                    gdf1.to_file(os.path.join(scarpDirPts,"scarp_%shrs_points.shp" % tstring))
                    # Export line shapefile for erosion scarp 
                    gdf2 = gpd.GeoDataFrame(dftstep, geometry=gpd.points_from_xy(dftstep.xScarp, dftstep.yScarp), crs=epsg)
                    gdf2 = gdf2[["geometry"]]
                    gdf2 = gpd.GeoSeries(LineString(gdf2.geometry.tolist()),crs=epsg)
                    gdf2.to_file(os.path.join(scarpDirLines,"scarp_%shrs.shp" % tstring))
                except:
                    pass
        ################ Determine maximum erosion scarp from XBeach output ################
        # If there's no erosion detected there won't be a maximim landward erosion scarp detected
        try:
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
            # Export max erosion scarp lines as points
            gdf1 = gpd.GeoDataFrame(df_es, geometry="geometry", 
                                    crs=epsg)
            gdf1 = gdf1[["geometry"]]
            gdf1 = gpd.GeoSeries(gdf1.geometry.tolist(),crs=epsg)
            gdf1.to_file(os.path.join(fcstHotspot.postProcessDir,"maxEroScarp_points.shp"))
            # Export max erosion scarp line 
            gdf2 = gpd.GeoDataFrame(df_es, geometry="geometry", 
                                    crs=epsg)
            gdf2 = gdf2[["geometry"]]
            gdf2 = gpd.GeoSeries(LineString(gdf2.geometry.tolist()),crs=epsg)
            gdf2.to_file(os.path.join(fcstHotspot.postProcessDir,"maxEroScarp.shp"))
        except:
            pass


        ############# Compute the maximum 2D erosion, flow depth, and flow velocity over the forecast #############
        # Start out by computing the intial bed difference and set that as the initial array
        max_ero = ds_zbi.zb.values-ds_zbi.zb.values
        ds_flowi = ds_zbi.isel({"meantime":0})
        max_flowDepth = ds_flowi.zs_max.values-ds_zbi.zb.values
        max_flowUVel = ds_flowi.u_max.values 
        max_flowVVel = ds_flowi.v_max.values
        for timestep in np.arange(eroStartIndex+2,ds["meantime"].sizes["meantime"],1):
            dsstep = ds.isel({"meantime":timestep})
            dsstep = dsstep.isel({"globaltime":timestep+1}) # global time and mean time not the same
            # Get the erosion difference from timestep to beginning
            ero_step = dsstep.zb.values-ds_zbi.zb.values
            # Get the flow depth at timestep
            flowDepth_step = dsstep.zs_max.values-dsstep.zb.values
            # Get the max u velocities at timestep
            flowUVel_step = dsstep.u_max.values
            # Get the max v velocities at timestep
            flowVVel_step = dsstep.v_max.values
            # Compute the maximums for each
            max_ero = np.maximum(max_ero, ero_step)
            max_flowDepth = np.maximum(max_flowDepth,flowDepth_step)
            max_flowUVel = np.maximum(max_flowUVel,flowUVel_step)
            max_flowVVel = np.maximum(max_flowVVel,flowVVel_step)
        # Export in grd format
        np.savetxt(os.path.join(fcstHotspot.postProcessDir,'xbout_maxEro.grd'),
                   max_ero,delimiter="\t")
        np.savetxt(os.path.join(fcstHotspot.postProcessDir,"xbout_maxFlowDepth.grd"),
                   max_flowDepth, delimiter="\t")
        np.savetxt(os.path.join(fcstHotspot.postProcessDir, "xbout_maxUVel.grd"),
                   max_flowUVel, delimiter="\t")
        np.savetxt(os.path.join(fcstHotspot.postProcessDir, "xbout_maxVVel.grd"),
                   max_flowVVel, delimiter="\t")

    # Use pickle to save xbeach model object info
    picklePath = os.path.join(fcstHotspot.forecastDir,"forecast_hotspot.pkl")
    with open(picklePath, "wb") as output:
        pickle.dump(fcstHotspot, output, pickle.HIGHEST_PROTOCOL)

    
## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise