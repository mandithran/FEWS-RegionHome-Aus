# ================= Modules ================= #
import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
import pytz
import numpy as np
import scipy

# ================= Paths ================= #
workDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waves"
stormPeriods = os.path.join(workDir, "ofiles\\observedStorms_Narrabeen_2020.csv")
oDir = os.path.join(workDir,"ofiles")
figDir = os.path.join(workDir,"figs")

# ================= Parameters ================= #
siteName = "Narrabeen"
timezoneUTC = pytz.utc
# Dataframe containing parameter values
dfp = pd.DataFrame(np.array([
                    # Significant wave height
                    ['hs','significant wave height','sienna',"$m$"],
                    # Wave period
                    ["tp", "wave period", "seagreen", "$s$"],
                    # Wave direction
                    ["dir","wave direction","darkslateblue","$^{\circ}$"]]
                    ),
                   # Column names
                   columns=['param_short', 'param_long',
                            'color','unit']
                  )


# ================= Local functions ================= #
def generateScatterPlot(fig=None, ax=None, obs=None, pred=None, 
                        leadtime=None, param=None,
                        siteName=None, stormObs = None, stormPred = None,
                        stormColor=None, unit=None):
    # Scatter plot of observed v predicted
    ax.scatter(obs,pred, c='lightgrey', s=8, alpha=.45)
    # Scatter plot of storms observed v predicted
    ax.scatter(stormObs,stormPred, c=sc, s=8, alpha=.3)
    # Legend
    ax.legend(['All data','Storms'],loc='upper right')
    # Plot diagonal line for reference
    xmin = min(min(obs),min(pred))
    xmax = max((max(obs),max(pred)))
    x = [xmin,xmax+(0.2*(xmax-xmin))]
    y = [xmin,xmax+(0.4*(xmax-xmin))]
    ax.plot(x,y,c='black',linewidth=.8,alpha=0.6)
    # Axes and plot titles
    ax.set_xlabel("observed (%s)" % unit)
    ax.set_ylabel("predicted (%s)" % unit)
    ax.set_title("%s-hr lead time" % (leadTime))
    # Calculate RMSE
    rmse = str(round(mean_squared_error(obs,pred, squared=False),2))
    rmse_storms = str(round(mean_squared_error(stormObs,stormPred, squared=False),2))
    # Calculate R-squared
    # Note: don't use r2_score from scikit learn; use scipy.stats.linregress
    # These two functions aren't the same
    # https://stackoverflow.com/questions/36153569/sklearn-r2-score-and-python-stats-lineregress-function-give-very-different-value
    r_value, p = scipy.stats.pearsonr(obs,pred)
    print(r_value)
    r = round(r_value,2)
    r_value, p = scipy.stats.pearsonr(stormObs,stormPred)
    r_storms = round(r_value,2)
    # Plot these values
    textx, texty = 0.07, 0.90
    shift = 0.09
    ax.text(textx, texty, "RMSE (all data) = %s %s" % (rmse, unit), transform=ax.transAxes,
            alpha=.6)
    ax.text(textx, texty-shift, "$r$ (all data)= %s" % r, transform=ax.transAxes,
            alpha=.6)
    ax.text(textx, texty-2*shift, "RMSE (storms) = %s %s" % (rmse_storms, unit), transform=ax.transAxes,
            c=sc)
    ax.text(textx, texty-3*shift, "$r$ (storms)= %s" % r_storms, transform=ax.transAxes,
            c=sc)
    return ax


# ================= Load Observed and Predicted Data ================= #
df = pd.read_csv(os.path.join(oDir, "waves-obsAndpred_Narrabeen_2020.csv"))
df.index = df['Unnamed: 0']
df = df.drop(['Unnamed: 0'],axis=1)
# Already in a format that is timezone-aware
df.index = pd.to_datetime(df.index)
# Get the unique number of lead times
leadtimes = df['leadtime_hrs'].unique()
# Reduce temporal resolution to hourly, since wave data collected hourly
# (and you're testing the skill of the storm periods)
df = df[df.index.strftime('%M') == '00']


# ================= Load Storm Event Data ================= #
dfs = pd.read_csv(stormPeriods)
dfs.index = dfs['datetime']
dfs.index = pd.to_datetime(dfs.index)


# ================= Plot Waves residuals ================= #
# Font sizes
plt.rcParams.update({'font.size':7})
plt.rc('xtick', labelsize=7)
plt.rc('ytick', labelsize=7)
plt.rc('axes', labelsize=8,labelpad=.8)
plt.rc('legend', handletextpad=0.0, fontsize=6)
# Plot by lead time
nrows = 4

# Loop through and make plots for all params
for index,row in dfp.iterrows():
    fig, axes = plt.subplots(nrows,2,figsize=(5.5,8.5))
    axs = np.array(axes).reshape(-1)
    counter = 0
    for leadTime in leadtimes:
        print("leadtime: %s" % leadTime)
        df_subset = df[df['leadtime_hrs']==leadTime]
        # Merge storm periods here, because merge may not work correctly
        # with all lead time time series present
        df_subset = pd.merge(df_subset, dfs, how='left',left_index=True, right_index=True)
        # Filter out storms to plot separately
        df_storms = df_subset[df_subset['storm']==True]
        # Scatter plot for the year, by lead time
        key = row.param_short
        varString = row.param_long
        observed = df_subset['%s_obs' % key]
        predicted = df_subset['%s_pred' % key]
        stormsObs = df_storms['%s_obs' % key]
        stormsPred = df_storms['%s_pred' % key]
        # Storm color
        sc = row.color
        # Units
        units = row.unit
        ax = generateScatterPlot(fig= fig, ax = axs[counter], obs=observed, 
                            pred=predicted, param=key,
                            leadtime=leadTime,siteName=siteName,
                            stormObs = stormsObs,stormPred=stormsPred,
                            stormColor=sc, unit=units)
        counter += 1
    fig.tight_layout()
    fig.subplots_adjust(top=0.90,hspace=.5)
    fig.suptitle("Observed vs. predicted %s - 2020" % row.param_long,
                fontsize=10,y=1)
    figName = 'ObsVPredWaves_%s_%s.png' % (siteName, key)
    # Delete unnecessary axes
    fig.delaxes(axes[3,1])
    #plt.show()
    fig.savefig(os.path.join(figDir,figName),dpi=250,bbox_inches='tight')                



# ================= Plot lead time of 3 days ================= #
# Plot by lead time
nrows = 3
fig, axes = plt.subplots(nrows,1,figsize=(3,6))
#fig.delaxes(axes[-1])
axs = np.array(axes).reshape(-1)
varlist = ['hs','tp','dir']
counter = 0
leadTime = 72
for index,row in dfp.iterrows():
    print("leadtime: %s" % leadTime)
    df_subset = df[df['leadtime_hrs']==leadTime]
    # Merge storm periods here, because merge may not work correctly
    # with all lead time time series present
    df_subset = pd.merge(df_subset, dfs, how='left',left_index=True, right_index=True)
    # Filter out storms to plot separately
    df_storms = df_subset[df_subset['storm']==True]
    # Scatter plot for the year, by lead time
    varString = "Waves"
    observed = df_subset['%s_obs' % row.param_short]
    predicted = df_subset['%s_pred' % row.param_short]
    stormObs = df_storms['%s_obs' % row.param_short]
    stormPred = df_storms['%s_pred' % row.param_short]
    # Storm color
    sc = row.color
    # Units
    units = row.unit
    ax = generateScatterPlot(fig= fig, ax = axs[counter], obs=observed, 
                        pred=predicted, param=row.param_short,
                        leadtime=leadTime,siteName=siteName,
                        stormObs = stormObs,stormPred=stormPred,
                        stormColor=sc,unit=units)
    counter += 1
    
axs[0].set_title("Significant wave height")
axs[1].set_title("Wave period")
axs[2].set_title("Wave Direction")
#fig.delaxes(axes[3])
fig.tight_layout()
fig.subplots_adjust(top=0.91,hspace=0.45)
fig.suptitle("Observed vs. predicted\n(72-hr lead time)",
             fontsize=9,y=1)
figName = 'ObsVPredWaves_%s_%s.png' % (siteName, varString)
plt.show()
fig.savefig(os.path.join(figDir,figName),dpi=250,bbox_inches='tight')