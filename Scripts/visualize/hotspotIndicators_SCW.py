# modules
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from datetime import datetime, time, timedelta
import pytz
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import seaborn as sns

# Use initial time to set up geodataframe
time_t0 = datetime(year=2020,month=2,day=1,hour=0)
time_t0_str = time_t0.strftime("%Y%m%d_%H%M")

# Set up time series to loop through
deltat = timedelta(hours=12) # timestep for water level time series
startTime = datetime(year=2020,month=2,day=1,hour=0)
endTime = datetime(year=2020,month=2,day=29,hour=12)

# These shapefiles are in UTM (EPSG:28356)
regionHome = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus"
indicatorPath_t0 = os.path.join(regionHome, "Forecasts", time_t0_str, 
                            "NSW\\hotspot\\Narrabeen\\XBeach\\postProcess\\indicators")
safeCorrPath_t0 = os.path.join(indicatorPath_t0,"safe-corridorOverall.shp")
#buildScarpPath_t0 = os.path.join(indicatorPath_t0,"building-scarpDistOverall.shp")

# Safe corridor
# Overall goal is to get a dataframe with id, geom, centroid, then columns for each time step
# Use the first timestep to initalize the dataframe
sc_gdf = gpd.read_file(safeCorrPath_t0)
newColName2 = "%s" % time_t0
sc_gdf[newColName2] = sc_gdf['SCW']
# TODO: bring ID column back when IDs are assigned
sc_gdf = sc_gdf.drop(columns=['SCW','ewl_dist'],axis=1)


# TODO: for now, merge assigned ids for corridors so that they can go from north to south
idsPath = os.path.join(regionHome,"Data\\Indicators\\Hotspot\\Narrabeen\\corridors50m.shp")
id_gdf = gpd.read_file(idsPath)
sc_gdf = sc_gdf.merge(id_gdf,how='left',on=['geometry'],right_index=False)
# Drop the Nans for now
sc_gdf = sc_gdf.dropna()

# Generate time series
timeSeries = np.arange(startTime,endTime+deltat,deltat)
for time in timeSeries:
    # Format time as string
    time_pd = pd.to_datetime(time) 
    time_str = time_pd.strftime("%Y%m%d_%H%M")
    print(time_str)
    # Paths
    indicatorPath = os.path.join(regionHome, "Forecasts", time_str, 
                            "NSW\\hotspot\\Narrabeen\\XBeach\\postProcess\\indicators")
    safeCorrPath = os.path.join(indicatorPath,"safe-corridorOverall.shp")
    step_gdf = gpd.read_file(safeCorrPath)
    step_gdf = step_gdf.rename(columns={"SCW":"%s" % time_pd})
    #TODO: Bring ID and ewl_dist columns back when ID is assigned
    step_gdf = step_gdf.drop(columns=["corr_id","ewl_dist",
                                      "centerxUTM","centeryUTM"],axis=1)
    sc_gdf = sc_gdf.merge(step_gdf,how='left',on=['geometry'],right_index=False)

# Sort by Id - runs north to south
startTime_str = pd.to_datetime(startTime)
sc_gdf = sc_gdf.drop(columns=["corr_id_y","centerxUTM_y",
                              "centeryUTM_y","%s_y" % startTime], axis=1)
sc_gdf = sc_gdf.rename(columns={"corr_id_x":"corr_id",
                                "centerxUTM_x":"centerxUTM",
                                "centeryUTM_x":"centeryUTM",
                                "%s_x" % startTime_str: startTime_str})
sc_gdf = sc_gdf.sort_values('corr_id')

# Format dataframe for heatmap
sc_gdf = sc_gdf.drop(columns=['geometry','centerxUTM','centeryUTM'])
sc_gdf = sc_gdf.set_index(sc_gdf['corr_id'])
sc_gdf = sc_gdf.drop(columns=['corr_id'],axis=1)


#=========================== Plot heatmap ===========================#
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.dates import DateFormatter

date_form = DateFormatter("%Y-%m-%d\n%H:%M")

# create dictionary with value to integer mappings
value_to_int = {value: i for i, value in enumerate(sorted(pd.unique(sc_gdf.values.ravel())))}

