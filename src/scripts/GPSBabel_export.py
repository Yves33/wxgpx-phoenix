import os,sys
import subprocess   # linked from autogui
import wx

def YesNo(question, caption = 'Yes or no?'):
    dlg = wx.MessageDialog(None, question, caption, wx.YES_NO | wx.ICON_QUESTION)
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    return result
def Info(message, caption = 'Insert program title'):
    dlg = wx.MessageDialog(None, message, caption, wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()
def Warn(message, caption = 'Warning!'):
    dlg = wx.MessageDialog(None, message, caption, wx.OK | wx.ICON_WARNING)
    dlg.ShowModal()
    dlg.Destroy()



# you should check the location of your gpxbabel installation
# and update its value in the strings below
if sys.platform=='darwin':
    gpsbabel="/Applications/GPSBabelFE.app/Contents/MacOS/gpsbabel"
    googleearth="/Applications/Google Earth.app/Contents/MacOS/Google Earth"
elif sys.platform=='win32':
    gpsbabel="C:\Program Files (x86)\GPSBabel\gpsbabel.exe"
    googleearth="C:\Program Files (x86)\Google\Google Earth\client\googleearth.exe"
else:
    gpsbabel="gpsbabel"
    googleearth=""

# build a list of supported formats
formats=subprocess.check_output([gpsbabel," -i"]).split("\n")
fformats=[f[1:].replace('\r','') for f in sorted(formats[35:733]) if not f.startswith("\t  ")]

#query user
try:
    (outfmt,outfile,options,google)=WxQuery("Export parameters",	\
				[('wxcombo','Output file format','|'.join(fformats),fformats[0],'str'),
                ('wxfile','Select name and location','',"C:\\",'str'),
                ('wxentry','Extra arguments',None,'','str'),
                ('wxcheck','Open with Earth',None,False,'bool')] \
				)
    infile=wx.StandardPaths.Get().GetTempDir()+"/gpsbabel.gpx"
    app.SaveFile(infile)
    args=" -t -i gpx -f " + infile + " -o " + outfmt.split(" ")[0] + " -F " + outfile
    subprocess.check_output([gpsbabel]+args.split())
    os.remove(infile)
    if google and outfmt.startswith('kml'):
       subprocess.check_output([googleearth,outfile]) 
except:
    dlg = wx.MessageDialog(None, "Whoups, something went wrong!", "Error", wx.OK | wx.ICON_WARNING)
    dlg.ShowModal()
    dlg.Destroy()


