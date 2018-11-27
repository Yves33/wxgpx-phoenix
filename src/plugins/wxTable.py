#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-#
## system imports
import os,sys
import inspect
import wx
import wx.grid as  wxgrid
import wx.lib.newevent

import numpy as np

## local modules imports 
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import msgwrap
import gpxobj
from wxquery.wxquery import WxQuery

class WxGpxTable(wx.grid.GridTableBase):
    def __init__(self,gpx):
        wx.grid.GridTableBase.__init__(self)
        self.gpx=gpx
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        
    def GetColLabelValue(self, col):
        return self.gpx.get_header_names()[col]

    def GetNumberRows(self):
        return self.gpx.get_row_count()

    def GetNumberCols(self):
        return self.gpx.get_col_count()

    def GetValue(self, row, col):
        try:
            if col > self.GetNumberCols():
                raise IndexError
            typ=self.gpx.get_header_types()[col]
            key=self.gpx.get_header_names()[col]
            if typ=='|b1':
                return int(self.gpx[key][row])
            elif typ=='<f8':
                return float(self.gpx[(key,1,0)][row])
            else:
                return str(self.gpx[key][row])
        except IndexError:
            return None
    
    def GetTypeName(self, row, col):
        try:
            if col > self.GetNumberCols():
                raise IndexError
            typ=self.gpx.get_header_types()[col]
            if typ=='|b1':
                return wx.grid.GRID_VALUE_BOOL
            elif typ=='<f8':
                return wx.grid.GRID_VALUE_FLOAT
            elif typ=='<i4':
                return wx.grid.GRID_VALUE_NUMBER
            else :
                return wx.grid.GRID_VALUE_STRING
        except IndexError:
            return None
        
    def SetValue(self, row,col,value):
        typ=self.gpx.get_header_types()[col]
        key=self.gpx.get_header_names()[col]
        if typ=='|b1':
            self.gpx[key][row]=(value==True)
        elif typ=='<f8':
            self.gpx[key][row]=float(value)/float(self.gpx.get_scale(key))
        elif typ=='<i4':
            self.gpx[key][row]=int(value)
        else:
            self.gpx[key][row]=str(value)
        
    def IsEmptyCell(self, row, col):
        if col > self.GetNumberCols():
            return True
        key=self.gpx.get_header_names()[col]
        if self.gpx[key][row] is not None:
            return True
        else:
            return False
                
class WxGpxGrid(wx.grid.Grid):
    def __init__(self,parent):
        wx.grid.Grid.__init__(self, parent, wx.NewId())
        self.parent=parent
        self.SetTable(None)
        #self.SetDefaultCellFont(wx.Font(10,wx.FONTFAMILY_DEFAULT,wx.NORMAL,wx.FONTWEIGHT_NORMAL,False))
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,self.OnLeftMouseDown)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnGridRightMouseDown)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightMouseDown)
        
    def AttachGpx(self,gpx):
        self.gpxtable=WxGpxTable(gpx)
        self.SetTable(self.gpxtable)
        self.SetDefaultCellOverflow(False)
        for col in range(0,gpx.get_col_count()-1):
            typ=self.gpxtable.gpx.get_header_types()[col]
            key=self.gpxtable.gpx.get_header_names()[col]
            if typ=='|b1':
                self.SetColFormatBool(col)
                attr = wx.grid.GridCellAttr()
                attr.SetEditor(wx.grid.GridCellBoolEditor())
                attr.SetRenderer(wx.grid.GridCellBoolRenderer())
                self.SetColAttr(col,attr)
                self.SetColSize(col,25)
            else:
                if key!='time':
                    self.SetColFormatFloat(col,2,4)
        
    def DetachGpx(self):
        self.SetTable(None)
        self.gpxtable=None
        
    def OnCellChange(self,event):
        msgwrap.message("ValChanged",arg1=self.parent.id)
        event.Skip()
    
    def OnLeftMouseDown(self,event):
        row=event.GetRow()
        col=event.GetCol()
        typ=self.gpxtable.gpx.get_header_types()[col]
        if typ=='|b1':
            self.gpxtable.SetValue(row,col,not self.gpxtable.GetValue(row,col))
            self.ForceRefresh()
            #don't propagete event!
        else:
            event.Skip()
    
    def OnGridRightMouseDown(self,event):
        row,col=event.GetRow(),event.GetCol()
        if not hasattr(self,"copy_menu"):
            self.copy_menu = wx.Menu()
            item = self.copy_menu.Append(-1, "Copy")
            self.Bind(wx.EVT_MENU, self.OnGridPopup, item)
        self.PopupMenu(self.copy_menu)
    
    def OnGridPopup(self, event):
        item = self.copy_menu.FindItemById(event.GetId())
        text = item.GetText()
        if text=='Copy':
            self.OnCopy()
        else:
            pass
        
    def OnLabelRightMouseDown(self,event):
        row = event.GetRow()
        col = event.GetCol()
        if row==-1:
            if self.GetSelectedCols()==[]:
                return
            if not hasattr(self,"col_menu"):
                self.col_menu = wx.Menu()
                for text in ["Delete column","Append column","Sort ascending", "Sort descending"]:
                    item = self.col_menu.Append(-1, text)
                    self.Bind(wx.EVT_MENU, self.OnColPopup, item)
            self.PopupMenu(self.col_menu)
        elif col==-1:
            if self.GetSelectedRows()==[]:
                return
            if not hasattr(self,"row_menu"):
                self.row_menu = wx.Menu()
                for text in ["Enable selected","Disable selected","Enable non selected", "Disable non selected","Toggle points"]:
                    item = self.row_menu.Append(-1, text)
                    self.Bind(wx.EVT_MENU, self.OnRowPopup, item)
            self.PopupMenu(self.row_menu)
        
    def OnColPopup(self, event):
        item = self.col_menu.FindItemById(event.GetId())
        text = item.GetText()
        key=self.gpxtable.gpx.get_header_names()[self.GetSelectedCols()[0]]
        if text=="Delete column":
            dlg = wx.MessageDialog(None, "Destroy col \" %s \"" % key,"Confirm",wx.OK|wx.CANCEL|wx.ICON_WARNING)
            if dlg.ShowModal()==wx.ID_OK:
                self.gpxtable.gpx.drop_column(key)
                tmpgpx=self.gpxtable.gpx
                self.DetachGpx()
                self.AttachGpx(tmpgpx)
            dlg.Destroy()
        elif text=="Append column":
            (name,)=WxQuery("New column",[("wxentry","Column name",None,"buffer",'str')])
            self.gpxtable.gpx.append_column(name,'float')
            tmpgpx=self.gpxtable.gpx
            self.DetachGpx()
            self.AttachGpx(tmpgpx)
        elif text=="Sort ascending":
            self.gpxtable.gpx.sort_asc(key)
        elif text=="Sort descending":
            self.gpxtable.gpx.sort_desc(key)
        self.ForceRefresh()

    def OnRowPopup(self,event):
        item = self.row_menu.FindItemById(event.GetId())
        text = item.GetText()
        if text=='Enable selected':
            self.gpxtable.gpx['ok'][self.GetSelectedRows()]=True
        if text=='Disable selected':
            self.gpxtable.gpx['ok'][self.GetSelectedRows()]=False
        if text=='Enable non selected':
            ns=list(set(range(self.gpxtable.gpx.get_row_count()))-set(self.GetSelectedRows()))
            self.gpxtable.gpx['ok'][ns]=True
        if text=='Disable non selected':
            ns=list(set(range(self.gpxtable.gpx.get_row_count()))-set(self.GetSelectedRows()))
            self.gpxtable.gpx['ok'][ns]=False
        if text=='Toggle points':
            self.gpxtable.gpx['ok']=np.invert(self.gpxtable.gpx['ok'])
        self.ForceRefresh()
        '''pub.sendMessage("ValChanged",arg1=self.parent.id)'''
        msgwrap.message("ValChanged",arg1=self.parent.id)
        
    def OnCopy(self):
        if self.GetSelectionBlockTopLeft() == []:
            rows = 1
            cols = 1
            iscell = True
        else:
            rows = self.GetSelectionBlockBottomRight()[0][0] - self.GetSelectionBlockTopLeft()[0][0] + 1
            cols = self.GetSelectionBlockBottomRight()[0][1] - self.GetSelectionBlockTopLeft()[0][1] + 1
            iscell = False
        data = ''
        for r in range(rows):
            for c in range(cols):
                if iscell:
                    data += str(self.GetCellValue(self.GetGridCursorRow() + r, self.GetGridCursorCol() + c))
                else:
                    data += str(self.GetCellValue(self.GetSelectionBlockTopLeft()[0][0] + r, self.GetSelectionBlockTopLeft()[0][1] + c))
                if c < cols - 1:
                    data += '\t'
            data += '\n'
        clipboard = wx.TextDataObject()
        clipboard.SetText(data)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")
            
