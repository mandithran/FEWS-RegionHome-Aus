import xarray as xr
import pandas as pd
import geopandas as gpd
import numpy as np

trange = pd.date_range("2020-09-01", "2020-09-07", freq="60min")
print(len(trange))
# Quiet first
arr1 = np.repeat([1.],24)
# Then long storm
arr2 = np.repeat([4.],8)
# Followed by a short quiet period
arr3 = np.repeat([1.],12)
# Followed by another long storm
arr4 = np.repeat([4.],24)
# Followed by a short quiet period
arr5 = np.repeat([1.],24)
# Followed by a long storm
arr6 = np.repeat([4.],24)
# Followed by a short quiet period
arr7 = np.repeat([1.],24)
# TODO
# add another blip of a storm at the end


arr = np.concatenate([arr1,arr2,arr3,arr4,arr5,arr6,arr7])

# Long quiet period
arr_end = np.repeat([1.],(len(trange)-len(arr)))
arr = np.concatenate([arr,arr_end])

df = pd.DataFrame({"datetime":trange,
                    "hsig":arr})



df['storm'] = np.where(df['hsig']>=3., True, False)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df)
# Determine storm blips, remove all of them including the last one
group_stormBlips = df[df['storm'] == True].groupby((df['storm'] != True).cumsum())
indeces2Remove = []
# Get a list of the different groups by their number
# This number doesn't have anything to do with the index
for k, v in group_stormBlips:
    if len(v) < 12:
        indeces2Remove = np.concatenate([indeces2Remove,v.index.values])
print(indeces2Remove)
# Drop these indeces from the waves timeseries
df = df.drop(index=indeces2Remove).reset_index()
# Determine quiet blips, remove all of them including the last one
group_quietBlips = df[df['storm'] == False].groupby((df['storm'] != False).cumsum())
indeces2Remove = []
# Get a list of the different groups by their number
# This number doesn't have anything to do with the index
for k, v in group_quietBlips:
    if len(v) < 48:
        indeces2Remove = np.concatenate([indeces2Remove,v.index.values])
print(indeces2Remove)
# Drop these indeces from the waves timeseries
df = df.drop(index=indeces2Remove).reset_index()
# Now determine the actual storm periods
group_storms = df[df['storm'] == True].groupby((df['storm'] != True).cumsum())
storms_df = pd.DataFrame(columns=["storm_start","storm_end"])
for k, v in group_storms:
    print(k)
    stormStart = v.datetime.values[0]
    stormEnd = v.datetime.values[-1]
    storms_df = storms_df.append({"storm_start":stormStart,
                      "storm_end":stormEnd},ignore_index=True)
print(storms_df)

# Remove also a storm period at the end if it's a storm - assume it's a full storm
# This is the most conservative option 7 days out

#group_quietBlips = df[df['storm'] == False].groupby((df['storm'] != False).filter(lambda x: len(x) > 12).cumsum())


#group_quietBlips = group_quietBlips.filter(lambda x: len(x) > 12)
"""indeces2Remove = []

for k, v in group_quietBlips:
    if len(v) <= 12:
        print("Less than 12")
        indeces2Remove = np.concatenate([indeces2Remove,v.index.values])
    print(f'[group {k}]')
    print(v)
    print('\n')
    
print(indeces2Remove)"""

#print(df)


"""df = pd.DataFrame({
  'item':['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M'], 
  'value':[12, 3, 5, 0, 2, 0, 23, 4, 2, 0, 13, 12, 13]
})

df['storm'] = np.where(df['value']>=1, True, False)
print(df)

group = df[df['storm'] == True].groupby((df['storm'] != True).cumsum())
for k, v in group:
    print(f'[group {k}]')
    print(v)
    print(len(v))
    print('\n')"""

#print(df[group])

# TODO: convert pandas group to a dataframe
# Compute the length of each one
# Filter by length
# Assign the "start" and "end" time attributes