import numpy as np
import os
import pandas as pd

storm = "2020_08_10"
mode = "pre-storm"

workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\topobathy"
ifilePath = os.path.join("C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\xbeach\\grd\\2020_08_10\\pre-storm")
xgrd = os.path.join(ifilePath,"x.grd")
ygrd = os.path.join(ifilePath,"y.grd")
zgrd = os.path.join(ifilePath,"ne_layer.grd")

def flattenGrd(arr2d_grdfile):
    "Takes a grd file, formatted for XBeach."
    arr2d = np.loadtxt(arr2d_grdfile,delimiter='\t')
    arr1d = arr2d.flatten()
    return arr1d

xx = flattenGrd(xgrd)
yy = flattenGrd(ygrd)
zz = flattenGrd(zgrd)

df = pd.DataFrame(xx,columns=['x'])
df['y'] = yy.flatten()
df['z'] = zz.flatten()
df.to_csv(os.path.join(ifilePath,'ne_layer_2020_08_10.csv'),index=False)