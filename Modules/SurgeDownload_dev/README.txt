#================ RUNNING THE MODULE ================#

This is an external FEWS module that fetches storm surge grids from the BOM server. It can be run directly from FEWS in manual forecast mode.

If you try to run the module and it throws an error about the file not being found, your system time in FEWS is probably too recent. There is a lag between the time indicated for the forecasts and the time the file is uploaded to the server.

To fix this, set back the sytem time to 6 hours earlier from "Now" in FEWS.

All python errors from this module will be sent to .\SurgeDownload\diagnostics.txt


#================ DEBUGGING AND EDITING THE MODULE ================#

Debugging and editing this module requires setting up an Anaconda virtual environment.

Directions to install Anaconda can be found here: https://docs.anaconda.com/anaconda/install/

Once Anaconda is installed:

1. Open terminal or command line and navigate to the following directory within your "Region Home" (where the FEWS program is located): $REGION_HOME$/Modules/SurgeDownload/python

2. Create the virtual environment by entering the following line into a terminal or command prompt: 

conda env create -f environment.yml --prefix bin\venv

This will create a conda virtual environment called "fews" in the bin/venv directory. This environment will have all the required dependencies needed to run the python scripts provided.

3. Activate the virtual environment by typing the following line into a terminal or command prompt:

conda activate .\bin\venv

4. Edit and debug the python script as needed. Instructions for installing additonal python packages can be found here: https://docs.anaconda.com/anaconda/user-guide/tasks/install-packages/

5. When you've made the necessary modifications, zip up the Module directory and place it in the ModuleDataSetFiles directory. 