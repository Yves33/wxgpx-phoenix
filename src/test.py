#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
import os,sys,warnings
import numpy as np

import wx
import wx.aui

sys.path.append(os.path.dirname(os.path.abspath(__file__) ) +"/modules/")
from pydispatch import dispatcher
'''
try:
    from wx.lib.pubsub import setupkwargs       #deprecated in pubsub 4.x
except ImportError:
    pass
from wx.lib.pubsub import pub
'''

from wxquery.wxquery import WxQuery
from wxmappanel.wxmappanel import WxMapBase,WxMapLayer,WxToolLayer,WxMapButton,WxMapImage
import gpxobj
import wxmapwidget
import wxlinescatterwidget
import wxstatusbarwidget

#
#pyinstaller specific path determination
#
def thispath():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

#
#
#
def test_gpx():
    if (len(sys.argv)<1):
        warnings.warn("You have to supply one file to open (*.gpx or *.fit)")
        sys.exit()
    filename, fileext = os.path.splitext(sys.argv[1])
    gpx=gpxobj.GpxObj()
    if fileext in ['.gpx','.GPX']:
        gpx.open_gpx(sys.argv[1])
    if fileext in ['.fit','.FIT']:
        gpx.open_fit(sys.argv[1])
    if fileext in ['.npz','.NPZ']:
        gpx.open_npx(sys.argv[1])
    #print( np.max(gpx.d['speed']),np.min(gpx.d['speed']),np.mean(gpx.d['speed']) )
    print ("################################################################")
    print ("Adding and removing columns...")
    print ("columns: ",gpx.get_col_count()," ",gpx.get_header_names())
    gpx.append_column('newcolumn','float')
    print ("columns: ",gpx.get_col_count()," ",gpx.get_header_names())
    gpx.drop_column('newcolumn')
    print ("columns: ",gpx.get_col_count()," ",gpx.get_header_names())
    print ("################################################################")
    print ("Saving in various formats...")
    print ("XML export: ")
    gpx.save_xml(thispath()+os.sep+"export.gpx",None)
    print ("npz export: ")
    gpx.save_npz(thispath()+os.sep+"export.pickle")
    print ("################################################################")
    print ("Computing...")
    print ("slope:"+str(np.nanmean(gpx.hv_slope(skipnan=True))))
    print ("speed:"+str(np.nanmean(gpx.hv_speed(skipnan=True))))
    print ("################################################################")
    print ("Changing units...")
    print ("Old units for speed: ",gpx.get_unit('speed')[0]+" description : "+gpx.get_unit('speed')[1]+" scale : "+str(gpx.get_scale('ele')))
    gpx.set_unit('speed','km/h')
    print ("New units for speed: ",gpx.get_unit('speed')[0]+" description : "+gpx.get_unit('speed')[1]+" scale : "+str(gpx.get_scale('ele')))
    print ("Average speed (SI): ",gpx.hv_speed().mean())
    print ("Average speed ("+gpx.get_unit('speed')[0]+"): ",gpx.hv_speed().mean()*gpx.get_scale('speed'))
    print(np.mean(gpx.d['speed']),np.max(gpx.d['speed']),np.min(gpx.d['speed']))
    print(np.mean(gpx.d['enhanced_speed']),np.max(gpx.d['enhanced_speed']),np.min(gpx.d['enhanced_speed']))
    print(np.mean(gpx.d['ball_speed']),np.max(gpx.d['ball_speed']),np.min(gpx.d['ball_speed']))
    print ("################################################################")

