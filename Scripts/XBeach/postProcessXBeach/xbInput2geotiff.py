import os
import numpy as np
import xarray as xr
import pandas as pd
from xbfewsTools import postProcTools

xbWorkDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\XBeach\\Narrabeen\\runs\\latest\\workDir"
xbOutput = os.path.join(xbWorkDir,"xboutput.nc")

#xfile = os.path.join(xbWorkDir,"x.grd")
#yfile = os.path.join(xbWorkDir,"y.grd")
zfile = os.path.join(xbWorkDir,"ne_layer.grd")

#xgrd = np.fromfile(xfile,dtype=float)
#print(xgrd.shape)

#################### Load dataset ####################
ds = xr.open_dataset(xbOutput)
ds = ds.isel({"globaltime":0})
ds = ds[["zb"]]

#################### Load xBeach-formatted grid ####################
vargrd = np.fromfile(zfile,dtype=float,sep='\t')


#Write out as csv
outPath = os.path.join(xbWorkDir,'nelayer.csv')
df = pd.DataFrame(ds.globalx.values.flatten(),columns=['x'])
df['y'] = ds.globaly.values.flatten()
df['z'] = vargrd
df.to_csv(outPath)


"""############### Interpolate irregular mesh onto regular mesh ###############

# Create data array for resampling
# Extract dimensions - based on minx, miny, maxx, maxy
minx = min(ds.globalx.values.flatten())
miny = min(ds.globaly.values.flatten())
maxx = max(ds.globalx.values.flatten())
maxy = max(ds.globaly.values.flatten())

# Set resolution based on cross-shore resolution of landward-most points
# Theoretically should be smallest resolution in the irregular grid
# Take first row and subtract last x value from second to last
reso = np.absolute(ds.globalx.values[0][-1]-ds.globalx.values[0][-2])
reso = 2*round(reso/2.) + 2 # round resolution up to the nearest 2 m (just to have a nice number)

# Create the regular grid
xx = np.arange(minx,maxx,reso)
yy = np.arange(miny,maxy,reso)

# N cols and N rows
ncols = len(xx)
nrows = len(yy)

#################### Load xBeach-formatted grid ####################
vargrd = np.fromfile(zfile,dtype=float,sep='\t')
vargrd = vargrd.reshape(ds.globaly.shape[0],
                        ds.globalx.shape[1])

# Run interpolation (check link above)
from scipy.interpolate import griddata
zi = griddata((ds.globalx.values.flatten(),ds.globaly.values.flatten()),
            vargrd.flatten(), (xx[None,:], yy[:,None]), method="nearest")

# Reshape interpolated array
zi = np.reshape(zi,(nrows,ncols))

# Write out
nePath = os.path.join(xbWorkDir,"neLayer.tif")
postProcTools.numpy2gtiff(arr=zi, epsg=int(28356), x1d=xx, y1d=yy,
                reso=reso,filepath=nePath)"""

