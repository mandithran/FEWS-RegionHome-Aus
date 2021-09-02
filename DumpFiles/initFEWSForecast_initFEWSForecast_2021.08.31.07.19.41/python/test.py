############ Modules ############
import sys
import os
import traceback
from xbfewsTools import fewsUtils
import shutil

# Commands for debugging
# Hindcast
# python C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initializeForecast.py c:/Users/z3531278/Documents/01_FEWS-RegionHome-Aus 20200301_0000 NSW C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev
# Forecast
# python C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev\python\initializeForecast.py c:/Users/z3531278/Documents/01_FEWS-RegionHome-Aus 20210620_0100 NSW C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Modules\initFEWSForecast_dev

def main(args=None):

    ############ Paths ############ 
    workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\initFEWSForecast"
    diagBlankFile = os.path.join(workDir,"diagOpen.txt")
    diagFile = os.path.join(workDir,"diag.xml")


    ############### Generate diagnostics file ###############
    # Copy and rename diagOpen.txt
    shutil.copy(diagBlankFile,diagFile)

    with open(diagFile, "a") as fileObj:
        currDir = os.getcwd()
        fileObj.write(fewsUtils.write2DiagFile(3,
            "Command-line arguments sent to python script from FEWS: %s" 
            % (str(args)) ))
        fileObj.write(fewsUtils.write2DiagFile(3,"Forecast initiated" ))
        fileObj.write(fewsUtils.write2DiagFile(3,"If Python error exit code 1 is triggered, see exceptions.log file in Module directory."))
        fileObj.write("</Diag>")


    with open('helloworld.txt', 'w') as f:
        f.write('Hello World')


## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error")
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise


