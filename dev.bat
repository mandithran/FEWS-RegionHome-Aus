echo off
setlocal enabledelayedexpansion
echo The current directory is %CD%

rem #============ Variables ============#
rem List of modules to zip
set list=initFEWSForecast AstroTides NSSDownload WaveDownload PreProcessXBeach 
(for %%a in (%list%) do ( 

   rem #============ Paths ============#
   set MOD_NAME=%%a
   set DEV_PATH=.\Modules\!MOD_NAME!_dev
   set DEST_PATH=.\Modules\!MOD_NAME!
   set ZIP_PATH=.\Modules\!MOD_NAME!.zip
   set DATA_PATH=.\Config\ModuleDataSetFiles\

   rem #============ Remove previous directory ============#
   if exist !DEST_PATH! RD /S /Q !DEST_PATH!

   rem #============ Copy and rename dev directory ============#
   xcopy /s /i !DEV_PATH! !DEST_PATH!

   rem #============ Remove any unwanted files ============#
   set DIAG_FILE=!DEST_PATH!\diag.xml
   IF EXIST !DIAG_FILE! DEL /F !DIAG_FILE!
   set LOG_FILE=!DEST_PATH!\exceptions.log
   IF EXIST !LOG_FILE! DEL /F !LOG_FILE!
   set NC_PATH=!DEST_PATH!\ncFiles
   IF EXIST !NC_PATH! DEL /F /Q !NC_PATH!


   rem #============ Zip File ============#
   7z a !ZIP_PATH! !DEST_PATH!

   rem #============ Remove folder that was just zipped ============#
   RD /S /Q !DEST_PATH!

   rem #============ Remove folder that was just zipped ============#
   move !ZIP_PATH! !DATA_PATH!

))
