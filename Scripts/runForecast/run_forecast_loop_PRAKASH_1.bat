rem Run: START /B C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Scripts\runForecast\run_forecast_loop_1.bat > forecastLog_1.txt 2>&1
rem arguments to test/debug: C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\ 2020-02-07 00:00 2020-02-07 12:00
set regionHome=C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\
set logFile=%regionHome%\\forecastLog_PRAKASH1.txt

rem Location if grabbing files from WRL1, keep the forward slashes or else it doesn't work
rem set surgeForecastLoc = "//ad.unsw.edu.au/OneUNSW/ENG/WRL/WRL1/Coastal/Data/Tide/WL_Forecast/BOM_Storm_Surge/raw/corrected"
rem # Location if grabbing file from a local folder
set surgeForecastLoc=D:\EWS\BOM\surge

rem Location if grabbing files from WRL1, keep the forward slashes or else it doesn't work
rem set waveForecastLoc = "//ad.unsw.edu.au/OneUNSW/ENG/WRL/WRL1/Coastal/Data/Wave/Forecast/BOM_products/BOM_nearshore_wave_transformation_tool/raw/Mesh"
rem Location if grabbing file from a local folder
set waveForecastLoc=D:\EWS\BOM\waves

rem Format: YYYY-MM-DD
set systemStartDate=2020-07-24 
rem Format: HH:MM
set systemStartTime=00:00
rem Format: YYYY-MM-DD
set systemEndDate=2020-09-02
rem Format: HH:MM
set systemEndTime=12:00

set CONDAPATH=C:\\Users\\mandiruns\\Anaconda3
set ENVPATH=%regionHome%\\bin\\windows\\python\\bin\\conda-venv

call %CONDAPATH%\Scripts\activate.bat %ENVPATH% >> %logFile%
"python" "C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Scripts\runForecast\run_forecast_loop.py" %regionHome% %systemStartDate% %systemStartTime% %systemEndDate% %systemEndTime% %surgeForecastLoc% %waveForecastLoc% >> %logFile%
pause