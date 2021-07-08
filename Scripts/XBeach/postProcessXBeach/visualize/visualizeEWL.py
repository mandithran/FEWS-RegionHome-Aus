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

################ Variables ################
epsg = 28356
siteName = "Narrabeen"


################ Paths ################

regionHome = "\\Users\\z3531278\Documents\\01_FEWS-RegionHome-Aus"
xbWorkDir = "\\Users\\z3531278\Documents\\01_FEWS-RegionHome-Aus\\Modules\\XBeach\\%s\\runs\\latest\\workDir" % siteName
postProcessDir = os.path.join(xbWorkDir,"postProcess")
mwlDirLines = os.path.join(postProcessDir,"mwl")
gaugesDir = os.path.join(postProcessDir,"gauges\\lines")
visualizeDir = os.path.join(postProcessDir,"visualize")
imagery = os.path.join(regionHome,"Data\\imagery\\narrabeen_epsg28356_P4.tif")

# Make directories if they don't exist
if not os.path.exists(visualizeDir):
    os.makedirs(visualizeDir)


################ plotmymap function ################
def plotmymap(fig, axs, gaugefile=None, ewlgdf= None, imagery=None, 
             time=None, epsg=None):

    ########## Get extent of raster image and set ticks ##########
    # Note: if there aren't enough ticks on the ends, \
    # change the lower and upper bounds to either +/- \
    # xint or yint
    """my_image = georaster.SingleBandRaster(imagery)
    xint, yint = 0.5, 0.5
    lowerX = xint*round(my_image.extent[0]/xint)+xint
    upperX = xint*round(my_image.extent[1]/xint)+xint
    xticks = np.arange(lowerX, upperX, xint)
    lowerY = yint*round(my_image.extent[2]/yint)
    upperY = yint*round(my_image.extent[3]/yint)+yint
    yticks = np.arange(lowerY, upperY, yint)"""

    my_image = rasterio.open(imagery)
    print("my_image.bounds: ", my_image.bounds)
    #import georaster
    #my_image2 = georaster.SingleBandRaster(imagery)
    #print("extent for my_image2: ", my_image2.extent)


    # Plot aerial imagery
    # sometimes the reading of the my_image.extent is really inconsistent. Randomly flips the y extents.
    from rasterio.plot import show
    show(my_image.read(),ax=axs, transform=my_image.transform)
    """plt.imshow(my_image.read(1), origin='upper', \
        extent=[my_image.bounds[0],\
        my_image.bounds[2],\
        my_image.bounds[1],\
        my_image.bounds[3]], \
        transform=ccrs.epsg(epsg))"""
    # Using this one makes it pink
    # Cropping is also NOT straightforward with imshow
    """extent = rasterio.plot.plotting_extent(my_image, transform=my_image.transform)
    print("extent")
    print(extent)
    plt.imshow(my_image.read(1), origin='upper', 
        extent=[extent[0]+200,
        extent[1]-200,
        extent[2]+400,
        extent[3]-400]) 
        #transform=ccrs.epsg(epsg))"""


    # Load EWL points
    gdf = gpd.read_file(gaugefile)

    # Clip EWL points to extent of raster
    gdf_clipped = postProcTools.clipShp(shp=gdf, mask=my_image)
    
    # Plot EWL points
    gdf_clipped.plot(ax = axs, color="blue")
    print(gdf.head())

    # Plot extreme water line
    ewlgdf_clipped = postProcTools.clipShp(shp=ewlgdf, mask=my_image)
    ewlgdf_clipped.plot(ax = axs, color="darkblue")
    
    # TODO: Plot Narrabeen info
    """# Percentages (decimals) relative to axes dimensions (not data dimensions)
    rectX = 0.72
    rectY = 0.72
    rectwidth = 0.25
    rectheight = 0.25
    rect = patches.Rectangle((rectX,rectY), width=rectwidth, height=rectheight,color='white',alpha=0.6,
                            transform=axs.transAxes)
    axs.add_patch(rect)
    txt = "%s" % siteName
    axs.text(rectX+.1, rectY+rectheight-0.03, txt, 
            transform=axs.transAxes, color='black',
            fontsize=12, ha='center', va='center')

    # Plot text
    tstepText = "time = %s hrs" % str(int(time))
    plt.text(rectX+.1, rectY+rectheight-0.06, tstepText, 
            transform=axs.transAxes, color='black',
            fontsize=12, ha='center', va='center',
            horizontalalignment='right',verticalalignment='top')"""

    return


################ Load model info using pickle ################
xbmodel = pickle.load(open(os.path.join(xbWorkDir,"model.pkl"),"rb"))
print(xbmodel.spinUpWindow/xbmodel.deltat)
print(xbmodel.deltat)


################ loop through and generate plots ################

counter = 1
# TODO: Change back to Mitch's way if need be
#ewlgdf = gpd.read_file(os.path.join(postProcessDir,"mwl.shp"))
#for file in os.listdir(mwlDirLines):
ewlgdf = gpd.read_file(os.path.join(postProcessDir,"ewl_XBeach.shp"))
for file in os.listdir(gaugesDir):
    if file.endswith(".shp"):

        print("Processing time step %s" % counter)
        # Parse filename
        # Time is in hrs from start time (which includes spin-up time)
        # TODO: change back
        time_h = str(file).split("_")
        time_h = time_h[1].split("h")[0]
        time_h = float(time_h)
        """time_h = str(file).split("_")
        time_h = time_h[1].split(".")[0]
        time_h = int(time_h.split("h")[0])
        time_np = np.timedelta64(time_h,"h")"""
        
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
        plotmymap(fig, ax, gaugefile=os.path.join(gaugesDir,file), 
                 ewlgdf= ewlgdf, imagery=imagery, time=time_h, epsg=epsg)


        ########### Save map ###########
        figPath = os.path.join(visualizeDir, '%s_%s.png' % (xbmodel.siteName,str(counter).zfill(5)))
        plt.savefig(figPath,dpi=250,bbox_inches='tight')
        counter += 1
        #raise