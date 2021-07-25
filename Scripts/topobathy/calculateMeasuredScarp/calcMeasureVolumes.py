import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator

# Load up each of these files
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\topobathy\\calculateMeasuredScarp"
sgrd_post = os.path.join(workDir,'./2020-09-02_poststorm_s.csv')
pgrd_post = os.path.join(workDir,'./2020-09-02_poststorm_p.csv')
zgrd_post = os.path.join(workDir,'./2020-09-02_poststorm_z.csv')

sgrd_post = np.loadtxt(sgrd_post)
pgrd_post = np.loadtxt(pgrd_post)
zgrd_post = np.loadtxt(zgrd_post)

# Determine if x and y spacing are equal everywhere
"""# Check x spacing
nrows,ncols = sgrd_post.shape
print(nrows)
for row in range(nrows):
    arr=sgrd_post[row,:]
    flag=all(np.diff(arr)==np.diff(arr)[0])
    if flag == False:
        print("False s (x)")
# Check y spacing
#for col in range(ncols):
for col in range(ncols):
    arr=pgrd_post[:,col]
    flag=all(np.diff(arr)==np.diff(arr)[0])
    if flag == False:
        print("False z (y)")"""

# make these smaller to increase the resolution
# generate 2 2d grids for the x & y bounds
x = sgrd_post[0,:]
y = pgrd_post[:,0]
# x and y are bounds, so z should be the value *inside* those bounds.
# Therefore, remove the last value from the z array.
z = zgrd_post[:-1, :-1]
levels = MaxNLocator(nbins=15).tick_values(-20, 20)
# pick the desired colormap, sensible levels, and define a normalization
# instance which takes data values and translates those into levels.
cmap = plt.get_cmap('viridis')
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
fig, ax0 = plt.subplots(nrows=1)
im = ax0.pcolormesh(x, y, z, cmap=cmap, norm=norm)
# Simple raster plot
#a = np.random.random((16, 16))
#plt.imshow(zgrd_post, cmap='viridis', interpolation='nearest')
plt.colorbar(im)
plt.show()


# Load up the pre-storm
