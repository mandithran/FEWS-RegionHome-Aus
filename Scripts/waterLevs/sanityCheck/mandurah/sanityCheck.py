"""
Note from WA Transport about datum:

Mandurah datum is the Low Water 2008, which is 2.682 m below benchmark, “Man Tidal 02” and 0.54 m below AHD (2009).  
If you want to convert the water levels to AHD, you need to subtract 0.54 m from the water levels.
"""


#================ Modules ================#
import pandas as pd
import pytz
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import os

#================ Paths ================#
obsFile = 'MAN2020.txt'
predFile = 'Mandurah_CapeBouvard_2019-2021_15min_tidepredictions.csv'


#================ Load Observations ================#
dfObs = pd.read_csv(obsFile)
# Drop metadata rows (for some reason, skiprows in read_csv doesn't work)
dfObs = dfObs.drop(dfObs.index[0:16])
# Rename columns
dfObs.columns = ['h_cm','datetime']
# Convert cm to m
dfObs['h_cm'] = pd.to_numeric(dfObs["h_cm"], downcast="float")
dfObs['h_meters'] = dfObs['h_cm']/100.
# Datum correction (see note above)
dfObs['h_meters'] = dfObs['h_meters'] - 0.54
dfObs = dfObs.drop('h_cm',1)
# Convert datetime column to datetime objects and set as index
dfObs.index = pd.to_datetime(dfObs['datetime'], format="%Y%m%d.%H%M/")
# Convert AWST to UTC
awst = pytz.timezone("Australia/Perth")
dfObs.index = dfObs.index.tz_localize(awst).tz_convert(pytz.utc)
dfObs = dfObs.drop('datetime',1)
print(dfObs.head())


#================ Load Predictions ================#
dfPred = pd.read_csv(predFile)
# Convert datetime column to datetime objects and set as index
dfPred.index = pd.to_datetime(dfPred['dates (UTC)'], utc=True)
dfPred = dfPred.drop('dates (UTC)',1)
print(dfPred.head())



#================ Designate a few time periods to plot ================#
d = {
    "Sample Period 1":('2020-01-02','2020-01-14'),
    "Sample Period 2":('2020-03-01','2020-03-14'),
    "Sample Period 3":('2020-06-01','2020-06-14'),
    "Sample Period 4":('2020-09-01','2020-09-14')
}


# ================= Plotting function ================= #
def generateTimeseriesPlot(fig=None, ax=None, df1=None, df2=None):
    # Plot total water levels
    ax.plot(df1.index,df1.iloc[:,0],color='dimgrey')
    ax.plot(df2.index,df2.iloc[:,0],color='royalblue')
    #ax.set_ylim(-1,2)
    #ax.set_ylabel(variable)
    #ax.set_title("%s" % (key))
    # Legend
    ax.legend(['observed total water level','predicted total water level'],loc='upper left')
    # Format the x axis 
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b %H:%M"))
    ax.tick_params(axis='x', which='major', bottom=True, 
                   labelbottom=True, rotation=30,labelsize=6)
    return ax


# ================= Make figure ================= #
# Font sizes
plt.rcParams.update({'font.size':7})
plt.rc('xtick', labelsize=7)
plt.rc('ytick', labelsize=7)
plt.rc('axes', labelsize=7,labelpad=1)
plt.rc('legend', handletextpad=1, fontsize=6)
# Fig params
fig, axes = plt.subplots(4,1,figsize=(5,8),sharex=False)
fig.subplots_adjust(top=0.94,hspace=.7)
axs = np.array(axes).reshape(-1)

# Plot time series
variable = "water level (m)"
counter = 0
for key in d:
    # Subset data based on storm periods
    beginDate = d[key][0]
    endDate = d[key][1]
    dfObs_sub = dfObs[beginDate:endDate]
    dfPred_sub = dfPred[beginDate:endDate]
    # Plot time series of twl and hsig (for reference)
    axwl = generateTimeseriesPlot(fig=fig,ax=axs[counter],df1=dfObs_sub, df2=dfPred_sub)
    counter += 1
# Save fig
figName = 'waterLevels_SanityCheck.png'
fig.savefig(figName,dpi=250,bbox_inches='tight')