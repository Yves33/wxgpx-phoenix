#!/usr/bin/env python3
#ported to python 3.7 and wxPython 4.0.x (phoenix)

import sys,os,math,warnings
import wx
import wx.lib.masked    as wxmasked
import wx
import wx.adv
import base64
from io import StringIO

# a few globals
_radio_style=wx.RA_SPECIFY_COLS
_radio_dim=1
#("wxnotebook",message,None,                        None,           typ_)     #typ_=any. you must provide an lvalue, but None is returned
#("wxentry",   message,None,                        default_value,  typ_)     #typ_=str,float,int default value is automaticaly converted to str
#("wxcombo",   message,'choice1|choice2|choice3',   default_value,  typ_)     #typ_=str,int,float
#("wxlist",    message,'choice1|choice2|choice3',   default_value,  typ_)     #typ_=str,int,float
#("wxspin",    message,'min|max|inc',               default_value,  typ_)     #typ_=float,int,str  (number of digits calculated from that default value) increment is ignored
#("wxhscale",  message,'min|max|inc',               default_value,  typ_)     #typ_=float,int,str  (number of digits calculated from that default value) increment is ignored
#("wxcheck",   message,None,                        default_value,  typ_)     #typ_=bool,int,str
#("wxradio",   message,'choice1|choice2|choice3',   default_value,  typ_)     #typ_=int,str
#("wxcolor",   message,None,                        default_value,  typ_)     #typ_=str,float,int
#("wxcalendar",message,'min|max',                   default_value,  typ_)     #typ_=str,datetime
#("wxdate",    message,'min|max',                   default_value,  typ_)     #typ_=str
#("wxtime",    message,'min|max',                   default_value,  typ_)     #typ_=str
#("wxlabel",   message,None,                        None,           typ_)     #typ_=any you must provide an lvalue, but None is returned
#("wxicon",    message,'xsize|ysize',               iconpath,       None)     #typ_=any you must provide an lvalue, but None is returned
#("wxfile",    message,'filefilterstring',          default_file,   typ_)     #typ_=str if an empty string is given as filterstring, then you can choose non existing file (to save file)
#("wxdir",     message,'filefilterstring',          default_dir,    typ_)     #typ_=str
#('wxchecklist',message,'choice1|choice2|choice3,'choice2|choice3','str')     #typ_=str. you can also provide the indexes that should be checked by default
##
## more to come
##
#("wxbutton",message,None,                       default_value|icon,  typ_,func, [args])    #typ_=str,int,bool
#("wxtext", message,None,                        default_value,  typ_)                      #typ_=str.
#("wxhtml", message,None,                        default_value,  typ_)                      #typ_=str. you must provide an lvalue, but None is returned
## another idea would be to implement monitors
#("wxgauge", message, 'min|max|current',               callback|id,None)
#("wxmeter", message, 'min|max|current',               callback|id,None)
#("wxpeakmeter", message, 'min|max|current',           callback|id,None)
#("wxprogress", message,'min|max|current',             callback|id,None)
#ctrl.SetToolTip(wx.ToolTip(tooltip))

# could be parsed from json
{"var1":{
        "type":"wxlabel",
        "message":"description of the var",
        "range":"None",
        "value":"value",
        "return":"str"
        }
}


def get_digits(number):
    if'.' in  number:
        return len(number.split('.')[1])
    else:
        return 0

def convert(x,typ_):
    if typ_=='float':
        return float(x)
    elif typ_=='int':
        return int(x)
    elif typ_=='str':
        return str(x)
    elif typ_=='bool':
        return bool(x)

def querylist(li):
    #pythonic way
    return '|'.join (map(str,li))
    l=''
    for name in li:
        l+='|'+str(name)
    return l[1:]

