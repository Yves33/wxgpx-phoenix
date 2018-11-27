#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-#
import os,sys
import numpy as np
import math
try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
    from ctypes import *
    hasOpenGL = True
except ImportError:
    hasOpenGL = False

import wx
import wx.aui
import wx.adv

sys.path.append(os.path.dirname(os.path.abspath(__file__) ) +"/modules/")
from wxquery.wxquery import WxQuery
import msgwrap
from wxmappanel.wxmappanel import WxMapBase,WxMapLayer,WxToolLayer,WxMapButton,WxMapImage,MetersToPixels,PixelsToMeters
import gpxobj


def FloatToRGB(f):
    cmap=1
    if cmap==0:
        cx=0.2
        blue = min((max((4*((1-cx)-f), 0.)), 1.))
        red  = min((max((4*(f-cx), 0.)), 1.))
        green= min((max((4*math.fabs(f-0.5)-1., 0.)), 1.))
        return (int(red*255), int(green*255), int(blue*255))
    elif cmap==1:
        a=(1-f)/0.25
        X=math.floor(a)
        Y=math.floor(255*(a-X))
        if X==0:(red,green,blue)=(255,Y,0)
        elif X==1:(red,green,blue)=(255-Y,255,0)
        elif X==2:(red,green,blue)=(0,255,Y)
        elif X==3:(red,green,blue)=(0,255-Y,255)
        elif X==4:(red,green,blue)=(0,0,255)
        else:(red,green,blue)=(0,0,0)
        return (int(red), int(green), int(blue))
    elif cmap==2:
        a=(1-f)/0.2
        X=math.floor(a)
        Y=math.floor(255*(a-X))
        if X==0:(red,green,blue)=(255,Y,0)
        elif X==1:(red,green,blue)=(255-Y,255,0)
        elif X==2:(red,green,blue)=(0,255,Y)
        elif X==3:(red,green,blue)=(0,255-Y,255)
        elif X==4:(red,green,blue)=(Y,0,255)
        elif X==5:(red,green,blue)=(255,0,255)
        return (int(red), int(green), int(blue))
    elif cmap==3:
        a=(1-f)
        Y=math.floor(255*a)
        return(255,Y,0)

