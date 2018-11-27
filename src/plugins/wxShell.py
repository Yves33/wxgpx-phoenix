#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
## system imports
import os,sys
import inspect
import wx
import wx.lib.newevent
from wx.py import shell

import numpy as np

## local imports
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import msgwrap
import gpxobj
from wxquery.wxquery import WxQuery

class WxShell(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.runbutton=wx.Button(self,0,"Run the script file below...")
        self.runbutton.Bind(wx.EVT_BUTTON, self.OnRunButtonClicked)
        sizer.Add(self.runbutton,0,wx.EXPAND)
        #if not getattr(sys,"frozen",False):
        #    self.scriptpath=os.path.dirname(os.path.abspath(__file__))+os.sep+".."+os.sep+"scripts/"
        #else:
        #    self.scriptpath=os.path.dirname(sys.executable)+os.sep+"scripts/"
        #scriptlist=sorted(os.listdir(self.scriptpath))
        scriptlist=self.scanscripts()
        self.lastscripts=['Browse file...']
        scriptlist.append(self.lastscripts[0])
        self.scriptcombo=wx.ComboBox(self,choices=scriptlist, style=wx.CB_READONLY)
        self.scriptcombo.SetValue(self.lastscripts[0])
        self.lastscript=self.lastscripts[0]
        self.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.UpdateScripts, self.scriptcombo)
        sizer.Add(self.scriptcombo,0,wx.EXPAND)
        self.pyshell = shell.Shell(self, -1, introText='Python Shell')
        sizer.Add(self.pyshell,1,wx.EXPAND)
        self.gpx=None
        #standard events
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftMouseDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnLeftMouseUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftMouseDblClick)
        self.Bind(wx.EVT_MOTION,self.OnMouseMotion)
        self.Bind(wx.EVT_ENTER_WINDOW,self.OnMouseEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW,self.OnMouseLeave)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightMouseDown)
        self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        #self.Bind(wx.EVT_SIZE,self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND,self.OnErase)
        #custom events
        msgwrap.register(self.OnSigCurChanged, "CurChanged")
        msgwrap.register(self.OnSigSelChanged, "SelChanged")
        msgwrap.register(self.OnSigValChanged, "ValChanged")

        self.pyshell.interp.locals={}
        self.Link()

    def scanscripts(self):
        if not getattr(sys,"frozen",False):
             self.scriptpath=os.path.dirname(os.path.abspath(__file__))+os.sep+".."+os.sep+"scripts/"
        else:
            self.scriptpath=os.path.dirname(sys.executable)+os.sep+"scripts/"
        fulllist=sorted(os.listdir(self.scriptpath))
        return[f for f in fulllist if not (f.startswith('__') or f.endswith('pyc') or f.startswith('lib'))]


    def Link(self):
        if self.gpx!=None:
            self.pyshell.interp.locals['gpx']=self.gpx
        self.pyshell.interp.locals['mapview']=self.mapwidget
        self.pyshell.interp.locals['timeview']=self.timewidget
        self.pyshell.interp.locals['app']=wx.GetApp().mainframe
        self.pyshell.interp.locals['sh']=self
        self.pyshell.interp.locals['rootdir']=os.path.normpath(os.path.dirname(os.path.abspath(__file__)+os.sep+".."+os.sep+".."+os.sep))
        self.pyshell.interp.locals['scriptdir']=os.path.normpath(os.path.dirname(os.path.abspath(__file__)+os.sep+".."+os.sep+".."+os.sep+"scripts"+os.sep))
        self.pyshell.interp.locals['plugindir']=os.path.normpath(os.path.dirname(os.path.abspath(__file__)+os.sep+".."+os.sep+".."+os.sep+"plugins"+os.sep))
        self.pyshell.interp.locals['testdir']=os.path.normpath(os.path.dirname(os.path.abspath(__file__)+os.sep+".."+os.sep+".."+os.sep+"testfiles"+os.sep))
        self.pyshell.interp.locals['WxQuery']=WxQuery
        self.pyshell.Execute('import numpy as np')

    def UpdateScripts(self,event):
        self.scriptcombo.Clear()
        scriptlist=self.scanscripts()
        #scriptlist=sorted(os.listdir(self.scriptpath))
        scriptlist=scriptlist+self.lastscripts
        for s in scriptlist:
            self.scriptcombo.Append(s)
        self.scriptcombo.SetValue(self.lastscript)

    def AttachGpx(self,data):
        self.gpx=data
        self.Link()
        # self.pyshell.interp.locals={'gpx' : self.gpx,\
                                    # 'mapview':self.mapwidget,\
                                    # 'timeview':self.timewidget,\
                                    # 'app':wx.GetApp().mainframe,\
                                    # 'sh' :self,\
                                    # 'WxQuery':WxQuery}
        # self.pyshell.Execute('import numpy as np')

    def upd(self):
        msgwrap.message("ValChanged",arg1=self.id)

    def run(self,filename=None):
        if filename!=None and os.path.isfile(filename):
            #self.pyshell.run("execfile('{}')".format(filename))
            self.pyshell.run("exec(open('{}').read())".format(filename))
            if filename not in self.lastscripts and os.path.normpath(self.scriptpath) not in os.path.normpath(filename) :
                self.lastscripts.insert(0,filename)

    def copy(self,string):
        if not wx.TheClipboard.IsOpened():
            clipdata = wx.TextDataObject()
            clipdata.SetText(string)
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(clipdata)
            wx.TheClipboard.Close()

    def clear(self):
        self.pyshell.clear()

    def DetachGpx(self):
        self.gpx=None

    def OnRunButtonClicked(self,event):
        if self.scriptcombo.GetValue().endswith("py"):
            if os.path.exists(self.scriptcombo.GetValue()):
                self.run(self.scriptcombo.GetValue())
                self.lastscript=self.scriptcombo.GetValue()
            else:
                self.run(self.scriptpath+self.scriptcombo.GetValue())
                self.lastscript=os.path.basename(self.scriptcombo.GetValue())
        else:
            dialog = wx.FileDialog(None, "Choose a file", self.scriptpath, "", "python file (*.py)|*.py", wx.OPEN)
            if dialog.ShowModal() == wx.ID_OK:
                self.run(dialog.GetPath())
                self.lastscript=dialog.GetPath()
                self.scriptcombo.SetValue(self.lastscript)

    def OnSigSelChanged(self,arg1,arg2,arg3):
        if arg1==self.id:
            return

    def OnSigValChanged(self,arg1):
        if arg1==self.id:
            return

    def OnSigCurChanged(self, arg1, arg2):
        if arg1==self.id:
            return

    def OnLeftMouseDown(self,event):pass
    def OnLeftMouseUp(self,event):pass
    def OnLeftMouseDblClick(self,event):pass
    def OnMouseMotion(self,event):pass
    def OnMouseEnter(self,event):pass
    def OnMouseLeave(self,event):pass
    def OnRightMouseDown(self,event):pass
    def OnMouseWheel(self,event):pass
    def OnPaint(self,event):pass
    def OnSize(self,event):
        self.pyshell.SetClientSize(self.GetClientSize())

    def OnErase(self,event):pass

class Plugin(WxShell):
    def __init__(self, *args, **kwargs):
       WxShell.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Shell"
