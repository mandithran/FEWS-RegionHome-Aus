import os
import xarray as xr
import numpy as np

regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
runsDir = os.path.join(regionHome,"Modules\\XBeach\\Narrabeen\\runs\\")

model1WorkDir = os.path.join(runsDir, "2021050300\\workDir")
model2WorkDir = os.path.join(runsDir, "2021050300_3\\workDir")

ds_m1 = xr.open_dataset(os.path.join(model1WorkDir,"xboutput.nc"))
ds_m2 = xr.open_dataset(os.path.join(model2WorkDir,"xboutput.nc"))


ds_diff = ds_m1[['nx','ny']]
ds_diff = ds_diff.expand_dims("time_check")

################ Check waves difference ################
datasets = []
for t in np.arange(1,ds_m1["meantime"].sizes["meantime"]-15,1):
#for t in np.arange(1,3,1):
    ds1 = ds_m1.isel({"meantime":t})
    ds2 = ds_m2.isel({"meantime":t})
    #print(ds1.H_mean[:,:].values)
    data = np.subtract(ds1.H_mean[:,:].values, ds2.H_mean[:,:].values)
    #print(data)
    ds_d = xr.DataArray(data,[("ny", ds1.ny),
                              ("nx", ds1.nx)])
    datasets.append(ds_d)
    
combined = xr.concat(datasets, dim="time_check")
mean_diff = combined.mean(dim="time_check")
mean_diff.to_netcdf(os.path.join(model1WorkDir,"diff_H_mean_MEAN.nc"))
std_diff = combined.std(dim="time_check")
std_diff.to_netcdf(os.path.join(model1WorkDir,"diff_H_mean_STD.nc"))


################ Check water levels difference ################
datasets = []
for t in np.arange(1,ds_m1["meantime"].sizes["meantime"]-15,1):
#for t in np.arange(1,3,1):
    ds1 = ds_m1.isel({"meantime":t})
    ds2 = ds_m2.isel({"meantime":t})
    #print(ds1.H_mean[:,:].values)
    data = np.subtract(ds1.zs_mean[:,:].values, ds2.zs_mean[:,:].values)
    #print(data)
    ds_d = xr.DataArray(data,[("ny", ds1.ny),
                              ("nx", ds1.nx)])
    datasets.append(ds_d)
    
combined = xr.concat(datasets, dim="time_check")
mean_diff = combined.mean(dim="time_check")
mean_diff.to_netcdf(os.path.join(model1WorkDir,"diff_zs_mean_MEAN.nc"))
std_diff = combined.std(dim="time_check")
std_diff.to_netcdf(os.path.join(model1WorkDir,"diff_zs_mean_STD.nc"))

# Check water level difference