def autocolor(color,_typ):
    if isinstance (color,str) and color.startswith('#') and len(color)==7:
        #got an html color
        if _typ=='str':
            return color
        elif _typ=='int':
            return tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2 ,4))
        elif _typ=='float':
            (r,g,b)= tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2 ,4))
            return(r/255.0,g/255.0,b/255.0)
    elif isinstance (color, tuple) and isinstance(color[0],float) and max(color)<=1.0:
        #got a float tupple
        (r,g,b)=color[0:3]
        if _typ=='str':
            col=wx.Colour(int(color[0]*255),int(color[1]*255),int(color[2]*255))
            return col.GetAsString(flags=wx.C2S_HTML_SYNTAX)
        elif _typ=='float':
            return (r,g,b)
        elif _typ=='int':
            return(int(r*255),int(g*255),int(b*255))
    elif isinstance (color, tuple) and isinstance(color[0],int) and max(color)<=255:
        #got a float tupple
        (r,g,b)=color[0:3]
        if _typ=='str':
            col=wx.Colour(color[0],color[1],color[2])
            return col.GetAsString(flags=wx.C2S_HTML_SYNTAX)
        elif _typ=='int':
            return (r,g,b)
        elif _typ=='float':
            return(r/255.0,g/255.0,b/255.0)
    elif isinstance (color, wx._core.Colour) and isinstance(color[0],int) and max(color)<=255:
        #got a float tupple
        (r,g,b)=color[0:3]
        if _typ=='str':
            return color.GetAsString(wx.C2S_HTML_SYNTAX)
        elif _typ=='int':
            return (r,g,b)
        elif _typ=='float':
            return(r/255.0,g/255.0,b/255.0)
    else:
        if _typ=='str':
            return '#000000'
        elif _typ=='int':
            return (0.0,0.0,0.0)
        elif _typ=='float':
            return(0,0,0)

def localpath(item):
    return os.path.dirname(os.path.abspath(__file__))+os.sep+os.sep+str(item)

