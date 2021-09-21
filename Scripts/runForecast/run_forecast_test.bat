rem Run: START /B C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Scripts\runForecast\run_forecast_loop_1.bat > forecastLog_1.txt 2>&1
rem arguments to test/debug: C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\ 2020-02-07 00:00 2020-02-07 12:00
set regionHome=C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\
set logFile=%regionHome%\\forecastLogFEWS.txt
rem Format: YYYY-MM-DD
set systemStartDate=2020-01-01 
rem Format: HH:MM
set systemStartTime=00:00
rem Format: YYYY-MM-DD
set systemEndDate=2020-01-02
rem Format: HH:MM
set systemEndTime=00:00
set CONDAPATH=C:\\Users\\mandiruns\\Anaconda3
set ENVPATH=%regionHome%\\bin\\windows\\python\\bin\\conda-venv
call %CONDAPATH%\Scripts\activate.bat %ENVPATH% >> %logFile%
"python" "C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Scripts\runForecast\run_forecast_test.py" %regionHome% %systemStartDate% %systemStartTime% %systemEndDate% %systemEndTime% >> %logFile%