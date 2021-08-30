import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

storm = "2020_02_09"
site = "Narrabeen"
mode = "pre-storm"

workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\topobathy"
ifilePath = os.path.join("C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\xbeach\\%s\\grd\\%s\\pre-storm\\4Long" % (site,storm))
xgrd = os.path.join(ifilePath,"x.grd")
ygrd = os.path.join(ifilePath,"y.grd")
zgrd = os.path.join(ifilePath,"z.grd")

xx = np.loadtxt(xgrd,delimiter='\t')
yy = np.loadtxt(ygrd,delimiter='\t')
zz = np.loadtxt(zgrd,delimiter='\t')

# Shape function prints rows, columns
# Grid from seaward to landward
print(xx.shape,yy.shape,zz.shape)
fig, ax = plt.subplots(1,1,figsize=(10,6.))
#colIndex = np.arange(0,xx.shape[1],1)
rowNum = 46
rowInd = rowNum - 1
ax.scatter(xx[rowInd,:],zz[rowInd,:], color='b')
print(xx[rowInd,:])
ax.set_xlabel('x')
ax.set_ylabel('elevation')
plt.show()

#print(zz[:,0])
#print()