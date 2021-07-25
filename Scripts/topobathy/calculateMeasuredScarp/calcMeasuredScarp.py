# Modules
import os
import pandas as pd

# Path
regionHome = 'C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus'
workDir = os.path.join(regionHome,'Scripts\\topobathy\\calculateMeasuredScarp')
dataDir = os.path.join(regionHome,'Data\\TopoBathy\\Narrabeen\\stormSurveys\\xyz')
storm = '2020_02_09'
prestorm = os.path.join(dataDir,'%s' % storm, '%s-pre-storm.csv' % storm)
poststorm = os.path.join(dataDir,'%s' % storm, '%s-post-storm.csv' % storm)

# Load files
prestorm_df = pd.read_csv(prestorm)
prestorm_df = prestorm_df.drop('Unnamed: 0',axis=1)
poststorm_df = pd.read_csv(poststorm)

# Check to see that points are the same by performing a merge
