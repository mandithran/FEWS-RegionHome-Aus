import numpy as np
import rasterio
import os
import seaborn as sns
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import geopandas as gpd
import pickle
from datetime import datetime, timedelta
from xbfewsTools import postProcTools

################ Variables ################
trange = np.arange(0,5,1)
siteName = "Narrabeen"
epsg = 28356


################ Paths ################

regionHome = "\\Users\\mandiruns\Documents\\01_FEWS-RegionHome-Aus"
xbWorkDir = "\\Users\\mandiruns\Documents\\01_FEWS-RegionHome-Aus\\Modules\\XBeach\\%s\\runs\\latest\\workDir" % siteName
postProcessDir = os.path.join(xbWorkDir,"postProcess")
scarpDir = os.path.join(postProcessDir,"scarp")
gaugesDir = os.path.join(postProcessDir,"gauges\\lines")
visualizeDir = os.path.join(postProcessDir,"visualize")
imagery = os.path.join(regionHome,"Data\\imagery\\narrabeen_epsg28356_P4.tif")


# Make directories if they don't exist
if not os.path.exists(visualizeDir):
    os.makedirs(visualizeDir)

################ plotmymap function ################
def plotmymap(axs, gaugefile=None, ewlgdf= None, imagery=None, 
             time=None, epsg=None):

    # Plot aerial imagery
    # sometimes the reading of the my_image.extent is really inconsistent. Randomly flips the y extents.
    from rasterio.plot import show
    show(my_image.read(),ax=axs, transform=my_image.transform)

    # Load and plot EWL points
    try:
        # Clip EWL points to extent of raster
        gdf = gpd.read_file(gaugefile)
        gdf_clipped = postProcTools.clipShp(shp=gdf, mask=my_image)
        gdf_clipped.plot(ax = axs, color="red")
        print(gdf.head())
    except:
        pass

    # Plot extreme water line
    ewlgdf.plot(ax = axs, color="darkred")

    # Plot time
    # Percentages (decimals) relative to axes dimensions (not data dimensions)
    rectX = 0.72
    rectY = 0.72
    rectwidth = 0.25
    rectheight = 0.25
    tstepText = "time = %s hrs" % str(int(time))
    plt.text(rectX+.1, rectY+rectheight-0.06, tstepText, 
        transform=axs.transAxes, color='white',
        fontsize=12, ha='center', va='center',
        horizontalalignment='right',verticalalignment='top')

    return

################ Load model info using pickle ################
xbmodel = pickle.load(open(os.path.join(xbWorkDir,"model.pkl"),"rb"))
spinUpSteps = 12 + 1

################ Load aerial imagery ################
my_image = rasterio.open(imagery)


################ Load and clip extreme line ################
ewlgdf = gpd.read_file(os.path.join(postProcessDir,"maxEroScarp.shp"))
ewlgdf_clipped = postProcTools.clipShp(shp=ewlgdf, mask=my_image)


################ loop through and generate plots ################
# TODO: incorporate delta t in pickle
print(xbmodel.startTime)
print(type(xbmodel.startTime))
print(xbmodel.endTime)
print(type(xbmodel.endTime))
"""trange = np.arange(np.datetime64(xbmodel.startTime), 
                   np.datetime64(xbmodel.endTime)+timedelta(hours=1),timedelta(hours=1))"""
trange = np.arange(xbmodel.startTime, xbmodel.endTime+timedelta(hours=1),timedelta(hours=1))
# TODO: change to accomodate spin-up time
for t in trange:
    tInt = t - np.datetime64(xbmodel.startTime)
    tHours = int(tInt.item().total_seconds()/3600)
    print("Processing time step at %s hours" % tHours)

    # Parse filename
    tHoursStr = str(tHours).zfill(4)
    fPath = os.path.join(scarpDir,"scarp_%shrs.shp" % tHoursStr)
    print(fPath)

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
    plotmymap(ax, gaugefile=fPath, 
                ewlgdf=ewlgdf_clipped, imagery=imagery, time=tHours, epsg=epsg)

    ########### Save map ###########
    figPath = os.path.join(visualizeDir, '%s_%s_scarp.png' % (siteName,tHoursStr))
    plt.savefig(figPath,dpi=250,bbox_inches='tight') 

        


        