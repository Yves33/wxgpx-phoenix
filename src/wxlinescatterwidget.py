#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-#
import os,sys

import wx
import wx.aui
import wx.adv

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.dates as dates
import matplotlib.patches as patches
import matplotlib as mpl
import matplotlib.transforms as mtransforms

import numpy as np
import datetime
import dateutil.parser
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__) ) +"/modules/")
from wxquery.wxquery import WxQuery
import msgwrap
import gpxobj


def ptinrect(l,t,r,b,x,y):
    return (min(l,r) < x <max(l,r)) and (min(b,t)<y<max(b,t))

def clamp(a,b,c):
    return sorted((a, b, c))[1]

class wxLineProps(object):
    def __init__(self,mydict):
        # set a few default values...
        self.d={'linewidth':1,\
                'marker':'.',\
                'markersize':0,\
                'color':'#990000',\
                'fill':False,
                'fillalpha':0.2}
        for key in mydict:
            self[key]=mydict[key]
            
    def __getitem__(self,key):
        return self.d[key]
        
    def __setitem__(self,key,value):
        self.d[key]=value
    
    
    
class WxLineScatterWidget(wx.Panel):
    axis_width=20
    axis_offset=1.05
    def __init__(self, *args, **kwargs):
        kwargs['style'] = kwargs.setdefault('style', wx.NO_FULL_REPAINT_ON_RESIZE) | wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__(self, *args, **kwargs)
        self.id=wx.NewId()
        self.plot1='none'
        self.plot2='none'
        self.plot3='none'
        self.lineprops1=wxLineProps({'color':'#990000','fill':True})
        self.lineprops2=wxLineProps({'color':'#009900','fill':True})
        self.lineprops3=wxLineProps({'color':'#000099','fill':True})
        self.autoy1=True
        self.autoy2=True
        self.autoy3=True
        self.smooth1=1
        self.smooth2=1
        self.smooth3=1
        self.xaxis=''
        self.press=False
        self.cursor=None
        self.span=None
        self.selstart=0
        self.selstop=0
        self.enablecursor=True
        self.enablespan=True
        self.cursorcolor='#FF0000'
        self.cursorwidth=1

        self.gpxfig = Figure()
        self.ax1 = self.gpxfig.add_subplot(1,1,1)           # create a grid of 1 row, 1 col and put a subplot in the first cell of this grid
        self.gpxfig.subplots_adjust(right=0.9,left=0.06)
        
        self.ax2=self.ax1.twinx()
        #self.ax2.spines["left"].set_visible(False)
        
        self.ax3=self.ax1.twinx()
        self.ax3.spines["right"].set_position(("axes", self.axis_offset))
        #self.ax3.spines["left"].set_visible(False)
        # canvas and events
        self.gpxcanvas=FigureCanvas(self,-1,self.gpxfig)
        self.gpxcanvas.mpl_connect('scroll_event', self.OnMouseWheel)
        self.gpxcanvas.mpl_connect('button_press_event', self.OnLeftMouseDown)
        self.gpxcanvas.mpl_connect('button_release_event', self.OnLeftMouseUp)
        self.gpxcanvas.mpl_connect('motion_notify_event', self.OnMouseMotion)
        self.gpxcanvas.mpl_connect('resize_event', self.OnSize)
        self.gpxcanvas.mpl_connect('figure_enter_event', self.OnMouseEnter)
        self.gpxcanvas.mpl_connect('figure_leave_event', self.OnMouseLeave)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightMouseDown)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.gpxcanvas, 1, wx.LEFT|wx.TOP|wx.GROW|wx.EXPAND)
        self.SetSizer(self.sizer)
        #self.OnSize(None)

        msgwrap.register(self.OnSigCurChanged, signal="CurChanged")
        msgwrap.register(self.OnSigSelChanged, signal="SelChanged")
        msgwrap.register(self.OnSigValChanged, signal="ValChanged")


        #set background color to pure white
        #that code does not work on linux...
        #color = wx.SystemSettings.GetColour(wx.wx.SYS_COLOUR_BTNFACE)
        color=wx.Colour(255,255,255)
        self.gpxfig.set_facecolor((color.red/255.0, color.green/255.0, color.blue/255.0))
        self.gpxfig.set_edgecolor((color.red/255.0, color.green/255.0, color.blue/255.0))
        self.gpxfig.set_edgecolor((0.0, 0.0, 0.0))
        self.gpxcanvas.SetBackgroundColour(color)
        
		# create right now the popup menu
        self.select_menu = wx.Menu()
        for text in ["Disable selected",\
                            "Enable selected",\
                            "Delete selected",\
                            "Disable non selected",\
                            "Enable non selected",\
                            "Delete non selected",\
                            "Toggle points"]:
            item = self.select_menu.Append(wx.NewId(), text)
            self.Bind(wx.EVT_MENU, self.OnPopup, item)

    def x_to_num(self,value,scaled=True):
        if self.xaxis=='time':
            return dates.date2num(dateutil.parser.parse(value))
        else:
            if scaled: 
                #return float(value)/self.gpx.get_scale(self.xaxis)
                return float(value)*self.gpx.get_scale(self.xaxis)
            else:
                return float(value)
    
    def num_to_x(self,value,scaled=True):
        if self.xaxis=='time':
            return dates.num2date(value)
        else:
            if scaled:
                #return value*self.gpx.get_scale(self.xaxis)
                return value/self.gpx.get_scale(self.xaxis)
            else:
                return value
                
    def x_max(self):
        if self.xaxis=='time':
            return self.x_to_num(self.gpx[self.xaxis][self.gpx.get_row_count()-1])
        else:
            return self.x_to_num(np.nanmax(self.gpx[self.xaxis]))
            
    def x_min(self):
        if self.xaxis=='time':
            return self.x_to_num(self.gpx[self.xaxis][0])
        else:
            return self.x_to_num(np.nanmin(self.gpx[self.xaxis]))
            
    def format_x_axis(self):
        if self.xaxis=='time':
            xlo=self.ax1.get_xlim()[0]
            xhi=self.ax1.get_xlim()[1]
            if (xhi-xlo)>0.003:
                self.ax1.xaxis.set_major_formatter(dates.DateFormatter("%H:%M"))
            else:
                self.ax1.xaxis.set_major_formatter(dates.DateFormatter("%H:%M:%S"))
            self.ax1.set_xlabel('Time (HH:MM:SS)')
        else:
            #self.ax1.set_xlabel('Distance (m)')
            self.ax1.set_xlabel(self.xaxis+" ("+self.gpx.get_unit(self.xaxis)[0]+")")
            #self.ax1.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.0f') )
            self.ax1.xaxis.set_major_formatter(mpl.ticker.ScalarFormatter())
            pass
    
    def get_axis(self,event,tolerance):
        bbox = self.ax1.get_window_extent().transformed(self.gpxfig.dpi_scale_trans.inverted())
        l=bbox.bounds[0]*self.gpxfig.dpi
        b=bbox.bounds[1]*self.gpxfig.dpi
        r=l+bbox.bounds[2]*self.gpxfig.dpi
        t=b+bbox.bounds[3]*self.gpxfig.dpi
        #convert screen coordinates to graph coordinates
        xlo=self.ax1.get_xlim()[0]
        xhi=self.ax1.get_xlim()[1]
        event.xdata=(event.x-l)/(r-l)*(xhi-xlo)+xlo
        if ptinrect(l-tolerance,t,l,b,event.x,event.y):
            ylo,yhi=self.ax1.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'left'
        if ptinrect(r,t,r+tolerance,b,event.x,event.y):
            ylo,yhi=self.ax2.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'right'
        if ptinrect(l,t,r,t+tolerance,event.x,event.y):
            ylo,yhi=self.ax1.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'top'
        if ptinrect(l,b-tolerance,r,b,event.x,event.y):
            ylo,yhi=self.ax1.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return 'bottom'
        #we need a small adjustment here, but this hack gives good results
        if ptinrect(r*self.axis_offset*0.985,t,r*self.axis_offset*0.985+tolerance,b,event.x,event.y):
            ylo,yhi=self.ax3.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo
            return "3rd"
        if ptinrect(l,t,r,b,event.x,event.y):
            ylo,yhi=self.ax1.get_ylim()
            event.ydata=(event.y-b)/(t-b)*(yhi-ylo)+ylo       
            return 'main'

    def update_axis(self,ax,plot,ylo,yhi,yauto,lineprops,smooth):
        if plot!='none':
            ## process data!!
            N=smooth
            #data=(1.0)*np.convolve(self.gpx[plot]*self.gpx.scale[plot], np.ones((N,))/N)[(N-1):]
            data=(1.0)*np.convolve(self.gpx[(plot,True)], np.ones((N,))/N)[(N-1):]
            data[self.gpx['ok']==False]=np.NAN
            ##end of data processing
            #remove fill_between collection
            for coll in ax.collections:
                ax.collections.remove(coll)
            #need to rebuild dates array in case something was deleted
            self.xvalues=[]
            for x in self.gpx[self.xaxis]:
                self.xvalues.append(self.x_to_num(x))
            ax.get_lines()[0].set_data(self.xvalues,data)
            self.format_x_axis()
            if lineprops['fill']:
                ax.fill_between(self.xvalues,0,data,facecolor=lineprops['color'], alpha=0.2)
            ax.get_lines()[0].set_color(lineprops['color'])
            ax.get_lines()[0].set_linewidth(lineprops['linewidth'])
            ax.get_lines()[0].set_marker(lineprops['marker'])
            ax.get_lines()[0].set_markersize(lineprops['markersize'])
            ax.set_autoscaley_on(yauto)
            ##now using legends instead of labels
            #ax.set_ylabel(plot+" ("+str(self.gpx.get_unit(plot)[0])+")")
            #ax.yaxis.label.set_color(lineprops['color'])
            lines = self.line1+self.line2+self.line3
            labs = [p for p in [self.plot1,self.plot2, self.plot3] if p!='none']
            self.ax1.legend(lines, labs, loc='best') #,bbox_to_anchor=(0.5, 1.3), ncol=3, fancybox=False, shadow=False)

            if not yauto:
                ax.set_ylim(ylo,yhi)
            else:
                ax.set_ylim(np.min(self.gpx[plot]*self.gpx.scale[plot]),np.max(self.gpx[plot]*self.gpx.scale[plot]))
            ax.set_visible(True)
            for tick in ax.get_yticklabels():
                tick.set_color(lineprops['color'])
            ax.spines["right"].set_edgecolor(lineprops['color'])
            ax.tick_params(axis='y', colors=lineprops['color'])
        else:
            ax.get_lines()[0].set_data(self.xvalues, np.zeros(self.gpx.get_row_count()))
            ax.set_visible(False)
        self.cursor.set_color(self.cursorcolor)
        self.cursor.set_linewidth(self.cursorwidth)
        self.format_x_axis()
        self.Draw(False)
        self.OnSize(None)
            
    def AttachGpx(self,data):
        self.gpx=data
        self.xvalues=[]
        self.xaxis=self.gpx.get_header_names()[0]
        for x in self.gpx[self.xaxis]:
            self.xvalues.append(self.x_to_num(x))
        self.ax1.set_xlabel('')
        self.line1=self.ax1.plot(self.xvalues, np.zeros(self.gpx.get_row_count()),picker=5,label='ax1')
        self.line2=self.ax2.plot(self.xvalues, np.zeros(self.gpx.get_row_count()),picker=5,label='ax2')
        self.line3=self.ax3.plot(self.xvalues, np.zeros(self.gpx.get_row_count()),picker=5,label='ax3')
        xlo= self.x_to_num(self.gpx[self.xaxis][0])
        xhi= self.x_to_num(self.gpx[self.xaxis][self.gpx.get_row_count()-1])
        if xlo!=xhi:
            self.ax1.set_xlim([xlo,xhi])
        if self.enablecursor==True:
            self.cursor=self.ax1.axvline(color='r',animated=True)
            mid=(self.ax1.get_xlim()[0]+self.ax1.get_xlim()[1])/2
            self.cursor.set_xdata(mid)
            #self.cursor.set_color('k')
            #self.cursor.set_linewidth(4)
        if self.enablespan==True:
            self.span=patches.Rectangle((self.ax1.get_xlim()[0],0), (self.ax1.get_xlim()[1]-self.ax1.get_xlim()[0])/3, 200, color='k',alpha=0.3,animated=True)
            self.ax1.add_patch(self.span)
            self.span.set_visible(False)
        self.SetDefaultPlots()
        self.OnSize(None)

    def DetachGpx(self):
        self.gpx=None
        self.plot1='none'
        self.plot2='none'
        self.plot3='none'
        self.autoy1=True
        self.autoy2=True
        self.autoy3=True
        self.fill1=True
        self.fill2=True
        self.fill3=True
        self.xaxis=''
        self.press=False
        if self.cursor!=None:
            self.cursor.remove()
            self.cursor=None
        if self.span!=None:
            self.span.remove()
            self.span=None

    def OnSigSelChanged(self,arg1,arg2,arg3):
        if arg1==self.id:
            return
        if self.span!=None:
            xlo=self.x_to_num(self.gpx[self.xaxis][arg2])
            xhi=self.x_to_num(self.gpx[self.xaxis][arg3])
            self.span.set_bounds(xlo,self.ax1.get_ylim()[0],xhi-xlo,self.ax1.get_ylim()[1]-self.ax1.get_ylim()[0])
            self.span.set_visible(True)
        
    def OnSigValChanged(self,arg1):
        if arg1==self.id:
            return
        self.update_axis(self.ax1,self.plot1,self.ax1.get_xlim()[0],self.ax1.get_xlim()[1],self.autoy1, self.lineprops1, self.smooth1)
        self.update_axis(self.ax2,self.plot2,self.ax2.get_xlim()[0],self.ax2.get_xlim()[1],self.autoy2, self.lineprops2, self.smooth2)
        self.update_axis(self.ax3,self.plot3,self.ax2.get_xlim()[0],self.ax2.get_xlim()[1],self.autoy3, self.lineprops3, self.smooth3)
    
    def OnSigCurChanged(self, arg1, arg2):
        if arg1==self.id:
            return
        if self.gpx!=None:
            xval=self.gpx[self.xaxis][arg2]
            self.gpxcanvas.restore_region(self.background)
            if self.cursor!=None:
                self.cursor.set_xdata(self.x_to_num(xval))
                self.ax1.draw_artist(self.cursor)
            if self.span!=None and self.span.get_visible():
                self.ax1.draw_artist(self.span)
            self.gpxcanvas.blit()
        self.UpdateStatusBar(arg2)
        
    def SetDefaultPlots(self):
        self.xaxis=self.gpx.get_header_names()[0]
        self.plot1=self.gpx.get_header_names()[1]
        self.plot2='none'
        self.plot3='none'
        self.update_axis(self.ax1,self.plot1,0,1,True, self.lineprops1, self.smooth1)
        self.update_axis(self.ax2,self.plot2,0,1,True, self.lineprops2, self.smooth2)
        self.update_axis(self.ax3,self.plot3,0,1,True, self.lineprops3, self.smooth3)
    
    def XAxisAllowed(self):
        l=''
        for name in self.gpx.get_header_names():
            l+='|'+name
        return l[1:]
        
    def YAxisAllowed(self):
        l=''
        for name in self.gpx.get_header_names():
            l+='|'+name
        return l[1:]
  
    def Draw(self,blit):
        if blit:
            self.gpxcanvas.restore_region(self.background)
        else:
            self.gpxcanvas.draw()
            self.background = self.gpxcanvas.copy_from_bbox(self.ax1.bbox)
        if self.span!=None and self.span.get_visible():
            self.ax1.draw_artist(self.span)
        if self.cursor!=None:
            self.ax1.draw_artist(self.cursor)
        self.gpxcanvas.blit()
        
    def OnSize(self,event):
        pixels=self.GetClientSize()
        if pixels[0]<20 or pixels[1]<20:
            return
        self.SetSize(pixels)
        self.gpxcanvas.SetSize(pixels)
        self.gpxfig.set_size_inches(float(pixels[0])/self.gpxfig.get_dpi(),float(pixels[1])/self.gpxfig.get_dpi())
        leg=self.ax1.xaxis.get_tightbbox(self.gpxcanvas.get_renderer())       
        leg1=self.ax1.yaxis.get_tightbbox(self.gpxcanvas.get_renderer())
        leg2=self.ax2.yaxis.get_tightbbox(self.gpxcanvas.get_renderer())
        leg3=self.ax3.yaxis.get_tightbbox(self.gpxcanvas.get_renderer())#leg2 and leg3 are exactly the same!!
        bottomalign=(leg.height+5)/pixels[1]
        leftalign=(leg1.width+5)/pixels[0]
        if self.plot2=='none' and self.plot3=='none':
            rightalign=(1-(5.0)/pixels[0])/self.axis_offset
        else:
            rightalign=(1-(leg2.width+5)/pixels[0])/self.axis_offset
        if pixels[1]>32:
            self.gpxfig.subplots_adjust(bottom=bottomalign)
        if pixels[0]>32:
            self.gpxfig.subplots_adjust(left=leftalign,right=rightalign)
        ##PYTHON3
        self.gpxfig.subplots_adjust(right=0.9,left=0.06,bottom=0.2)
        self.Draw(False)
        
    def OnLeftMouseDblClick(self,event):
        #dble click. Let's get prepared
        xlo=self.num_to_x(self.ax1.get_xlim()[0],False)
        xhi=self.num_to_x(self.ax1.get_xlim()[1],False)
        y1lo=self.ax1.get_ylim()[0]
        y1hi=self.ax1.get_ylim()[1]
        y2lo=self.ax2.get_ylim()[0]
        y2hi=self.ax2.get_ylim()[1]
        y3lo=self.ax3.get_ylim()[0]
        y3hi=self.ax3.get_ylim()[1]

        (dummy,xaxis,xlo,xhi,self.cursorcolor,self.cursorwidth,
        dummy,self.plot1,y1lo,y1hi,self.autoy1,self.smooth1,
        self.lineprops1['color'],self.lineprops1['linewidth'],self.lineprops1['marker'],self.lineprops1['markersize'],self.lineprops1['fill'],\
        dummy,self.plot2,y2lo,y2hi,self.autoy2,self.smooth2,
        self.lineprops2['color'],self.lineprops2['linewidth'],self.lineprops2['marker'],self.lineprops2['markersize'],self.lineprops2['fill'],\
        dummy,self.plot3,y3lo,y3hi,self.autoy3,self.smooth3,
        self.lineprops3['color'],self.lineprops3['linewidth'],self.lineprops3['marker'],self.lineprops3['markersize'],self.lineprops3['fill'])=\
            WxQuery("Graph Settings",\
                [('wxnotebook','X Axis',None,None,None),
                 ('wxcombo','X axis',self.XAxisAllowed(),self.xaxis,'str'),
                 ("wxentry","Start",None,str(xlo),'str'),
                 ("wxentry","End",None,str(xhi),'str'),
                 ('wxcolor','Cursor color',None,self.cursorcolor,'str'),
                 ('wxspin','Cursor width','0|6|1',self.cursorwidth,'int'),

                 ('wxnotebook','Y1Axis',None,None,None),
                 ('wxcombo','Channel 1',self.YAxisAllowed(),self.plot1,'str'),
                 ('wxentry','Bottom',None,y1lo,'float'),
                 ('wxentry','Top',None,y1hi,'float'),
                 ('wxcheck','Auto Scale','-9|-8', self.autoy1,'bool'), #8
                 ('wxhscale','Smooth','1|12|1|1',self.smooth1,'int'),
                 ('wxcolor','Color',None,self.lineprops1['color'],'str'),
                 ('wxspin','Line width','0|12|1',self.lineprops1['linewidth'],'int'),
                 ('wxcombo','Marker','.|o|+|x|^|4|s|*|D',self.lineprops1['marker'],'str'),
                 ('wxspin','Marker size','0|12|1',self.lineprops1['markersize'],'int'),
                 ('wxcheck','Fill area',None,self.lineprops1['fill'],'bool'),
                 
                 ('wxnotebook','Y2 Axis',None,None,None),
                 ('wxcombo','Channel 2',self.YAxisAllowed(),self.plot2,'str'),
                 ('wxentry','Bottom',None,y2lo,'float'),
                 ('wxentry','Top',None,y2hi,'float'),
                 ('wxcheck','Auto Scale','-20|-19', self.autoy2,'bool'),
                 ('wxhscale','Smooth','1|12|1|1',self.smooth2,'int'),
                 ('wxcolor','Color',None,self.lineprops2['color'],'str'),
                 ('wxspin','Line width','0|12|1',self.lineprops2['linewidth'],'int'),
                 ('wxcombo','Marker','.|o|+|x|^|4|s|*|D',self.lineprops2['marker'],'str'),
                 ('wxspin','Marker size','0|12|1',self.lineprops2['markersize'],'int'),
                 ('wxcheck','Fill area',None,self.lineprops2['fill'],'bool'),
                 
                 ('wxnotebook','Y3 Axis',None,None,None),
                 ('wxcombo','Channel 3',self.YAxisAllowed(),self.plot3,'str'),
                 ('wxentry','Bottom',None,y3lo,'float'),
                 ('wxentry','Top',None,y3hi,'float'),
                 ('wxcheck','Auto Scale','-31|-30', self.autoy3,'bool'),
                 ('wxhscale','Smooth','1|12|1|1',self.smooth3,'int'),
                 ('wxcolor','Color',None,self.lineprops3['color'],'str'),
                 ('wxspin','Line width','0|12|1',self.lineprops3['linewidth'],'int'),
                 ('wxcombo','Marker','.|o|+|x|^|4|s|*|D',self.lineprops3['marker'],'str'),
                 ('wxspin','Marker size','0|12|1',self.lineprops3['markersize'],'int'),
                 ('wxcheck','Fill area',None,self.lineprops3['fill'],'bool')
                ])
        if self.xaxis==xaxis:
            xlo=max(self.x_to_num(xlo,False),self.x_min())
            xhi=min(self.x_to_num(xhi,False),self.x_max())
            self.ax1.set_xlim([xlo,xhi])
        else:#time units have changed... don't bother and set to full x range
            self.xaxis=xaxis
            self.ax1.set_xlim([self.x_min(),self.x_max()])
        self.update_axis(self.ax1,self.plot1,y1lo,y1hi,self.autoy1, self.lineprops1, self.smooth1)
        self.update_axis(self.ax2,self.plot2,y2lo,y2hi,self.autoy2, self.lineprops2, self.smooth2)
        self.update_axis(self.ax3,self.plot3,y3lo,y3hi,self.autoy3, self.lineprops3, self.smooth3)
                   
    def OnLeftMouseDown(self,event):
        where=self.get_axis(event,self.axis_width)
        #if hasattr(event, 'guiEvent') and int(event.guiEvent.type)==5:
        #calling direcly the dialog may freeze on unix (linux-osX systems) under wx backend
        #workaround   is to release mouse
        #see http://stackoverflow.com/questions/16815695/modal-dialog-freezes-the-whole-application
        #event.guiEvent.GetEventObject().ReleaseMouse() for pick_event
        if event.button==1:
            if event.dblclick:
                try:
                    event.guiEvent.GetEventObject().ReleaseMouse()
                except:
                    pass
                self.OnLeftMouseDblClick(event)
                return
            if  where=='bottom':
                (self.x0,self.y0)=(event.xdata,event.ydata)
                self.press=True
            if where=='main' and self.span!=None:
                self.span.set_visible(True)
                (self.x0,self.y0)=(event.xdata,event.ydata)
                self.selstart=self.x0
                self.selstop=self.x0
                self.span.set_bounds(event.xdata,self.ax1.get_ylim()[0],0,self.ax1.get_ylim()[1]-self.ax1.get_ylim()[0])
                self.press=True
        elif event.button==3:
            if where=='main':
                self.OnRightMouseDown(event)
    
    def OnLeftMouseUp(self,event):
        where=self.get_axis(event,self.axis_width)
        self.press = False
        if event.button==1 and self.span!=None:
            if where=='main':
                idx1=np.searchsorted(self.ax1.get_lines()[0].get_data()[0],self.x0)
                idx2=np.searchsorted(self.ax1.get_lines()[0].get_data()[0],event.xdata)
                self.selstart=min(idx1,idx2)
                self.selstop=max(idx1,idx2)
                if self.selstart==self.selstop:
                    self.span.set_visible(False)
                msgwrap.message("SelChanged",arg1=self.id,arg2=self.selstart,arg3=self.selstop)
                self.press=False
    
    def OnRightMouseDown(self,event):
        #may be necessary in some OSes
        event.guiEvent.GetEventObject().ReleaseMouse()
        if self.selstart==self.selstop:
            self.select_menu.Enable(self.select_menu.FindItem("Disable selected"),False)
            self.select_menu.Enable(self.select_menu.FindItem("Enable selected"),False)
            self.select_menu.Enable(self.select_menu.FindItem("Delete selected"),False)
        else:
            self.select_menu.Enable(self.select_menu.FindItem("Disable selected"),True)
            self.select_menu.Enable(self.select_menu.FindItem("Enable selected"),True)
            self.select_menu.Enable(self.select_menu.FindItem("Delete selected"),True)
        self.select_menu.Enable(self.select_menu.FindItem("Toggle points"),True)
        # on some OS (and depending on wxPython/wxWidgets version, calling
        # wx.PopupMenu will fail unless it is called after matplotlib handler has returned
        # for some magic reason, we do not need to specify wx.Point(event.x, event.y) in parameterss
        #self.PopupMenu(self.select_menus)
        wx.CallAfter(self.PopupMenu,self.select_menu)
            
    def OnMouseMotion(self,event):
        where=self.get_axis(event,self.axis_width)
        if where=='bottom' or where=='right' or where=='left' or where=='3rd':
            wx.SetCursor(wx.Cursor(wx.CURSOR_MAGNIFIER))
        else:
            wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        if where=='bottom' and self.press:
            dx = event.xdata - self.x0
            dy = event.ydata - self.y0
            self.ax1.set_xlim(self.ax1.get_xlim()[0]-dx,self.ax1.get_xlim()[1]-dx)
            self.Draw(False)
        if where=='main' and self.press:
            self.span.set_bounds(self.x0,\
                                self.ax1.get_ylim()[0],\
                                event.xdata-self.x0,\
                                self.ax1.get_ylim()[1]-self.ax1.get_ylim()[0])
            self.Draw(True)
        if where=='main' and self.cursor!=None:
            self.cursor.set_xdata(event.xdata)
            xval=event.xdata
            idx=np.searchsorted(self.ax1.get_lines()[0].get_data()[0],xval)
            while self.gpx['ok'][idx]==False and idx>=0:        #look for nearest enabled point
                idx-=1
            idx=clamp(idx,0,self.gpx.get_row_count()-1)
            self.cursor.set_xdata(self.x_to_num(self.gpx[self.xaxis][idx]))
            msgwrap.message("CurChanged",arg1=self.id,arg2=idx)
            ##send a message for the status bar
            self.UpdateStatusBar(idx)
            self.Draw(True)
        
    def OnMouseWheel(self,event):
        where=self.get_axis(event,self.axis_width)
        if where=='bottom':
            xmax=self.x_max()
            xmin=self.x_min()
            xlo,xhi=self.ax1.get_xlim()
            if event.button == 'down':
                scale_factor = 1.2
            else:
                scale_factor = 1/1.2
            nxhi=event.xdata+(scale_factor*(xhi-event.xdata))
            nxlo=event.xdata-(scale_factor*(event.xdata-xlo))
            nxhi=min(nxhi,xmax)
            nxlo=max(nxlo,xmin)
            self.ax1.set_xlim([nxlo,nxhi])
            self.format_x_axis()
        elif where=='left' or where=='right' or where=='3rd':
            if where=='left':
                ax=self.ax1
                plot=self.plot1
            elif where=='right':
                ax=self.ax2
                plot=self.plot2
            elif where=='3rd':
                ax=self.ax3
                plot=self.plot3
            ymax=np.max(self.gpx[plot]*self.gpx.scale[plot])
            ymin=np.min(self.gpx[plot]*self.gpx.scale[plot])
            ylo,yhi=ax.get_ylim()
            if event.button == 'down':
                scale_factor = 1.2
            else:
                scale_factor = 1/1.2
            nyhi=event.ydata+(scale_factor*(yhi-event.ydata))
            nylo=event.ydata-(scale_factor*(event.ydata-ylo))
            nyhi=min(nyhi,ymax)
            nylo=max(nylo,ymin)
            ax.set_ylim([nylo,nyhi])
        self.Draw(False)
        
    def OnMouseEnter(self,event):
        self.SetFocus()                 # stupid bug in wxSplitterWindow, mouse wheel is always send to the same panel in wxSplittedWIndow
        
    def OnMouseLeave(self,event):
        wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        pass

    def OnPopup(self, event):
        item = self.select_menu.FindItemById(event.GetId())
        text = item.GetText()
        if text=="Disable selected":
            self.gpx['ok'][self.selstart:self.selstop]=False
        if text=="Enable selected":
            self.gpx['ok'][self.selstart:self.selstop]=True
        if text=="Disable non selected":
            self.gpx['ok'][:self.selstart]=False
            self.gpx['ok'][self.selstop:]=False
        if text=="Enable non selected":
            self.gpx['ok'][:self.selstart]=True
            self.gpx['ok'][self.selstop:]=True
        if text=="Delete selected":
            if wx.MessageDialog(None, "Delete Points...?",\
                                'Are you sure you want to delete these points',\
                                wx.YES_NO | wx.ICON_QUESTION).ShowModal()==wx.ID_YES:
                for _ in range(self.selstart, self.selstop):
                    self.gpx.drop_row(self.selstart)            #each time we delete, the rest of the array is shifted. so we have to delete always the same index
        if text=="Delete non selected":
            if wx.MessageDialog(None, "Delete Points...?",\
                                'Are you sure you want to delete these points',\
                                wx.YES_NO | wx.ICON_QUESTION).ShowModal()==wx.ID_YES:
                for _ in range(self.selstop,self.gpx.get_row_count()):
                    self.gpx.drop_row(self.selstop)             #delete first end of range, to avoid shifting selstop
                for _ in range(0,self.selstart):
                    self.gpx.drop_row(0)
        if text=="Toggle points":
            self.gpx['ok']=np.invert(self.gpx['ok'])
        msgwrap.message("ValChanged",arg1=self.id)
        self.update_axis(self.ax1,self.plot1,self.ax1.get_ylim()[0],self.ax1.get_ylim()[1],self.autoy1, self.lineprops1, self.smooth1)
        self.update_axis(self.ax2,self.plot2,self.ax2.get_ylim()[0],self.ax2.get_ylim()[1],self.autoy2, self.lineprops2, self.smooth2)
        self.update_axis(self.ax3,self.plot3,self.ax3.get_ylim()[0],self.ax3.get_ylim()[1],self.autoy3, self.lineprops3, self.smooth3)
    
    def UpdateStatusBar(self,idx):
        if self.plot1!="none":
            msg1=self.plot1+\
                " ("+str(self.gpx.get_unit(self.plot1)[0])+"): "\
                +str(self.gpx[self.plot1][idx]*self.gpx.scale[self.plot1])
        else:
            msg1=""
        if self.plot2!="none":
            msg2=self.plot2+\
                " ("+str(self.gpx.get_unit(self.plot2)[0])+"): "\
                +str(self.gpx[self.plot2][idx]*self.gpx.scale[self.plot2])
        else:
            msg2=""
        if self.plot3!="none":
            msg3=self.plot3+\
                " ("+str(self.gpx.get_unit(self.plot3)[0])+"): "\
                +str(self.gpx[self.plot3][idx]*self.gpx.scale[self.plot3])
        else:
            msg3=""
        msgwrap.message("StatusChanged",arg1=self.id,\
                            arg2=self.gpx['time'][idx],\
                            arg3=msg1,\
                            arg4=msg2,\
                            arg5=msg3
                            )

    
