import numpy as np
import os
import pandas as pd

storm = "2020_02_09"
site = "Narrabeen"
mode = "pre-storm"
longshoreReso = '100m'

workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\topobathy"
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
ifilePath = os.path.join("Data\\xbeach\\%s\\grd\\%s\\pre-storm\\%sAlongshore" % (site,storm,longshoreReso))
xgrd = os.path.join(ifilePath,"x.grd")
ygrd = os.path.join(ifilePath,"y.grd")
zgrd = os.path.join(ifilePath,"z.grd")

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
fname = '%s_%s_%s.csv' % (site,storm,longshoreReso)
df.to_csv(os.path.join(ifilePath,fname),index=False)