class GpxMapLayer(WxMapLayer):
    # there's a bug in XP (at least) that randomly generates a line staring from topletft and stopping at mouse
    def __init__(self, *args, **kwargs):
        WxMapLayer.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        self.name="Gpx layer"
        self.gpx=None
        self.current_x=0
        self.current_y=0
        self.current=0
        self.trackcolorkey='speed'
        self.trackcolordefault=(1.0,0.0,0.0,1.0)
        self.currentcolor=(0.0,1.0,0.0,1.0)
        self.currentmagkey='speed'
        self.currentthetakey='course'
        self.currentindic='Arrowhead'
        self.currentzoom=25
        self.linewidth=2.0
        msgwrap.register(self.OnSigCurChanged, "CurChanged")
        msgwrap.register(self.OnSigSelChanged, "SelChanged")
        msgwrap.register(self.OnSigValChanged, "ValChanged")

    def AttachGpx(self,data):
        self.gpx=data
        self._gpx=np.ones(self.gpx.get_row_count(),dtype={'names':['_x','_y','_r','_g','_b','_d'],'formats':['int','int','int','int','int','float']})
        if self.gpx.has_field('speed'):
            self.BuildColorTable(self.trackcolorkey)
        else:
            self._gpx['_r']=255
            self._gpx['_g']=0
            self._gpx['_b']=0
        self.parent.EncloseGeoBbox(self.gpx.d['lat'].min(),self.gpx.d['lon'].min(),self.gpx.d['lat'].max(),self.gpx.d['lon'].max())
        self.parent.Draw()
        self.parent.Refresh()

    def DetachGpx(self):
        self.gpx=None
        self._gpx=None

    def DrawOffscreen(self,dc):
        if self.gpx==None:
            return
        self.NPLatLonToScreen()
        self.bufferdata=np.dstack((self._gpx['_x'],self._gpx['_y'], \
                                        self._gpx['_r']/255.0,self._gpx['_g']/255.0,self._gpx['_b']/255.0,
                                        self.gpx['ok']*1.0)).flatten()
        pen=self.parent.renderer
        pen.SetLineWidth(self.linewidth)
        pen.RGBALines(self.bufferdata)

    def DrawOnscreen(self,dc):
        if self.currentindic=='Dot':
            self.DrawDot(dc)
        if self.currentindic=='Arrowhead':
            self.DrawArrowhead(dc)
        if self.currentindic=='Vector from':
            self.DrawVector(dc,False)
        if self.currentindic=='Vector to':
            self.DrawVector(dc,True)

    def DrawDot(self,dc):
        pen=self.parent.renderer
        pen.SetLineWidth(1)
        pen.SetPenColor(*self.currentcolor)
        pen.SetBrushColor(*self.currentcolor)
        if self.gpx!=None:
            pen.Circle(self.current_x, self.current_y,5)

    def DrawArrowhead(self,dc):
        pen=self.parent.renderer
        pen.SetLineWidth(1)
        pen.SetPenColor(*self.currentcolor)
        pen.SetBrushColor(*self.currentcolor)
        if self.gpx!=None:
            #sf=1+self.gpx[self.trackcolorkey][self.current]/(self.gpx[self.trackcolorkey].max()-self.gpx[self.trackcolorkey].min())
            sf=1.0
            deg=self.gpx['course'][self.current]*0.01745329251
            cosf=math.cos(deg)
            sinf=math.sin(deg)
            rt=lambda x,y:[x*cosf-y*sinf+self.current_x,y*cosf+x*sinf+self.current_y]
            pen.Polygon(rt(0,-12*sf)+rt(-4*sf,0*sf)+rt(4*sf,0*sf))

    def DrawVector(self,dc,back=False):
        pen=self.parent.renderer
        pen.SetLineWidth(1)
        pen.SetPenColor(*self.currentcolor)
        pen.SetBrushColor(*self.currentcolor)
        if self.gpx!=None:
            deg=self.gpx[self.currentthetakey][self.current]*0.01745329251
            mag=1+(self.gpx[self.currentmagkey][self.current]-self.gpx[self.currentmagkey].min())/(self.gpx[self.currentmagkey].max()-self.gpx[self.currentmagkey].min())
            sf=1.0       # of sf=mag if you also want the arrowhead to sclae
            mag=self.currentzoom/2+(mag-1)*self.currentzoom
            cosf=math.cos(deg)
            sinf=math.sin(deg)
            rt=lambda x,y:[x*cosf-y*sinf+self.current_x,y*cosf+x*sinf+self.current_y]
            if not back:
                pen.Line(*(rt(0,0)+rt(0,(-8-mag))))
                pen.Polygon(rt(0,(-12*sf-mag))+\
                        rt(-4*sf,(0*sf-mag))+\
                        rt(4*sf,(0*sf-mag)))
            else:
                pen.Line(*(rt(0,0)+rt(0,(+8+mag))))
                pen.Polygon(rt(0,(0*sf))+\
                        rt(-4*sf,(12*sf))+\
                        rt(4*sf,(12*sf)))

    def OnMouseMotion(self,event):
        #if not self.active:
        #    return False
        if not self.parent.dragging:
            if self.gpx!=None:
                self._gpx['_d']=np.power((self._gpx['_x']-event.GetX()),2)+np.power((self._gpx['_y']-event.GetY()),2)
                #i=np.argmin(self.gpx[('_d',0,1)])
                #idx=self.gpx[('idx',0,1)][i]
                i=np.argmin(self._gpx['_d'][np.where(self.gpx['ok']==True)])
                idx=self.gpx['idx'][np.where(self.gpx['ok']==True)][i]
                self.current=idx
                self.current_x=self._gpx['_x'][idx]
                self.current_y=self._gpx['_y'][idx]
                msgwrap.message("CurChanged",arg1=self.id,arg2=idx)
                self.parent.Draw(False)
                self.parent.Refresh()
                return False                # let other layer process this event

    def BuildColorTable(self,meas):
        if meas not in self.gpx.get_header_names():
            #build palette from provided color
            self._gpx['_r']=self.trackcolordefault[0]*255
            self._gpx['_g']=self.trackcolordefault[1]*255
            self._gpx['_b']=self.trackcolordefault[2]*255
            return
        cmin=self.gpx[meas].min()
        crange=self.gpx[meas].max()-cmin
        ## wxPython /matplotlib version
        #import matplotlib.cm as cm
        #import matplotlib.pyplot as plt
        #palette = plt.get_cmap('jet')
        #for idx in range(0,len(self.gpx[meas])-1):
            #value=(float(self.gpx[meas][idx]-cmin)/crange)
            #self._gpx['_r'][idx]= int(255*palette(value)[0])
            #self._gpx['_g'][idx]= int(255*palette(value)[1])
            #self._gpx['_b'][idx]= int(255*palette(value)[2])
        ## wxPython without matplotlib
        for idx in range(0,len(self.gpx[meas])-1):
            value=(float(self.gpx[meas][idx]-cmin)/crange)
            self._gpx['_r'][idx]= FloatToRGB(value)[0]
            self._gpx['_g'][idx]= FloatToRGB(value)[1]
            self._gpx['_b'][idx]= FloatToRGB(value)[2]

    def NPLatLonToScreen(self):
        if self.gpx==None:
            return
        zoom=self.parent.zoom
        left=self.parent.left
        top=self.parent.top
        #oshift=2 * math.pi * 6378137 / 2.0
        #res=(2*math.pi*6378137)/ (256*2**zoom)
        oshift=math.pi * 6378137
        res=(math.pi*6378137)/ (128*2**zoom)
        self._gpx['_y'] = np.log(np.tan((self.gpx['lat']+90.0)*math.pi/360.0)) / (math.pi/180.0) *( oshift / 180 )
        self._gpx['_x'] = self.gpx['lon'] * oshift / 180.0
        self._gpx['_x']=(self._gpx['_x']+oshift)/res
        self._gpx['_y']=(self._gpx['_y']+oshift)/res
        self._gpx['_x']=self._gpx['_x']-left
        self._gpx['_y']=((2 ** zoom) * 256)-self._gpx['_y']-top

    def OnLeftMouseDblClick(self,event):
        if not self.active:
            return False
        if self.gpx!=None:
            l=''
            for name in self.gpx.get_header_names()+['use custom color']:
                l+='|'+name
            (dummy,self.trackcolorkey, self.linewidth,self.trackcolordefault,\
            dummy,self.currentindic,self.currentcolor,self.currentthetakey,\
            self.currentmagkey,self.currentzoom)=WxQuery("color table to use",
                                            [('wxnotebook','Track',None,None,None),\
                                             ('wxcombo','Key for color code',l[1:],self.trackcolorkey,'str'),\
                                             ('wxspin','Line width','1|10|1',self.linewidth,'float'),\
                                             ('wxcolor','Custom color',None,self.trackcolordefault,'float'),\
                                             ('wxnotebook','Indicator',None,None,None),\
                                             ('wxcombo','Style','Dot|Arrowhead|Vector from|Vector to',self.currentindic,'str'),\
                                             ('wxcolor','Custom color',None,self.currentcolor,'float'),\
                                             ('wxcombo','Key for angle',l[1:],self.currentthetakey,'str'),\
                                             ('wxcombo','Key for magnitude',l[1:],self.currentmagkey,'str'),
                                             ('wxspin','Zoom factor','0|150|1',str(self.currentzoom),'float')])
            self.trackcolordefault+=(1.0,)
            self.currentcolor+=(1.0,)
            self.BuildColorTable(self.trackcolorkey)
            self.parent.Draw()
            return True

    def OnSigSelChanged(self,arg1,arg2,arg3):
        if arg1==self.id:
            return

    def OnSigValChanged(self,arg1):
        if arg1==self.id:
            return
        self.BuildColorTable(self.trackcolorkey)
        self.parent.Refresh()
        self.parent.Draw()
        self.parent.Refresh()

    def OnSigCurChanged(self, arg1, arg2):
        if arg1==self.id:
            return
        if self.gpx!=None:
            self.current=arg2
            self.current_x=self._gpx['_x'][arg2]
            self.current_y=self._gpx['_y'][arg2]
            self.parent.Draw(False)
            self.parent.Refresh()

panz64='''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'''

class WxMapWidget(WxMapBase):
    def __init__(self, *args, **kwargs):
        WxMapBase.__init__(self, *args, **kwargs)
        self.SetMapSrc("Open street maps")
        self.AppendLayer(WxToolLayer(self,"Gpx tools"))
        self.GetNamedLayer("Gpx tools").AppendTool(WxMapButton("PanZoom",WxMapImage.FromBase64(panz64),None))
        self.GetNamedLayer("Gpx tools").SelectTool("PanZoom")
        self.AppendLayer(GpxMapLayer(self))

    def AttachGpx(self,data):
        for layer in self.layers:
            #some layers may not be gpx aware. scalelayer,toollayer, ...
            try:
                layer.AttachGpx(data)
            except:
                pass

    def DetachGpx(self):
        for layer in self.layers:
            #some layers may not be gpx aware. scalelayer,toollayer, ...
            try:
                layer.DetachGpx()
            except:
                pass
        pass

    def OnRightMouseDown(self,event):
        for layer in self.layers:
            if layer.OnRightMouseDown(event):
                return
        if not hasattr(self,"map_src_menu"):
            self.map_src_menu = wx.Menu()
            for text in self.ListMapSrc():
                item = self.map_src_menu.Append(-1, text)
                self.Bind(wx.EVT_MENU, self.OnPopup, item)
        self.PopupMenu(self.map_src_menu)

    # def OnRightMouseDown(self,event):
        # for layer in self.layers:
            # layer.OnRightMouseDown(event)
        # if not hasattr(self,"map_src_menu"):
            # self.map_popup =wx.Menu()
            # self.map_src_menu = wx.Menu()
            # self.map_popup.AppendSubMenu(self.map_src_menu,"Map source")
            # self.map_layer_menu = wx.Menu()
            # self.map_popup.AppendSubMenu(self.map_layer_menu,"Visible layers")
            # for text in self.ListMapSrc():
                # item = self.map_src_menu.Append(-1, text)
                # self.Bind(wx.EVT_MENU, self.OnPopup, item)
        # self.PopupMenu(self.map_popup)

    def OnPopup(self, event):
        item = self.map_src_menu.FindItemById(event.GetId())
        text = item.GetText()
        self.SetMapSrc(self.ListMapSrc().index(item.GetText()))
        self.Draw()
        self.Refresh()
