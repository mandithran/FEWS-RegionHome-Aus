set CONDAPATH=C:\\Users\\z3531278\\Anaconda3
set ENVPATH=C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\bin\\windows\\python\\bin\\conda-venv
call %CONDAPATH%\Scripts\activate.bat %ENVPATH%

"python" "C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Scripts\downloadForecasts\download_latest_surge_data.py"
"python" "C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\Scripts\downloadForecasts\download_latest_wave_data.py"