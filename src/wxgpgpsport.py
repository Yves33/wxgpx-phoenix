#!/usr/bin/env python3

import os,sys
import numpy as np
import datetime
import configparser

import wx
import wx.aui 
import wx.adv 

if not getattr(sys, "frozen", False):
    #required imports for plugins in frozen version. as these are loaded dynamically, they are not handled properly by py2exe or pyinstaller
    import wx.lib.agw.peakmeter
    import wx.lib.agw.speedmeter
    import wx.html2
    import wx.py
    import wx.grid

#local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__) ) +"/modules/")
from wxquery.wxquery import WxQuery
import msgwrap
import gpxobj
import wxmapwidget
import wxlinescatterwidget
import wxstatusbarwidget
#autogui will not work on all platform. on OSX, it requires quartz module
try:
    import pyautogui
except ImportError:
    hasautogui=False
else:
    hasautogui=True

#
#pyinstaller specific path determination
#
def thispath():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

if __name__ == "__main__":

    class MainFrameDropTarget(wx.FileDropTarget):
        def __init__(self, window):
            wx.FileDropTarget.__init__(self)
            self.window = window

        def OnDropFiles(self, x, y, filenames):
            for filepath in filenames:
                wx.GetApp().mainframe.OpenFile(filepath)
                print(filepath)
                # try to open file and return True or False
                # return True if file is fit or xml or npz
            return True

    class MainFrame(wx.Frame):
        def __init__(self, parent, id, title, size=(500,500)):
            wx.Frame.__init__(self, parent,id,size=(750,500),title=title,style=wx.DEFAULT_FRAME_STYLE)
            self.Bind(wx.EVT_CLOSE, self.OnClose)
            #self.id=wx.NewId()                              # deprecated in wxPython  phonix
            self.id=wx.Window.NewControlId()                 
            self.gpx=None
            self.replaytimer=None
            self.selstart=0
            self.selstop=0
            self.plugins={}

            # mappanel raises errors on invalid images, which are displayed in dialogs.
            # this redirects error logging to stderr
            wx.Log.SetActiveTarget(wx.LogStderr())

            # standard initialisation of default values
            self.config=configparser.ConfigParser()
            self.config.read(thispath()+os.sep+"wxgpgpsport.ini")
            if not self.config.get("map","map_cache") or self.config.get("map","map_cache")=="default":
                map_cache=None
            elif  os.path.isabs(self.config.get("map","map_cache")):
                map_cache=os.path.normpath(self.config.get("map","map_cache"))
            else:
                map_cache=os.path.normpath(thispath()+os.sep+self.config.get("map","map_cache"))

            #building interface
            self.InitMenus()
            panel = wx.Panel(self, -1)
            fdtarget=MainFrameDropTarget(self)
            #panel.SetDropTarget(fdtarget)
            hsplitter=wx.SplitterWindow(self,style=wx.SP_3D|wx.SP_3DSASH|wx.SP_BORDER|wx.SP_LIVE_UPDATE)
            vsplitter=wx.SplitterWindow(hsplitter,style=wx.SP_3D|wx.SP_3DSASH|wx.SP_BORDER|wx.SP_LIVE_UPDATE)
            hsplitter.SetSashGravity(0.666)
            vsplitter.SetSashGravity(0.500)
            # time panel
            self.timewidget=wxlinescatterwidget.WxTimeWidget(hsplitter)
            self.timewidget.SetDropTarget(fdtarget)
            # map widget
            self.mapwidget=wxmapwidget.WxMapWidget(vsplitter,usegl=self.config.getboolean("map","map_usegl"),\
                                                            localcache=map_cache,\
                                                            numthreads=self.config.getint("map","map_numthreads"),\
                                                            style=wx.BORDER_SUNKEN)
            #self.mapwidget=wxmapwidget.WxMapWidget(vsplitter,usegl=False,localcache=map_cache,style=wx.BORDER_SUNKEN)
            self.mapwidget.mapproviders=[]
            providers=self.config.get("map","tile_providers")
            for l in providers.split('\n'):
                self.mapwidget.AppendTileProvider(*tuple(l.split(',')))
            self.mapwidget.SetMapSrc(self.config.get("map","map_source"))
            self.mapwidget.SetUserAgent(self.config.get("map","http_user_agent"))
            self.mapwidget.SetDropTarget(fdtarget)
            # notebook
            # on OSX, the native notebook control does not allow for a large number of tabs
            # so we use a specific aui notebook with specific style to dismiss close button
            # or a wx.Choicebook
            # notebook=wx.Notebook(vsplitter)
            # notebook=wx.Choicebook(vsplitter,wx.ID_ANY)
            self.notebook=wx.aui.AuiNotebook(vsplitter,style=wx.aui.AUI_NB_DEFAULT_STYLE&~(wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB))
            # pack everything...
            hsplitter.SplitHorizontally(vsplitter, self.timewidget)
            vsplitter.SplitVertically(self.mapwidget, self.notebook)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(hsplitter, 1, wx.EXPAND)
            self.SetSizer(sizer)
            # status bar
            self.sb = wxstatusbarwidget.wxStatusBarWidget(self)
            self.SetStatusBar(self.sb)

            msgwrap.register(self.OnSigCurChanged, "CurChanged")
            msgwrap.register(self.OnSigSelChanged, "SelChanged")
            msgwrap.register(self.OnSigValChanged, "ValChanged")

            self.Show()
            self.mapwidget.Draw(True)
            #force a resize event to adjust all widgets properly
            #self.__resize()

        def OnClose(self,event):
            #for some unknown reason, the normal way to exit a wxPython app generates segfault on windows
            os._exit(0)

        def __resize(self):
            w,h=self.GetSize()
            self.SetSize((w+1,h))
            self.SetSize((w,h))

        def InitPlugins(self):
            sys.path.insert(0, thispath()+os.sep+"plugins/")
            pluginlist=[f for f in os.listdir(thispath()+os.sep+"plugins/") if (f.endswith('.py') and not f.startswith("_"))]
            for f in sorted(pluginlist):
                fname, ext = os.path.splitext(f)
                if ext == '.py' and fname[0]!='_' and fname[0]!='.':
                    mod = __import__(fname)
                    self.plugins[fname] = mod.Plugin(self.notebook,map=self.mapwidget,time=self.timewidget)
                    self.notebook.AddPage(self.plugins[fname],self.plugins[fname].GetName(),False)
            sys.path.pop(0)
            self.mapwidget.Draw(True)

        def StaticPlugins(self):
            # for test purpose only: this routine is never called in non frozen environment
            if not getattr(sys,"frozen",False):
                sys.path.insert(0, thispath()+os.sep+"plugins/")
            import wxShell
            import wxWaypoints
            import wxScatter
            import wxGauge
            import wxMeter
            import wxStatistics
            import wxMeasure
            import wxTable
            import wxPolar
            import wxHistogram
            import wxHelp
            pluginlist=self.config.get("app","plugins").split('\n')
            for  f in sorted(pluginlist):
                fname, ext = os.path.splitext(f)
                mod= __import__(fname)
                self.plugins[fname] = mod.Plugin(self.notebook,map=self.mapwidget,time=self.timewidget)
                self.notebook.AddPage(self.plugins[fname],self.plugins[fname].GetName(),False)
            self.mapwidget.Draw(True)


        def InitMenus(self):
            menubar = wx.MenuBar()
            self.filemenu = wx.Menu()
            item = self.filemenu.Append(wx.ID_OPEN, "&Open\tCTRL+O")
            self.Bind(wx.EVT_MENU, self.OnOpenMenu, item)
            item = self.filemenu.Append(wx.ID_SAVEAS, "&Save as...\tCTRL+S")
            self.Bind(wx.EVT_MENU, self.OnSaveMenu, item)
            item = self.filemenu.Append(wx.ID_EXIT, "Quit","Quit application")
            self.Bind(wx.EVT_MENU, self.OnQuitMenu, item)
            menubar.Append(self.filemenu, "&File")
            self.editmenu = wx.Menu()
            item = self.editmenu.Append(wx.ID_UNDO, "&Undo\tCTRL+Z")
            item.Enable(False)
            item = self.editmenu.Append(wx.ID_REDO, "&Redo\tCTRL+SHIFT+Z")
            item.Enable(False)
            self.editmenu.AppendSeparator()
            item = self.editmenu.Append(wx.ID_CUT, "&Cut\tCTRL+X")
            item.Enable(False)
            item = self.editmenu.Append(wx.ID_COPY, "&Copy\tCTRL+C")
            item.Enable(False)
            item = self.editmenu.Append(wx.ID_PASTE, "&Paste\tCTRL+V")
            item.Enable(False)
            item = self.editmenu.Append(wx.ID_SELECTALL, "&Select All\tCTRL+A")
            item.Enable(False)
            menubar.Append(self.editmenu, "&Edit")
            self.gpxmenu = wx.Menu()
            item = self.gpxmenu.Append(wx.ID_ANY, "&Units\tCTRL+U")
            self.Bind(wx.EVT_MENU, self.OnUnitsMenu, item)
            item.Enable(False)
            item = self.gpxmenu.Append(wx.ID_ANY, "&Replay\tCTRL+R",kind=wx.ITEM_CHECK)
            self.Bind(wx.EVT_MENU, self.OnReplayMenu, item)
            item.Enable(False)
            menubar.Append(self.gpxmenu, "&Gpx")
            self.SetMenuBar(menubar)

        def OnQuitMenu(self,event):
            #self.Close(True)
            #for some unknown reason, I get segfaults if I just close the main frame
            os._exit(0)

        def OnSaveMenu(self,event):
            wildcard = "Compressed Numpy Array (*.npz)|*.npz|"+\
                        "GPX XML file (*.gpx)|*.gpx"
            dialog = wx.FileDialog(None, "Choose a file", os.getcwd(), "", wildcard, wx.FD_SAVE)
            if dialog.ShowModal() == wx.ID_OK:
                #self.gpx.save_npz(dialog.GetPath())
                self.SaveFile(dialog.GetPath())

        def SaveFile(self,filename):
            if 'wxShell' in self.plugins:
                self.plugins["wxShell"].run(thispath()+os.sep+"scripts"+os.sep+"onSaveFile.py")
            if filename[-4:]=='.npz' or filename[-4:]=='.NPZ':
                self.gpx.save_npz(filename)
            elif filename[-4:]=='.gpx' or filename[-4:]=='.GPX':
                allowedfields=self.gpx.get_header_names()
                allowedfields.remove('ok')
                allowedfields.remove('idx')
                allowedfields.remove('lat')
                allowedfields.remove('lon')
                (fields,save_enabled)=WxQuery("GPX export dialog",\
                                        [('wxchecklist','Choose fields to export','|'.join(allowedfields),'time|speed','str'), \
                                         ('wxcheck','Exported only enabled points',None,False,'bool')])
                if save_enabled:
                    # np.where returns a tupple of numpy.ndarray where we need a list
                    self.gpx.save_xml(filename,fields.split('|'),np.where(self.gpx['ok']==True)[0].tolist())
                else:
                    self.gpx.save_xml(filename,fields.split('|'),None)

        def OnOpenMenu(self,event):
            wildcard = "Fit file (*.fit)|*.fit|"+\
                        "GPS Exchange (*.gpx,*.gpx.gz)|*.gpx;*gpx.gz|"+\
                        "Numpy Array (*.npz)|*.npz"
            dialog = wx.FileDialog(None, "Choose a file", os.getcwd(), "", wildcard, wx.FD_OPEN)
            if dialog.ShowModal() == wx.ID_OK:
                self.OpenFile(dialog.GetPath())

        def OpenFile(self,filename):
            #todo
            if not filename[-4:]in['.fit','.FIT','.npz','.NPZ','.gpx','.GPX','.xml','.XML']:
                return
            if self.gpx!=None:
                self.mapwidget.DetachGpx()
                self.timewidget.DetachGpx()
                for k in self.plugins:
                    self.plugins[k].DetachGpx()
                del self.gpx
            c=0
            progressdlg = wx.ProgressDialog("Loading", "Loading file", 17,style=wx.PD_SMOOTH|wx.PD_CAN_ABORT|wx.PD_AUTO_HIDE)
            self.gpx=gpxobj.GpxObj()                            ;c+=1;progressdlg.Update(c)
            if filename[-4:]=='.fit' or filename[-4:]=='.FIT':
                self.gpx.open_fit(filename)
            elif filename[-4:]=='.npz' or filename[-4:]=='.NPZ':
                self.gpx.open_npz(filename)
            else:
                self.gpx.open_gpx(filename)                     ;c+=1;progressdlg.Update(c,"Parsing file")
            #   self.gpx.parse_trkpts()                         ;c+=1;progressdlg.Update(c) # now included in open_gpx
            ## we calculate a few standard indicators:
            # deltat    time between two adjacent points. some GPS do not log at equally spaced times
            # deltaxy   horizontal distance between two ajacent points.
            # distance  cumulative distance calculated from haversine formula   (m)
            # duration  cumulative duration calculated from time tag            (s)
            # course   course calculated from haversine formula               (degrees)
            # speed     instantaneous speed calculated from haversine formula. only if no doppler speed is found
            # acc       instantaneous acceleration                              calculated drom speed column
            # slope     only if an elevation 'ele' tag is found                 instantaneous slope!!not reliable
            if not self.gpx.has_field('time'):
                # rare case, but time tag is not mandatory in gpx description
                dlg = wx.MessageBox('Your gpx file does not seem to include time values. Do you want to generate time series?','Generate fake times?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION )
                if dlg == wx.YES:
                    deltat=WxQuery("Enter time gap between GPS points",[("wxentry","Time gap in seconds",None,"1.0",'float')])[0]
                    self.gpx.append_column('time','str')
                    base=datetime.datetime.today()
                    self.gpx['time']=[(base+datetime.timedelta(0,sec*deltat)).strftime("%Y-%m-%dT%H:%M:%SZ") for sec in range(0, self.gpx.get_row_count())]
            #some fields such as 'speed' or 'distance' may be directly imported from gpx/fit/tcx file
            if not self.gpx.has_field('deltat'):
                self.gpx.append_column('deltat','float')                ;c+=1;progressdlg.Update(c,"Computing Time deltas")
                self.gpx['deltat']=self.gpx.duration()                  ;c+=1;progressdlg.Update(c)
            if not self.gpx.has_field('deltaxy'):
                self.gpx.append_column('deltaxy','float')               ;c+=1;progressdlg.Update(c,"Computing Location deltas")
                self.gpx['deltaxy']=self.gpx.hv_distance()              ;c+=1;progressdlg.Update(c)
            if not self.gpx.has_field('distance'):
                self.gpx.append_column('distance','float')              ;c+=1;progressdlg.Update(c,"Computing distances")
                self.gpx['distance']=np.cumsum(self.gpx['deltaxy'])     ;c+=1;progressdlg.Update(c)
            if not self.gpx.has_field('duration'):
                self.gpx.append_column('duration','float')              ;c+=1;progressdlg.Update(c,"Computing durations")
                self.gpx['duration']=np.cumsum(self.gpx['deltat'])      ;c+=1;progressdlg.Update(c)
            if not self.gpx.has_field('course'):
                self.gpx.append_column('course','float')                ;c+=1;progressdlg.Update(c,"Computing course")
                self.gpx['course']=self.gpx.hv_course()                 ;c+=1;progressdlg.Update(c)
            if not self.gpx.has_field('speed'):
                self.gpx.append_column('speed','float')                 ;c+=1;progressdlg.Update(c,"Computing speed")
                self.gpx['speed']=self.gpx.hv_speed(True)               ;c+=1;progressdlg.Update(c)
            if not self.gpx.has_field('slope'):
                self.gpx.append_column('slope','float')                 ;c+=1;progressdlg.Update(c,"Computing slope")
                self.gpx['slope']=self.gpx.hv_slope(200,True)           ;c+=1;progressdlg.Update(c)
            progressdlg.Close()
            progressdlg.Destroy()
            self.gpx.set_unit('deltaxy','m')
            self.gpx.set_unit('deltat','s')
            # todo: check that the units are known
            self.gpx.set_unit('speed',self.config.get("units","default_speed_unit"))
            self.gpx.set_unit('distance',self.config.get("units","default_distance_unit"))
            self.gpx.set_unit('duration',self.config.get("units","default_time_unit"))
            #self.gpx.set_unit('speed','km/h')
            #self.gpx.set_unit('distance','m')
            #self.gpx.set_unit('duration','s')
            self.timewidget.AttachGpx(self.gpx)
            self.mapwidget.AttachGpx(self.gpx)
            self.gpxmenu.Enable(self.gpxmenu.FindItem("Units"),True)
            self.gpxmenu.Enable(self.gpxmenu.FindItem("Replay"),True)
            for k in self.plugins:
                self.plugins[k].AttachGpx(self.gpx)
            # new
            if 'wxShell' in self.plugins:
                self.plugins["wxShell"].run(thispath()+os.sep+"scripts"+os.sep+"onOpenFile.py")

            self.SetTitle(filename)
            self.__resize()

        def OnUnitsMenu(self,event):
            li=[]
            un='|'.join(gpxobj.units.keys())
            # as _x, _y, _r, _g, _b and _d are no more in gpx file, we could avoid checking first character...
            for head in self.gpx.get_header_names():
                if not head.startswith('_'):
                    li.append(("wxcombo",str(head),un,self.gpx.get_unit(head)[0],'str'))
            res=WxQuery("Adjust units",li)
            i=0
            for head in self.gpx.get_header_names():
                if not head.startswith('_'):
                    self.gpx.set_unit(head,res[i])
                    i+=1
            msgwrap.message("ValChanged",arg1=self.id)
            self.Refresh()

        def OnReplayMenu(self,event):
            if self.replaytimer==None:
                (speed,)=WxQuery("Replay speed: x",[("wxentry","Replay speed",None,"100",'int')])
                self.replaytimer=wx.Timer(self)
                self.Bind(wx.EVT_TIMER,self.OnReplayTimer,self.replaytimer)
                self.replaytimer.Start(speed)
                self.idx=self.selstart
                wx.GetApp().blockmousemotion=True
            else:
                self.replaytimer.Stop()
                self.replaytimer=None
                wx.GetApp().blockmousemotion=False
            pass

        def OnReplayTimer(self,event):
            self.idx+=1
            if self.idx > self.selstop-1:
                self.idx=self.selstart
            #skip disabled portions
            while not self.gpx['ok'][self.idx]:
                self.idx+=1
                if self.idx > self.selstop:
                    self.idx=self.selstart
            msgwrap.message("CurChanged",arg1=self.id,arg2=self.idx)

        def OnSigCurChanged(self, arg1, arg2):
            if arg1==self.id:
                return
            if self.gpx!=None:
                if self.replaytimer==None:
                    self.idx=arg2

        def OnSigSelChanged(self,arg1,arg2,arg3):
            if arg1==self.id:
                return
            self.selstart=arg2
            self.selstop =arg3

        def OnSigValChanged(self,arg1):
            if arg1==self.id:
                return

    class DemoApp(wx.App):
        def __init__(self):
            wx.App.__init__(self,redirect=False)

        def OnInit(self):
            splash_file=thispath()+os.sep+"images"+os.sep+"splash256.jpg"
            if os.path.exists(splash_file):
                splash_image = wx.Image(splash_file, wx.BITMAP_TYPE_ANY, -1)
                splash=wx.adv.SplashScreen(splash_image.ConvertToBitmap(),wx.adv.SPLASH_CENTRE_ON_SCREEN|wx.adv.SPLASH_TIMEOUT,1000,None, -1)
                splash.Show()
            self.mainframe = MainFrame(None,-1,"GPX visualizer")
            self.mainframe.InitPlugins()
            # if not getattr(sys,"frozen",False):
                # self.mainframe.InitPlugins()
            # else:
                # self.mainframe.StaticPlugins()
            # Startup plugin is now lauched from here!
            if 'wxShell' in self.mainframe.plugins:
                self.mainframe.plugins["wxShell"].run(thispath()+os.sep+"scripts"+os.sep+"onStartup.py")
            self.SetTopWindow(self.mainframe)
            self.blockmousemotion=False
            #self.SetCallFilterEvent(True) #wxPython classic
            self.FilterEvent=self.FilterEvent
            return True

        def FilterEvent(self,event):
            # trap mouse motion event when in replay mode
            if (event.GetEventType()==wx.wxEVT_MOTION) and self.blockmousemotion==True:
                return True
            # emulate mouse wheel with ctl+left (wheel up) or ctl+right (wheel right). mandatory for laptop usage
            # use pyautogui for cross platform efficiency
            if hasautogui:
                if event.GetEventType()==wx.wxEVT_LEFT_DOWN and event.ControlDown():
                    pyautogui.scroll(1)
                    return True
                if event.GetEventType()==wx.wxEVT_RIGHT_DOWN and event.ControlDown():
                    pyautogui.scroll(-1)
                    return True
            # if event was not processed, return -1
            return -1

    print(sys.version)
    app = DemoApp()
    app.MainLoop()
    os._exit(0) # required for linux
