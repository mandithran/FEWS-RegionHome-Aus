"""
visualizeIndicators.py
Author: Mandi Thran
Date: 01/10/21

DESCRIPTION:
This script generates a series of snapshots to create animations of how the
safe corridor width and dune toe-scarp distance storm impact indicators
evolve over a forecast.
"""

# Modules
import numpy as np
import rasterio
import os
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cartopy.crs as ccrs
import geopandas as gpd
from xbfewsTools import postProcTools
import pickle
from datetime import datetime, timedelta
from shapely.geometry import Point, LineString
import pandas as pd

################ Variables ################
epsg = 28356
siteName = "Narrabeen"
scwFlag = False
bsdFlag = True


################ Paths ################

regionHome = "\\Users\\mandiruns\Documents\\01_FEWS-RegionHome-Aus"
forecastDir = os.path.join(regionHome, "Forecasts\\20200208_0000\\NSW\\hotspot\\Narrabeen")
workDir = os.path.join(regionHome,"Scripts\\visualize\\Animations\\Hotspot\\Narrabeen")
xbWorkDir = os.path.join(forecastDir,"XBeach")
xgrd = os.path.join(xbWorkDir,'x.grd')
ygrd = os.path.join(xbWorkDir,'y.grd')
postProcessDir = os.path.join(xbWorkDir,"postProcess")
mwlDirLines = os.path.join(postProcessDir,"mwl")
gaugesDir = os.path.join(postProcessDir,"gauges\\lines")
visualizeDir = os.path.join(postProcessDir,"visualize")
imagery = os.path.join(regionHome,"Data\\imagery\\Narrabeen\\narrabeen_epsg28356_P4.tif")
indicatorsPath = os.path.join(postProcessDir,"indicators")
scwPath = os.path.join(indicatorsPath,"scw\\points")
bsdPath = os.path.join(indicatorsPath,"bsd\\points")
dataDir = os.path.join(regionHome,"Data")
transectsDir = os.path.join(dataDir,"Indicators\\Hotspot\\Narrabeen")
transectsShp = os.path.join(transectsDir,"xb_transects_utm.shp")

# Make directories if they don't exist
if not os.path.exists(visualizeDir):
    os.makedirs(visualizeDir)


################ splitLine function ################
def splitLine(gdf):
    # Right_x = the x value of the point to the right of the ewl point
    # The ewl point should be along the XBeach transect
    # Assumes "forward" is facing towards the beach
    # For Narrabeen, this means the "rightmost" points are always to the north
    # of the ewl point of interest
    # Make new columns that have the geometries to the left and right of the main point
    gdf['geom_left'] = gdf['geometry'].shift(1)
    gdf['geom_right'] = gdf['geometry'].shift(-1)

    # Get the midpoint of the point to the right of the geometry
    # This means averaging the x, y values with the point to the right
    # of any given point in the geodataframe.
    # The conditional in this function takes care of the endpoints, since
    # the northern-most endpoint will not have a point to the right of it
    # In this special case, a midpoint is not calculated and the right-hand point
    # is just taken to be the endpoint itself
    gdf['right_x'] = gdf.apply(lambda row: np.average([row['geometry'].x,
                                                                        row['geom_right'].x]) 
                                                        if row['geom_right'] != None 
                                                        else row['geometry'].x, 
                                                axis = 1)
    gdf['right_y'] = gdf.apply(lambda row: np.average([row['geometry'].y,
                                                                        row['geom_right'].y]) 
                                                        if row['geom_right'] != None 
                                                        else row['geometry'].y, 
                                                axis = 1)

    # Repeat a similar procedure for the left-hand midpoint
    gdf['left_x'] = gdf.apply(lambda row: np.average([row['geometry'].x,
                                                                        row['geom_left'].x]) 
                                                        if row['geom_left'] != None 
                                                        else row['geometry'].x, 
                                                axis = 1)
    gdf['left_y'] = gdf.apply(lambda row: np.average([row['geometry'].y,
                                                                        row['geom_left'].y]) 
                                                        if row['geom_left'] != None 
                                                        else row['geometry'].y, 
                                                axis = 1)
    gdf['line_segs'] = gdf.apply(lambda row: LineString([Point(row['right_x'], row['right_y']),
                                                                        Point(row['left_x'], row['left_y'])]),
                                                                        axis=1)
    gdf_Seg = gpd.GeoDataFrame(gdf['indicator'], geometry=gdf['line_segs'])
    gdf_Seg = gdf_Seg.set_crs(epsg)

    return gdf_Seg


