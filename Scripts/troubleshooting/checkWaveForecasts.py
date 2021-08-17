import xarray as xr
from xbfewsTools import preProcWaves
import pickle
import os
import geopandas as gpd
import pandas as pd

pd.set_option('display.max_rows', 1000)

# Paths
wavesDir = "J:\\Coastal\\Data\\Wave\\Forecast\\BOM products\\BOM nearshore wave transformation tool\\raw\\Mesh"
forecastDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Forecasts_firstrun\\20200202_1200\\NSW\\hotspot\\Narrabeen"

hotspotFcst = pickle.load(open(os.path.join(forecastDir,"forecast_hotspot.pkl"),"rb"))
wavesDs = preProcWaves.loadAuswave(forecast=hotspotFcst, wavesDir=wavesDir)
offshore_df = pd.DataFrame({"lat":hotspotFcst.offshoreWaveLat,
                                "lon":hotspotFcst.offshoreWaveLon},
                                index=[0])
offshore_gdf = gpd.GeoDataFrame(offshore_df,geometry=gpd.points_from_xy(offshore_df.lon,offshore_df.lat))
offshore_gdf.set_crs(epsg=hotspotFcst.auswaveEPSG)
wavesOffshoreDs = preProcWaves.extractAusWavePts(ds=wavesDs,meshPts=offshore_gdf,epsg=hotspotFcst.auswaveEPSG)
wavesOffshoreDs = wavesOffshoreDs[['hs']]
offshore_df = wavesOffshoreDs.to_dataframe()
#print(offshore_df)
morstart_ = None
morstop_ = None
hotspotFcst.stormPeriods = preProcWaves.determineStormPeriods(df=offshore_df)
print(hotspotFcst.stormPeriods)