# Modules
import os
import pandas as pd
import geopandas as gpd

# Paths
dataPath = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\CoastSat\\NSW"
# Profiles that have nss and wave forecast points assigned
# See checkWaveAndSurgeFcstPnts.py
ifile = os.path.join(dataPath,'01profiles_cleaned.shp')

# Projections
wgs84 = int(4326)
utm = int(28356)

#===================== Load shapefile with profiles =====================#
gdf = gpd.read_file(ifile)
gdf = gdf.set_crs(epsg=utm)
print(gdf.columns)
#gdf = gdf[0:25]


#===================== Determine unique sites =====================#
sites = gdf.site_id.unique()
print(sites)


#===================== Load values from each of the sites into dataframe =====================#
gdf_slopes = pd.DataFrame(columns=['id', 'beta'])
for site in sites:
    betaPath = os.path.join(dataPath,'csv_full',site,'transect_coordinates_and_beach_slopes.csv')
    gdf_site = pd.read_csv(betaPath)
    gdf_site = gdf_site[['Transect id','Beach face slope']]
    gdf_site = gdf_site.rename(columns={"Transect id":"id","Beach face slope":"beta"})
    gdf_slopes = gdf_slopes.append(gdf_site)
    #print(betaPath)


#===================== Merge the original gdf with the slopes based on id =====================#
gdf = gdf.merge(gdf_slopes,how='left',on=['id'],right_index=False)
# Drop nans
gdf = gdf.dropna()
# Export to file
gdf.to_file(os.path.join(dataPath,'02profiles_cleaned.shp'))
#print(gdf)