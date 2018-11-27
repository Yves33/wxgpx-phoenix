import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
import wx

def idx2x(idx):
    return timeview.x_to_num(gpx[timeview.xaxis][idx])


# old construct showing an extra frame with a button that clears all the patches
# replaced with raw_input(promptstring)  
class ControlFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None, title='Script control')
        self.check=wx.CheckBox(self, label='A check box')
        self.dobut = wx.Button(self,-1,label='Do something')
        self.quitbut = wx.Button(self,-1,label='Quit')
        self.Bind(wx.EVT_BUTTON, self.onquitbutton, self.quitbut)
        self.Bind(wx.EVT_BUTTON, self.ondobutton, self.dobut)
        self.Bind(wx.EVT_CHECKBOX, self.oncheckbox, self.check)
        vbox= wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.check,1,wx.EXPAND)
        vbox.Add(self.dobut,1,wx.EXPAND)
        vbox.Add(self.quitbut,1,wx.EXPAND)
        self.SetSizer(vbox)
        # add patches, text and annotations to timeview

    def onquitbutton(self, evt):
        self.Destroy()
        
    def ondobutton(self, evt):
        print("Button was pressed")
        
    def oncheckbox(self, evt):
        print("checkbox is now: ",self.check.GetValue())
        
# the output goes to system console and not to wx.shell, unless we force it to go to the shell
sh.pyshell.redirectStdout(True)
control=ControlFrame(sh)
control.Show()