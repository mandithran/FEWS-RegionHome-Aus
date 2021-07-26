echo off
set root=C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus
set region_home=C:\Users\z3531278\Documents\01_FEWS-RegionHome-Aus\
REM set workflowtestrun=%3
start cmd.exe /k %root%\bin\windows\Delft-FEWSc.exe -Dregion.home=%region_home% > logfile.txt REM -DautoRollingBarrel=false -Xmx1024m -DoldPID=13096_1555070573358 -Djava.locale.providers=SPI,JRE -Dstart.time=1555070573676 -Djava.library.path=%root%\bin\windows -Wvm.location=%root%\bin\windows\jre\bin\server\jvm.dll -Wclasspath.1=%region_home%\sa_patch.jar -Wclasspath.2=%root%\bin\*.jar -Wmain.class=nl.wldelft.fews.system.workflowtestrun.WorkflowTestRun -Warg.1=%region_home% -Warg.2=%workflowtestrun% > logfile.txt
PAUSE