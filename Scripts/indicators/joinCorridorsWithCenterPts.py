# Modules
import os
import geopandas as gpd

# Projections
wgs84 = int(4326)
utm = int(28356)

# Paths
regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
siteName = "Narrabeen"
dataPath = os.path.join(regionHome,"Data")
indicatorPath = os.path.join(dataPath, "Indicators\\Hotspot\\%s"  % siteName)
corrshp = os.path.join(indicatorPath, "corridorsPolyline100m.shp")
corrpts = os.path.join(indicatorPath, "corridorsPolyline100m_centerpts.shp")
corr_out = os.path.join(indicatorPath,"corridors100m.shp")

# Load files
gdf = gpd.read_file(corrshp)
gdf = gdf.set_crs(epsg=utm)
gdf_pts = gpd.read_file(corrpts)
gdf_pts = gdf_pts.set_crs(epsg=utm)

# Drop/rename certain columns
gdf = gdf[['corr_id','geometry']]
gdf_pts['geom_center'] = gdf_pts['geometry']
gdf_pts = gdf_pts[['corr_id','geom_center']]

# Merge geodataframes
gdf = gdf.merge(gdf_pts, how='left', on='corr_id')

# Assign center points as columns, not as shapely geometries
gdf['centerxUTM'] = gdf.geom_center.x
gdf['centeryUTM'] = gdf.geom_center.y
gdf = gdf.drop(columns=['geom_center'],axis=1)

# Write new file
gdf.to_file(corr_out)
print(gdf.head())