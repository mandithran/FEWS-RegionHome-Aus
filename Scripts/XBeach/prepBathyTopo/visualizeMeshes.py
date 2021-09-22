"""
This script exports the meshes for the SYD.msh output, the SYD.spec output,
and the XBeach output. The csv outputs can then be quickly visualized
using GIS software. 

"""


import os
import xarray as xr
import numpy as np
import pandas as pd

#============== Variables ==============#
regionHomeDir = "C:\\Users\\mandiruns\Documents\\01_FEWS-RegionHome-Aus"
workDir = os.path.join(regionHomeDir,"Scripts\\XBeach\\prepBathyTopo")


#============== Paths ==============#
#meshFile = os.path.join(workDir, "ncFiles", "SYD.msh.20210220T1200Z.nc")
meshFile = "J:\\Coastal\\Data\\Wave\\Forecast\\BOM_products\\BOM_nearshore_wave_transformation_tool\\raw\\Mesh\\test\\PER\\PER.msh.20200305T0000Z.nc"
specFile = os.path.join(workDir, "ncFiles", "SYD.spec.20210220T1200Z.nc")
xBeachNC = os.path.join(regionHomeDir,"Data\\TopoBathy\\Narrabeen\\prep\\ifiles", "xboutput.nc")
oDir =  os.path.join(workDir,"ofiles")


# Un-comment this block to process the non-spectral Auswave output (with parameters)
#============== Process nc file for site ==============#
# Load dataset
ds = xr.open_dataset(meshFile)


# Take a look at existing coordinates, dimensions, and variables
# if verbose mode is specified
print("NetCDF file metadata:")
print(ds.keys)

# Send lat, lon, and variables to pandas df
#ds = ds.isel(time=[0],noel=[0],element=[0])
#df = ds.to_dataframe(ds)
#print(df)
df = pd.DataFrame({"lon":ds["longitude"].values,
                    "lat":ds["latitude"].values})
print(df.head())
#varKeys = np.array(list(ds.keys()))
#vars2Delete = np.array(["longitude","latitude","crs","tri"])
#dataVars = np.setdiff1d(varKeys, vars2Delete)

#for var in dataVars:
#    df[var] = ds[var][0,:].values

df.to_csv(os.path.join(oDir,"PER.msh.20200305T0000Z.csv"),index=False)


# Un-comment this block to process spectral output
"""#============== Spec File ==============#
# Load dataset
ds = xr.open_dataset(specFile)

# Take a look at existing coordinates, dimensions, and variables
# if verbose mode is specified
print("NetCDF file metadata:")
#print(ds.keys)

df = pd.DataFrame({"lon":ds["longitude"][0].values,
                    "lat":ds["latitude"][0].values})

varKeys = np.array(list(ds.keys()))
vars2Delete = np.array(["longitude","latitude","crs","tri",
                "efth","frequency","frequency1","frequency2",
                "station", "station_name","time"])
dataVars = np.setdiff1d(varKeys, vars2Delete)

#Add Station names and IDS
df["stationName"] = ds.station_name.values
df["stationID"] = ds.station.values

for var in dataVars:
    df[var] = ds[var][0,:].values

df.to_csv(os.path.join(workDir, "ncFiles", "sydSpec.csv"))"""

# Uncomment this block to process the xbeach output
"""# Load dataset
ds = xr.open_dataset(xBeachNC)

# Take a look at existing coordinates, dimensions, and variables
# if verbose mode is specified
print("NetCDF file metadata:")

ncols = 154
nrows = 138

# Drop excess data variables except for bed level at t=0
ds = ds.get(['zb'])
ds = ds.isel({"globaltime":0})

# Write nrows and ncols as metadata
ds.attrs["nrows"] = nrows
ds.attrs["ncols"] = ncols
ds.attrs["epsg"] = 28356

xx = ds["globalx"][:,:].values.flatten()
yy = ds["globaly"][:,:].values.flatten()
zz = ds["zb"][:,:].values.flatten()

# Export flattened array to csv
df = pd.DataFrame({"x":xx,
                    "y":yy,
                    "z":zz})

df.to_csv(os.path.join(workDir, "ofiles", "xBeachGrid.csv"), index=False)


# Export bed level file to nc
ds.to_netcdf(os.path.join(workDir, "ofiles", "xbNarra_zb.nc"))"""