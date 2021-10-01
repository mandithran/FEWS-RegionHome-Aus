rem #=========================== Region Home ===========================#
rem Location of the Region Home directory
set regionHome=C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\

rem #=======================+==== Log file ===================++========#
rem Location and name of the log file for the group of forecasts/hindcasts
set logFile=%regionHome%\\forecastLog_MCCALLUM1.txt

rem #================= BOM Storm Surge Forecasts Location ==============#
rem Location if grabbing files from WRL1, keep the forward slashes or else it doesn't work
rem set surgeForecastLoc = "//ad.unsw.edu.au/OneUNSW/ENG/WRL/WRL1/Coastal/Data/Tide/WL_Forecast/BOM_Storm_Surge/raw/corrected"
rem # Location if grabbing file from a local folder
set surgeForecastLoc=%regionHome%/ExternalForecasts/BOM/surge

rem #===================== BOM Wave Forecasts Location =================#
rem Location if grabbing files from WRL1, keep the forward slashes or else it doesn't work
rem set waveForecastLoc = "//ad.unsw.edu.au/OneUNSW/ENG/WRL/WRL1/Coastal/Data/Wave/Forecast/BOM_products/BOM_nearshore_wave_transformation_tool/raw/Mesh"
rem Location if grabbing file from a local folder
set waveForecastLoc=%regionHome%/ExternalForecasts/BOM/waves

rem #=========== Dates and Times for Batch of Hindcast Runs ============#
rem Start date of hindcasts, format: YYYY-MM-DD
set systemStartDate=2020-02-08 
rem Start time of hindcasts, format: HH:MM
set systemStartTime=00:00
rem Format: YYYY-MM-DD
set systemEndDate=2020-02-08
rem Format: HH:MM
set systemEndTime=00:00

rem #================== Anaconda virtual environment ===================#
rem Specify the path for Anaconda, should have activate.bat in it
set CONDAPATH=C:\\Users\\mandiruns\\Anaconda3
rem Specify the path to the virtual environment
set ENVPATH=%regionHome%\\bin\\windows\\python\\bin\\conda-venv
rem Call the script that activates the virtual environment
call %CONDAPATH%\Scripts\activate.bat %ENVPATH% >> %logFile%
rem Path to script
set SCRIPTPATH=%regionHome%\Scripts\runForecast\run_forecast_loop.py

rem #==================== Run run_forecast_loopy.py ====================#
"python" %SCRIPTPATH% %regionHome% %systemStartDate% %systemStartTime% %systemEndDate% %systemEndTime% %surgeForecastLoc% %waveForecastLoc% >> %logFile%
pause