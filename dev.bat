echo off
echo The current directory is %CD%

rem #============ Variables ============#
set "DEV_NAME=SurgeDownload_dev"
set "TAR_NAME=SurgeDownload"

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

rem #============ Zip File ============#
7z a %ZIP_PATH% %TAR_PATH%

rem #============ Remove folder that was just zipped ============#
RD /S /Q %TAR_PATH%

rem #============ Remove folder that was just zipped ============#
move %ZIP_PATH% %DATA_PATH%