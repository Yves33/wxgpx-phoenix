#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
## system imports
import os,sys
import inspect
import wx
import wx.html2
import wx.lib.newevent

##local imports
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import msgwrap
import gpxobj
from wxquery.wxquery import WxQuery

class WxHelp(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.html=wx.html2.WebView.New(self)
        if not getattr(sys,"frozen",False):
            self.html.LoadURL("file:///"+os.path.dirname(os.path.abspath(__file__) ) +"/../docs/Readme.html")
        else:
            self.html.LoadURL("file:///"+os.path.dirname(sys.executable)+os.sep+"docs/Readme.html")
        sizer.Add(self.html,wx.CENTER|wx.EXPAND)
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
        self.Bind(wx.EVT_SIZE,self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND,self.OnErase)
        #custom events
        msgwrap.register(self.OnSigCurChanged, "CurChanged")
        msgwrap.register(self.OnSigSelChanged, "SelChanged")
        msgwrap.register(self.OnSigValChanged, "ValChanged")
        
    def AttachGpx(self,data):
        self.gpx=data

    def DetachGpx(self):
        self.gpx=None

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
        self.html.SetClientSize(self.GetClientSize())

    def OnErase(self,event):pass

class Plugin(WxHelp):
    def __init__(self, *args, **kwargs):
       WxHelp.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Help"
