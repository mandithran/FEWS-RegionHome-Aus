import numpy as np
import os
import pandas as pd

storm = "2020_08_10"
mode = "pre-storm"

workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\topobathy"
ifilePath = os.path.join(workDir,"ifiles")
xgrd = os.path.join(ifilePath,"%s-x-%s.grd" % (storm,mode))
ygrd = os.path.join(ifilePath,"%s-y-%s.grd" % (storm,mode))
zgrd = os.path.join(ifilePath,"%s-z-%s.grd" % (storm,mode))

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
df.to_csv(os.path.join(workDir,'ofiles','%s-%s.csv' % (storm,mode)))