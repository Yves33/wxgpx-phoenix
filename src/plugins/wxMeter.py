#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
## system imports
import os,sys
import inspect
import math
import wx
import wx.lib.newevent
import wx.lib.agw.speedmeter as sm				#from agw import speedmeter as sm

##local imports
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import msgwrap
import gpxobj
from wxquery.wxquery import WxQuery

class WxMeter(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        self.key='speed'
        self.gpx=None
        self.current=0
        self.size=150
        sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.l1=wx.StaticText(self,wx.NewId(),"Value:")
        self.speedmeter = sm.SpeedMeter(self, agwStyle=sm.SM_DRAW_HAND|sm.SM_DRAW_SECTORS|sm.SM_DRAW_MIDDLE_TEXT|sm.SM_DRAW_SECONDARY_TICKS|sm.SM_ROTATE_TEXT)
        self.speedmeter.SetSpeedBackground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.speedmeter.SetMinSize(wx.Size(self.size,self.size))
        self.speedmeter.SetAngleRange(-math.pi/6, 7*math.pi/6)
        self.speedmeter.SetIntervals(range(0, 201, 20))
        self.speedmeter.SetIntervalColours([wx.BLACK]*10)
        self.speedmeter.SetTicks([str(interval) for interval in range(0, 201, 20)])
        self.speedmeter.SetTicksColour(wx.WHITE)
        self.speedmeter.SetNumberOfSecondaryTicks(5)
        self.speedmeter.SetTicksFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.speedmeter.SetMiddleText("Km/h")
        self.speedmeter.SetMiddleTextColour(wx.WHITE)
        self.speedmeter.SetMiddleTextFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.speedmeter.SetHandColour(wx.Colour(255, 50, 0))
        self.speedmeter.DrawExternalArc(False)
        self.speedmeter.SetSpeedValue(44)
        self.speedmeter.Show()
        sizer.Add(self.l1,0,wx.CENTER)
        sizer.Add(self.speedmeter,0,wx.CENTER|wx.EXPAND)
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftMouseDblClick)
        #custom events
        msgwrap.register(self.OnSigCurChanged, "CurChanged")
        msgwrap.register(self.OnSigSelChanged, "SelChanged")
        msgwrap.register(self.OnSigValChanged, "ValChanged")
            
    def AttachGpx(self,data):
        self.gpx=data
        step=int(math.ceil(self.gpx[(self.key,1,1)].max()/10))
        self.speedmeter.SetIntervals(range(0, step*10+1, step))
        self.speedmeter.SetTicks([str(interval) for interval in range(0, step*10+1, step)])
        self.speedmeter.SetSpeedValue(self.gpx[(self.key,1,1)][0])
        self.speedmeter.SetMiddleText(self.gpx.get_unit(self.key)[0])

    def DetachGpx(self):
        pass
        
    def OnSigSelChanged(self,arg1,arg2,arg3):
        if arg1==self.id:
            return
        step=int(math.ceil(self.gpx[(self.key,1,1)].max()/10))
        self.speedmeter.SetIntervals(range(0, step*10+1, step))
        self.speedmeter.SetTicks([str(interval) for interval in range(0, step*10+1, step)])
        self.speedmeter.SetSpeedValue(self.gpx[(self.key,1,1)][arg2])
        
    def OnSigValChanged(self,arg1):
        if arg1==self.id:
            return
        step=int(math.ceil(self.gpx[(self.key,1,1)].max()/10))
        self.speedmeter.SetIntervals(range(0, step*10+1, step))
        self.speedmeter.SetTicks([str(interval) for interval in range(0, step*10+1, step)])
        #self.speedmeter.SetSpeedValue(self.gpx[(self.key,1,1)][self.current])
        self.speedmeter.SetMiddleText(self.gpx.get_unit(self.key)[0])
            
    def OnSigCurChanged(self, arg1, arg2):
        if arg1==self.id:
            return
        self.speedmeter.SetSpeedValue(self.gpx[(self.key,1,0)][arg2])
        self.l1.SetLabel("{:.2f} {}".format(self.gpx[(self.key,1,0)][arg2],self.gpx.get_unit(self.key)[0]))
        self.current=arg2

    def OnLeftMouseDown(self,event):pass
    def OnLeftMouseUp(self,event):pass
    def OnLeftMouseDblClick(self,event):
        if self.gpx!=None:
            values=[x for x in self.gpx.get_header_names() if x!='time' ]
            (self.key,self.size)=WxQuery("Value to monitor",\
                [
                 ('wxcombo','Choose','|'.join(values),self.key,'str'),
                 ('wxspin','Size','150|300|10',self.size,'int')
                ])
            self.speedmeter.SetMinSize(wx.Size(self.size, self.size))
            self.Layout()
            step=int(math.ceil(self.gpx[(self.key,1,1)].max()/10))
            self.speedmeter.SetIntervals(range(0, step*10+1, step))
            self.speedmeter.SetTicks([str(interval) for interval in range(0, step*10+1, step)])
            self.speedmeter.SetSpeedValue(self.gpx[(self.key,1,0)][self.current])
            self.speedmeter.SetMiddleText(self.gpx.get_unit(self.key)[0])
            self.l1.SetLabel("{:.2f} {}".format(self.gpx[(self.key,1,0)][self.current],self.gpx.get_unit(self.key)[0]))
            
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
        textrect=shift(self.l1.GetClientRect(),self.l1.GetPosition())
        speedrect=wx.Rect(textrect[0]+textrect[2]/2-self.size[0]/2,
                          textrect[1]+textrect[3],
                          self.size[0],
                          self.size[1])
        imgrect=speedrect.Union(textrect)
        
        bitmap = wx.EmptyBitmap(imgrect.Width,imgrect.Height,-1)
        memory.SelectObject(bitmap)
        memory.Blit(0,0,imgrect.Width,imgrect.Height,context,imgrect.Left,imgrect.Top)
        memory.SelectObject(wx.NullBitmap)
        bitmap.SaveFile(path,wx.BITMAP_TYPE_PNG)
    
    
class Plugin(WxMeter):
    def __init__(self, *args, **kwargs):
       WxMeter.__init__(self, *args, **kwargs)  
    
    def GetName(self):
        return "Meter"
