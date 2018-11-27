#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-#
import os,sys
import wx
import wx.aui
import wx.adv
import msgwrap

class wxStatusBarWidget(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent)
        self.SetFieldsCount(4)
        self.SetStatusWidths([-1, -1, -1, -1])
        self.SetStatusText("A status Bar...", 0)
        self.SetStatusText("A status Bar...", 1)
        self.SetStatusText("A status Bar...", 2)
        self.SetStatusText("A status Bar...", 3)

        msgwrap.register(self.OnSigStatusChanged, signal="StatusChanged")
        
    def OnSigStatusChanged(self, arg1,arg2,arg3,arg4,arg5):
        self.SetStatusText(arg2, 0)
        self.SetStatusText(arg3, 1)
        self.SetStatusText(arg4, 2)
        self.SetStatusText(arg5, 3)
