# Main script for retrieving and importing storm surge
# ============= System Packages ============= #
import sys
import os
from importSurge import retrieveSurge
from importSurge import processSurge
from importSurge import fewsUtils
from datetime import datetime
import traceback
import shutil

# ============ Modules ============== #
import wget

def main(args=None):
    """The main routine."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # First argument in Module config file is the path to this python script
    # First argument read by this python script is the second argument in the config file
    # First argument: server location
    serverLoc = str(args[0])
    # Second argument is the datetime
    sysTime = str(args[1])
    # Third argument is the current working directory
    workDir = str(args[2])

    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")

    #============== Parse system time ==============#
    systemTime = datetime(int(sysTime[:4]),
                                   int(sysTime[4:6]),
                                   int(sysTime[6:8]),
                                   hour=int(sysTime[9:11]))

    roundedTime = retrieveSurge.round_hours(systemTime, 6)

    #============== Parse BOM file name  ==============#
    bomDT = str(str(roundedTime.year)+
            str(roundedTime.month).zfill(2)+
            str(roundedTime.day).zfill(2)+
            str(roundedTime.hour).zfill(2))
    fname = "IDZ00154_StormSurge_national_" + bomDT + ".nc"

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

    #============== Fetch BOM file from server  ==============#
    url = serverLoc + fname
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