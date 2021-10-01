#====================================================================================
# Script: pickDuneToe.py
# Author: Mandi Thran
# Date: 15 September 2021

# This script visualizes the cross-shore profiles of an XBeach input grid, one by one.
# To control the row number of the profile that is visualized, change the rowNum 
# variable. This script is used to identify the location of the dune toes, which are
# used to generate the storm impact indicators for the hotspot forecasts. It this 
# case, rowNum=1 relates to the northern-most row (profile). As rowNum increases,
# profiles are visualized progressively to the south.

# The inputs are designated in the "Variables" section.

# For best results, activate and run in the virtual environment associated with
# running FEWS forecasts.
#====================================================================================


#=============== Modules ===============#
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt


#=============== Variables ===============#
# The main variable controlling which profile is visualized
# In the Narrabeen example, rowNum = 1 is the northern-most profile
# (row) of the grid. As the numbers increase, the profiles are
# visualized progressively south.
rowNum = 69
# The date of the storm. Used to load the specific pre-storm
# survey used in the XBeach model.
storm = "2020_02_09"
# Site name
site = "Narrabeen"
# Loads the pre-storm survey as opposed to the post-storm survey.
mode = "pre-storm"
# Alongshore resolution, again used to load the correct XBeach grid.
alongshore_reso = 50 # in meters
# The region home specified in FEWS.
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
# The working directory where this script is contained.
workDir = os.path.join(regionHome,"Scripts\\topobathy")
# File path leading to the XBeach grids
ifilePath = os.path.join(regionHome, "Data\\xbeach\\%s\\grd\\%s\\pre-storm\\%smAlongshore" % (site,storm,alongshore_reso))


#=============== Specify/load grids ===============#
xgrd = os.path.join(ifilePath,"x.grd")
ygrd = os.path.join(ifilePath,"y.grd")
zgrd = os.path.join(ifilePath,"z.grd")
xx = np.loadtxt(xgrd,delimiter='\t')
yy = np.loadtxt(ygrd,delimiter='\t')
zz = np.loadtxt(zgrd,delimiter='\t')


#=============== Plot profile ===============#
# Shape function prints rows, columns
# Grid goes from seaward to landward with increasing
# column index
print(xx.shape)
# Figure specifications
fig, ax = plt.subplots(1,1,figsize=(10,6.))
# Convert row number to an index number
rowInd = rowNum - 1
# Scatter plot of chainage (x) vs elevation (z)
ax.scatter(xx[rowInd,:],zz[rowInd,:], color='b')
# Axes labels
ax.set_xlabel('x')
ax.set_ylabel('elevation')
# Show the plot
plt.show()
