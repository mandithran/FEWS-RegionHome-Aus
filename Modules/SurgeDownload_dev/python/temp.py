import os
import pandas as pd

#============== Load Location Set ==============#
locSetFname = "surgeLocations.csv"
locSetPath = os.path.join(".\Config\MapLayerFiles", locSetFname)
df = pd.read_csv(locSetPath)
print(df)