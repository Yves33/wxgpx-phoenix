@echo off
cd ..
del /s /q /f *.pyc
SET TARGET=wxgpgpsport
pyinstaller.exe -p .\modules\ -p .\plugins\ --windowed --clean ^
--additional-hooks-dir=hooks ^
--exclude-module FixTk ^
--exclude-module tcl ^
--exclude-module _tkinter ^
--exclude-module tkinter ^
--exclude-module Tkinter ^
--exclude-module tk ^
--exclude-module win32com ^
--exclude-module pywin32 ^
--exclude-module pubsub ^
--exclude-module smokesignal ^
%TARGET%.py 
xcopy /e /Y /i images dist\%TARGET%\images
xcopy /e /Y /i docs dist\%TARGET%\docs
xcopy /e /Y /i scripts dist\%TARGET%\scripts
xcopy /e /Y /i plugins dist\%TARGET%\plugins
xcopy /Y wxgpgpsport.ini dist\wxgpgpsport\
pause