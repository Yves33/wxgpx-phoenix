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
from wxmappanel.wxmappanel import WxMapBase,WxMapLayer,WxToolLayer,WxMapButton,WxMapImage,PixelsToLatLon
from wxquery.wxquery import WxQuery

# small utilities functions for line intesection
def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

# Return true if line segments AB and CD intersect
def intersect(A,B,C,D):
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
            
class wxWaypointLayer(WxMapLayer):
    def __init__(self,parent,name):
        WxMapLayer.__init__(self,parent,name)
        self.x1,self.y1=(0,0)
        self.x2,self.y2=(0,0)
        self.doors=[]
        self.mousedown=False
        self.active=False
        self.linecolor=(1.0,1.0,1.0,1.0)
        self.fillcolor=(1.0,1.0,1.0,1.0)
        self.linewidth=2.0
        self.pointwidth=3.0
            
    def RegisterPanel(self,panel):
        self.panel=panel
    
    def AttachGpx(self,gpx):
        pass
    
    def DetachGpx(self):
        pass
        
    def DrawOffscreen(self,dc):
        pass
            
    def DrawOnscreen(self,dc):
        pen=self.parent.renderer
        pen.SetLineWidth(self.linewidth)
        pen.SetPenColor(*self.linecolor)
        pen.SetBrushColor(*self.fillcolor)
        pen.SetFont('HELVETICA12')
        for idx in range(0,len(self.doors)):
            (x1,y1)=self.parent.GeoToScreen(self.doors[idx][0],self.doors[idx][1])
            (x2,y2)=self.parent.GeoToScreen(self.doors[idx][2],self.doors[idx][3])
            pen.Circle(x1,y1,self.pointwidth)
            pen.Circle(x2,y2,self.pointwidth)
            pen.Line(x1,y1,x2,y2)
            pen.Text(str(idx),x1-10,y1-10)
        if self.mousedown:
            pen.Line(self.x1,self.y1,self.x2,self.y2)
                
    def OnLeftMouseDown(self,event):
        if self.active:
            (self.x1,self.y1)=(event.GetX(),event.GetY())
            (self.x2,self.y2)=(event.GetX(),event.GetY())
            self.mousedown=True
            self.parent.Draw(False)
            self.parent.Refresh()
            return True
        else:
            return False
        
    def OnMouseMotion(self,event):
        if self.active:
            if self.mousedown:
                (self.x2,self.y2)=(event.GetX(),event.GetY())
                self.parent.Draw(False)
                self.parent.Refresh()
                return True
        return False
        
    def OnLeftMouseUp(self,event):
        if self.active:
            if self.mousedown:
                self.mousedown=False
                (self.x2,self.y2)=(event.GetX(),event.GetY())
                (lat1,lon1)=self.parent.ScreenToGeo(self.x1,self.y1)
                (lat2,lon2)=self.parent.ScreenToGeo(self.x2,self.y2)
                self.doors.append((lat1,lon1,lat2,lon2))
                self.CopyWaypointsToPanel()
                self.parent.Draw(False)
                self.parent.Refresh()
                return True
        return False
    
    def OnRightMouseDown(self,event):
        if self.active:
            for idx in range(0,len(self.doors)):
                (x1,y1)=self.parent.GeoToScreen(self.doors[idx][0],self.doors[idx][1])
                (x2,y2)=self.parent.GeoToScreen(self.doors[idx][2],self.doors[idx][3])
                (x,y)=event.GetX(),event.GetY()
                if (x-x1)**2+(y-y1)**2<12 or (x-x2)**2+(y-y2)**2<self.pointwidth**2:
                    del self.doors[idx]
                    self.CopyWaypointsToPanel()
                    self.parent.Draw(False)
                    self.parent.Refresh()
                    return True
        return False
    
    def CopyWaypointsToPanel(self):
        textbuffer=""
        for d in range(0, len(self.doors)):
            textbuffer=textbuffer+"\n"+",".join(map(str,self.doors[d]))
        self.panel.waypointsTE.SetValue(textbuffer)
        self.panel.osdlabel.SetLabel("Number of doors: "+str(len(self.doors)))
    
class SimpleGrid(wx.grid.Grid):
    def __init__(self, parent):
        wx.grid.Grid.__init__(self, parent, -1)
        self.CreateGrid(10, 1)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.ascend=False
        self.data=[]
        self.headers=[]
        self.SetRowLabelSize(32)
    
    def OnSize(self,event):
        for col in range(7):
            if (event.Size[0]-32.0)/(7.0)>0:
                self.SetColSize(col, (event.Size[0]-32.0)/(7.0))
        self.Centre( wx.HORIZONTAL )
        
    def SetHeaders(self,headers):
        self.headers=headers
        while self.GetNumberCols()<len(headers):
            self.AppendCols(1)
        for c in range(0,len(headers)):
            self.SetColLabelValue(c, headers[c])
        self.AutoSize()

    def SetData(self,data):
        self.data=data
        self.ClearGrid()
        while self.GetNumberRows()<len(data):
            self.AppendRows(1)
        for r in range(0,len(data)):
            for c in range (0, len(data[r])):
                self.SetCellValue(r, c, str(data[r][c]))
        self.AutoSize()
        
    def OnLabelRightClick(self,event):
        if event.GetCol()>=0:
            col=event.GetCol()
            data=sorted(self.data, key=lambda k:(k[col]), reverse=self.ascend)
            self.SetData(data)
            self.ascend= not self.ascend
        
    def OnCellRightClick(self,event):
        menu = wx.Menu()
        item = wx.MenuItem(menu, wx.NewId(),"Copy Table")
        self.Bind(wx.EVT_MENU, self.CopyAll, item)
        menu.AppendItem(item)
        self.PopupMenu(menu)
        menu.Destroy()

    def CopyAll(self,event):
        buffer=""
        buffer+="\t".join(self.headers)+"\n"
        for r in range(0,len(self.data)):
            buffer+="\t".join(map(str,self.data[r]))+"\n"
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(wx.TextDataObject(buffer))
        wx.TheClipboard.Close()

#flag64='''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'''
flag64='''iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAABH5JREFUeNrsV11oHFUU/u7dn9ls/k1tQkTWNGqIbX0QsSmCCj6mtOiDIASKQWjzoH0s1ScFwTcJFaEihbwIvhRpFV802AqpVZtiQ2lCQ5sfE7tL/vZndnd2duZ67ty7djbZJBMk9aUXDnfmzplzvvOdc8+dYUIIyMEYC4+83/dtiKOf7mAL9t07w2Nv0KMydmlI32HffR1nov/g0X5Mj/8B+6+lI3KNJHf9ZO9LUS6OhYU4FGKij7luXJtQE+NwGP85XWZnDn05ee3Bg+2HH0CMIMF1HBIXHa6F8Xd7vmiMYsDY24544lnUd/fCeKILbE8HEKJXuZZ8GvnxK6/FRi9enXpv/9Wes7deqcEcvzH03PGmWPh892c3DbovrQfAKrhdmg84Oew5dnTAePJpsJa9pL4GZO4Ci5PATIoAMMBZBtoO0JsG4u2dSAydxvSnpw+TCclQRtq8fqL3xSh3B2NMnKx/qgt2Zk26qK8F4N/hEhKHUMQSncDtEcCcJ2dFSkgDYJDtKElMzjGKfhGw8kDyEvDyMIRdxp2hZ9KSTZljo7MDTfu60fzCq2Dt+7Bw7iPpIlIrBesKRFOxMEbxtJFjAh0i5nhECQsp8dKg17JzcMsOej7/BiiaFCMFadtAgaKevUx24hCOvWkNVGWDtgUZyCoHnjOu1j2ppU/PrRwBp3n6AjFGa+YKsEJpS/5JpUzXbQdJ1wkCQBuVADzHQQbpl00FeOkGXZMjM6OYCNUp9qQ9t3qDbG69wsCmUdfQt7M0cdpF8KUmrIKQLJYyXoUFA+AxkNH0BmSgZHrOhO0oQOsBWmkodNsC8NUAY8FTYOfUbi451awxzaJNAQlnBwxY2WD0V1gq5Txnjqx8ViNFRQkgSAqYL6KA/lURKgCi7GwS0NoGAOGtizCtMbJqZxXheJAiVgHM4G5goJJSYsDdURFqBhhtHS4UXCkRWozSq9GQmiMkdIzKXaAAlGukTjOAgAx4gdlpr+cLhyO/YsDMhWGXBPLLstiyXruMNEVhtEbQ3OIiXmfSJmhWuwCoLmCPoTSYW7c9AC9oijq/Wo/lbAesooGZtcKVubQ5+dtC7ua531NTlSO3vSESO9XXcfit/W0f8lAjuOS0TAxwpvgNSZHsucgnDepPoWAA5Mu/3nl89JNf5s+P3k0vyO8CEtrooJMHluaSJXN2+IMf5+eO9LYMNEV5QqWYGIgSc7YLizpwZjFGnbgRq3lnZiJlfu3vxzUACAIt8BMaMDgydoYWktppSUtZi/DVUeH5sxNvDvcn3n69u3kwdTv2WPLWPTpRYS0XnMmplcK1jy8vXJpZtZZINyX1t2UgrOzfJ/l7ncONp7dXEJg99f3sVzRf0F9SmgrPWUbryECKmsGtAXDlTyrbATqB1FnVDlK+897V4C3NnrPVJ9l/Ha6OtrCTlzj+5/EIwCMAfOOxHvQLaFcAkHs61Rg1dMYeDoqqPsDJ8cTFHzwWGH84AJjv77iVpi6SVv1MdrZ7et61v2M/gKj+Z4v42qtZ+YfbLQD/CDAAe8bDoMG2OE4AAAAASUVORK5CYII='''
        
class WxWaypoints(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        self.gpx=None
        self.waypoints=[]
        self.disableoutside=True
        self.results=[]
        sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.osdlabel=wx.StaticText(self,wx.NewId(),"Number or doors: 0")
        self.waypointsTE=wx.TextCtrl(self, -1,"",style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER|wx.TE_DONTWRAP,size=(200,75))
        self.analysebutton=wx.Button(self,-1,"Analyse")
        self.resultsgrid=SimpleGrid(self)
        self.resultsgrid.SetHeaders(['lap','start','stop','duration','distance','avg speed','top speed'])
        sizer.Add(self.osdlabel,0,wx.TOP)
        sizer.Add(self.waypointsTE,0,wx.TOP|wx.ALL|wx.CENTER|wx.EXPAND)
        sizer.Add(self.analysebutton,0,wx.TOP|wx.CENTER)
        sizer.Add(wx.StaticText(self,wx.NewId(),"Results:"),0,wx.TOP)
        sizer.Add(self.resultsgrid,0,wx.TOP|wx.ALL|wx.CENTER|wx.EXPAND)
        self.waypointslayer=wxWaypointLayer(self.mapwidget,"Waypoints layer")
        self.mapwidget.AppendLayer(self.waypointslayer)
        self.waypointslayer.RegisterPanel(self)
        self.mapwidget.GetNamedLayer("Gpx tools").AppendTool(WxMapButton("Waypoints",WxMapImage.FromBase64(flag64),self.waypointslayer.SetActive))
        self.waypointsTE.Bind(wx.EVT_TEXT_ENTER,self.OnTextEnter)
        self.waypointsTE.Bind(wx.EVT_KEY_DOWN,self.OnTextKeydown)
        self.analysebutton.Bind(wx.EVT_BUTTON, self.OnAnalyseButton)
        #custom events
        msgwrap.register(self.OnSigCurChanged, "CurChanged")
        msgwrap.register(self.OnSigSelChanged, "SelChanged")
        msgwrap.register(self.OnSigValChanged, "ValChanged")
                    
    def AttachGpx(self,data):
        self.gpx=data
        
    def DetachGpx(self):
        pass

    #not working on osx wx.TE_PROCESS_ENTER is ignored. a workaround is proposed below
    def OnTextEnter(self,event):
        textbuffer=self.waypointsTE.GetValue()
        self.waypointslayer.doors=[]
        for line in textbuffer.split("\n"):
            try:
                self.waypointslayer.doors.append(tuple(map(float,line.split(","))))
            except:
                pass
        self.osdlabel.SetLabel("Number of doors: "+str(len(textbuffer.split("\n"))))
        self.mapwidget.Draw()
        self.mapwidget.Refresh()
    
    #workaround for wx.TE_PROCESS_ENTER not working on osx
    def OnTextKeydown(self,event):
        if event.GetKeyCode()==wx.WXK_RETURN:
            self.OnTextEnter(event)
        event.Skip()

    def OnAnalyseButton(self,event):
        doorliststr=','.join(str(e) for e in range(0,len(self.waypointslayer.doors)))
        (waypointsstr,disableoutside)=WxQuery('Comma separated list of doors',\
                    [('wxentry','WayPoints',None,doorliststr,'str'),\
                     ('wxcheck','Disable invalid points',None,self.disableoutside,'bool')])
        self.waypoints=map(int, waypointsstr.split(','))
        self.disableoutside=disableoutside
        self.Analyse()
        
    def Analyse(self):
        # remove any unkown door number
        self.waypoints=[w for w in self.waypoints if ((w<len(self.waypointslayer.doors)) and (w>=0))]
        #now calculate all intersections with these doors...
        if self.gpx!=None and len(self.waypoints)>0:
            sect_door=[]
            sect_idx=[]
            segments=[]
            for p in xrange(1,self.gpx.get_row_count()):
                for d in xrange(0,len(self.waypointslayer.doors)):
                    d1=(self.waypointslayer.doors[d][0],self.waypointslayer.doors[d][1])
                    d2=(self.waypointslayer.doors[d][2],self.waypointslayer.doors[d][3])
                    p1=(self.gpx['lat'][p-1],self.gpx['lon'][p-1])
                    p2=(self.gpx['lat'][p],self.gpx['lon'][p])
                    if intersect(p1,p2,d1,d2) or intersect(p1,p2,d2,d1) or intersect(p2,p1,d2,d1) or intersect(p2,p1,d2,d1):
                        sect_door.append(d)
                        sect_idx.append(p)
            #then find the right sequences...
            for d in xrange(0,len(sect_door)):
                if sect_door[d:d+len(self.waypoints)]==self.waypoints:
                    if np.all( self.gpx['ok'][sect_idx[d]-1:sect_idx[d+len(self.waypoints)-1]+1] ):
                        segments.append((sect_idx[d]-1,sect_idx[d+len(self.waypoints)-1]+1))
            if self.disableoutside:
                self.gpx['ok'][0:self.gpx.get_last_row_idx()+1]=False
                for s in segments:
                    self.gpx['ok'][s[0]:s[1]]=True
                msgwrap.message("ValChanged",arg1=self.id)
            data=[]
            lap=0
            for s in segments:
                lap+=1
                #['lap','start','stop','duration','distance','avg speed','top speed']
                data.append([lap,\
                            self.gpx['time'][s[0]][11:19],\
                            self.gpx['time'][s[1]][11:19],\
                            np.sum(self.gpx['deltat'][s[0]:s[1]]), \
                            np.sum(self.gpx['deltaxy'][s[0]:s[1]]), 
                            np.sum(self.gpx['deltaxy'][s[0]:s[1]])/np.sum(self.gpx['deltat'][s[0]:s[1]])*self.gpx.get_scale('speed'),\
                            self.gpx[('speed',1)][s[0]:s[1]].max()])
            self.resultsgrid.SetData(data)
            w,h=self.GetSize()
            self.SetSize((w+1,h))
            self.SetSize((w,h))
            
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
       
class Plugin(WxWaypoints):
    def __init__(self, *args, **kwargs):
       WxWaypoints.__init__(self, *args, **kwargs)  
    
    def GetName(self):
        return "Waypoints"
