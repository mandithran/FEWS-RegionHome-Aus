############ Modules ############
import os
import traceback


def main(args=None):
        import sys
        import shutil
        import pickle
        from xbfewsTools import fewsForecast
        """from xbfewsTools import fewsUtils"""

        workDir = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\initFEWSForecast"

        with open(os.path.join(workDir,'test.txt'), 'w') as f:
                f.write('here')

## If Python throws an error, send to exceptions.log file
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("exceptions.log", "w") as logfile:
            logfile.write(str(e))
            logfile.write(traceback.format_exc())
        raise