rem Run: START /B C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Scripts\runForecast\run_forecast_loop_1.bat > forecastLog_1.txt 2>&1
rem arguments to test/debug: C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\ 2020-02-07 00:00 2020-02-07 12:00
set regionHome=C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\
rem Format: YYYY-MM-DD
set systemStartDate=2020-02-15 
rem Format: HH:MM
set systemStartTime=00:00
rem Format: YYYY-MM-DD
set systemEndDate=2020-02-21
rem Format: HH:MM
set systemEndTime=12:00
set CONDAPATH=C:\Users\z3531278\Anaconda3
set ENVPATH=%regionHome%\bin\windows\python\bin\conda-venv\
call %CONDAPATH%\Scripts\activate.bat %ENVPATH%
"C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe" "C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Scripts\runForecast\run_forecast_loop.py" %regionHome% %systemStartDate% %systemStartTime% %systemEndDate% %systemEndTime%
pause