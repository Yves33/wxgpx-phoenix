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

#clever hack to import files from parent directory
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import gpxobj

def ptinrect(l,t,r,b,x,y):
    return (min(l,r) < x <max(l,r)) and (min(b,t)<y<max(b,t))
    
class WxHistogram(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        self.gpxfig = Figure()
        self.ax = self.gpxfig.add_subplot(111)
        self.gpxfig.subplots_adjust(right=0.9,left=0.06)
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
        
        self.dragging=False
        #plugin specific initialization
        self.barsrc='speed'
        self.barbins=50
        self.autoscale=True
        self.grid=False
        self.kwargs={'color':'#0000FF',\
                        'align':'center',\
                        'orientation':'vertical'}
    
    def Plot(self,lo=None,hi=None,bins=50,xrange=None,yrange=None):
        self.lo=min(self.gpx[(self.barsrc,1,1)]) if lo==None else lo
        self.hi=max(self.gpx[(self.barsrc,1,1)]) if hi==None else hi
        hist, bins = np.histogram(self.gpx[(self.barsrc,1,1)],self.barbins,(self.lo,self.hi))
        width = 0.7 * (bins[1] - bins[0])
        center = (bins[:-1] + bins[1:]) / 2
        self.ax.cla()
        self.ax.bar(center, hist, width=width,**self.kwargs)
        self.ax.set_xlabel(self.barsrc+" ("+self.gpx.get_unit(self.barsrc)[0]+")")
        self.ax.set_ylabel('Occurence')
        if xrange!=None:
            self.ax.set_xlim(xrange)
        if yrange!=None:
            self.ax.set_ylim(yrange)
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
        leg=self.ax.xaxis.get_tightbbox(self.gpxcanvas.get_renderer())       
        leg1=self.ax.yaxis.get_tightbbox(self.gpxcanvas.get_renderer())
        bottomalign=(leg.height+15)/pixels[1]
        leftalign=(leg1.width+15)/pixels[0]
        rightalign=(1-(15.0)/pixels[0])
        if (leftalign<rightalign):
            self.gpxfig.subplots_adjust(bottom=bottomalign,left=leftalign,right=rightalign)
            
    def OnLeftMouseDown(self,event):
        if event.button==1:
            if event.dblclick:
                try:
                    event.guiEvent.GetEventObject().ReleaseMouse()
                except:
                    pass
                self.OnLeftMouseDblClick(event)
                return
            else:
                if self.get_axis(event,25)=='bottom' or self.get_axis(event,25)=='left':
                    self.dragging=True
                    (self.x0,self.y0)=(event.xdata,event.ydata)
                
    def OnLeftMouseDblClick(self,event):
        (dummy,xlo,xhi,ylo,yhi,self.autoscale,self.grid,\
        dummy,self.barsrc,self.lo,self.hi,self.barbins,self.kwargs['color'],extra)=\
            WxQuery("Graph Settings",\
                [('wxnotebook','Axes',None,None,None),
                 ('wxentry','X Low',None,self.ax.get_xlim()[0],'float'),
                 ('wxentry','X High',None,self.ax.get_xlim()[1],'float'),
                 ('wxentry','Y Low',None,self.ax.get_ylim()[0],'float'),
                 ('wxentry','Y High',None,self.ax.get_ylim()[1],'float'),
                 ('wxcheck','Autoscale',None,self.autoscale,'bool'),
                 ('wxcheck','Show Grid',None,self.grid,'bool'),
                 ('wxnotebook','Histogram',None,None,None),
                 ('wxcombo','Category',self.XAxisAllowed(),self.barsrc,'str'),
                 ('wxcombo','Start',str(self.lo)+'|'+str(min(self.gpx[(self.barsrc,1,1)])),str(self.lo),'float'),
                 ('wxcombo','End',str(self.hi)+'|'+str(max(self.gpx[(self.barsrc,1,1)])),str(self.hi),'float'),
                 ('wxspin','Number of bars','10|100|1',self.barbins,'int'),
                 ('wxcolor','Color',None,self.kwargs['color'],'str'),
                 ('wxentry','Extra arguments',None,{},'str')
                ])
        self.kwargs.update(ast.literal_eval(extra))
        if self.autoscale:
            self.Plot(self.lo,self.hi,self.barbins)
        else:
            self.Plot(self.lo,self.hi,self.barbins,(xlo,xhi),(ylo,yhi))
            
    def get_axis(self,event,tolerance):
        bbox = self.ax.get_window_extent().transformed(self.gpxfig.dpi_scale_trans.inverted())
        l=bbox.bounds[0]*self.gpxfig.dpi
        b=bbox.bounds[1]*self.gpxfig.dpi
        r=l+bbox.bounds[2]*self.gpxfig.dpi
        t=b+bbox.bounds[3]*self.gpxfig.dpi
        #convert screen coordinates to graph coordinates
        xlo=self.ax.get_xlim()[0]
        xhi=self.ax.get_xlim()[1]
        event.xdata=(event.x-l)/(r-l)*(xhi-xlo)+xlo
        if ptinrect(l-tolerance,t,l,b,event.x,event.y):
            ylo,yhi=self.ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'left'
        if ptinrect(r,t,r+tolerance,b,event.x,event.y):
            ylo,yhi=self.ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'right'
        if ptinrect(l,t,r,t+tolerance,event.x,event.y):
            ylo,yhi=self.ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'top'
        if ptinrect(l,b-tolerance,r,b,event.x,event.y):
            ylo,yhi=self.ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'bottom'
        if ptinrect(l,t,r,b,event.x,event.y):
            ylo,yhi=self.ax.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo       
            return 'main'
    
    def OnMouseWheel(self,event):
        scale_factor = 1.2 if event.button=='down' else (1.0/1.2)
        where=self.get_axis(event,25)
        if where=='bottom':
            xlo,xhi=self.ax.get_xlim()
            nxhi=event.xdata+(scale_factor*(xhi-event.xdata))
            nxlo=event.xdata-(scale_factor*(event.xdata-xlo))
            self.ax.set_xlim([min(nxlo,nxhi),max(nxlo,nxhi)])
        elif where=='left':
            ylo,yhi=self.ax.get_ylim()
            nyhi=event.ydata+(scale_factor*(yhi-event.ydata))
            nylo=event.ydata-(scale_factor*(event.ydata-ylo))
            self.ax.set_ylim([min(nylo,nyhi),max(nylo,nyhi)])
        self.gpxcanvas.draw()
        
    def OnLeftMouseUp(self,event):
        self.dragging=False
        
    def OnMouseMotion(self,event):
        where=self.get_axis(event,25)
        if where=='bottom' or where=='left':
            wx.SetCursor(wx.Cursor(wx.CURSOR_MAGNIFIER))
        else:
            wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        if where=='bottom' and self.dragging:
            dx = event.xdata - self.x0
            self.ax.set_xlim(self.ax.get_xlim()[0]-dx,self.ax.get_xlim()[1]-dx)
        if where=='left' and self.dragging:
            dy = event.ydata - self.y0
            self.ax.set_ylim(self.ax.get_ylim()[0]-dy,self.ax.get_ylim()[1]-dy)
        self.gpxcanvas.draw()
        
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
        
class Plugin(WxHistogram):
    def __init__(self, *args, **kwargs):
       WxHistogram.__init__(self, *args, **kwargs)  
    
    def GetName(self):
        return "Histogram"
