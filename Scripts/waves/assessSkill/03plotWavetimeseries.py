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
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves"
waveDirectory = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves"
waveData = os.path.join(waveDirectory, "ifiles\\offshoreSydneyWaveObs.csv")
oDir = os.path.join(workDir,"ofiles")
figDir = os.path.join(workDir,"figs")

# ================= Parameters ================= #
siteName = "Narrabeen"
timezoneUTC = pytz.utc
leadTime = 72

# Dataframe containing parameter values
dfp = pd.DataFrame(np.array([
                    # Significant wave height
                    ['hs','significant wave height','sienna',"$m$",0,10],
                    # Wave period
                    ["tp", "wave period", "seagreen", "$s$",0,22],
                    # Wave direction
                    ["dir","wave direction","darkslateblue","$^{\circ}$",0,360]]
                    ),
                   # Column names
                   columns=['param_short', 'param_long',
                            'color','unit','ymin','ymax']
                  )

# Storm periods to plot
d = {
    # February 2020 storm, Feb 8 to Feb 11 GMT
    "February 2020 storm":('2020-02-08','2020-02-11'),
    # May 2020 storm
    "May 2020 storm":('2020-05-20','2020-05-26'),
    # July 2020 storm
    "July 2020 storm":('2020-07-14','2020-07-16'),
    # November 2020 storm
    "November 2020 storm":('2020-10-25','2020-10-28')
}


# ================= Local functions ================= #
def generateTimeseriesPlot(fig=None, ax=None, df=None, param=None,
                           paramdf=None):
    # Plot Hsig on a secondary axis 
    #if param != 'hs':
        #ax2 = ax.twinx()
        #ax2.plot(df.index,df.hsig,c='darkgrey',linestyle='dashed',linewidth=.8)
        #ax2.set_ylabel("$H_{sig}$ (m)")
        #ax2.set_ylim(0.,9.)
        #ax2.legend(['observed $H_{sig}$'],loc='upper right')
    #else:
        #pass
    # Plot variable of interest
    obs = "%s_obs" % param
    pred = "%s_pred" % param
    # Color of parameter
    sc = dfp[dfp.param_short == param].color.values[0]
    ax.plot(df.index,df[obs],color='dimgrey')
    ax.plot(df.index,df[pred],color=sc)
    #yrange = max(df.wl_obs) - min(df.wl_obs)
    # Get the ymin, ymax from df
    ymin = float(dfp[dfp.param_short == param].ymin.values[0])
    ymax = float(dfp[dfp.param_short == param].ymax.values[0])
    ax.set_ylim(ymin,ymax)
    label = dfp[dfp.param_short == param].param_long.values[0]
    unit = dfp[dfp.param_short == param].unit.values[0]
    ax.set_ylabel("%s (%s)" % (label, unit))
    ax.set_title("%s" % (key))
    # Legend
    ax.legend(['observed %s' % label,'predicted %s' % label],loc='upper left')
    # Format the x axis 
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b %H:%M"))
    ax.tick_params(axis='x', which='major', bottom=True, 
                   labelbottom=True, rotation=30,labelsize=6)
    return ax


# ================= Load Observed and Predicted Data ================= #
df = pd.read_csv(os.path.join(oDir, "waves-obsAndpred_Narrabeen_2020.csv"))
df.index = df['Unnamed: 0']
df = df.drop(['Unnamed: 0'],axis=1)
# Already in a format that is timezone-aware
df.index = pd.to_datetime(df.index)
# Reduce temporal resolution to hourly, since wave data collected hourly
# (and you're testing the skill of the storm periods)
df = df[df.index.strftime('%M') == '00']
print(type(df.index[0]))


# ================= Load Wave Data ================= #
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
# Set time zone (now UTC)
dfw_obs= dfw_obs.tz_localize(timezoneUTC)


# ================= Merge wave data and storm event data ================= #
df = pd.merge(df, dfw_obs, how='left',left_index=True, right_index=True)


# ================= Plot wave time series ================= #
# Font sizes
plt.rcParams.update({'font.size':7})
plt.rc('xtick', labelsize=7)
plt.rc('ytick', labelsize=7)
plt.rc('axes', labelsize=7,labelpad=1)
plt.rc('legend', handletextpad=1, fontsize=6)

# Plot time series
for index,row in dfp.iterrows():
    # Fig params
    fig, axes = plt.subplots(4,1,figsize=(5,8),sharex=False)
    fig.subplots_adjust(top=0.94,hspace=.7)
    df_subset = df[df['leadtime_hrs']==leadTime]
    axs = np.array(axes).reshape(-1)
    counter = 0
    variable = row.param_short
    print(variable)
    for key in d:
        # Subset data based on storm periods
        stormBegin = d[key][0]
        stormEnd = d[key][1]
        df_sub = df_subset[stormBegin:stormEnd]
        # Plot time series of twl and hsig (for reference)
        axwl = generateTimeseriesPlot(fig=fig,ax=axs[counter],df=df_sub,param=variable,
                                    paramdf = dfp)
        counter += 1
    # Save fig
    figName = '%s_timeseries_%shrsLeadTime.png' % (variable, leadTime)
    fig.savefig(os.path.join(figDir,figName),dpi=250,bbox_inches='tight')

plt.show()