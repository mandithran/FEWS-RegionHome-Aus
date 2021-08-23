# Modules
import os
import xarray as xr
import pandas as pd

# Paths
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
ncPath = os.path.join(regionHome,"Data\\Waves\\Sydney\\auswave\\example")
ifile = os.path.join(ncPath,"SYD.msh.20200208T0000Z.nc")


ds = xr.open_dataset(ifile)
ds = ds.isel({"time":100})
print(ds.keys())
df = pd.DataFrame({"lon":ds["longitude"].values,
                   "lat":ds["latitude"].values,
                   "dir":ds["dir"].values,
                   "hs":ds["hs"].values})

df.to_csv(os.path.join(ncPath,"Syd_samplemesh.csv"),index=False)
