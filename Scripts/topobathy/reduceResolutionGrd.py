import numpy as np
import os
import pandas as pd

#np.set_printoptions(suppress=True,
#   formatter={'float_kind':'{:16.3f}'.format}, linewidth=130)

reductionFactorLongshore = int(3)
reductionFactorCrosshore = int(1)

workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\topobathy"
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
ifilePath = os.path.join(regionHome,"Data\\xbeach\\Narrabeen\\grd\\2020_02_09\\pre-storm")
ofilePath = os.path.join(ifilePath,"4Long")
xgrd = "x.grd"
ygrd = "y.grd"
zgrd = "z.grd"
ne_layer = "ne_layer.grd"

def reduceReso(fname,factorLongshore,factorCrosshore):
    arr2d = np.loadtxt(os.path.join(ifilePath,fname))
    print(arr2d.shape)
    arr2d = arr2d[::factorLongshore,::factorCrosshore].round(2)
    print(arr2d.shape)
    np.savetxt(os.path.join(ofilePath,fname), arr2d, '%10.2f', delimiter='\t')

reduceReso(xgrd,reductionFactorLongshore,reductionFactorCrosshore)
reduceReso(ygrd,reductionFactorLongshore,reductionFactorCrosshore)
reduceReso(zgrd,reductionFactorLongshore,reductionFactorCrosshore)
reduceReso(ne_layer,reductionFactorLongshore,reductionFactorCrosshore)


#print(arr2d[::2,:])