# Main script for retrieving and importing storm surge
import sys
import os
import glob
import wget
from importSurge import processSurge
from importSurge import fewsUtils
from datetime import datetime
import traceback
import shutil

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
    # Third argument is working directory
    workDir = str(args[2])

    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")


    #============== Write out initial commands to diag file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Current directory: %s" %currDir))
        fileObj.write(fewsUtils.write2DiagFile(3,"Import Directory: % s" % importDir))
        fileObj.write(fewsUtils.write2DiagFile(3,"Site: % s" % siteName))
        fileObj.write(fewsUtils.write2DiagFile(3,"If Python error exit code 1 is triggered, see exceptions.log file in Module directory."))
        fileObj.write("</Diag>")

    #============== Grab most recently downloaded nc file ==============#
    # Uses a function from processSurge.py
    newestNC = processSurge.getMostRecentFile(importDir=importDir)

    #============== Process nc file as time series .csv for site ==============#
    csvFile = processSurge.processSurge_nc(importDir=importDir, fname=newestNC, site=siteName)

    #============== Write more info to diagnostics file ==============#
    # Remove </Diag> line since you are appending more lines
    fewsUtils.clearDiagLastLine(diagFile)
    with open(diagFile, "a") as fileObj:
        fileObj.write(fewsUtils.write2DiagFile(3, "Target nc file: % s" % os.path.join(importDir,newestNC)))
        fileObj.write(fewsUtils.write2DiagFile(3, "Processed timeseries csv file: %s" % csvFile))
        fileObj.write("</Diag>")
        

## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise