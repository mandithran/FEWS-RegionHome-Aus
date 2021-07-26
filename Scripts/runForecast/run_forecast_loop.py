#============================================================================#

#============================================================================#


# Modules
import os
import datetime

# Paths
workDir = "C:\\Users\\z3531278\Documents\\01_FEWS-RegionHome-Aus\\Scripts\\runForecast"

# Variables

# Log file
logf = open(os.path.join(workDir,"exceptionsWaves.log"), "w")

# Main Coastal Forecast loop
try:
    print("Hello Loop!")

except Exception as e:     # most generic exception you can catch
    logf.write("Failed. {0}\n".format(str(e)))
    logf.write('Recorded at %s.\n' % 
                (datetime.datetime.now()))