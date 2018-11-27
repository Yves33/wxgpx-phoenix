#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
## system imports
import os,sys
import inspect
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.dates as dates
import matplotlib.patches as patches
import matplotlib as mpl
import matplotlib.cm as cm

import numpy as np
import ast

import wx

##local imports
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import msgwrap
import gpxobj
from wxquery.wxquery import WxQuery


def ptinrect(l,t,r,b,x,y):
    return (min(l,r) < x <max(l,r)) and (min(b,t)<y<max(b,t))

class WxScatter(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        self.gpxfig = Figure()
        self.ax = self.gpxfig.add_subplot(111,polar=True)
        self.ax.set_theta_zero_location("N")
        self.gpxfig.subplots_adjust(right=0.9,left=0.1)
        # canvas and events
        self.gpxcanvas=FigureCanvas(self,-1,self.gpxfig)
        self.gpxcanvas.mpl_connect('draw_event', self.OnDraw)
        self.gpxcanvas.mpl_connect('scroll_event', self.OnMouseWheel)
        self.gpxcanvas.mpl_connect('button_press_event', self.OnLeftMouseDown)
        self.gpxcanvas.mpl_connect('button_release_event', self.OnLeftMouseUp)
        self.gpxcanvas.mpl_connect('motion_notify_event', self.OnMouseMotion)
        self.gpxcanvas.mpl_connect('resize_event', self.OnSize)
        self.gpxcanvas.mpl_connect('figure_enter_event', self.OnMouseEnter)
        self.gpxcanvas.mpl_connect('figure_leave_event', self.OnMouseLeave)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.gpxcanvas, 1, wx.LEFT|wx.TOP|wx.GROW|wx.EXPAND)
        self.SetSizer(self.sizer)

        msgwrap.register(self.OnSigCurChanged, "CurChanged")
        msgwrap.register(self.OnSigSelChanged, "SelChanged")
        msgwrap.register(self.OnSigValChanged, "ValChanged")
        
        #that code does not work on linux...
        color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
        self.gpxfig.set_facecolor((color.red/255.0, color.green/255.0, color.blue/255.0))
        self.gpxfig.set_edgecolor((color.red/255.0, color.green/255.0, color.blue/255.0))
        self.gpxcanvas.SetBackgroundColour(color)

        #plugin specific initialization
        self.thetasrc='course'
        self.radiussrc='speed'
        self.autoscale=True
        self.grid=False
        self.kwargs={'color':'#0000FF'}
        self.grid=False

    def Plot(self,xrange=None,yrange=None):
        self.ax.cla()
        self.ax.scatter(self.gpx[(self.thetasrc,1,1)]/360*2*np.pi,\
                            self.gpx[(self.radiussrc,1,1)],\
                            c=self.gpx[(self.radiussrc,1,1)],\
                            marker='o',
                            cmap=cm.jet)
        self.ax.set_theta_zero_location("N")
        self.ax.set_theta_direction(-1)
        self.ax.grid(self.grid)
        self.gpxcanvas.draw()
        self.OnSize(None)

    def AttachGpx(self,data):
        self.gpx=data
        self.Plot()
        self.OnSize(None)

    def DetachGpx(self):
        self.gpx=None

    def OnSigSelChanged(self,arg1,arg2,arg3):
        if arg1==self.id:
            return

    def OnSigValChanged(self,arg1):
        if arg1==self.id:
            return
        self.Plot()

    def OnSigCurChanged(self, arg1, arg2):
        if arg1==self.id:
            return

    def OnDraw(self,event):
        pass

    def OnSize(self,event):
        pixels=self.GetClientSize()
        if pixels[0]<20 or pixels[1]<20:
            return
        self.gpxfig.set_size_inches(float(pixels[0])/self.gpxfig.get_dpi(),float(pixels[1])/self.gpxfig.get_dpi())
        self.gpxfig.subplots_adjust(right=0.85,left=0.15,top=0.85,bottom=0.15)

    def OnLeftMouseDown(self,event):
        if event.button==1:
            if event.dblclick:
                try:
                    event.guiEvent.GetEventObject().ReleaseMouse()
                except:
                    pass
                self.OnLeftMouseDblClick(event)
                return

    def OnLeftMouseDblClick(self,event):
        (dummy,xlo,xhi,ylo,yhi,self.autoscale,self.grid,\
        dummy,self.thetasrc,self.radiussrc,extra)=\
            WxQuery("Graph Settings",\
                [('wxnotebook','Axes',None,None,None),
                 ('wxentry','Theta Low',None,self.ax.get_xlim()[0],'float'),
                 ('wxentry','Theta High',None,self.ax.get_xlim()[1],'float'),
                 ('wxentry','Radius Low',None,self.ax.get_ylim()[0],'float'),
                 ('wxentry','Radius High',None,self.ax.get_ylim()[1],'float'),
                 ('wxcheck','Autoscale',None,self.autoscale,'bool'),
                 ('wxcheck','Show Grid',None,self.grid,'bool'),
                 ('wxnotebook','Polar plot',None,None,None),
                 ('wxcombo','Theta',self.XAxisAllowed(),self.thetasrc,'str'),
                 ('wxcombo','Radius',self.XAxisAllowed(),self.radiussrc,'str'),
                 ('wxentry','Extra arguments',None,{},'str')
                ])
        self.kwargs.update(ast.literal_eval(extra))
        if self.autoscale:
            self.Plot()
        else:
            self.Plot((xlo,xhi),(ylo,yhi))

    def OnMouseWheel(self,event):
        scale_factor = 1.2 if event.button=='down' else (1.0/1.2)
        rmin,rmax=self.ax.get_ylim()
        self.ax.set_ylim(rmin*scale_factor, rmax*scale_factor)
        self.gpxcanvas.draw()

    def OnLeftMouseUp(self,event):
        pass

    def OnMouseMotion(self,event):
        pass

    def OnMouseEnter(self,event):
        pass

    def OnMouseLeave(self,event):
        pass

    def XAxisAllowed(self):
        l=''
        for name in self.gpx.get_header_names():
            if name not in ['time','ok'] and name[0]!='_':
                l+='|'+name
        return l[1:]

class Plugin(WxScatter):
    def __init__(self, *args, **kwargs):
       WxScatter.__init__(self, *args, **kwargs)

    def GetName(self):
        return "Polar"
