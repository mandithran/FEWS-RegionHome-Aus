import os
from importWaves import retrieveWaves
import traceback
from datetime import datetime
import pandas as pd
import shutil
from importWaves import fewsUtils
import wget

def main(args=None):
    """The main routine."""

    #============== Parse arguments from FEWS ==============#
    # First argument: server location
    serverLoc = "http://dapds00.nci.org.au/thredds/fileServer/rr6/waves/"
    # Second argument is the datetime
    sysTime = "20210228_0000"
    # Third argument is the current working directory
    workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\WaveDownload"

    locSetFilename = "surgeLocations.csv"
    regionHomeDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
    siteName = "Narrabeen"
    
    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")

    #============== Parse system time ==============#
    # TODO make a full function for parsing system time in fews utils
    systemTime = datetime(int(sysTime[:4]),
                                   int(sysTime[4:6]),
                                   int(sysTime[6:8]),
                                   hour=int(sysTime[9:11]))

    roundedTime = retrieveWaves.round_hours(systemTime, 6)

    #============== Load Location Set ==============#
    locSetPath = os.path.join(regionHomeDir, "./Config/MapLayerFiles", locSetFilename)
    df = pd.read_csv(locSetPath)

    #============== Parse BOM file name  ==============#
    bomDate = str(str(roundedTime.year)+
            str(roundedTime.month).zfill(2)+
            str(roundedTime.day).zfill(2))
    bomTime = str(str(roundedTime.hour).zfill(2)+
            str(roundedTime.minute).zfill(2))
    bomDT = str(bomDate+"T"+bomTime+"Z")
    cityCode = df.loc[df["Name"]==siteName, "City_code"].iloc[0]
    fname = "%s.msh.%s.nc" % (cityCode,bomDT)
    print(fname)
    
    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)

    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Current directory: %s" %currDir))
        fileObj.write(fewsUtils.write2DiagFile(3,"Server location: % s \n" % serverLoc))
        fileObj.write(fewsUtils.write2DiagFile(3, "Current system time: %s \n" % systemTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Rounding system time down to: % s \n" % roundedTime))
        fileObj.write(fewsUtils.write2DiagFile(3, "Destination directory: % s \n" % workDir))
        fileObj.write(fewsUtils.write2DiagFile(3, "Downloading file: % s \n" %fname))
        fileObj.write(fewsUtils.write2DiagFile(3,"If Python error exit code 1 is triggered, see exceptions.log file in Module directory."))
        fileObj.write("</Diag>")


    #============== Full server dir  ==============#
    servDir = serverLoc + "%s/%s/" %(bomDate,bomTime)

    #============== Fetch BOM file from server  ==============#
    url = servDir + fname
    print(url)
    downloadDir = os.path.join(workDir,"ncFiles")
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)
    bomFile = wget.download(url, out=os.path.join(workDir,'ncFiles'))

## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise