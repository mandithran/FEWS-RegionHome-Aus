import numpy as np
import os
import pandas as pd

#np.set_printoptions(suppress=True,
#   formatter={'float_kind':'{:16.3f}'.format}, linewidth=130)

reductionFactor = int(2)

workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\topobathy"
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
ifilePath = os.path.join(regionHome,"Data\\xbeach\\Narrabeen\\grd\\2020_02_09\\pre-storm")
ofilePath = os.path.join(ifilePath,"%sReso" % reductionFactor)
xgrd = "x.grd"
ygrd = "y.grd"
zgrd = "z.grd"
ne_layer = "ne_layer.grd"

def reduceReso(fname,factor):
    arr2d = np.loadtxt(os.path.join(ifilePath,fname))
    arr2d = arr2d[::factor,:].round(2)
    np.savetxt(os.path.join(ofilePath,fname), arr2d, '%10.2f', delimiter='\t')

reduceReso(xgrd,reductionFactor)
reduceReso(ygrd,reductionFactor)
reduceReso(zgrd,reductionFactor)
reduceReso(ne_layer,reductionFactor)


#print(arr2d[::2,:])