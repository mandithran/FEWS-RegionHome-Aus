# Main script for retrieving and importing storm surge
import sys
import os
import glob
import wget
from importSurge import processSurge
from datetime import datetime
import traceback

def main(args=None):
    """The main routine."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # First argument in Module config file is the path to this python script
    # First argument read by this python script is the second argument in the config file
    # First argument: Import Directory
    importDir = str(args[0])
    # Second argument is the site name, specified as part of a Location Set
    siteName = str(args[1])

    #============== Grab most recently downloaded nc file ==============#
    # Uses a function from processSurge.py
    newestNC = processSurge.getMostRecentFile(importDir=importDir)

    #============== Process nc file as time series .csv for site ==============#
    csvFile = processSurge.processSurge_nc(importDir=importDir, fname=newestNC, site=siteName)

    #============== Generate diagnostics file ==============#
    diagFile = "diagnostics.txt"
    f = open(diagFile, "w")
    currDir = os.getcwd()
    f.write("Current Directory: % s \n" % currDir)
    f.write("Import Directory: % s \n" % importDir)
    # Print arguments from FEWS to diagnostics file
    f.write("Target nc file: % s \n" % os.path.join(importDir,newestNC))
    f.write("Processed timeseries csv file: %s \n" % csvFile)
    f.close()

## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except:
        with open("diagnostics.txt", "a") as logfile:
            traceback.print_exc(file=logfile)
        raise