# Modules
import os
import sys
import traceback
import shutil
import pickle
"""
import pandas as pd
from xbfewsTools import fewsUtils
from xbfewsTools import xBeachModel
from xbfewsTools import preProcWatLevs
from xbfewsTools import preProcWaves
from datetime import datetime, timedelta
import fileinput"""

# For debugging:
# Forecast:
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PostProcessXBeach_dev/postprocess-main.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PostProcessXBeach_dev 20210707_0000 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus Narrabeen
# Hindcast
# C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PostProcessXBeach_dev/postprocess-main.py C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\PostProcessXBeach_dev 20200707_0000 C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus Narrabeen

def main(args=None):

    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    # Path to Region Home, defined in global properties file
    workDir = str(args[0])
    # System time according to FEWS
    sysTimeStr = str(args[1])
    # Region home
    regionHome = str(args[2])
    # Site Name
    siteName = str(args[3])

    #============== Determine appropriate forecast directory ==============#
    # This is based on system time given from FEWS
    # C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\XBeach\Narrabeen\2020070700SystemTime-Narrabeen
    modelRunDir = os.path.join(regionHome,"Modules\\XBeach",siteName,
                               "%sSystemTime-%s" %(sysTimeStr,siteName))
    
    #============== Grid parameters ==============#
    
    #============== Paths ==============#
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    hotspotFcst = os.path.join(modelRunDir,"forecast_hotspot.pkl")

    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write("</Diag>")

    #============== Load hotspot forecast object with pickle ==============#
    hotspotFcst = pickle.load(open(hotspotFcst, "rb"))
    print(hotspotFcst.roundedTime)
    

    # TODO: run these two to completion, reset FEWS system time so you have a model to work with



    ################################# Process extreme water line #################################


    ################################# Process erosion scarp #################################


    ################################# TODO: "remember" scarp/water line #################################

    
## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise