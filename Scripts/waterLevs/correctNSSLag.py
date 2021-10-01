#==========================================================================================
# correctNSSLag.py
# Author: Mandi Thran
# Date: 01/10/21

# DESCRIPTION:
# For some of the 2020 National Storm Surge System forecasts, there was a lag in the storm 
# surge signal. This script re-processes the raw netCDF files and corrects the lag. It puts 
# the corrected storm surge files into a new folder called “corrected”. Note: this has 
# already been done for the problematic period in the 2020 forecasts.
#==========================================================================================


#====================== Modules ======================#
import os
import xarray as xr
import re
from datetime import datetime, timedelta
import pytz
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


#====================== Paths ======================#
drive = "\\\\ad.unsw.edu.au\\OneUNSW\\ENG\\WRL\\WRL1"
nssDir = os.path.join(drive,"Coastal\\Data\\Tide\\WL_Forecast\\BOM_Storm_Surge\\raw")
workDir = "C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\waterLevs"
outDir = os.path.join(drive,"Coastal\\Data\\Tide\\WL_Forecast\\BOM_Storm_Surge\\raw\\corrected")

from numpy import savetxt


#====================== Local functions ======================#
def parseTimeNSS(string=None):
    dateTimeStr = re.split("_", string)[3].split(".")[0]
    dateTime = datetime.strptime(dateTimeStr, '%Y%m%d%H')
    dateTime = pytz.utc.localize(dateTime)
    return dateTime

# Copy parsing netcdf files from 01assessNSSSkill.py
fixPeriodStart = datetime(2019,10,1,0)
fixPeriodStart = pytz.utc.localize(fixPeriodStart)
#fixPeriodEnd = datetime(2020,12,8,6)
# Bug was fixed around July 14 2020
fixPeriodEnd = datetime(2020,7,14)
fixPeriodEnd = pytz.utc.localize(fixPeriodEnd)
# This buffer period is there because you have to include files that go beyond the fix point
# ...in order to be able to shift the forecasts back to the correct position
fixPeriodBuffer = fixPeriodEnd + timedelta(hours=96)

####################### NSS #######################
# Note there was a bug in the NSS from at least before July 10, 2020
# This caused a time lag of the surge signal by 48 hrs
# Load list of files - NSS Forecast
filesList = []
missingTimeSteps = []
# We only want the netcdf files
for fi in os.listdir(nssDir):
    if fi.endswith(".nc"):
        filesList.append(fi)
# Add these to a dataframe
df_files = pd.DataFrame(filesList,columns=['fileName'])
# Parse the forecast start time from filename, and add as a new column
df_files['fileDateTime'] = [parseTimeNSS(str(row)) for row in df_files['fileName']]
# Make datetime the new index for this df
df_files = df_files.set_index(["fileDateTime"])
df_files = df_files.sort_index()
# Keep only files for certain time period (From before July 13 2020, when bug fix was implemented, includes the buffer)
df_files = df_files[df_files.index>=fixPeriodStart]
df_files = df_files[df_files.index<fixPeriodBuffer]



# Loop through NSS Files
for indexDT in df_files.index:
    if indexDT <= fixPeriodEnd:
        print(indexDT)
        try:
            ifile1name = df_files.fileName[indexDT]
            f2Ind = indexDT + timedelta(hours=72)
            ifile2name = df_files.fileName[f2Ind]

            # Import first file
            ifile1 = os.path.join(nssDir, ifile1name)
            ifile2 = os.path.join(nssDir, ifile2name)
            # Load forecast file
            ds = xr.open_dataset(ifile1)
            # Parse time from file
            dateTime = parseTimeNSS(string=ifile1name)
            dt64 = np.datetime64(dateTime)


            # Drag the surge signal back 48 hours (i.e. shift it 48 hours earlier)
            ds_surge = ds[['surge']]
            #print(ds_surge.time.values)
            ds_surge['time'] = ds_surge['time'] - np.timedelta64(48, 'h')


            # Chop off the extra time at the beginning of surge signal now
            ds_surge = ds_surge.where(ds_surge.time >= dt64, drop=True).squeeze()
            joinTime = ds_surge.time[-1].values
            # Import the next file, which is 48 hrs ahead of the joinTime for the first file
            # since you're dragging back the forecast to this time
            ds2 = xr.open_dataset(ifile2)
            
            # Shift this time series back 48 hours (this new start time and the new end time for file 1 should now match up)
            ds_surge2 = ds2[['surge']]
            ds_surge2['time'] = ds_surge2['time'] - np.timedelta64(48, 'h')

            # Remove the first time entry for this dataset
            ds_surge2 = ds_surge2.where(ds_surge2.time > joinTime, drop=True).squeeze()

            # Since it is a 3-day forecast, concatenate 2 days of the new shifted forecast from file 2
            ds_surge2 = ds_surge2.where(ds_surge2.time <= (joinTime+np.timedelta64(48,'h')), drop=True).squeeze()


            # Point dimension in netCDF file isn't "labeled" (i.e. points don't "know" what their lon/lat is)
            # This code block below identifies the indeces where the two datasets don't overlap
            # We want to keep only the points that are contained within each df
            # But to do that we need to extract and compare their lon/lat info
            # Convert the lat, lon, and NSS point index values to dfs
            def mergeDatasets(ds1,ds2):
                df1 = pd.DataFrame({'lat':ds1.lat.values,'lon':ds1.lon.values})
                df1['NSSindex'] = ds1.point.values
                df2 = pd.DataFrame({'lat':ds2.lat.values,'lon':ds2.lon.values})
                df2['NSSindex'] = ds2.point.values
                # Determine the NSS indeces of the points in the FIRST dataframe that are NOT in the second one
                dfmerged1 = pd.merge(df1, df2,  how='left', left_on=['lat','lon'], right_on = ['lat','lon'])
                ind1 = dfmerged1[dfmerged1['NSSindex_y'].isnull()].index.tolist()
                dropInd1 = dfmerged1['NSSindex_x'][ind1].values
                # Now drop these from the original df
                ds1 = ds1.drop_sel(point=dropInd1)
                # Repeat this process for the second df
                # Determine the NSS indeces of the points in the SECIBD dataframe that are NOT in the first one
                dfmerged2 = pd.merge(df2, df1, how='left', left_on=['lat','lon'], right_on = ['lat','lon'])
                ind2 = dfmerged2[dfmerged2['NSSindex_y'].isnull()].index.tolist()
                dropInd2 = dfmerged2['NSSindex_x'][ind2].values
                # Now drop these points
                ds2 = ds2.drop_sel(point=dropInd2)
                dsMerged = ds1.merge(ds2,join='outer')

                return dsMerged

            # Merge these dfs 
            ds_surgeCorrected = mergeDatasets(ds_surge,ds_surge2)

            # In original file, change name of "surge" to "surge_uncorrected"
            ds = ds.rename({"surge":"surge_uncorrected"})

            # Merge the dataframes
            ds = mergeDatasets(ds,ds_surgeCorrected)
            
            # Export file with corrected surge
            ds.to_netcdf(os.path.join(outDir,ifile1name))

        except:
            missingTimeSteps.append(indexDT)

savetxt(os.path.join(workDir,'missingTimeSteps.csv'), missingTimeSteps, delimiter=',')
# Plot observed v predicted v corrected predicted for Mandurah to check if it worked
# Grab from 05plotSurgeNTStimeseries
d = {
    # May 2020 storm, May 23 to 29 GMT
    "May 2020 storm 1":('2020-05-2','2020-05-16')
}


# # ================= Local functions ================= #
# def generateTimeseriesPlot(fig=None, ax=None, df=None, correctedx=None,correctedy=None):
#     # Plot total water levels
#     ax.plot(df.index,df.nts,color='dimgrey')
#     ax.plot(df.index,df.surge,color='royalblue')
#     ax.plot(correctedx,correctedy,color='purple')
#     print(df.wl_obs)
#     ax.set_ylim(-1,2)
#     ax.set_ylabel(variable)
#     ax.set_title("%s" % (key))
#     # Legend
#     ax.legend(['observed non-tidal residual','predicted non-tidal residual'],loc='upper left')
#     # Format the x axis 
#     ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b %H:%M"))
#     ax.tick_params(axis='x', which='major', bottom=True, 
#                    labelbottom=True, rotation=30,labelsize=6)
#     return ax


# # ================= Load Observed and Predicted Data ================= #
# siteName = "Mandurah"
# df = pd.read_csv(os.path.join(workDir, "WL-NTR-obsAndpred_%s_2020.csv" % siteName))
# df.index = df['Unnamed: 0']
# df = df.drop(['Unnamed: 0'],axis=1)
# # Already in a format that is timezone-aware
# df.index = pd.to_datetime(df.index)
# # Reduce temporal resolution to hourly, since wave data collected hourly
# # (and you're testing the skill of the storm periods)
# df = df[df.index.strftime('%M') == '00']


# # ================= Plot non-tidal residuals and surge time series ================= #
# # Font sizes
# leadTime = 72
# plt.rcParams.update({'font.size':7})
# plt.rc('xtick', labelsize=7)
# plt.rc('ytick', labelsize=7)
# plt.rc('axes', labelsize=7,labelpad=1)
# plt.rc('legend', handletextpad=1, fontsize=6)
# # Fig params
# fig, axes = plt.subplots(4,1,figsize=(5,8),sharex=False)
# fig.subplots_adjust(top=0.94,hspace=.7)
# df_subset = df[df['leadtime_hrs']==leadTime]
# axs = np.array(axes).reshape(-1)


# # Isolate corrected timeseries at Mandurah
# lat = -32.508727999999998
# lon = 115.704099999999997
# dsTest = ds.where((ds.lat==lat) & (ds.lon==lon), drop=True).squeeze()
# print(list(dsTest.keys()))

# # Plot time series
# variable = "surge (m)"
# counter = 0
# for key in d:
#     # Subset data based on storm periods
#     stormBegin = d[key][0]
#     stormEnd = d[key][1]
#     df_sub = df_subset[stormBegin:stormEnd]
#     print(df_sub.columns)
#     # Plot time series of twl and hsig (for reference)
#     axwl = generateTimeseriesPlot(fig=fig,ax=axs[counter],df=df_sub,
#                                   correctedx=dsTest.time.values,
#                                   correctedy=dsTest.surge.values)
#     counter += 1
# # Save fig
# figName = 'SurgeCorrectionTest_%shrsLeadTime.png' % leadTime
# fig.savefig(os.path.join(workDir,figName),dpi=250,bbox_inches='tight')
# plt.show()