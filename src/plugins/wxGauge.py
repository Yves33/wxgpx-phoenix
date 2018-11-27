#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
## system imports
import os,sys
import inspect
import wx
import wx.lib.newevent
import wx.lib.agw.peakmeter as pm #from agw import peakmeter as pm

import numpy as np
import math

##local imports
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import msgwrap
import gpxobj
from wxquery.wxquery import WxQuery
        
class WxGauge(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        self.key='speed'
        self.gpx=None
        sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.l1=wx.StaticText(self,wx.NewId(),"Value:")
        #self.l2=wx.StaticText(self,wx.NewId(),"Map height:")
        #self.l3=wx.StaticText(self,wx.NewId(),"Current path: empty")
        self.peakmeter = pm.PeakMeterCtrl(self, -1, style=wx.SIMPLE_BORDER, agwStyle=pm.PM_VERTICAL)
        self.peakmeter.SetMaxSize(wx.Size(20,1200))
        self.peakmeter.SetMeterBands(1,20)
        self.peakmeter.SetBandsColour(wx.GREEN,wx.YELLOW,wx.RED)
        self.peakmeter.SetRangeValue(10,20,22)
        self.peakmeter.SetData([12],0,1)
        sizer.Add(self.l1,0,wx.CENTER)
        #sizer.Add(self.l2,0,wx.CENTER)
        #sizer.Add(self.l3,0,wx.CENTER)
        sizer.Add(self.peakmeter,0,wx.CENTER)
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftMouseDblClick)
        
        msgwrap.register(self.OnSigCurChanged, signal="CurChanged")
        msgwrap.register(self.OnSigSelChanged, signal="SelChanged")
        msgwrap.register(self.OnSigValChanged, signal="ValChanged")
            
    def AttachGpx(self,data):
        self.gpx=data
        #high=math.ceil(np.percentile(self.gpx[(self.key,1,1)],90))
        #low=math.ceil(np.percentile(self.gpx[(self.key,1,1)],25))
        #self.peakmeter.SetRangeValue(low,high,math.ceil(self.gpx[(self.key,1,1)].max()))
        #step=int(math.floor(self.gpx[(self.key,1,1)].max()/20))
        #self.peakmeter.SetRangeValue(6*step,15*step,20*step)
        high=math.ceil(np.percentile(self.gpx[(self.key,1,1)],90))
        low=math.ceil(np.percentile(self.gpx[(self.key,1,1)],25))
        self.peakmeter.SetRangeValue(low,high,math.ceil(self.gpx[(self.key,1,1)].max()))
        #self.peakmeter.SetRangeValue(math.ceil(self.gpx[(self.key,1,1)].max()/4),\
        #                             math.ceil(self.gpx[(self.key,1,1)].max()*3/4),
        #                             math.ceil(self.gpx[(self.key,1,1)].max()))

    def DetachGpx(self):
        pass
        
    def OnSigSelChanged(self,arg1,arg2,arg3):
        if arg1==self.id:
            return
        high=math.ceil(np.percentile(self.gpx[(self.key,1,1)],90))
        low=math.ceil(np.percentile(self.gpx[(self.key,1,1)],25))
        self.peakmeter.SetRangeValue(low,high,math.ceil(self.gpx[(self.key,1,1)].max()))
        
    def OnSigValChanged(self,arg1):
        if arg1==self.id:
            return
        high=math.ceil(np.percentile(self.gpx[(self.key,1,1)],90))
        low=math.ceil(np.percentile(self.gpx[(self.key,1,1)],25))
        self.peakmeter.SetRangeValue(low,high,math.ceil(self.gpx[(self.key,1,1)].max()))
            
    def OnSigCurChanged(self, arg1, arg2):
        if arg1==self.id:
            return
        self.peakmeter.SetData([self.gpx[(self.key,1,0)][arg2]],0,1)
        self.l1.SetLabel("{:.2f} {}".format(self.gpx[(self.key,1,0)][arg2],self.gpx.get_unit(self.key)[0]))
        self.current=arg2

    def OnLeftMouseDown(self,event):pass
    def OnLeftMouseUp(self,event):pass
    def OnLeftMouseDblClick(self,event):
        if self.gpx!=None:
            values=[x for x in self.gpx.get_header_names() if x!='time' ]
            (self.key,)=WxQuery("Value to monitor",\
                [
                 ('wxcombo','Choose','|'.join(values),self.key,'str'),
                ])
            high=math.ceil(np.percentile(self.gpx[(self.key,1,1)],90))
            low=math.ceil(np.percentile(self.gpx[(self.key,1,1)],25))
            self.peakmeter.SetRangeValue(low,high,math.ceil(self.gpx[(self.key,1,1)].max()))
            self.peakmeter.SetData([self.gpx[(self.key,1,0)][self.current]],0,1)
            self.l1.SetLabel("{:.2f} {}".format(self.gpx[(self.key,1,0)][self.current],self.gpx.get_unit(self.key)[0]))
        else:
            print(os.path.dirname(os.path.abspath(__file__)))
            self.Screenshot(os.path.dirname(os.path.abspath(__file__))+os.sep+'test.jpg')
            
    def OnMouseMotion(self,event):pass
    def OnMouseEnter(self,event):pass
    def OnMouseLeave(self,event):pass
    def OnRightMouseDown(self,event):return False
    def OnMouseWheel(self,event):pass
    def OnPaint(self,event):pass
    def OnSize(self,event):pass  
    def OnErase(self,event):pass
    
    def Screenshot(self,path):
        def shift(r,p):
            return wx.Rect(r[0]+p[0],r[1]+p[1],r[2],r[3])
            
        context = wx.ClientDC(self)
        memory = wx.MemoryDC()
        pmrect=shift(self.peakmeter.GetClientRect(),self.peakmeter.GetPosition())
        textrect=shift(self.l1.GetClientRect(),self.l1.GetPosition())
        imgrect=pmrect.Union(textrect)
        
        bitmap = wx.EmptyBitmap(imgrect.Width,imgrect.Height,-1)
        memory.SelectObject(bitmap)
        memory.Blit(0,0,imgrect.Width,imgrect.Height,context,imgrect.Left,imgrect.Top)
        memory.SelectObject(wx.NullBitmap)
        bitmap.SaveFile(path,wx.BITMAP_TYPE_JPEG)
    
    
class Plugin(WxGauge):
    def __init__(self, *args, **kwargs):
       WxGauge.__init__(self, *args, **kwargs)  
    
    def GetName(self):
        return "Gauge"
