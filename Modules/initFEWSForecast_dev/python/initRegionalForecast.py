# Modules

import traceback
import sys
import os
import shutil
import pickle


def main(args=None):

    # For debugging:
    # python C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initRegionalForecast.py C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus 20210809_0100 Narrabeen C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\initFEWSForecast

    ############ Arguments ############ 
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # Path to Region Home, defined in global properties file
    regionHome = str(args[0])
    # System time according to FEWS
    sysTimeStr = str(args[1])
    # Site Name
    siteName = str(args[2])
    # Work dir
    workDir = str(args[3])

    print("hi")

## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise