###todo
* Export speedmeter and gauge as movies (usign ffmpeg bg should be green for chroma filter)
* Improved wxpython speedmeter (stacking transparent pngs)

###(December 1st,2018)
* Implemented drop file support in map and time panels.
* Implemented support for numthreads in wxgpgpsport.ini
* Implemented support for http_user_agent in wxgpgpsport.ini file
* Changed the way the legend is displayed in graph
* Ported to Python 3 & wxPython-phoenix. The code is compatible and tested with python 2.7, but is not anymore compatible with wxPython-classic.
* Introduced alternative signal dispatchers (PyDispatcher, SmokeSignal) as alternatives to pypubsub. (pypubsub imports in wx.lib are extremely hackish, which makes its encapsulation by PyInstaller unreliable). The default is now PyDispatcher.
* Migrated to Threading instead of deprecated _thread (old code is still present, though)
* Rearranged the source directory to separate scripts (launch_xxx and generate_xxx).
* Created additional hooks for pyinstaller. The generate_xxx_binary have been reworked to exclude Tk and tkinter
* various bug corrections due to or unmasked by the migration to python3/wxPython phoenix

###(March 30, 2018)
* Fixed bug in gpxobj that sometimes prevent loading corrupted fit files (line 467)

###(Ferbruary 26,2018)
* Fixed bug in fitparse that prevented loading large files (crc error in base.py, line84)

###(September 07,2017)
* Fixed bug in wxmappanel.DrawLocalTile function (incorrect tile frame when tile image is not available)
* Added SaveBuffer(buff,filename,imgtype) to wxGLArtist and wxDCArtist (untested)
* Added CacheAll(maxzoom) to download all zoom levels for a given area (well... only generates a list of tiles.)
* Changed name of Startup script to onStartup.py and moved implementation to app (so the plugin is now executed after all plugin have loaded)
* Created onOpenFile.py and onSaveFile.py which are executed immediately after opening aand before saving a file.
(Not tested in frozen verion. An onOpenFile.py script could for exemple convert from GMT to local time, set appropriate units...)
* Fixed documentation, now generated through python markdown module

###(July 28,2017)
* Set window title to reflect current file path
* Fixed units for course in wxMeasure plugin (not configurable)
* Modified proof of concept script to create an overlay on map and draw stuff on it (test_overlay.py and liboverlay.py)
* Added a proof of concept script to create patches on time view (test_patches.py)
* Added a demo script to create an interactive frame with controls and buttons (test_interactive_frame.py)

###(July 14,2017)
* Jibe analysis script now calculates the downwind distance lost
* Minor bugfix in gpxobj.py (recomputes 'idx' column each time points are deleted). This allows reopening npz files that were not properly saved.
* 'idx', is not exported anymore in npz files.
* Added an __init__.py file to script folder to be able to import from this folder (from scripts import whateveryouwant)
* __init__.py, *.pyc and lib*.py files are now ignored from script list
* Added a proof of concept script to create an overlay on map and draw stuff on it (test_overlay.py and liboverlay.py)

###(July 06,2017)
* wxmappanel.Haversine (lat1, lon1, lat2, lon2) now returns tupple (distance, course).
* In measure plugin,
    - dump cumulative distance, "as the crow flies" distance and course.
    - dump individual segment length and course.

###(July 04,2017)
* GPSBabel import script
* GPSBabel export script (with google earth visualisation option if kml is chosen)
* Add previously executed scripts to script list in shell plugin (still minor bugs in remembering last executed script)
* Fixed wxMapBase.TruncCache(size,count)
* Fixed wxquery 'wxfile' (Filter for non existing files is now '' instead of None)
* Fixed bug that prevented loading gpx when Time info displayed 1/10th of seconds
* Renamed (CAPITALIZE)and updated documentation
* Created this CHANGELOG file.

###(July 02,2017)
* Initial binary releases for OSX and win32
* Adapted code to be compliant with PyInstaller-3.2
* Updates in documentation
* Reorganisation of github repo structure
