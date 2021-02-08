import numpy as np
import pandas as pd

def retrieveSurgeFile():
    s = pd.Series([1,3,5,np.nan,6,8])
    return("Hello surge %s" % s)