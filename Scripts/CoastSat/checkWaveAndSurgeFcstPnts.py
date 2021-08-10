import geopandas as gpd
import os
import matplotlib.pyplot as plt

# Paths
dataPath = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\CoastSat\\NSW"
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\CoastSat"

# Projections
wgs84 = int(4326)
utm = int(28356)

# Load shapefile
gdf = gpd.read_file(os.path.join(dataPath,"regionalTransects_NSW.shp"))
gdf = gdf.set_crs(epsg=utm)
print(gdf.columns)

#========================== General check of point stats ==========================#
# Get the min and max lat, lon
# Make sure you get something reasonable
print(min(gdf['nss_lat']),max(gdf['nss_lat']))
print(min(gdf['nss_lon']),max(gdf['nss_lon']))

# Check for any nan values in NSS points
# You should get empty geodataframes
print(gdf[gdf['nss_lat'].isnull()])
print(gdf[gdf['nss_lon'].isnull()])

# Get the min and max lat, lon
# Make sure you get something reasonable
print(min(gdf['wave_lat']),max(gdf['wave_lat']))
print(min(gdf['wave_lon']),max(gdf['wave_lon']))

# Check for any nan values in Wave points
# There should be a few profiles that are not within range
# of the wave forecasts
print(gdf[gdf['wave_lat'].isnull()])
print(gdf[gdf['wave_lon'].isnull()])


#========================== Check NSS Points ==========================#
# Compute distance between profile lines and their respective NSS points
# Separate out the nss points into their own df
gdf_nss = gpd.GeoDataFrame(gdf[['id', 'nss_lat', 'nss_lon']].copy(),
          geometry=gpd.points_from_xy(gdf.nss_lon, gdf.nss_lat))
# Assign projection to nss point gdf
gdf_nss = gdf_nss.set_crs(epsg=wgs84, inplace=True)
# Reproject nss points to UTM 
gdf_nss =  gdf_nss.to_crs(epsg=utm)
# Re-merge dataframes
gdf = gdf.merge(gdf_nss, on=['id','nss_lat','nss_lon'], how='left')
gdf = gpd.GeoDataFrame(gdf,geometry=gdf.geometry_x).set_crs(epsg=utm)
gdf = gdf.rename(columns={"geometry_y":"geometry_nss"})
gdf = gdf.drop(['geometry_x'],axis=1)
print(gdf.columns)
# Compute distances
gdf['nss_dist'] = gdf.geometry.distance(gdf["geometry_nss"])
print("Maximum distance NSS points:")
print(gdf.nss_dist.max())
# Print the max
fig1, ax1 = plt.subplots()
ax1 = gdf.nss_dist.plot.hist(bins=12)
ax1.set_title("Histogram of distances away from\nprofile (NSS points)")
plt.xlabel("Distance away from profile (m)")
#plt.show()
fig1.savefig(os.path.join(workDir,"nss_distancesHistogram.png"))


#========================== Check Wave Forecast Points ==========================#
# Compute distance between profile lines and their respective NSS points
# Separate out the nss points into their own df
gdf_wave = gpd.GeoDataFrame(gdf[['id', 'wave_lat', 'wave_lon']].copy(),
          geometry=gpd.points_from_xy(gdf.wave_lon, gdf.wave_lat))
# Assign projection to nss point gdf
gdf_wave = gdf_wave.set_crs(epsg=wgs84, inplace=True)
# Reproject nss points to UTM 
gdf_wave =  gdf_wave.to_crs(epsg=utm)
# Re-merge dataframes
gdf = gdf.merge(gdf_wave, on=['id','wave_lat','wave_lon'], how='left')
gdf = gpd.GeoDataFrame(gdf,geometry=gdf.geometry_x).set_crs(epsg=utm)
gdf = gdf.rename(columns={"geometry_y":"geometry_wave"})
gdf = gdf.drop(['geometry_x'],axis=1)
print(gdf.head())
print(gdf.columns)
# Drop nans
gdf = gdf.dropna()
# Compute distances
gdf['wave_dist'] = gdf.geometry.distance(gdf["geometry_wave"])
print(gdf.wave_dist)
# Print the max
print("Maximum distance wave points:")
print(gdf.wave_dist.max())
fig2, ax2 = plt.subplots()
ax2 = gdf.wave_dist.plot.hist(bins=12)
ax2.set_title("Histogram of distances away from\nprofile (Wave forecast points)")
plt.xlabel("Distance away from profile (m)")
fig2.savefig(os.path.join(workDir,"wave_distancesHistogram.png"))
#gdf = gdf.sort_values(by=['wave_dist'],ascending=False)
#print(gdf.head(20))
#plt.show()

# Drop the other geometry columns and export
gdf = gdf.drop(['geometry_wave','geometry_nss'],axis=1)
gdf.to_file(os.path.join(dataPath,"01profiles_cleaned.shp"))