#
#
#
def test_wxquery():
    entries=[('wxnotebook','Entry',None,None,None),                                                 #0
             ('wxentry','Textual entry',None,'default_value','str','this is an optionnal tooltip'),
             ('wxentry','Integer entry',None,127,'int'),
             ('wxentry','Floating point value entry',None,127.30,'float'),
             ('wxnotebook','Combo/list',None,None,None),
             ('wxcombo','Textual Combo','choice1|choice2|choice3','choice2','str'),                 #5
             ('wxcombo','Integer Combo','125|2|1538',2,'int'),
             ('wxcombo','Float Combo','12.5|2.0|1.538',2,'float'),
             ('wxlist','List','January|February|March|April|May|June','April','str'),
             ('wxnotebook','Spin/Range',None,None,None),
             ('wxspin','Integer spin','1|13|2',6,'int'),                                            #10
             ('wxspin','Float spin','0.321|10.321|0.100',3.701234567,'float'),
             ('wxhscale','Integer range','0|12|1|0',6,'int'),
             ('wxhscale','Float range','0|12|1|0',6,'float'),
             ('wxnotebook','CheckBox and radio',None,None,None),
             ('wxcheck','CheckBox',None,False,'bool'),                                              #15
             ('wxradio','Radio','One|Two|Three|Four|Five','Three','str'),
             ('wxnotebook','Date/Time',None,None,None),
             ('wxdate','Date','2014-01-10|2015-05-10','2015-03-10','str'),
             ('wxtime','Time','00:00:00|23:59:59','12:30:17','str'),
             ('wxcalendar','Calendar','2014-05-10|2015-05-10','2015-05-10','str'),                  #20
             ('wxnotebook','Static',None,None,None),
             ('wxlabel','A label',None,'Second part of label','str','tooooltiiip'),
             ('wximage','An Image','32|32',thispath()+"/images/map.png",'str'),
             ('wxnotebook','Picker',None,None,None),
             ('wxcolor','Color Picker',None,'#AA0055','str'),                                       #25
             ('wxcolor','Color Picker (int)',None,(255,0,0),'int'),
             ('wxcolor','Color Picker (float)',None,(1.0,0.0,0.0),'float'),
             ('wxfile','File picker','Acrobat files (*.pdf)|*.pdf',"C:\\",'str','extra1',23.154),
             #('wxfile','File picker','',"C:\\",'str','extra1',23.154),
             ('wxdir','Dir picker',None,"C:\\",'str'),
             ('wxnotebook','Checkbox',None,None,None),                                              #30
             ('wxcheck','CheckBox','32|-33|34|-35',True,'bool'),                                    # special syntax list of controls to enable disable with checkbox
             ('wxentry','enabled with check',None,'default_value','str'),
             ('wxentry','disabled with check',None,'default_value','str'),
             ('wxentry','enabled with check',None,'default_value','str'),
             ('wxentry','disabled with check',None,'default_value','str'),                          #35
             ('wxentry','not affected',None,'default_value','str'),
             ('wxnotebook','Checklist',None,None,None),
             ('wxchecklist','CheckList','apple|orange|banana|pears|stawberry|pinapple|cherry|apple|orange|banana|pears|stawberry|pinapple|cherry','apple|banana|pears','str')
            ]
    app = wx.App(False)
    print(WxQuery("A sample dialog",entries))
    app.MainLoop()