class WxQueryDialog(wx.Dialog):
    def __init__(self,windowtitle, entries):
        wx.Dialog.__init__(self, None, title=windowtitle,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.entries=entries
        self.widgets=[]
        self.response=[]
        self.notebook=None

        if entries[0][0]!='wxnotebook':
            self.sizer = wx.FlexGridSizer(cols=2)
            self.panel=self
        else:
            self.sizer=None
            self.notebook=wx.Notebook(self)
            #wait for the notebook entry...
            pass
        disableditems=[]
        for entry in entries:
            #for readability...
            _widget=entry[0]
            _label=entry[1]
            _range=entry[2]
            _default=entry[3]
            _typ=entry[4]
            if len(entry)>5:
                _extra=entry[5:]
            if entry[0]=='wxnotebook':
                if self.sizer!=None:
                    self.sizer.Fit(self.panel)
                    self.sizer.Layout()
                self.panel=wx.Panel(self.notebook)
                self.widgets.append(self.panel)
                self.sizer=wx.FlexGridSizer(cols=2)
                self.widgets[-1].SetSizer(self.sizer)
                self.notebook.AddPage(self.widgets[-1],_label,False)
            elif entry[0]=='wxcombo':
                self.widgets.append(wx.ComboBox(self.panel,choices=_range.split('|'),value=""))
                self.widgets[-1].SetValue(str(_default))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxentry':
                self.widgets.append(wx.TextCtrl(self.panel,value=str(_default)))
                self.widgets[-1].SetValue(str(_default))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxspin':
                if _typ=='int':
                    self.widgets.append(wx.SpinCtrl(self.panel,\
                                                    min=int(_range.split('|')[0]),\
                                                    max=int(_range.split('|')[1]),\
                                                    value=str(_default)))
                elif _typ=='float':
                    self.widgets.append(wx.SpinCtrlDouble(self.panel,-1, \
                                                    min=float(_range.split('|')[0]),\
                                                    max=float(_range.split('|')[1]),\
                                                    inc=float(_range.split('|')[2]),\
                                                    value=str(_default)))
                    self.widgets[-1].SetDigits(get_digits(_range.split('|')[2]))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxhscale':
                self.widgets.append(wx.Slider(self.panel, minValue=int(_range.split('|')[0]),\
                                                            maxValue=int(_range.split('|')[1]),\
                                                            value=int(_default),\
                                                            size=(250, -1),\
                                                            style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxcheck':
                self.widgets.append(wx.CheckBox(self.panel, label=''))
                self.widgets[-1].SetValue(_default)
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                if _range!=None:
                    self.widgets[-1].SetName(_range)
                    self.widgets[-1].Bind(wx.EVT_CHECKBOX,self.OnCheckbox)
                    #_range='1|2|3|4' items 1,2,3,4 should be disabled when check is false
                    for x in _range.split('|'):
                        if int(x)>0 and _default==False:
                            disableditems.append(int(x))
                        elif int(x)<0 and _default==True:
                            disableditems.append(int(math.fabs(int(x))))
            elif entry[0]=='wxradio':
                self.widgets.append(wx.RadioBox(self.panel, label='',choices=_range.split('|'),style=wx.RA_SPECIFY_COLS,majorDimension=1))
                self.widgets[-1].SetSelection(_range.split('|').index(_default))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxcolor':
                self.widgets.append(wx.ColourPickerCtrl(self.panel))
                self.widgets[-1].SetColour(autocolor(_default,'str'))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxdate':
                self.widgets.append(wx.adv.DatePickerCtrl(self.panel))
                dt=wx.DateTime().Today()
                dt.SetYear(int(_default.split('-')[0]))
                dt.SetMonth(int(_default.split('-')[1]))
                dt.SetDay(int(_default.split('-')[2]))
                self.widgets[-1].SetValue(dt)
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxcalendar':
                self.widgets.append(wx.adv.CalendarCtrl(self.panel))
                dt=wx.DateTime().Today()
                dt.SetYear(int(_default.split('-')[0]))
                dt.SetMonth(int(_default.split('-')[1])-1)
                dt.SetDay(int(_default.split('-')[2]))
                self.widgets[-1].SetDate(dt)
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxtime':
                self.widgets.append(wxmasked.TimeCtrl(self.panel,fmt24hr = True))
                self.widgets[-1].SetValue(_default)
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxlabel':
                self.widgets.append(wx.StaticText(self.panel,label=_default))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wximage':
                img = wx.Image(_default)
                img.Rescale(int(_range.split('|')[0]), int(_range.split('|')[1]))
                bmp = wx.Bitmap(img)
                self.widgets.append(wx.StaticBitmap(self.panel,-1, bmp, wx.DefaultPosition, style=wx.BITMAP_TYPE_PNG))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wximage64':
                img = wx.ImageFromStream(cStringIO.StringIO(base64.b64decode(b64)))
                img.Rescale(int(_range.split('|')[0]), int(_range.split('|')[1]))
                bmp = wx.BitmapFromImage(img)
                self.widgets.append(wx.StaticBitmap(self.panel,-1, bmp, wx.DefaultPosition, style=wx.BITMAP_TYPE_PNG))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxlist':
                self.widgets.append(wx.ListBox(self.panel,choices=_range.split('|')))
                self.widgets[-1].SetSelection(_range.split('|').index(_default))
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxfile':
                if len(_range)!=0:
                    self.widgets.append(wx.FilePickerCtrl(self.panel,wildcard=_range))
                else:
                    self.widgets.append(wx.FilePickerCtrl(self.panel,wildcard=_range,style=wx.FLP_SAVE))
                self.widgets[-1].SetPath(_default)
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxdir':
                self.widgets.append(wx.DirPickerCtrl(self.panel))
                self.widgets[-1].SetPath(_default)
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            elif entry[0]=='wxchecklist':
                self.widgets.append(wx.CheckListBox(self.panel,choices=_range.split('|')))
                #try co convert _default to list of int
                if _default.split('|')[0].isdigit():
                    indexes = [int(i) for i in _default.split('|')]
                    self.widgets[-1].SetCheckedItems(indexes)
                else:
                    indexes = [_range.split('|').index(item) for item in _default.split('|')]
                    self.widgets[-1].SetCheckedItems(indexes)
                self.sizer.Add(wx.StaticText(self.panel,label=_label),1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
                self.sizer.Add(self.widgets[-1], 1, wx.ALL|wx.CENTER|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
            # any argument after typ_ is considered as tooltip, then  extra argument
            if len(entry)>5:
                self.widgets[-1].SetToolTip(wx.ToolTip(entry[5]))
        hbox = wx.BoxSizer(wx.VERTICAL)
        if self.notebook==None:
            self.sizer.Fit(self)
            hbox.Add(self.sizer, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        else:
            if self.sizer!=None:
                self.sizer.Fit(self.panel)
                self.sizer.Layout()
            hbox.Add(self.notebook, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        #disabled any items marked as disabled by checkboxes
        for i in disableditems:
            self.widgets[i].Disable()
        okBtn = wx.Button(self,wx.ID_OK,"OK")
        okBtn.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL,"Cancel")
        vbox= wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(okBtn, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(cancelButton, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        hbox.Add(vbox,flag=wx.EXPAND)
        self.SetSizer(hbox)
        self.sizer.Layout()
        hbox.Layout()
        self.sizer.Fit(self)
        hbox.Fit(self)
        self.ProcessEvent(wx.SizeEvent((-1,-1)))

    def GetValues(self):
        self.response=[]
        for idx in range(0,len(self.widgets)):
            _w=self.widgets[idx]
            _typ=self.entries[idx][4]
            if 'Panel' in str(type(_w)):
                self.response.append(None)
            elif 'ComboBox' in str(type(_w)):
                self.response.append(convert(_w.GetValue(),_typ))
            elif 'TextCtrl' in str(type(_w)):
                self.response.append(convert(_w.GetValue(),_typ))
            elif 'SpinCtrl' in str(type(_w)):
                self.response.append(convert(_w.GetValue(),_typ))
            elif 'FloatSpin' in str(type(_w)):
                self.response.append(convert(_w.GetValue(),_typ))
            elif 'Slider' in str(type(_w)):
                self.response.append(convert(_w.GetValue(),_typ))
            elif 'CheckBox' in str(type(_w)):
                self.response.append(convert(_w.GetValue(),_typ))
            elif 'RadioBox' in str(type(_w)):
                self.response.append(convert(_w.GetItemLabel(_w.GetSelection()),_typ))
            elif 'ColourPickerCtrl' in str(type(_w)):
                self.response.append(autocolor(_w.GetColour(),_typ))
            elif 'DatePickerCtrl' in str(type(_w)):
                self.response.append(convert(_w.GetValue().FormatISODate(),_typ))
            elif 'CalendarCtrl' in str(type(_w)):
                self.response.append(convert(_w.GetDate().FormatISODate(),_typ))
            elif 'TimeCtrl' in str(type(_w)):
                self.response.append(convert(_w.GetValue(),_typ))
            elif 'StaticText' in str(type(_w)):
                self.response.append(None)
            elif 'StaticBitmap' in str(type(_w)):
                self.response.append(None)
            elif 'ListBox' in str(type(_w)) and not 'CheckListBox' in str(type(_w)):
                self.response.append(convert(_w.GetString(_w.GetSelection()),_typ))
            elif 'FilePickerCtrl' in str(type(_w)):
                self.response.append(convert(os.path.normpath(_w.GetPath()),_typ))
            elif 'DirPickerCtrl' in str(type(_w)):
                self.response.append(convert(os.path.normpath(_w.GetPath()),_typ))
            elif 'CheckListBox' in str(type(_w)):
                self.response.append('|'.join(_w.GetCheckedStrings()))
            else:
                warnings.warn("Don't know how to convert "+str(type(_w)),UserWarning)
        return self.response

    def OnCheckbox(self,event):
        # checkbox becomes true
        name=event.GetEventObject().GetName()
        for i in [int(x) for x in name.split('|') if int(x)>0]:
            self.widgets[i].Enable(event.IsChecked())
        for i in [int(math.fabs(int(x))) for x in name.split('|') if int(x)<0]:
            self.widgets[i].Enable(not event.IsChecked())

def WxQuery(title, entries):
    dlg = WxQueryDialog(title,entries)
    res = dlg.ShowModal()
    values=None
    if res == wx.ID_OK:
       values=dlg.GetValues()
    #dlg.Destroy()
    return values

if __name__ == "__main__":
    import os
#NAUTILUS_SCRIPT_SELECTED_FILE_PATHS    Newline-delimited paths for selected files (only if local)
#NAUTILUS_SCRIPT_SELECTED_URIS          Newline-delimited URIs for selected files
#NAUTILUS_SCRIPT_CURRENT_URI            The current location
#NAUTILUS_SCRIPT_WINDOW_GEOMETRY        The position and size of the current window
#targets = os.environ.get('NAUTILUS_SCRIPT_SELECTED_FILE_PATHS,'').splitlines()
#see also http://www.ibm.com/developerworks/library/l-script-linux-desktop-2/

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
             ('wxdate','Date','2014-05-10|2015-05-10','2015-02-10','str'),
             ('wxtime','Time','00:00:00|23:59:59','12:30:17','str'),
             ('wxcalendar','Calendar','2014-05-10|2015-05-10','2015-05-10','str'),                  #20
             ('wxnotebook','Static',None,None,None),
             ('wxlabel','A label',None,'Second part of label','str','tooooltiiip'),
             ('wximage','An Image','32|32',localpath('icon.png'),'str'),
             ('wxnotebook','Picker',None,None,None),
             ('wxcolor','Color Picker',None,'#AA0055','str'),                                       #25
             ('wxcolor','Color Picker (int)',None,(255,0,0),'int'),
             ('wxcolor','Color Picker (float)',None,(1.0,0.0,0.0),'float'),
             ('wxfile','File picker','Acrobat files (*.pdf)|*.pdf',"C:\\",'str','extra1',23.154),
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
    print (WxQuery("A sample dialog",entries))
    app.MainLoop()
