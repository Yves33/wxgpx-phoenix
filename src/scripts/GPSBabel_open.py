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
elif sys.platform=='win32':
    gpsbabel="C:\Program Files (x86)\GPSBabel\gpsbabel.exe"
else:
    gpsbabel="gpsbabel"

# build a list of supported formats
formats=subprocess.check_output([gpsbabel," -i"]).split("\n")
fformats=[f[1:].replace('\r','') for f in formats[35:733] if not f.startswith("\t  ")]

#query user
try:
    (infmt,infile,options)=WxQuery("File to import",	\
				[('wxcombo','Input file format','|'.join(fformats),fformats[0],'str'),
                ('wxfile','Select file','Any file (*.*)|*.*',"C:\\",'str'),
                ('wxentry','Extra arguments',None,'','str')] \
				) 
    outfile=wx.StandardPaths.Get().GetTempDir()+"/gpsbabel.tmp"
    args=" -t -i " + infmt.split(" ")[0] + " -f " + infile + " -o gpx -F "+outfile
    subprocess.check_output([gpsbabel]+args.split())
    app.OpenFile(outfile)
    gpx=app.gpx
    os.remove(outfile)
except:
    dlg = wx.MessageDialog(None, "Whoups, something went wrong!", "Error", wx.OK | wx.ICON_WARNING)
    dlg.ShowModal()
    dlg.Destroy()


