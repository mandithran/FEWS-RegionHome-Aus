rem arguments to test/debug: C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\ 2020-02-07 00:00 2020-02-07 12:00
set regionHome=%1
rem Format: YYYY-MM-DD
set systemStartDate=%2 
rem Format: HH:MM
set systemStartTime=%3
rem Format: YYYY-MM-DD
set systemEndDate=%4
rem Format: HH:MM
set systemEndTime=%5
"C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\bin\windows\python\bin\conda-venv\python.exe" "C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Scripts\runForecast\run_forecast_loop.py" %regionHome% %systemStartDate% %systemStartTime% %systemEndDate% %systemEndTime%
