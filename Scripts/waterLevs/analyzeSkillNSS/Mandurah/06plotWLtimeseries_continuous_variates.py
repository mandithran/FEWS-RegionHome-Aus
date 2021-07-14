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
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs\\analyzeSkillNSS\\%s" % siteName
waveDirectory = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves"
dataDir = 'C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\waterLevs\\Mandurah'
waveData = os.path.join("C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Data\\Waves\\Mandurah\\MAN54_YEARLY_PROCESSED\\MDW2020_Z.csv")
oDir = os.path.join(workDir,"ofiles")
figDir = os.path.join(workDir,"figs")


# ================= Parameters ================= #
timezoneUTC = pytz.utc
variate = 'concatenate'

# Storm periods to plot
plotPeriods = [datetime(2020,5,4,0),
               #datetime(2020,5,3,0),
               datetime(2020,5,1,0)]
               
               #datetime(2020,5,20,0),
               #datetime(2020,5,23,0),]

# ================= Local functions ================= #
def generateTimeseriesPlot(fig=None, ax=None, df=None):
    # Plot Hsig on a secondary axis 
    #ax2 = ax.twinx()
    #ax2.plot(df.index,df.hsig,c='darkgrey',linestyle='dashed',linewidth=.8)
    #ax2.set_ylabel("$H_{sig}$ (m)")
    #yhrange = max(df.hsig) - min(df.hsig)
    #yminh = min(df.hsig)-(.2*yhrange)
    #ymaxh = max(df.hsig)+(.3*yhrange)
    #ax2.set_ylim(0.,9.)
    # Plot total water levels
    ax.plot(df.index,df.wl_obs,color='dimgrey')
    ax.plot(df.index,df.twl_for,color='royalblue')
    #yrange = max(df.wl_obs) - min(df.wl_obs)
    #ymin = min(df.wl_obs)-(.2*yrange)
    #ymax = max(df.wl_obs)+(.7*yrange)
    ax.set_ylim(-1,2)
    ax.set_ylabel(variable)
    ax.set_title("%s" % (key))
    # Legend
    ax.legend(['observed','predicted (tide + surge)'],loc='upper left')
    #ax2.legend(['observed $H_{sig}$'],loc='upper right')
    # Format the x axis 
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b %H:%M"))
    ax.tick_params(axis='x', which='major', bottom=True, 
                   labelbottom=True, rotation=30,labelsize=6)
    return ax

# ================= Load tide predictions and water level observations ================= #
# This was converted to GMT in 01assessNSSSkill scripts
ifile = os.path.join(oDir,'WL-NTR-obs_Mandurah_%s.csv' % variate)
df_obs = pd.read_csv(ifile)
# Convert datetime column to datetime objects and set as index
df_obs.index = df_obs['Unnamed: 0']
df_obs = df_obs.drop(['Unnamed: 0'],axis=1)
df_obs.index = pd.to_datetime(df_obs.index, utc=True)
df_obs.index = df_obs.index.rename('datetime')


# ================= Load continuous forecast ================= #
ifile = os.path.join(oDir,'WL-NTR-ContinuousTimeSeries_Mandurah_2020_%s.csv' % variate)
df = pd.read_csv(ifile,skiprows=3,names=['datetime','null','fileDatetime','fileName','surge','tide'])
df = df.drop('null',axis=1)
df.index = df['datetime']
df.index = pd.to_datetime(df.index)
df = df.drop(['datetime'],axis=1)
# Reduce temporal resolution to hourly, since wave data collected hourly
# (and you're testing the skill of the storm periods)
df = df[df.index.strftime('%M') == '00']
df = df.sort_values(by='datetime')


# ================= Load Wave Data ================= #
#dfw_obs = pd.read_csv(waveData, skiprows=4)
#dfw_obs = dfw_obs.iloc[:,0:2]
# Convert datetime column to datetime objects and set as index
#dfw_obs.index = pd.to_datetime(dfw_obs['Unnamed: 0'], format="%d/%m/%Y %H:%M")
#awst = pytz.timezone("Australia/Perth")
#dfw_obs.index = dfw_obs.index.tz_localize(awst).tz_convert(pytz.utc)
#dfw_obs = dfw_obs.drop('Unnamed: 0',1)
# Rename columns
#dfw_obs.columns = ['hsig']


# ================= Merge water levels and storm event data ================= #
#df = pd.merge(df, dfw_obs, how='left',left_index=True, right_index=True)
#print(df.head())


# ================= Merge observations and forecasts ================= #
df = pd.merge(df,df_obs,how='inner',left_index=True,right_index=True)
df["twl_for"] = df["tide_m"] + df["surge"]
df['fileDatetime'] = pd.to_datetime(df['fileDatetime'],utc=True)
print(df.columns)


# ================= Plot Water level time series ================= #
# Font sizes
plt.rcParams.update({'font.size':7})
plt.rc('xtick', labelsize=7)
plt.rc('ytick', labelsize=7)
plt.rc('axes', labelsize=7,labelpad=1)
plt.rc('legend', handletextpad=1, fontsize=6)
# Fig params
fig, axes = plt.subplots(len(plotPeriods),1,figsize=(4,4),sharex=False)
fig.subplots_adjust(top=0.94,hspace=.7)
axs = np.array(axes).reshape(-1)

# Plot time series
variable = "offshore water level (m)"
counter = 0
for key in plotPeriods:
    dateTime = pytz.utc.localize(key)
    df_sub = df[df.fileDatetime==dateTime]
    df_sub = df_sub.sort_values(by='datetime')
    # Plot time series of twl and hsig (for reference)
    axwl = generateTimeseriesPlot(fig=fig,ax=axs[counter],df=df_sub)
    counter += 1

# Save fig
figName = 'TWLtimeseries_Continuous_%s.png' % (variate)
fig.savefig(os.path.join(figDir,figName),dpi=250,bbox_inches='tight')
plt.show()
print(figDir)