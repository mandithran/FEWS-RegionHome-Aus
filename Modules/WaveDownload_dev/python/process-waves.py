# Modules
import traceback
import sys
import os
import shutil
from importWaves import fewsUtils
from importWaves import retrieveWaves
import xarray as xr
import pandas as pd
from datetime import datetime

import numpy as np
import netCDF4
import geopandas as gpd

def main(args=None):
    """The main routine."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    regionHomeDir = str(args[0])
    workDir = str(args[1])
    siteName = str(args[2])
    sysTime = str(args[3])
    locSetFilename = str(args[4])
    jonSwapParam = str(args[5])
    dirSpread = str(args[6])
    dtbc = str(args[7])

    #============== Paths ==============#
    modulePath = os.path.join(regionHomeDir,"Modules")
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")

    #============== Write out initial commands to diag file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)

    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Current directory: %s" %currDir))
        fileObj.write(fewsUtils.write2DiagFile(3,"If Python error exit code 1 is triggered, see exceptions.log file in Module directory."))
        fileObj.write("</Diag>")


    #============== Read in Auswave mesh point locations ==============#
    # "Points of interest"
    ifile = os.path.join(workDir, "auswaveOutPts_Narrabeen.csv")
    df = pd.read_csv(ifile)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat))
    ausWaveEPSG = int(4939)
    gdf.set_crs(epsg=ausWaveEPSG)

    #============== Load Location Set ==============#
    locSetPath = os.path.join(regionHomeDir, "./Config/MapLayerFiles", locSetFilename)
    df = pd.read_csv(locSetPath)

    #============== Parse system time ==============#
    # TODO make a full function for parsing system time in fews utils
    systemTime = datetime(int(sysTime[:4]),
                          int(sysTime[4:6]),
                          int(sysTime[6:8]),
                          hour=int(sysTime[9:11]))

    roundedTime = retrieveWaves.round_hours(systemTime, 12)
    rt = pd.to_datetime(str(roundedTime))
    rt_str = rt.strftime('%Y%m%d%H')
    xbWorkDir = os.path.join(modulePath,".\XBeach",siteName,"runs",rt_str,"workDir")
    # Subtract twelve hours from this rounded time to give a proper spin-up period
    print(type(roundedTime))
    roundedTimeSpin = rt - np.timedelta64(12, "h")

    #============== Load Location Set ==============#
    locSetPath = os.path.join(regionHomeDir, "./Config/MapLayerFiles", locSetFilename)
    df = pd.read_csv(locSetPath)


    # TODO: Import location set and use it to parse filename
    # TODO: Configure Input grid for Mandurah
    #============== Parse BOM file name  ==============#
    bomDate = str(str(roundedTimeSpin.year)+
            str(roundedTimeSpin.month).zfill(2)+
            str(roundedTimeSpin.day).zfill(2))
    bomTime = str(str(roundedTimeSpin.hour).zfill(2)+
            str(roundedTimeSpin.minute).zfill(2))
    bomDT = str(bomDate+"T"+bomTime+"Z")
    cityCode = df.loc[df["Name"]==siteName, "City_code"].iloc[0]
    fname = "%s.msh.%s.nc" % (cityCode,bomDT)
    print(fname)

    #============== Read in Auswave output ==============#
    ausWavedf = os.path.join(workDir, "ncFiles", fname)
    ds = xr.open_dataset(ausWavedf)

    #============== Slice it to a 3-day forecast for now ==============#
    startTime = min(ds.time[:].values)
    endTime = startTime + np.timedelta64(84,"h")
    ds =ds.sel(time=slice(startTime,endTime))

    #============== Keep only the mesh points of interest ==============#
    # Convert xarray dataset to geodataframe
    dfPts = pd.DataFrame({"Lon":ds.longitude.values,
                        "Lat":ds.latitude.values})
    gdfPts = gpd.GeoDataFrame(dfPts, geometry=gpd.points_from_xy(dfPts.Lon,dfPts.Lat))
    gdfPts.set_crs(epsg=4939)
    from shapely.ops import nearest_points
    # unary union of the geomtries 
    pts = gdfPts.geometry.unary_union
    # Find the nearest geometries in Auswave output to "points of interest"
    # Return the old Auswave index value for slicing Auswave output
    def nearGeom(point, pts=None, gdfIn=None, outVar=None):
        # find the nearest point and return the corresponding Place value
        nearest = gdfIn.geometry == nearest_points(point, pts)[1]
        geometries = gdfIn[nearest].geometry.to_numpy()[0]
        indeces = gdfIn[nearest].index.to_numpy()[0]
        if outVar == "index":
            return indeces
        elif outVar == "geometries":
            return geometries
        else:
            raise
    gdf["oldIndex"] = gdf.apply(lambda row: nearGeom(row.geometry, pts=pts, gdfIn=gdfPts, outVar="index"), axis=1)
    indArr = gdf["oldIndex"].to_numpy()
    ds = ds.isel(node=indArr)

    #============== Get timestep of timeseries in seconds ==============#
    t2 = ds.coords["time"][1].values
    t1 = ds.coords["time"][0].values
    dt = t2-t1
    dt = dt.astype('timedelta64[s]').astype(int).astype(float)

    #============== Create XBeach working directories if they don't exist ==============#
    if not os.path.exists(xbWorkDir):
        os.makedirs(xbWorkDir)


    #============== Loop through and generate wavefiles ==============#
    roundDec = 3
    for index in np.arange(0,ds.sizes['node']):
        dfOut = pd.DataFrame({"Hsig":ds.hs[:,0].values.round(roundDec),
                             "Tp":ds.tp[:,0].values.round(roundDec),
                             "dir":ds.dir[:,0].values.round(roundDec),
                             "JS":jonSwapParam,
                             "dirSpread":dirSpread,
                             "dt_sec":dt.round(roundDec),
                             "dtbc":dtbc})
        ofileName = "wavefile%s.txt" % (index+1)
        dfOut.to_csv(os.path.join(xbWorkDir,ofileName), sep='\t', header=False, index=False)


    #============== Add wavefile name as gdf entry ==============#
    gdf["ind"] = gdf.index.astype(int)
    gdf["wavefile"] = [f"wavefile{i+1}.txt" for i in gdf.index]

    
    #============== Generate input file that directs XBeach to wavefiles ==============#
    # Load XBeach mesh as geodataframe - netCDF format
    xbf = os.path.join(modulePath,".\XBeach",siteName,"inputFiles\\bathyTopo","xbNarra_zb_2021.nc")
    xbds = xr.open_dataset(xbf)
    ncolXB = xbds.ncols
    nrowXB = xbds.nrows

    # Convert to geodataframe to do point searching
    xbgdf = xbds.to_dataframe()
    xbgdf = gpd.GeoDataFrame(xbgdf, geometry=gpd.points_from_xy(xbgdf.globalx,xbgdf.globaly))
    xbEPSG = int(xbds.epsg)
    xbgdf.set_crs(xbEPSG)

    # Using points of interest (now in ds), find closest points on XBeach mesh,
    # return value of index in XBeach output
    # Reproject points to projection used in XBeach
    gdf_proj = gdf.copy()
    gdf_proj.set_crs(epsg=ausWaveEPSG, inplace=True)
    gdf_proj['geometry'] = gdf_proj['geometry'].to_crs(epsg=xbEPSG)
    # unary union of the geomtries 
    pts = xbgdf.geometry.unary_union
    gdf_proj["xbIndex"] = gdf_proj.apply(lambda row: 
                     nearGeom(row.geometry, pts=pts, gdfIn=xbgdf, outVar="index"), axis=1)
    
    # Grab the index in the relevant row, first column
    # Column indeces go up starting from seaward points
    # Split xbeach indeces into separate rows, cols
    indList = gdf_proj.xbIndex.tolist()
    gdf_proj[["xbcol","xbrow"]] = pd.DataFrame(indList, index=gdf_proj.index)
    gdf_proj['targetCol'] = 0 # First column, starting from seaward boundary
    gdf_proj['targetRow'] = gdf_proj.xbrow
    print(gdf_proj)

    # Grab relevant geometries from XBeach grid using target indeces
    # Slice by desired cols first
    #gdf_proj['targetX'] = xbgdf.loc[0]
    targetColArr = gdf_proj['targetCol'].values
    targetRowArr = gdf_proj['targetRow'].values
    targetInd = zip(targetColArr,targetRowArr)
    xbgdf_subset = xbgdf.loc[targetInd]
    xbgdf_subset['xtarget'] = xbgdf_subset.geometry.x
    xbgdf_subset['ytarget'] = xbgdf_subset.geometry.y
    # Round vals
    xbgdf_subset = xbgdf_subset.round({'xtarget':2,'ytarget':2})
    # Bring old index over for merging
    xbgdf_subset['ind'] = gdf_proj['ind'].values
    print(xbgdf_subset)
    
    # Merge dfs
    df = pd.merge(gdf_proj,xbgdf_subset,on="ind")
    print(df)

    # Round and convert coordinates to ints
    df['xtarget'] = df['xtarget'].round(decimals=0).astype(int)
    df['ytarget'] = df['ytarget'].round(decimals=0).astype(int)

    # Template
    template = """LOCLIST
{}"""

    # Send to txt file
    with open(os.path.join(xbWorkDir, "loclist.txt"), 'w') as fp:
        fp.write(template.format(df.to_csv(index=False, columns=["xtarget","ytarget","wavefile"],
              header=False,sep=' ',line_terminator='\n')))

    
    #============== Load Location Set ==============#
    #locSetPath = os.path.join(regionHomeDir, "./Config/MapLayerFiles", locSetFilename)
    #df = pd.read_csv(locSetPath)

    #============== Grab most recently downloaded nc file ==============#
    # Uses a function from processSurge.py
    #downloadDir = os.path.join(workDir,"ncFiles")
    #newestNC = processSurge.getMostRecentFile(downloadDir=downloadDir)



## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise