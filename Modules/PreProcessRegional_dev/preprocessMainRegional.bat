@echo off
set PYTHON_SCRIPT=%1
set REGION_HOME=%2
set TIME_0=%3
set REGION_NAME=%4
set WORK_DIR=%5

set CONDAPATH=C:\\Users\\z3531278\\Anaconda3
set ENVPATH=C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\bin\\windows\\python\\bin\\conda-venv

call %CONDAPATH%\Scripts\activate.bat %ENVPATH%
"python" %PYTHON_SCRIPT% %REGION_HOME% %TIME_0% %REGION_NAME% %WORK_DIR%