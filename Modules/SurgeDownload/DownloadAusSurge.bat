@echo off
setlocal EnableDelayedExpansion

IF EXIST log.txt del /F log.txt

echo Hello World

set sourceLocation=%1
set targetLocation=%2
set "targetLocation=C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus/Import/AusSurge/"
set refTime=%3
set refTime=20200401_2300
set myProduct=%4

echo Ref time
echo %refTime%

type diagOpen.txt > diag.xml
echo.^<line level=^"3^" description=^"Running DownloadGlobSnow.bat^"/^>>>diag.xml
echo.^<line level=^"3^" description=^"Downloading %myProduct%^"/^>>>diag.xml
rem echo.^<line level=^"3^" description=^"Downloading from %sourceLocation%^"/^>>>diag.xml
rem echo.^<line level=^"3^" description=^"Downloading to %targetLocation%^"/^>>>diag.xml
echo.^<line level=^"3^" description=^"Reference time (cycle) !refTime:~-2!^"/^>>>diag.xml
echo.^<line level=^"3^" description=^"Reference time (cycle) !refTime!^"/^>>>diag.xml
echo.^<line level=^"3^" description=^"Reference time (test) %refTime%"/^>>>diag.xml
rem echo.^<line level=^"3^" description=^"For meaning of exit codes, see https://www.gnu.org/software/wget/manual/html_node/Exit-Status.html^"/^>>>diag.xml

rem ####### Parse Datetime ##########
set "currYYYY=!refTime:~0,4!"
set "currMM=!refTime:~4,2!"
set "currDD=!refTime:~6,2!"
set "currHH=!refTime:~9,2!"
echo current yyyy, hh, dd, mm
echo %currYYYY%
echo %currMM%
echo %currDD%
echo %currHH%


set "number_to_round=1867.603187561035"

for /f "tokens=1,2 delims=." %%a  in ("%number_to_round%") do (
  set first_part=%%a
  set second_part=%%b
)

set second_part=%second_part:~0,1%
echo %second_part%
if defined second_part if %second_part% GEQ 5 ( 

    set /a rounded=%first_part%+1
) else ( 
    set /a rounded=%first_part%
)

echo rounded
echo %rounded%

rem set "refYear=!refTime:~0,4!"
rem set "myURL=%sourceLocation%/%refYear%/data/GlobSnow_SWE_L3A_%refTime%_v.1.0.nc.gz"

rem ####### Run wget to fetch file from server #######
rem Address to view catalogue in browser: http://opendap.bom.gov.au:8080/thredds/catalog/surge/forecast/RnD/catalog.html
set "myURL=http://opendap.bom.gov.au:8080/thredds/fileServer/surge/forecast/RnD/IDZ00154_StormSurge_national_2020120218.nc"
rem wget64 --no-check-certificate -N !myURL! -P %targetLocation% -o temp.txt
wget64 --no-check-certificate -N !myURL! -P !targetLocation! -o temp.txt

rem ####### Write out more diagnostics regarding the exit code for wget #######
 set logText=<temp.txt
  IF %errorlevel%==0 (
   	echo.^<line level=^"3^" description=^"Downloading !myURL!^; wget exit code: %errorlevel%^"/^>>>diag.xml
   	echo.^<line level=^"3^" description=^"%logText%^"/^>>>diag.xml
   	) ELSE (
		 echo.^<line level=^"0^" description=^"Downloading !myURL!^; wget exit code: %errorlevel%^"/^>>>diag.xml
  	)
)

echo.^</Diag^>>>diag.xml

PAUSE