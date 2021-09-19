@echo off
set PYTHON_SCRIPT=%1
set REGION_HOME=%2
set TIME_0=%3
set WORK_DIR=%4

set CONDAPATH=C:\\Users\\mandiruns\\Anaconda3
set ENVPATH=C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\bin\\windows\\python\\bin\\conda-venv

call %CONDAPATH%\Scripts\activate.bat %ENVPATH%
"python" %PYTHON_SCRIPT% %REGION_HOME% %TIME_0% %WORK_DIR%