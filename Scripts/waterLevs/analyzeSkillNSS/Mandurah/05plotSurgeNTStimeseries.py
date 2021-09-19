# ================= Modules ================= #
import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
import pytz
import numpy as np
import scipy
from datetime import datetime, timedelta
import matplotlib.dates as mdates


# ================= Paths ================= #
siteName = 'Mandurah'
workDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs\\analyzeSkillNSS\\%s" % siteName
waveDirectory = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves"
waveData = os.path.join("C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Data\\Waves\\Mandurah\\MAN54_YEARLY_PROCESSED\\MDW2020_Z.csv")
oDir = os.path.join(workDir,"ofiles","trial1-firstRound")
figDir = os.path.join(workDir,"figs")


# ================= Parameters ================= #
timezoneUTC = pytz.utc
leadTime = 72
# Storm periods to plot
"""d = {
    # May 2020 storm, May 23 to 29 GMT
    "May 2020 storm 1":('2020-05-2','2020-05-16'),
    # May 2020 storm, May 23 to 29 GMT
    "May 2020 storm 2":('2020-05-20','2020-06-02'),
    # June 2020 storm
    "June 2020 storm":('2020-06-20','2020-07-04n'),
    # July 2020 storm
    "July 2020 storm":('2020-07-10','2020-07-24')
}"""

# Non-storms for interest
d = {
    "July2020":('2020-07-1','2020-07-21')
}


# ================= Local functions ================= #
def generateTimeseriesPlot(fig=None, ax=None, df=None):
    # Plot Hsig on a secondary axis 
    ax2 = ax.twinx()
    ax2.plot(df.index,df.hsig,c='darkgrey',linestyle='dashed',linewidth=.8)
    ax2.set_ylabel("$H_{sig}$ (m)")
    #yhrange = max(df.hsig) - min(df.hsig)
    #yminh = min(df.hsig)-(.2*yhrange)
    #ymaxh = max(df.hsig)+(.3*yhrange)
    ax2.set_ylim(0.,9.)
    # Plot total water levels
    ax.plot(df.index,df.nts,color='dimgrey')
    ax.plot(df.index,df.surge,color='royalblue')
    print(df.wl_obs)
    #yrange = max(df.wl_obs) - min(df.wl_obs)
    #ymin = min(df.wl_obs)-(.2*yrange)
    #ymax = max(df.wl_obs)+(.7*yrange)
    ax.set_ylim(-1,2)
    ax.set_ylabel(variable)
    ax.set_title("%s" % (key))
    # Legend
    ax.legend(['observed non-tidal residual','predicted non-tidal residual'],loc='upper left')
    ax2.legend(['observed $H_{sig}$'],loc='upper right')
    # Format the x axis 
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b %H:%M"))
    ax.tick_params(axis='x', which='major', bottom=True, 
                   labelbottom=True, rotation=30,labelsize=6)
    return ax

# ================= Load Observed and Predicted Data ================= #
df = pd.read_csv(os.path.join(oDir, "WL-NTR-obsAndpred_%s_2020.csv" % siteName))
df.index = df['Unnamed: 0']
df = df.drop(['Unnamed: 0'],axis=1)
# Already in a format that is timezone-aware
df.index = pd.to_datetime(df.index)
# Reduce temporal resolution to hourly, since wave data collected hourly
# (and you're testing the skill of the storm periods)
df = df[df.index.strftime('%M') == '00']
print(type(df.index[0]))


# ================= Load Wave Data ================= #
dfw_obs = pd.read_csv(waveData, skiprows=4)
dfw_obs = dfw_obs.iloc[:,0:2]
print(dfw_obs.head())
# Convert datetime column to datetime objects and set as index
dfw_obs.index = pd.to_datetime(dfw_obs['Unnamed: 0'], format="%d/%m/%Y %H:%M")
awst = pytz.timezone("Australia/Perth")
dfw_obs.index = dfw_obs.index.tz_localize(awst).tz_convert(pytz.utc)
dfw_obs = dfw_obs.drop('Unnamed: 0',1)
# Rename columns
dfw_obs.columns = ['hsig']
print(dfw_obs.head())

# ================= Merge water levels and storm event data ================= #
df = pd.merge(df, dfw_obs, how='left',left_index=True, right_index=True)
print(df.head())


# ================= Plot non-tidal residuals and surge time series ================= #
# Font sizes
plt.rcParams.update({'font.size':7})
plt.rc('xtick', labelsize=7)
plt.rc('ytick', labelsize=7)
plt.rc('axes', labelsize=7,labelpad=1)
plt.rc('legend', handletextpad=1, fontsize=6)
# Fig params
fig, axes = plt.subplots(4,1,figsize=(5,8),sharex=False)
fig.subplots_adjust(top=0.94,hspace=.7)
df_subset = df[df['leadtime_hrs']==leadTime]
axs = np.array(axes).reshape(-1)


# Plot time series
variable = "surge (m)"
counter = 0
for key in d:
    # Subset data based on storm periods
    stormBegin = d[key][0]
    stormEnd = d[key][1]
    df_sub = df_subset[stormBegin:stormEnd]
    print(df_sub.columns)
    # Plot time series of twl and hsig (for reference)
    axwl = generateTimeseriesPlot(fig=fig,ax=axs[counter],df=df_sub)
    counter += 1
# Save fig
figName = 'NTStimeseries_%shrsLeadTime.png' % leadTime
fig.savefig(os.path.join(figDir,figName),dpi=250,bbox_inches='tight')
plt.show()
print(figDir)
