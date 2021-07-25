import geopandas as gpd
import os

# Paths
dataPath = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\CoastSat\\NSW"

# Load shapefile
gdf = gpd.read_file(os.path.join(dataPath,"regionalTransects_NSW.shp"))
print(gdf.head())
print(gdf.columns)

# Check NSS stuff
# Get the min and max lat, lon
print(min(gdf['nss_lat']),max(gdf['nss_lat']))
print(min(gdf['nss_lon']),max(gdf['nss_lon']))

# Return any nan values in NSS points
# You should get empty geodataframes
print(gdf[gdf['nss_lat'].isnull()])
print(gdf[gdf['nss_lon'].isnull()])

# Compute distance between profile lines and their respective NSS points
#plots_df['scarp_dist'] = plots_df.geometry.apply(lambda g: scarpOverall.distance(g).min())
