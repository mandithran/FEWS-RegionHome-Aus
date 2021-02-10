# Main script for retrieving and importing storm surge
import sys
import os
import wget
from importSurge import retrieveSurge
from datetime import datetime
import traceback

def main(args=None):
    """The main routine."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # First argument in Module config file is the path to this python script
    # First argument read by this python script is the second argument in the config file
    # First argument: server location
    serverLoc = str(args[0])
    # Second argument is the import destination directory (the import folder specified in the config file)
    destDir = str(args[1])
    # Third argument is the datetime
    sysTime = str(args[2])

    #============== Parse system time ==============#
    systemTime = datetime(int(sysTime[:4]),
                                   int(sysTime[4:6]),
                                   int(sysTime[6:8]),
                                   hour=int(sysTime[9:11]))

    print("Current system time: %s " % systemTime)
    roundedTime = retrieveSurge.round_hours(systemTime, 6)
    print("Rounding system time down to: % s" % roundedTime)

    #============== Parse BOM file name  ==============#
    bomDT = str(str(roundedTime.year)+
            str(roundedTime.month).zfill(2)+
            str(roundedTime.day).zfill(2)+
            str(roundedTime.hour).zfill(2))
    fname = "IDZ00154_StormSurge_national_" + bomDT + ".nc"

    #============== Fetch BOM file from server  ==============#
    url = serverLoc + fname
    print("url % s" % url)
    bomFile = wget.download(url, out=destDir)

    #============== Generate diagnostics file ==============#
    diagFile = "diagnostics.txt"
    f = open(diagFile, "w")
    currDir = os.getcwd()
    f.write("Current directory: % s \n" % currDir)
    # Print arguments from FEWS to diagnostics file
    f.write("Server location: % s \n" % serverLoc)
    f.write("Destination directory: % s \n" % destDir)
    f.write("Datetime string: % s \n" %sysTime)
    f.close()

## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except:
        with open("exceptions.log", "a") as logfile:
            traceback.print_exc(file=logfile)
        raise