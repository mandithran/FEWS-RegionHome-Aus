# Modules
import os
import pandas as pd
import xarray as xr
import numpy as np

# Paths
workDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Data\\TopoBathy\\Narrabeen\\prep"

# Load XBeach mesh as geodataframe - netCDF format
xbf = os.path.join(workDir,"ofiles","xbNarra_zb_2021.nc")
xbds = xr.open_dataset(xbf)
ncolXB = xbds.ncols
nrowXB = xbds.nrows

# Select every 4 rows
rowArr = np.arange(0,nrowXB,4)

# Select every 4 columns
colArr = np.arange(0,ncolXB,4)

# Index ds (select)
xbds = xbds.isel(nx=colArr,ny=rowArr)

# Overwrite new number of cols/rows
xbds.attrs["nrows"] = len(xbds.ny.values)
xbds.attrs["ncols"] = len(xbds.nx.values)
print(xbds.keys)

# Export file to nc
xbds.to_netcdf(os.path.join(workDir,"ofiles","xbNarra_zb_2021_testing.nc"))

# Export flattened array to csv
xx = xbds["globalx"][:,:].values.flatten()
yy = xbds["globaly"][:,:].values.flatten()
zz = xbds["zb"][:,:].values.flatten()
df = pd.DataFrame({"x":xx,
                    "y":yy,
                    "z":zz})

df.to_csv(os.path.join(workDir,"ofiles", "xBeachGrid_2021_testing.csv"), index=False)


"""data = np.arange(20).reshape(4, 5)
ds = xr.Dataset({"A": (["x", "y"], data)})
print(ds.A)
print("result:")
ds2 = ds.isel(x=[0,2],y=[0,2,4])
print(ds2.A)"""
#ds2 = ds.drop_sel(y=["a", "c"])
#print(ds2.A)