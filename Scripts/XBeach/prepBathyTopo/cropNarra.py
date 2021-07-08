# Modules
import os
import pandas as pd
import xarray as xr

# Paths
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\TopoBathy\\Narrabeen\\prep"

# Column to begin "cropping"
colIndex = 13

# Load XBeach mesh as geodataframe - netCDF format
xbf = os.path.join(workDir,"ofiles","xbNarra_zb.nc")
xbds = xr.open_dataset(xbf)
ncolXB = xbds.ncols
nrowXB = xbds.nrows

xbds = xbds.isel(nx=slice(colIndex+1,ncolXB))
xbds.attrs["ncols"] = len(xbds.nx.values)
print(xbds.keys)

# Export file to nc
xbds.to_netcdf(os.path.join(workDir,"ofiles","xbNarra_zb_2021.nc"))

# Export flattened array to csv
xx = xbds["globalx"][:,:].values.flatten()
yy = xbds["globaly"][:,:].values.flatten()
zz = xbds["zb"][:,:].values.flatten()
df = pd.DataFrame({"x":xx,
                    "y":yy,
                    "z":zz})

df.to_csv(os.path.join(workDir,"ofiles", "xBeachGrid_2021.csv"), index=False)