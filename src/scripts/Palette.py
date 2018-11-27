'''
    This script enables using any palette from matplotlib to display gpx trace on the map.
    Illustrates dynamic code execution and linking through monkey patching.
    Very dangerous, but soooo efficient!
'''


import matplotlib.cm as cm
import matplotlib.pyplot as plt
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import wxmapwidget
from wxmapwidget import FloatToRGB

mymonkeypatch='''
def MyBuildColorTable(self,meas):
    _meas_='%s'
    _cmap_='%s'
    cmin=self.gpx[_meas_].min()
    crange=self.gpx[_meas_].max()-cmin
    palette = plt.get_cmap(_cmap_)
    for idx in range(0,len(self.gpx[_meas_])-1):
        value=(float(self.gpx[_meas_][idx]-cmin)/crange)
        self._gpx['_r'][idx]= int(255*palette(value)[0])
        self._gpx['_g'][idx]= int(255*palette(value)[1])
        self._gpx['_b'][idx]= int(255*palette(value)[2])
'''
 
myoriginalroutine='''
def MyBuildColorTable(self,meas):
        if meas not in self.gpx.get_header_names():
            #build palette from provided color
            self._gpx['_r']=self.trackcolordefault[0]*255
            self._gpx['_g']=self.trackcolordefault[1]*255
            self._gpx['_b']=self.trackcolordefault[2]*255
            return
        cmin=self.gpx[meas].min()
        crange=self.gpx[meas].max()-cmin
        for idx in range(0,len(self.gpx[meas])-1):
            value=(float(self.gpx[meas][idx]-cmin)/crange)
            self._gpx['_r'][idx]= FloatToRGB(value)[0]
            self._gpx['_g'][idx]= FloatToRGB(value)[1]
            self._gpx['_b'][idx]= FloatToRGB(value)[2]
''' 
        
        
mpl_color_maps=['viridis', 'inferno', 'plasma', 'magma','Blues', 'BuGn', 'BuPu','GnBu', 'Greens', 'Greys', 'Oranges', 'OrRd',   \
                'PuBu', 'PuBuGn', 'PuRd', 'Purples', 'RdPu','Reds', 'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd','afmhot', 'autumn',    \
                'bone', 'cool','copper', 'gist_heat', 'gray', 'hot','pink', 'spring', 'summer', 'winter','BrBG', 'bwr',         \
                'coolwarm', 'PiYG', 'PRGn', 'PuOr','RdBu', 'RdGy', 'RdYlBu', 'RdYlGn', 'Spectral','seismic','Accent','Dark2',   \
                'Paired', 'Pastel1','Pastel2', 'Set1', 'Set2', 'Set3','gist_earth', 'terrain', 'ocean', 'gist_stern','brg',     \
                'CMRmap', 'cubehelix','gnuplot', 'gnuplot2', 'gist_ncar','nipy_spectral', 'jet', 'rainbow','gist_rainbow',      \
                'hsv', 'flag', 'prism']
                           
(usempl,cmap,meas,color)=WxQuery("Color settings",[('wxcheck','Use matplotlib','1|2',True,'bool'),\
                                        ('wxcombo','Color Map','|'.join(mpl_color_maps),'jet','str'),\
                                        ('wxcombo','Measurement','|'.join(gpx.get_header_names()),'speed','str'),\
                                        ('wxcolor','Indicator color',None,mapview.GetNamedLayer('Gpx layer').currentcolor,'float')])
if usempl:                                       
    exec(mymonkeypatch % (meas,cmap))
else:
    exec(myoriginalroutine)
wxmapwidget.GpxMapLayer.BuildColorTable=MyBuildColorTable
mapview.GetNamedLayer('Gpx layer').currentcolor=color+(1.0,)
sh.upd()