class WxTimeWidget(WxLineScatterWidget):
    def __init__(self, *args, **kwargs):
        WxLineScatterWidget.__init__(self, *args, **kwargs)
        self.lineprops1=wxLineProps({'color':'#990000','fill':True})
        self.lineprops2=wxLineProps({'color':'#009900','fill':True})
        self.lineprops3=wxLineProps({'color':'#000099','fill':True})
    
    def XAxisAllowed(self):
        return 'time|duration|distance'
        
    def YAxisAllowed(self):
        l=''
        for name in self.gpx.get_header_names():
            if name not in ['time','ok'] and name[0]!='_':
                l+='|'+name
        l+='|none'
        return l[1:]
    
    def SetDefaultPlots(self):
        self.xaxis='time'
        self.plot1='speed'
        self.plot2='none'
        self.plot3='none'
        self.ax1.set_xlim([self.x_min(),self.x_max()])
        self.update_axis(self.ax1,self.plot1,0,1,True, self.lineprops1, self.smooth1)
        self.update_axis(self.ax2,self.plot2,0,1,True, self.lineprops2, self.smooth2)
        self.update_axis(self.ax3,self.plot3,0,1,True, self.lineprops3, self.smooth3)
            
class WxScatterWidget(WxLineScatterWidget):
    def __init__(self, *args, **kwargs):
        WxLineScatterWidget.__init__(self, *args, **kwargs)
        self.lineprops1=wxLineProps({'color':'#000099','linewidth':0,'marker':'o','markersize':3,'fill':False})
        self.lineprops2=wxLineProps({'color':'#009900','linewidth':0,'marker':'+','markersize':3,'fill':False})
        self.lineprops3=wxLineProps({'color':'#990000','linewidth':0,'marker':'^','markersize':3,'fill':False})
        self.enablecursor=False
        self.enablespan=False
        
    def XAxisAllowed(self):
        l=''
        for name in self.gpx.get_header_names():
            if name not in ['time','ok',] and name[0]!='_':
                l+='|'+name
        return l[1:]
        
    def YAxisAllowed(self):
        l=''
        for name in self.gpx.get_header_names():
            if name not in ['time','ok'] and name[0]!='_':
                l+='|'+name
        return l[1:]
    
    def SetDefaultPlots(self):
        self.xaxis='course'
        self.plot1='speed'
        self.plot2='none'
        self.plot3='none'
        self.ax1.set_xlim([self.x_min(),self.x_max()])
        self.update_axis(self.ax1,self.plot1,0,1,True, self.lineprops1, self.smooth1)
        self.update_axis(self.ax2,self.plot2,0,1,True, self.lineprops2, self.smooth2)
        self.update_axis(self.ax3,self.plot3,0,1,True, self.lineprops3, self.smooth3)