n = len(value_to_int)     
# discrete colormap (n samples from a given cmap)
cmap = colors.ListedColormap(['red','green','yellow'])
boundaries = np.arange(0,n,1)
norm = colors.BoundaryNorm(boundaries, cmap.N, clip=True)
# Plot heatmap
fig, (ax1, ax2) = plt.subplots(2, sharex=False, figsize=(12, 7))
cbar_ax = fig.add_axes([.91, .575, .03, .3])
fig.canvas.draw()
sns.heatmap(sc_gdf.replace(value_to_int), ax=ax1, cmap=cmap, cbar_ax=cbar_ax) 

# modify colorbar:
colorbar = ax1.collections[0].colorbar 
r = colorbar.vmax - colorbar.vmin 
colorbar.set_ticks([colorbar.vmin + r / n * (0.5 + i) for i in range(n)])
colorbar.set_ticklabels(list(value_to_int.keys()))    
# Tick labels
labels = ax1.get_xticklabels()
labels = [str(l).split(" ")[2].split("'")[1] + "\n" + str(l).split(" ")[3].split("'")[0] for l in labels]
ax1.set_xticklabels(labels, rotation = 40, va="center")
ax1.tick_params(axis='x',pad=30)
n = 6  # Keeps every 7th label
[l.set_visible(False) for (i,l) in enumerate(ax1.xaxis.get_ticklabels()) if i % n != 0]


# ================= Load Wave Data ================= #
waveDirectory = os.path.join(regionHome,"Data\\Waves\\Sydney\\observations")
waveData = os.path.join(waveDirectory, "offshoreSydneyWaveObs.csv")
dfw_obs = pd.read_csv(waveData)
# Waves in AEST
dfw_obs.columns = ['datetime','hrms','hsig','h10','hmax','tz','Tp','wdir','nan']
# Keep only the parameters of interest
dfw_obs = dfw_obs[['datetime','hsig']]
# Convert date time string to date time object
dfw_obs["datetime"] = pd.to_datetime(dfw_obs["datetime"], format="%d/%m/%Y %H:%M")
# Set datetime as index
dfw_obs.index = dfw_obs['datetime']
dfw_obs = dfw_obs.drop('datetime',axis=1)
# Subtract 10 hours from time series (convert AEST to UTC)
dfw_obs.index = dfw_obs.index - timedelta(hours=int(10))
# Need to do some things with axes labels and shared axes because heatmap won't let me specify x,y
sc_gdf_T = sc_gdf.transpose()
sc_gdf_T.index = pd.to_datetime(sc_gdf_T.index)
# Filter to appropriate time frame designated above
dfw_obs = dfw_obs[dfw_obs.index>=startTime-timedelta(hours=12)] 
dfw_obs = dfw_obs[dfw_obs.index<=endTime] 
# Resample wave data for the sake of the ticks - should be equal interval
upsampled = dfw_obs.resample('H', origin=dfw_obs.index[0]).asfreq()
interpolated = upsampled.interpolate(method='linear')


# ================= Plot Wave Data ================= #
ax2.plot(interpolated.index,interpolated['hsig'])
ax2.set_xlim([interpolated.index[0], interpolated.index[-1]])
# Tick labels
dt_strings = interpolated.index.strftime('%Y-%m-%d %H:%M')
# Really struggled to get axes aligned, sharex=True didn't work for heatmap + line plot
# Consider using an alternative to the seaborn heatmap in the future so you can sharex and make the indeces datetime index
ax2.set_xticks(interpolated.index)
ax2.set_xticklabels(dt_strings)
labels2 = ax2.get_xticklabels()
print(len(ax2.get_xticklabels()))
labels2 = [str(l).split(" ")[2].split("'")[1] + "\n" + str(l).split(" ")[3].split("'")[0] for l in labels2] #+ .split("'")[1] "\n" + str(l).split(" ")[3].split("'")[0]
ax2.set_xticklabels(labels2, rotation = 40, va="center")
ax2.tick_params(axis='x',pad=30)
n = 72
[l.set_visible(False) for (i,l) in enumerate(ax2.xaxis.get_ticklabels()) if i % n != 0]
plt.subplots_adjust(hspace=0.5)
plt.show()