def assignColors(gdf):
    gdf['colors'] = gdf['indicator']
    gdf.loc[gdf['colors'] == 'Low', 'colors'] = 'green'
    gdf.loc[gdf['colors'] == 'Medium', 'colors'] = 'yellow'
    gdf.loc[gdf['colors'] == 'High', 'colors'] = 'red'
    return gdf



################ plotmymap function ################
def plotmymap(fig, axs, gaugefile=None, ewlgdf= None, 
              imagery=None, time=None, epsg=None,
              scwMode=False, bsdMode=False, scwFile=None,
              bsdFile=None, xbtransects=None, gdfgrd=None):

    ########## Get extent of raster image and set ticks ##########
    # Note: if there aren't enough ticks on the ends, \
    # change the lower and upper bounds to either +/- \
    # xint or yint
    my_image = rasterio.open(imagery)

    # Plot aerial imagery
    # sometimes the reading of the my_image.extent is really inconsistent. Randomly flips the y extents.
    # Tried imshow... turned up pink, cropping not straightforward
    from rasterio.plot import show
    show(my_image.read(),ax=axs, transform=my_image.transform)

    # Plot xbeach transects
    gdf_xb = gpd.read_file(xbtransects)
    gdf_xb_clipped = postProcTools.clipShp(shp=gdf_xb, mask=my_image)
    gdf_xb_clipped.plot(ax = axs, color="black", linewidth=0.5)

    # Load EWL points
    #gdf = gpd.read_file(gaugefile)

    # Clip EWL points to extent of raster
    #gdf_clipped = postProcTools.clipShp(shp=gdf, mask=my_image)
    
    # Plot EWL points
    #gdf_clipped.plot(ax = axs, color="dodgerblue", edgecolors='black', markersize=70)

    """# Plot extreme water line
    ewlgdf_clipped = postProcTools.clipShp(shp=ewlgdf, mask=my_image)
    ewlgdf_clipped.plot(ax = axs, color="darkblue")"""

    # Plot SCW Indicators:
    if scwMode:

        gdf_scw = gpd.read_file(scwFile)
        # Merge with Xbeach grid gdf to get the col/row indeces
        gdf_scw = gdfgrd.merge(gdf_scw, how='inner', on=['geometry'])
        gdf_scw = gdf_scw.sort_values('rowInd')
        gdf_scw = gdf_scw.set_index('rowInd')

        # Assign more generic column name "indicator" for the functions
        gdf_scw['indicator'] = gdf_scw['SCW']

        # Split extreme water line into segments to be colored by SCW indicator
        gdf_scw = splitLine(gdf_scw)

        # Assign colors to SCW indicator levels
        gdf_scw = assignColors(gdf_scw)

        # Clip scw line segments gdf to raster bounds
        gdf_scw_clipped = postProcTools.clipShp(shp=gdf_scw, mask=my_image)

        # Plot colored scw line segments
        gdf_scw_clipped.plot(ax=axs, edgecolors='black', markersize=70, color=gdf_scw_clipped['colors'])


    # Plot BSD Indicators:
    if bsdFlag:
        try:
            gdf_bsd = gpd.read_file(bsdFile)

            # Merge with Xbeach grid gdf to get the col/row indeces
            gdf_bsd = gdfgrd.merge(gdf_bsd, how='inner', on=['geometry'])
            gdf_bsd = gdf_bsd.sort_values('rowInd')
            gdf_bsd = gdf_bsd.set_index('rowInd')

            # Assign more generic column name "indicator" for the functions
            gdf_bsd['indicator'] = gdf_bsd['BSD']

            print(gdf_bsd)
            for k,g in gdf_bsd.groupby(gdf_bsd.index - np.arange(gdf_bsd.shape[0])):

                # Split scarp lines into segments to be colored by BSD indicator
                g = splitLine(g)

                # Assign colors to indicators
                g = assignColors(g)

                # Clip bsd line segments gdf to raster bounds
                gdf_bsd_clipped = postProcTools.clipShp(shp=g, mask=my_image)

                # Plot colored scw line segments
                gdf_bsd_clipped.plot(ax=axs, edgecolors='black', markersize=70, color=gdf_bsd_clipped['colors'])

        except:
            pass
        

    # Plot Narrabeen info
    # Percentages (decimals) relative to axes dimensions (not data dimensions)
    rectX = 0.7
    rectY = 0.89
    rectwidth = 0.28
    rectheight = 0.1
    rect = patches.Rectangle((rectX,rectY), width=rectwidth, height=rectheight,color='white',alpha=0.6,
                            transform=axs.transAxes)
    axs.add_patch(rect)
    txt = "%s" % siteName
    axs.text(rectX+.14, rectY+rectheight-0.03, txt, 
            transform=axs.transAxes, color='black',
            fontsize=14, ha='center', va='center')

    # Plot text
    tstepText = "time = %s hrs" % str(int(time))
    plt.text(rectX+.14, rectY+rectheight-0.06, tstepText, 
            transform=axs.transAxes, color='black',
            fontsize=14, ha='center', va='center',
            horizontalalignment='right',verticalalignment='top')

    return


