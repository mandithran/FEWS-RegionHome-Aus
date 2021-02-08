#================ RUNNING THE MODULE ================#



#================ DEBUGGING AND EDITING THE MODULE ================#

Debugging and editing this module requires installing an Anaconda virtual environment.

Directions to install Anaconda can be found here: https://docs.anaconda.com/anaconda/install/

Once Anaconda is installed:

1. Open terminal or command line and navigate to the following directory within your "Region Home" (where the FEWS program is located): $REGION_HOME$/Modules/SurgeDownload/python

2. Create the virtual environment by entering the following line into a terminal or command prompt: 

conda env create -f environment.yml --prefix bin\venv

This will create a conda virtual environment called "fews" in the bin/venv directory. This environment will have all the required dependencies needed to run the python scripts provided.

3. Activate the virtual environment by typing the following line into a terminal or command prompt:

conda activate fews

4. Edit and debug the python script as needed. Instructions for installing additonal python packages can be found here: https://docs.anaconda.com/anaconda/user-guide/tasks/install-packages/

*****SAVE ENVIRONMENT STATE AND REGENERATE EXE FILE******