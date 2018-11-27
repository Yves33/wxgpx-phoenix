##!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
## system imports
import os,sys
import inspect
import wx
import wx.lib.newevent

import numpy as np
import datetime

## local imports
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import msgwrap
import gpxobj
      
class WxStatistics(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.text=wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.text.AppendText("Statistics:\n")
        sizer.Add(self.text,wx.CENTER|wx.EXPAND)
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
                
    def Statistics(self):
        #todo: return if no point is selected
        if len(np.where(self.gpx['ok']==True))==0:
            return
        self.text.Clear()
        self.text.AppendText("Statistics:\n")
        # distance
        # we use unscaled deltaxy and we scale later with 'distance' scale, which may differ from deltaxy
        self.text.AppendText("Distance: ")
        distance=self.gpx.get_scale('distance')*np.sum(self.gpx[('deltaxy',0,1)])
        self.text.AppendText(str(distance))
        self.text.AppendText(" "+self.gpx.get_unit('distance')[0]+"\n")
        # average and max speed
        self.text.AppendText("Average Speed: "+str(self.gpx.nanmean(self.gpx[('speed',1,1)]))+" "+self.gpx.get_unit('speed')[0]+"\n")
        self.text.AppendText("Max Speed: "+str(self.gpx[('speed',1,1)].max())+" "+self.gpx.get_unit('speed')[0]+"\n")
        # duration
        total=np.sum(self.gpx[('deltat',0,1)])
        self.text.AppendText("Total Time: "+str(datetime.timedelta(seconds=total))+" - ("+str(total)+" s)\n")
        # todo: calculate 5xbest 5 s;5xbest 10s; 5xbest 30
        self.text.AppendText("Best 5 measure average (" +self.gpx.get_unit('speed')[0]+"):\n")
        a=(1.0)*np.convolve(self.gpx[('speed',1,0)], np.ones((5,))/5)[(5-1):]
        # a[a.argsort()[-10:]] will give you the last ten values after sorting the array
        # we need to modify it to retrieve only valid value
        b=a[np.where(self.gpx['ok'])]
        #top5=b[b[np.where(self.gpx['ok']==True)].argsort()[-5:]]
        top5=b[b.argsort()[-5::]]
        for idx in range(0,len(top5)):
            self.text.AppendText("\t"+str(top5[idx])+"\n")
        ## todo: calculate total vertical drop
        ## due to massive inaccuracy in gps elevation measurments
        ## this calculation has been removed!
        #if self.gpx.has_field('ele'):
        #    deltaz=np.ediff1d(self.gpx['ele'],to_begin=0)
        #    a=(1.0)*np.convolve(deltaz, np.ones((215,))/215)[(215-1):]
        #    b=a[np.where(self.gpx['ok'])]
        #    self.text.AppendText( "Vertical drop (ascending): " +str(np.sum(b[np.where(b>0)])) +"\n"  )
        #    self.text.AppendText( "Vertical drop (descending): "+str(np.sum(b[np.where(b<0)])) +"\n"  )
       
        self.Refresh()
        
    def AttachGpx(self,data):
        self.gpx=data
        self.Statistics()
        
    def DetachGpx(self):
        self.gpx=None
        self.text.Clear()
        
    def OnSigSelChanged(self,arg1,arg2,arg3):
        if arg1==self.id:
            return
        
    def OnSigValChanged(self,arg1):
        if arg1==self.id:
            return
        self.Statistics()
            
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
        self.text.SetClientSize(self.GetClientSize())
        
    def OnErase(self,event):pass
       
class Plugin(WxStatistics):
    def __init__(self, *args, **kwargs):
       WxStatistics.__init__(self, *args, **kwargs)  
    
    def GetName(self):
        return "Stats"
