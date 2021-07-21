import xarray as xr
import pandas as pd

ds = xr.Dataset({"temperature": (["x", "y", "time"], temp),
                 "precipitation": (["x", "y", "time"], precip)},
                  coords={"lon": (["x", "y"], lon),
                          "lat": (["x", "y"], lat),
                          "time": pd.date_range("2014-09-06", periods=3),
                          "reference_time": pd.Timestamp("2014-09-05")})