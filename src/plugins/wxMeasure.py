#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
## system imports
import os,sys
import inspect
import wx
import wx.grid
import wx.lib.newevent

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
    from ctypes import *
    hasOpenGL = True
except ImportError:
    hasOpenGL = False

## local modules imports 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import msgwrap
import gpxobj
from wxmappanel.wxmappanel import WxMapBase,WxMapLayer,WxToolLayer,WxMapButton,WxMapImage,WxPathLayer,PixelsToLatLon,Haversine
from wxquery.wxquery import WxQuery

class wxMeasureMapLayer(WxPathLayer):
    def __init__(self,parent,name="Measure layer"):
        WxPathLayer.__init__(self,parent,name)
        self.SetActive(False)
        
    def RegisterPanel(self,panel):
        self.panel=panel
        
    def DrawOffscreen(self,dc):
        def myformat(d):
            if d>999.99:
                return "{:.2f}".format(d/1000)+" km"
            else:
                return "{:.2f}".format(d)+" m"
        self.SetPointWidth(5.0)        
        #super(wxMeasureMapLayer, self).DrawOffscreen(dc)
        WxPathLayer.DrawOffscreen(self,dc)
        width,height=self.parent.GetClientSize()
        self.panel.widthlabel.SetLabel("Map width:   "+myformat(width*self.parent.pixelscale))
        self.panel.heightlabel.SetLabel("Map height:   "+myformat(height*self.parent.pixelscale))
        self.panel.osdlabel.SetLabel("Current path: "+myformat(self.GetPathLength()))
        if len(self.path)>1:
            info=''
            info+="As the crow flies:"
            info+="\nDistance: "+myformat(Haversine(self.path[0][0],self.path[0][1],
                                                    self.path[-1][0],self.path[-1][1])[0])
            info+="\nCourse: "+ str(Haversine(self.path[0][0],self.path[0][1],
                                         self.path[-1][0],self.path[-1][1])[1]) + " deg"
            info+='\n--------------'
            info+='\nIndividual segments'
            for idx in range(0,len(self.path)-1):
                info+="\nDistance: "+myformat(Haversine(self.path[idx][0],self.path[idx][1],
                                                    self.path[idx+1][0],self.path[idx+1][1])[0])
                info+="\tCourse: "+str(Haversine(self.path[idx][0],self.path[idx][1],
                                             self.path[idx+1][0],self.path[idx+1][1])[1]) + " deg"
            self.panel.text.Clear()
            self.panel.text.AppendText(info)
    
    def OnLeftMouseDblClick(self, event):
        for l in self.parent.layers:
            print(l.name,l.active)
            
#meas64='''iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAv0lEQVR4nL3SIU4DURDG8V83lZWIKoqpINyhSMoBGlQ1pgfgEEgUkhMUiWiKaIJidUlISJHUVFVU8Cq6LyBYYN8m/ZLJTCb5T76ZDDXV+KGX4QLnOMIKM9xg/deADLc4xgfa+MQ7usgxwqbM0RXu8YQhOjjDI0IRd7+tlOMZp996h1gU8BInZfABJnhIgaGFOV7sblEJjppijOsUGPp49XWwSjA08ZYKR/WKIUnw/hVfOSTyl7EIGPwzx4BQ28EWbl45TMMjvg0AAAAASUVORK5CYII='''
meas64='''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'''

class WxMeasure(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.widthlabel=wx.StaticText(self,wx.NewId(),"Map width:")
        self.heightlabel=wx.StaticText(self,wx.NewId(),"Map height:")
        self.osdlabel=wx.StaticText(self,wx.NewId(),"Current path: empty")
        self.moreinfolabel=wx.StaticText(self,wx.NewId(),"More informations:")
        sizer.Add(self.widthlabel,0,wx.TOP)
        sizer.Add(self.heightlabel,0,wx.TOP)
        sizer.Add(self.osdlabel,0,wx.TOP)
        sizer.Add(self.moreinfolabel,0,wx.TOP)
        self.text=wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH2,size=(-1, 1200))
        sizer.Add(self.text,0,wx.TOP|wx.EXPAND)
        self.measurelayer=wxMeasureMapLayer(self.mapwidget)
        self.mapwidget.AppendLayer(self.measurelayer)
        self.measurelayer.RegisterPanel(self)
        self.mapwidget.GetNamedLayer("Gpx tools").AppendTool(WxMapButton("Measure",WxMapImage.FromBase64(meas64),self.measurelayer.SetActive))
        #custom events
        msgwrap.register(self.OnSigCurChanged, "CurChanged")
        msgwrap.register(self.OnSigSelChanged, "SelChanged")
        msgwrap.register(self.OnSigValChanged, "ValChanged")
                            
    def AttachGpx(self,data):
        pass
        
    def DetachGpx(self):
        pass
        
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
    def OnRightMouseDown(self,event):return False
    def OnMouseWheel(self,event):pass
    def OnPaint(self,event):pass
    def OnSize(self,event):pass
    def OnErase(self,event):pass
       
class Plugin(WxMeasure):
    def __init__(self, *args, **kwargs):
       WxMeasure.__init__(self, *args, **kwargs)  
    
    def GetName(self):
        return "Measure"