class WxTable(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.mapwidget = kwargs.pop('map', None)
        self.timewidget = kwargs.pop('time', None)
        wx.Panel.__init__(self,*args, **kwargs)
        self.id=wx.NewId()
        self.gpxgrid=WxGpxGrid(self)
        #standard events
        #self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftMouseDown)
        #self.Bind(wx.EVT_LEFT_UP,self.OnLeftMouseUp)
        #self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftMouseDblClick)
        #self.Bind(wx.EVT_MOTION,self.OnMouseMotion)
        #self.Bind(wx.EVT_ENTER_WINDOW,self.OnMouseEnter)
        #self.Bind(wx.EVT_LEAVE_WINDOW,self.OnMouseLeave)
        #self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightMouseDown)
        #self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        #self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        #self.Bind(wx.EVT_ERASE_BACKGROUND,self.OnErase)
        #custom events
        msgwrap.register(self.OnSigCurChanged, "CurChanged")
        msgwrap.register(self.OnSigSelChanged, "SelChanged")
        msgwrap.register(self.OnSigValChanged, "ValChanged")
               
    def AttachGpx(self,gpx):
        self.gpxgrid.AttachGpx(gpx)
        
    def DetachGpx(self):
        self.gpxgrid.DetachGpx()
        
    def OnSigSelChanged(self,arg1,arg2,arg3):
        if arg1==self.id:
            return
        self.gpxgrid.SelectRow(arg2,False)
        for row in range(arg2+1,arg3):
            self.gpxgrid.SelectRow(row,True)
        self.gpxgrid.MakeCellVisible(arg2,self.gpxgrid.GetGridCursorCol())
        
    def OnSigValChanged(self,arg1):
        if arg1==self.id:
            return
        # check if a new column or line has changed.
        if ((self.gpxgrid.gpxtable._rows==self.gpxgrid.gpxtable.GetNumberRows())\
            and(self.gpxgrid.gpxtable._cols==self.gpxgrid.gpxtable.GetNumberCols())):
            self.gpxgrid.ForceRefresh()
        else:
            tmpgpx=self.gpxgrid.gpxtable.gpx
            self.gpxgrid.DetachGpx()
            self.gpxgrid.AttachGpx(tmpgpx)
            self.gpxgrid.ForceRefresh()
            
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
        self.gpxgrid.SetSize(self.GetSize())
        
    def OnErase(self,event):pass
       
class Plugin(WxTable):
    def __init__(self, *args, **kwargs):
       WxTable.__init__(self, *args, **kwargs)  
    
    def GetName(self):
        return "Table"
