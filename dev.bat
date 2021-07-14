echo off
echo The current directory is %CD%

rem #============ Variables ============#
set "DEV_NAME=PreProcessXBeach_dev"
set "TAR_NAME=PreProcessXBeach"

rem #============ Paths ============#
set "DEV_PATH=.\Modules\%DEV_NAME%"
set "TAR_PATH=.\Modules\%TAR_NAME%"
set "ZIP_PATH=.\Modules\%TAR_NAME%.zip"
set "DATA_PATH=.\Config\ModuleDataSetFiles\"


rem #============ Remove previous directory ============#
if exist %TAR_PATH% RD /S /Q %TAR_PATH%

rem #============ Copy and rename dev directory ============#
xcopy /s /i %DEV_PATH% %TAR_PATH%

rem #============ Remove any unwanted files ============#
set "DIAG_FILE=%TAR_PATH%\diag.xml"
IF EXIST %DIAG_FILE% DEL /F %DIAG_FILE%
set "LOG_FILE=%TAR_PATH%\exceptions.log"
IF EXIST %LOG_FILE% DEL /F %LOG_FILE%

rem #============ Zip File ============#
7z a %ZIP_PATH% %TAR_PATH%

rem #============ Remove folder that was just zipped ============#
RD /S /Q %TAR_PATH%

rem #============ Remove folder that was just zipped ============#
move %ZIP_PATH% %DATA_PATH%