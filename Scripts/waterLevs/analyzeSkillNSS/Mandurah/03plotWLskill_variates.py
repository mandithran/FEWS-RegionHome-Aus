# ================= Modules ================= #
import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
import pytz
import numpy as np
import scipy
from datetime import datetime

# ================= Paths ================= #
siteName = 'Mandurah'
workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs\\analyzeSkillNSS\\%s" % siteName
waveDirectory = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves"
stormPeriods = os.path.join(waveDirectory, "assessSkill\\%s\\ofiles\\" % siteName,
                            "observedStorms_%s_2020.csv" % siteName)
oDir = os.path.join(workDir,"ofiles")
figDir = os.path.join(workDir,"figs")
# Start and end times
startTime = datetime(2020,1,1,tzinfo=pytz.utc)
endTime = datetime(2020,12,31,tzinfo=pytz.utc)
#  Set to true to include surge in forecasted TWL. 
# Set to false to test water level skill when just including astronomical tide predictions and not surge predicitons
nts = True
variate = "set0"
titleString = ""


# ================= Parameters ================= #
timezoneUTC = pytz.utc


# ================= Local functions ================= #
def generateScatterPlot(fig=None, ax=None, obs=None, pred=None, 
                        leadtime=None,
                        siteName=None, stormObs = None, stormPred = None):
    # Storm color
    sc = "darkblue"
    # Scatter plot of observed v predicted
    ax.scatter(obs,pred, c='lightgrey', s=8, alpha=.6)
    # Scatter plot of storms observed v predicted
    ax.scatter(stormObs,stormPred, c=sc, s=8, alpha=.3)
    # Legend
    ax.legend(['All data','Storms'],loc='upper right')
    # Plot diagonal line for reference
    xmin = min(min(obs),min(pred))
    xmax = max((max(obs),max(pred)))
    x = [xmin,xmax+(0.2*(xmax-xmin))]
    y = [xmin,xmax+(0.2*(xmax-xmin))]
    ax.plot(x,y,c='black',linewidth=.8,alpha=0.6)
    # Axes and plot titles
    ax.set_xlabel("observed ($m$)")
    ax.set_ylabel("predicted ($m$)")
    ax.set_title("%s-hr lead time" % (leadTime))
    # Calculate RMSE
    rmse = str(round(mean_squared_error(obs,pred, squared=False),2))
    rmse_storms = str(round(mean_squared_error(stormObs,stormPred, squared=False),2))
    # Calculate R-squared
    # Note: don't use r2_score from scikit learn; use scipy.stats.linregress
    # These two functions aren't the same
    # https://stackoverflow.com/questions/36153569/sklearn-r2-score-and-python-stats-lineregress-function-give-very-different-value
    r_value, p = scipy.stats.pearsonr(obs,pred)
    r = round(r_value,2)
    r_value, p = scipy.stats.pearsonr(stormObs,stormPred)
    r_storms = round(r_value,2)
    # Plot these values
    textx, texty = 0.05, 0.88
    shift = 0.09
    ax.text(textx, texty, "RMSE (all data) = %s m" % rmse, transform=ax.transAxes,
            alpha=.6)
    ax.text(textx, texty-shift, "$r$ (all data)= %s" % r, transform=ax.transAxes,
            alpha=.6)
    ax.text(textx, texty-2*shift, "RMSE (storms) = %s m" % rmse_storms, transform=ax.transAxes,
            c=sc)
    ax.text(textx, texty-3*shift, "$r$ (storms)= %s" % r_storms, transform=ax.transAxes,
            c=sc)
    print("returning plot for %s lead time" % leadtime)
    return ax, rmse, rmse_storms, r, r_storms


# ================= Load Observed and Predicted Data ================= #
df = pd.read_csv(os.path.join(oDir, "WL-NTR-LeadTimeSeries_%s_2020_%s.csv" % (siteName,variate)))
df.rename(columns={'Unnamed: 0':'datetime'}, inplace=True)
df.index = df['datetime']
df = df.drop(['datetime'],axis=1)
# Already in a format that is timezone-aware
df.index = pd.to_datetime(df.index, utc=True)
# Get the unique number of lead times
leadtimes = df['leadtime_hrs'].unique()
# Reduce temporal resolution to hourly, since wave data collected hourly
# (and you're testing the skill of the storm periods)
df = df[df.index.strftime('%M') == '00']


df = df[df.index>=startTime] 
df = df[df.index<endTime]


# ================= Load Storm Event Data ================= #
dfs = pd.read_csv(stormPeriods)
dfs.columns = ['datetime','hsig','storm']
dfs.index=dfs['datetime']
dfs.index = pd.to_datetime(dfs.index)


# ================= Plot Non-tidal residuals ================= #
# Font sizes
plt.rcParams.update({'font.size':7})
plt.rc('xtick', labelsize=7)
plt.rc('ytick', labelsize=7)
plt.rc('axes', labelsize=8,labelpad=1)
plt.rc('legend', handletextpad=0.0, fontsize=6)
# Plot by lead time
nrows = 5
fig, axes = plt.subplots(nrows,2,figsize=(6,8.5))
#fig.delaxes(axes[-1])
axs = np.array(axes).reshape(-1)
counter = 0
r_list = []
rstorm_list = []
rmse_list = []
rmsestorm_list = []
for leadTime in leadtimes: 
    print(leadTime)
    df_subset = df[df['leadtime_hrs']==leadTime]
    # Merge storm periods here, because merge may not work correctly
    # with all lead time time series present
    df_subset = pd.merge(df_subset, dfs, how='left',left_index=True, right_index=True)
    # Filter out storms to plot separately
    df_storms = df_subset[df_subset['storm']==True]
    # Scatter plot for the year, by lead time
    varString = "non-tidal residuals"
    ax, rmse, rmsestorm, r, r_storms = generateScatterPlot(fig= fig, ax = axs[counter], obs=df_subset.nts, 
                        pred=df_subset.surge,
                        leadtime=leadTime,siteName=siteName,
                        stormObs = df_storms.nts,stormPred=df_storms.surge)

    counter += 1
