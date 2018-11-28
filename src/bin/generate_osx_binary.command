#!/usr/bin/env bash
cd "$(dirname "$0")"
cd ..
echo $PWD
pyinstaller --clean --windowed wxgpgpsport.py --icon ./images/Map.ico \
-p ./modules/ \
-p ./plugins/ \
--additional-hooks-dir=hooks \
--exclude-module FixTk \
--exclude-module tcl \
--exclude-module _tkinter \
--exclude-module tkinter \
--exclude-module Tkinter \
--exclude-module tk \
--exclude-module pubsub \
--exclude-module smokesignal \
--workpath $TMPDIR
cp -R images dist/wxgpgpsport.app/Contents/MacOS/
cp -R docs dist/wxgpgpsport.app/Contents/MacOS/
cp -R scripts dist/wxgpgpsport.app/Contents/MacOS/
cp -R plugins dist/wxgpgpsport.app/Contents/MacOS/
cp wxgpgpsport.ini dist/wxgpgpsport.app/Contents/MacOS/