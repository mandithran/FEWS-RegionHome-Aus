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

def main(args=None):

    #args = [a for a in sys.argv[1:] if not a.startswith("-")]

    #============== Parse arguments from FEWS ==============#
    regionHome = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus"
    # TODO: CHANGE THIS BACK FROM _DEV
    workDir = os.path.join(regionHome, "Modules\PostProcessXBeach_dev")
    siteName = "Narrabeen"
    
    #============== Grid parameters ==============#
    
    #============== Paths ==============#
    xbWorkDir = os.path.join(regionHome,"Modules\\XBeach\\%s\\runs\\latest\\workDir" % siteName)
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")
    xbpkl = os.path.join(xbWorkDir,"model.pkl")

    #============== Generate diagnostics file ==============#
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)
    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write("</Diag>")

    #============== Load XBeach model object with pickle ==============#
    xbmodel = pickle.load(open(xbpkl, "rb"))


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