#
#
#
def test_mappanel():
    class SampleMapLayer(WxMapLayer):
        def __init__(self,parent,name="Sample layer"):
            WxMapLayer.__init__(self,parent,name)
            self.current_x=0
            self.current_y=0
            #self.img=WxMapImage.FromFile(os.path.dirname(os.path.abspath(__file__))+os.sep+"up.png")
            #self.img=WxMapImage.FromBase64(panz64)

        def DrawOffscreen(self,dc):
            width,height=self.parent.GetClientSize()
            pen=self.parent.renderer
            pen.SetLineWidth(3.0)
            pen.SetPenColor(0.0,1.0,0.0,1.0)
            pen.SetBrushColor(0.0,1.0,0.0,0.5)
            pen.Circle(width/2, height/2,15)

        def DrawOnscreen(self,dc):
            pen=self.parent.renderer
            pen.SetLineWidth(1.0)
            pen.SetPenColor(1.0,0.0,1.0,1.0)
            pen.SetBrushColor(1.0,0.0,1.0,1.0)
            pen.SetFont('HELVETICA12')
            lat,lon=self.parent.ScreenToGeo(self.current_x, self.current_y)
            pen.Text("lat:"+str(lat)+" lon:"+str(lon), self.current_x, self.current_y)
            pen.SetPenColor(1.0,0.0,0.0,1.0)
            pen.SetBrushColor(0.5,0.0,0.0,1.0)
            pen.Circle(self.current_x, self.current_y,5)

        def OnMouseMotion(self,event):
            self.current_x=event.GetX()
            self.current_y=event.GetY()
            self.parent.Draw(False)     # just blit layers
            return False                # continue event propagation)

        def Say(self,tof):
            print("sample map layer received",tof)

    class TestFrame(wx.Frame):
        def __init__(self, parent, id, title, size=(500, 500)):
            wx.Frame.__init__(self, parent,id,size=(500,500),title=title,style=wx.DEFAULT_FRAME_STYLE)
            self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
            self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)

            Bordeaux=(44.8404400,-0.5805000)
            LaRochelle=(46.167,-1.167)

            panel = wx.Panel(self, -1)                  # each frame needs a top level panel

            self.window = WxMapBase(panel,usegl=True)   # our WxMapWidget
            hbox = wx.BoxSizer(wx.VERTICAL)             # a box
            hbox.Add(self.window, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 0)
            panel.SetSizer(hbox)
            self.window.SetMapSrc("Open street maps")
            test=0
            if test==0:
                self.window.AppendLayer(SampleMapLayer(self.window))
            elif test==1:
                self.window.AppendLayer(WxPathLayer(self.window))
            elif test==2:
                self.tools=WxToolLayer(self.window)
                self.tools.AppendTool(WxMapButton("first",WxMapImage.FromBase64(panz64),None))
                self.tools.AppendTool(WxMapButton("second",WxMapImage.FromBase64(panz64),None))
                self.tools.AppendTool(WxMapButton("third",WxMapImage.FromBase64(panz64),None))
                self.tools.SelectTool("second")
                self.window.AppendLayer(self.tools)
            self.Show()
            self.window.SetSize(self.GetClientSize())   #can't get the map to show unless we force a resize
            #self.window.SetGeoZoomAndCenter(20,(Bordeaux))
            self.window.EncloseGeoBbox(min(Bordeaux[0],LaRochelle[0]),\
                                        min(Bordeaux[1],LaRochelle[1]),\
                                        max(Bordeaux[0],LaRochelle[0]),\
                                        max(Bordeaux[1],LaRochelle[1]))
            print(self.window.GetCacheDir())

        def OnCloseFrame(self, evt):
            sys.exit()

        def OnQuit(self,event):
            self.Close(True)

        def OnKeyPress(self,event):
            if event.GetKeyCode() == wx.WXK_SPACE:
                #self.window.CacheAll(10)
                self.window.renderer.SaveBuffer(self.window.mapbuffer,os.path.dirname(os.path.abspath(__file__))+"/saved.png")

    class DemoApp(wx.App):
        def OnInit(self):
            frame = TestFrame(None,-1,"Demo App")
            self.SetTopWindow(frame)
            return True

    app = DemoApp(0)
    app.MainLoop()