fig.tight_layout()
fig.subplots_adjust(top=0.94,hspace=.5)
fig.suptitle("Observed vs. predicted non-tidal residuals (storm surge) - 2020\n" + 
            "%s" % titleString,
             fontsize=10,y=1)
figName = 'ObsVPred_%s_%s_%s.png' % (siteName, varString,variate)
#fig.delaxes(axes[2,1])
fig.savefig(os.path.join(figDir,figName),dpi=250,bbox_inches='tight')
plt.show()


# ================= Plot total water levels ================= #
# Plot by lead time
nrows = 5
fig, axes = plt.subplots(nrows,2,figsize=(6,8.5))
#fig.delaxes(axes[-1])
axs = np.array(axes).reshape(-1)
counter = 0
for leadTime in leadtimes:
    df_subset = df[df['leadtime_hrs']==leadTime]
    # Merge storm periods here, because merge may not work correctly
    # with all lead time time series present
    df_subset = pd.merge(df_subset, dfs, how='left',left_index=True, right_index=True)
    df_subset['twl_for'] = df_subset["tide_m"] + df_subset['surge']
    # Filter out storms to plot separately
    df_storms = df_subset[df_subset['storm']==True]
    # Scatter plot for the year, by lead time
    varString = "TWL"
    ax, rmse, rmsestorm, r, r_storms = generateScatterPlot(fig= fig, ax = axs[counter], obs=df_subset.wl_obs, 
                        pred=df_subset.twl_for,
                        leadtime=leadTime,siteName=siteName,
                        stormObs = df_storms.wl_obs,stormPred=df_storms.twl_for)
    r_list.append(r)
    rstorm_list.append(r_storms)
    rmse_list.append(rmse)
    rmsestorm_list.append(rmsestorm)
    counter += 1
fig.tight_layout()
fig.subplots_adjust(top=0.94,hspace=.5)
fig.suptitle("Observed vs. predicted offshore water levels - 2020 \n" +
             "%s" % titleString,
             fontsize=10,y=1)
if nts == False:
        figName = 'ObsVPred_%s_%s_%s.png' % (siteName, varString, variate)
else:
        figName = 'ObsVPred_%s_%s_%s.png' % (siteName, varString, variate)

#fig.delaxes(axes[2,1])
fig.savefig(os.path.join(figDir,figName),dpi=250,bbox_inches='tight')



# ================= Plot lead time of 3 days ================= #
# Plot by lead time
nrows = 2
fig, axes = plt.subplots(nrows,1,figsize=(3,4))
#fig.delaxes(axes[-1])
axs = np.array(axes).reshape(-1)
df['twl_for'] = df['tide_m'] + df['surge']
varlist = [['nts','surge'],['wl_obs','twl_for']]
counter = 0
leadTime = 72
for v in varlist:
    print("leadtime: %s" % leadTime)
    df_subset = df[df['leadtime_hrs']==leadTime]
    # Merge storm periods here, because merge may not work correctly
    # with all lead time time series present
    df_subset = pd.merge(df_subset, dfs, how='left',left_index=True, right_index=True)
    # Filter out storms to plot separately
    df_storms = df_subset[df_subset['storm']==True]
    # Scatter plot for the year, by lead time
    varString = "TWLandNTS"
    ax = generateScatterPlot(fig= fig, ax = axs[counter], obs=df_subset[v[0]], 
                        pred=df_subset[v[1]],
                        leadtime=leadTime,siteName=siteName,
                        stormObs = df_storms[v[0]],stormPred=df_storms[v[1]])
    counter += 1
axs[0].set_title("Non-tidal residuals (surge)")
axs[1].set_title("Total water level (tides + surge)")
fig.tight_layout()
fig.subplots_adjust(top=0.86,hspace=.45)
fig.suptitle("Observed vs. predicted\n(72-hr lead time)",
             fontsize=9,y=1)
if nts == False:
        figName = 'ObsVPred_%s_%s_%s.png' % (siteName, varString, variate)
        fig.delaxes(axes[0])
else:
        figName = 'ObsVPred_%s_%s_%s.png' % (siteName, varString, variate)
fig.savefig(os.path.join(figDir,figName),dpi=250,bbox_inches='tight')
plt.show()

"""# Plot line plot of lead time vs skill
import seaborn as sns
fig, axes = plt.subplots(2,1,figsize=(6,6))
sns.lineplot(x=leadtimes,y=r_list, ax=axes[0])
sns.lineplot(x=leadtimes,y=rstorm_list, ax=axes[0])
sns.lineplot(x=leadtimes,y=rmse_list, ax=axes[1])
sns.lineplot(x=leadtimes,y=rmsestorm_list, ax=axes[1])
print(r_list,rmse_list)
plt.show()"""