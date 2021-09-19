set CONDAPATH=C:\\Users\\mandiruns\\Anaconda3
set ENVPATH=C:\\Users\\mandiruns\\Documents\\01_FEWS-RegionHome-Aus\\bin\\windows\\python\\bin\\conda-venv
call %CONDAPATH%\Scripts\activate.bat %ENVPATH%

"python" "C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Scripts\downloadForecasts\download_latest_surge_data.py"
"python" "C:\Users\mandiruns\Documents\01_FEWS-RegionHome-Aus\Scripts\downloadForecasts\download_latest_wave_data.py"