#
#
#
def test_mapwidget():
    class TestFrame(wx.Frame):
        def __init__(self, parent, id, title, size=(500, 500)):
            wx.Frame.__init__(self, parent,id,size=(500,500),title=title,style=wx.DEFAULT_FRAME_STYLE)
            self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

            Bordeaux=(44.8404400,-0.5805000)
            LaRochelle=(46.167,-1.167)

            panel = wx.Panel(self, -1)                  # each frame needs a top level panel
            self.window = wxmapwidget.WxMapWidget(panel,usegl=True) # our WxMapWidget
            hbox = wx.BoxSizer(wx.VERTICAL)             # a box
            hbox.Add(self.window, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 0)
            panel.SetSizer(hbox)
            #self.window.LoadProviders(os.path.dirname(os.path.abspath(__file__))+os.sep+"providers.txt")
            self.window.SetMapSrc("Open street maps")
            self.Show()
            self.window.SetSize(self.GetClientSize())   #can't get the map to show unless we force a resize
            #self.window.SetGeoZoomAndCenter(20,(Bordeaux))
            self.window.EncloseGeoBbox(min(Bordeaux[0],LaRochelle[0]),\
                                        min(Bordeaux[1],LaRochelle[1]),\
                                        max(Bordeaux[0],LaRochelle[0]),\
                                        max(Bordeaux[1],LaRochelle[1]))
            self.gpx=gpxobj.GpxObj()
            if (len(sys.argv)<1):
                print("You have to supply one file to open (*.gpx or *.fit)")
                sys.exit()
            filename, fileext = os.path.splitext(sys.argv[1])
            self.gpx=gpxobj.GpxObj()
            if fileext in ['.gpx','.GPX']:
                self.gpx.open_gpx(sys.argv[1])
            if fileext in ['.fit','.FIT']:
                self.gpx.open_fit(sys.argv[1])
            if fileext in ['.npz','.NPZ']:
                self.gpx.open_npx(sys.argv[1])
            self.gpx.append_column('duration','float')
            self.gpx.set_unit('duration','min');
            self.gpx['duration']=np.cumsum(self.gpx.duration())
            self.gpx.append_column('course','float')
            self.gpx['course']=self.gpx.hv_course()
            self.gpx.append_column('hv_speed',float)
            self.gpx['hv_speed']=self.gpx.hv_speed()
            self.window.AttachGpx(self.gpx)
            self.window.EncloseGeoBbox(self.gpx.d['lat'].min(),\
                                self.gpx.d['lon'].min(),\
                                self.gpx.d['lat'].max(),\
                                self.gpx.d['lon'].max())
            self.window.Draw(True)

        def OnCloseFrame(self, evt):
            exit()

        def OnQuit(self,event):
            self.Close(True)

    class DemoApp(wx.App):
        def OnInit(self):
            frame = TestFrame(None,-1,"Demo App")
            self.SetTopWindow(frame)
            return True

    app = DemoApp(0)
    app.MainLoop()

#
#
#
def test_timewidget():
    from wx.py import shell

    class TestFrame(wx.Frame):
        def __init__(self, parent=None):
            wx.Frame.__init__(self, parent,size = (500,250),title="TimeWidget Test",style=wx.DEFAULT_FRAME_STYLE)
            panel = wx.Panel(self, -1)                                                           # each frame needs a top level panel
            self.window = wxlinescatterwidget.WxTimeWidget(panel)                                # our WxMapWidget
            hbox = wx.BoxSizer(wx.VERTICAL)
            hbox.Add(self.window, 2, wx.EXPAND | wx.ALL)
            panel.SetSizer(hbox)
            self.Show()

            self.gpx=gpxobj.GpxObj()
            if (len(sys.argv)<1):
                print("You have to supply one file to open (*.gpx or *.fit)")
                sys.exit()
            filename, fileext = os.path.splitext(sys.argv[1])
            self.gpx=gpxobj.GpxObj()
            if fileext in ['.gpx','.GPX']:
                self.gpx.open_gpx(sys.argv[1])
            if fileext in ['.fit','.FIT']:
                self.gpx.open_fit(sys.argv[1])
            if fileext in ['.npz','.NPZ']:
                self.gpx.open_npx(sys.argv[1])

            #self.gpx.append_column('distance','float')
            #self.gpx['distance']=np.cumsum(self.gpx.hv_distance())
            #self.gpx.set_unit('distance','km')
            self.gpx.append_column('duration','float')
            self.gpx.set_unit('duration','min');
            self.gpx['duration']=np.cumsum(self.gpx.duration())
            self.gpx.append_column('bear','float')
            self.gpx['bear']=self.gpx.hv_course()
            self.gpx.append_column('hv_speed',float)
            self.gpx['hv_speed']=self.gpx.hv_speed()
            self.gpx.append_column('hv_vel',float)
            self.gpx['hv_vel']=self.gpx.hv_pace(500)

            self.window.AttachGpx(self.gpx)
            self.Refresh()

        def OnQuit(self,event):
            self.Close(True)

    class DemoApp(wx.App):
        def OnInit(self):
            frame = TestFrame()
            self.SetTopWindow(frame)
            return True

    app = DemoApp(0)
    app.MainLoop()



########################################################
########################################################
########################################################

sys.argv.append(r"E:\wxgpx-releases\wxgpx_testfiles\roller.fit")
#test_timewidget()
#test_mapwidget()
test_mappanel()
#test_wxquery()
#test_gpx()
warnings.warn("Edit this file and choose which test to start",UserWarning)