################ Load model info using pickle ################
hotspotFcst = pickle.load(open(os.path.join(forecastDir,"forecast_hotspot.pkl"),"rb"))
print(hotspotFcst.spinUpWindow/hotspotFcst.deltat)
print(hotspotFcst.deltat)


################ Load x.grd, y.grd ################
xx = np.loadtxt(xgrd,delimiter='\t')
yy = np.loadtxt(ygrd,delimiter='\t')
nrows = xx.shape[0]
ncols = xx.shape[1]
# Flatten the xx, yy arrays
x = xx.flatten()
y = yy.flatten()
# Generate multiIndex
indArrays = np.where(xx != None)
tuples = list(zip(*indArrays))
index = pd.MultiIndex.from_tuples(tuples, names=["rowInd", "colInd"])
# Convert to dataframe with multi-indexing
dfgrd = pd.DataFrame(x, columns=["x"], index=index)
dfgrd['y'] = y
# Convert this to geodataframe
gdfgrd = gpd.GeoDataFrame(
    dfgrd, geometry=gpd.points_from_xy(dfgrd.x, dfgrd.y))
gdfgrd = gdfgrd.set_crs(epsg)
gdfgrd = gdfgrd.reset_index()


################ loop through and generate plots ################
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
# Counter
counter = 1
# Timestep in hours
for t_step in tseries_hrs:

    if t_step % 10 == 0:
        print("Processing grid at %s hours model time" % t_step)
    
    ########### Paths ###########
    tstep_hrs_str = f'{(t_step):.2f}'.zfill(6)
    scwFile = os.path.join(scwPath,"scw_%shrs.shp" % tstep_hrs_str)
    bsdFile = os.path.join(bsdPath, "bsd_%shrs.shp" % tstep_hrs_str)

    ########### Map parameters ###########
    fig = plt.figure(figsize=(8.75, 10.5),facecolor="white")
    sns.set_style('white')
    # set projection to use
    projex = ccrs.epsg(epsg)
    # tick style
    sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
    # axis
    ax = fig.add_subplot(1, 1, 1, projection=projex)

    ########### Plot map ###########
    plotmymap(fig, ax, imagery=imagery, time=t_step, epsg=epsg,
                scwMode=scwFlag, scwFile = scwFile, 
                bsdMode=bsdFlag, bsdFile = bsdFile,
                xbtransects=transectsShp, gdfgrd = gdfgrd)

    ########### Save map ###########
    if scwFlag and bsdFlag:
        print("Error. Plot either the safe corridor width indicator or the building-scarp distance indicator")
        raise
    if scwFlag:
        figDir = os.path.join(visualizeDir,'scw')
        if not os.path.exists(figDir):
            os.makedirs(figDir)
        figPath = os.path.join(figDir, 'scw_%s_%s.png' % (hotspotFcst.siteName,str(counter).zfill(5)))
        plt.savefig(figPath,dpi=250,bbox_inches='tight')
    elif bsdFlag:
        figDir = os.path.join(visualizeDir,'bsd')
        if not os.path.exists(figDir):
            os.makedirs(figDir)
        figPath = os.path.join(figDir, 'bsd_%s_%s.png' % (hotspotFcst.siteName,str(counter).zfill(5)))
        plt.savefig(figPath,dpi=250,bbox_inches='tight')
    counter += 1
    plt.close('all')

   