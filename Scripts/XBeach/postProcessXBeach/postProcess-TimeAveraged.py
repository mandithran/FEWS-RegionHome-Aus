#################### Modules ####################
import xarray as xr
import os
from xbfewsTools import postProcTools


##################### Variables ####################
siteName = "Narrabeen"
vars2process = ["zb"]
epsg = int(28356)
globaltime = 84


#################### Paths ####################
regionHome = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus"
xbWorkDir = os.path.join(regionHome,"Modules\\XBeach\\%s\\runs\\latest\\workDir" % siteName)
postProcessDir = os.path.join(xbWorkDir,"postProcess")
gridsDir = os.path.join(postProcessDir,"grids")
xboutput = os.path.join(xbWorkDir,"xboutput.nc")


#################### Create paths if they don't exist ####################
if not os.path.exists(postProcessDir):
    os.makedirs(postProcessDir)
for v in vars2process:
    opath = os.path.join(gridsDir,v)
    if not os.path.exists(opath):
        os.makedirs(opath)
    

#################### Load dataset ####################
ds = xr.open_dataset(xboutput)
ds = ds.isel({"globaltime":globaltime})
ds = ds[["zb"]]


############### Interpolate irregular mesh onto regular mesh ###############
xx,yy,reso,zi = postProcTools.interpXBmesh(ds=ds)


########### Create an additional mask to mask interpolation artefacts with "nans" ###########
# Takes xarray dataset and returns a geopandas geoseries
gs = postProcTools.generateXBmask(ds=ds, epsg=epsg)


ofileStr = "zb_t%s" % globaltime

########### Convert numpy into rasterio raster object for output ###########
raster = postProcTools.numpy2gtiff(arr=zi,epsg=epsg,x1d=xx,y1d=yy,reso=reso,
                    filepath=os.path.join(postProcessDir,"%s.tif" % ofileStr))


########### Mask XBeach output ###########
masked = postProcTools.maskXBoutput(inRaster=os.path.join(postProcessDir,'%s.tif' % ofileStr),
                                    shp=gs,
                                    outRaster=os.path.join(postProcessDir,'%s_masked.tif' % ofileStr))
