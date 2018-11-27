#!/usr/bin/env python
# adapted from https://github.com/sinapsi/wxpymaps/
import os,sys,math
import warnings
from threading import Thread,Timer
#import _thread
import urllib
import queue

import wx
import wx.lib.newevent

import base64
from io import StringIO,BytesIO

#from urllib import FancyURLopener
#from threading import Timer

try:
    from wx import glcanvas
    from OpenGL.extensions import alternate
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GL.ARB.framebuffer_object import *
    from OpenGL.GL.EXT.framebuffer_object import *
    from OpenGL.GL.EXT.framebuffer_blit import *
    from ctypes import *
    glGenFramebuffers=alternate(glGenFramebuffers,glGenFramebuffersEXT)
    glGenRenderbuffers=alternate(glGenRenderbuffers,glGenRenderbuffersEXT)
    glBindFramebuffer=alternate(glBindFramebuffer,glBindFramebufferEXT)
    glBlitFramebuffer=alternate(glBlitFramebuffer,glBlitFramebufferEXT)
    glBindRenderbuffer=alternate(glBindRenderbuffer,glBindRenderbufferEXT)
    glRenderbufferStorage=alternate(glRenderbufferStorage,glRenderbufferStorageEXT)
    glFramebufferRenderbuffer=alternate(glFramebufferRenderbuffer,glFramebufferRenderbufferEXT)
    glFramebufferTexture2D=alternate(glFramebufferTexture2D,glFramebufferTexture2DEXT)
    hasOpenGL = True
except ImportError:
    hasOpenGL = False

try:
    from OpenGL.GLUT import *
    hasGLUT=True
except ImportError:
    hasGLUT = False

DOWNLOAD_THREAD_NUM = 1
QUEUE_WAIT = 0.5
#map src format: ("friendly-name", "url/{x}/{y}/{z}/{q}","cache_dir")
#{x}{y}{z}{q} will be replaced with computed values of zoom, longitude, latitude or quadkey
# a list of possible urls can be found on https://leaflet-extras.github.io/leaflet-providers/preview/
# these values may change periodically - you can renew them using the monitor console from your web browser
#"https://khms2.google.com/kh/v=147&x={0}&y={1}&z={2}"
#"https://www.google.com/maps/vt/pb=!1m4!1m3!1i{2}!2i{0}!3i{1}!2m3!1e0!2sm!3i258145710"
#"https://c.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png"
#"http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
MAPSRC=[
("Google maps",                 "http://mt1.google.com/vt/lyrs=m@132&hl=en&x={x}&y={y}&z={z}","google_maps"),\
("Google terrain",              "http://mt1.google.com/vt/lyrs=t&x={x}&y={y}&z={z}","google_terrain"),\
("Google terrain+maps",         "http://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}","google_terrain_maps"),\
("Google satellite",            "http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}","google_satellite"),\
("Google satellite+maps",       "http://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}","google_satellite_maps"),\
("Open street maps",            "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png","openstreetmaps"),\
("Open cycle maps",             "http://b.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png","opencyclemaps"),\
("Open public transport",       "http://tile.xn--pnvkarte-m4a.de/tilegen/{z}/{x}/{y}.png","openpublictransport"),\
("Maps for free",               "http://khm1.googleapis.com/kh?v=175&hl=fr&x={x}&y={y}&z={z}&token=20949","mapsforfree"),\
("Virtual earth maps",          "http://a1.ortho.tiles.virtualearth.net/tiles/r{q}.jpeg?g=50","virtualearth_maps"),\
("Virtual earth satellite",     "http://a1.ortho.tiles.virtualearth.net/tiles/a{q}.jpeg?g=50","virtualearth_satellite"),\
("Virtual earth satellite+maps","http://a1.ortho.tiles.virtualearth.net/tiles/a{q}.jpeg?g=50","virtualearth_satellite_maps"),\
("Mapquest osm",                "http://otile1.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png","mapquestosm"),\
("Geoportail satellite",        "http://wxs.ign.fr/j5tcdln4ya4xggpdu4j0f0cn/geoportail/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image%2Fjpeg","geoportail"),\
("Here maps",                   "https://1.base.maps.api.here.com/maptile/2.1/maptile/2e2ccff948/normal.day/{z}/{x}/{y}/256/png8?app_id=xWVIueSv6JL0aJ5xqTxb&app_code=djPZyynKsbTjIUDOBcHZ2g&lg=eng&ppi=72","here_maps"),\
("Here satellite",              "https://1.aerial.maps.api.here.com/maptile/2.1/maptile/2e2ccff948/hybrid.day/{z}/{x}/{y}/256//png8?app_id=xWVIueSv6JL0aJ5xqTxb&app_code=djPZyynKsbTjIUDOBcHZ2g&lg=eng&ppi=72","here_satellite"),\
("Here terrain",                "https://4.aerial.maps.api.here.com/maptile/2.1/maptile/2e2ccff948/terrain.day/{z}/{x}/{y}/256/png8?app_id=xWVIueSv6JL0aJ5xqTxb&app_code=djPZyynKsbTjIUDOBcHZ2g&lg=eng&ppi=72","here_terrain"),\
("Mapquest maps",               "https://d.tiles.mapbox.com/v4/mapquest.streets-mb/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwcXVlc3QiLCJhIjoiY2Q2N2RlMmNhY2NiZTRkMzlmZjJmZDk0NWU0ZGJlNTMifQ.mPRiEubbajc6a5y9ISgydg","mapquest_maps"),\
("Mapquest satellite",          "https://d.tiles.mapbox.com/v4/mapquest.satellite-mb/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwcXVlc3QiLCJhIjoiY2Q2N2RlMmNhY2NiZTRkMzlmZjJmZDk0NWU0ZGJlNTMifQ.mPRiEubbajc6a5y9ISgydg","mapquest_satellite")
]

tile_to_download = queue.LifoQueue(maxsize=0)   #why a lifo and not a fifo?

(DownloadImageEvent, EVT_DOWNLOAD_IMAGE) = wx.lib.newevent.NewEvent()

#utility functions directly copied from globalmaptiles.py
def Haversine(lat1,lon1,lat2,lon2):
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    radius = 6378137    #meters
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1))* math.cos(math.radians(lat2))*math.sin(dlon/2)*math.sin(dlon/2)
    dist = radius*2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    #calculate course
    dlon=lon2-lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(dlon))
    course=(math.degrees(math.atan2(x,y))+360)%360
    return (dist,course)
    
def LatLonToMeters(lat, lon ):
    mx = lon * (math.pi*6378137) / 180.0
    my = math.log( math.tan((90 + lat) * math.pi / 360.0 )) / (math.pi / 180.0)
    my = my * (math.pi*6378137) / 180.0
    return mx, my

def MetersToPixels(mx, my, zoom):
    px = (mx + (math.pi*6378137)) / (2*math.pi*6378137/(256*(2**zoom)))
    py = (my + (math.pi*6378137)) / (2*math.pi*6378137/(256*(2**zoom)))
    return px, py

def MetersToLatLon(mx, my ):
    lon = (mx / (math.pi*6378137)) * 180.0
    lat = (my / (math.pi*6378137)) * 180.0
    lat = 180 / math.pi * (2 * math.atan( math.exp( lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat, lon

def PixelsToMeters(px, py, zoom):
    mx = px * (2*math.pi*6378137/(256*(2**zoom))) - (math.pi*6378137)
    my = py * (2*math.pi*6378137/(256*(2**zoom))) - (math.pi*6378137)
    return mx, my

def PixelsToLatLon(x,y,zoom):
    mx, my = PixelsToMeters(x, y, zoom)
    lat, lon = MetersToLatLon(mx, my)
    return -lat, lon

def LatLonToPixels(lat,lon,zoom):
    mx, my = LatLonToMeters(lat, lon)
    x, y = MetersToPixels(mx, my, zoom)
    y = ((2 ** zoom) * 256) - y
    return x, y
    
#main classes
class DownloadThread(Thread):
    def __init__(self,frame):
        Thread.__init__(self)
        self.frame = frame
    
    def GetUrl(self,x,y,z):
        def quad_key( tx, ty, zoom ):
            quadKey = ""
            for i in range(zoom, 0, -1):
                digit = 0
                mask = 1 << (i-1)
                if (tx & mask) != 0:
                    digit += 1
                if (ty & mask) != 0:
                    digit += 2
                quadKey += str(digit)
            return quadKey

        return self.frame.mapproviders[self.frame.GetMapSrc()][1].format(x=x,y=y,z=z,q=quad_key(int(x),int(y),int(z)))

    def DownloadTile(self, tile):
        x, y, zoom = map(str, tile.tile)
        url=self.GetUrl(x,y,zoom)
        filename = self.frame.GetCacheDir() + "/" + x + "-" + y + "-" + zoom + ".png"
        useragent=self.frame.http_user_agent

        if sys.version_info.major >= 3:
            try:
                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', useragent)]
                urllib.request.install_opener(opener)
                url = urllib.request.urlretrieve(url, filename)
                return url
            except IOError as e:
                return False
        else:
            try:
                opener = urllib.FancyURLopener()
                opener.addheaders = [("User-agent", useragent)]
                opener.retrieve(url,filename)
                #url = urllib.urlretrieve(url, filename)
            except IOError as e:
                return False

    def run(self):
        while True:
            tile = tile_to_download.get()
            self.img = self.DownloadTile(tile)
            if(self.img is not False):
                evt = DownloadImageEvent(downloaded_tile=tile)
                wx.PostEvent(self.frame, evt)
            tile_to_download.task_done()
#class mozurllib(FancyURLopener):
#        #version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'
#        #version = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.2 (KHTML, like Gecko) JavaFX/8.0 Safari/537.2'
#        version = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'
'''class DownloadThread2:
    def __init__(self, frame):
        self.frame = frame

    def start(self):
        _thread.start_new_thread(self.run, ())

    def stop(self):
        self.keepGoing = False

    def isrunning(self):
        return self.running

    def GetUrl(self,x,y,z):
        def quad_key( tx, ty, zoom ):
            quadKey = ""
            for i in range(zoom, 0, -1):
                digit = 0
                mask = 1 << (i-1)
                if (tx & mask) != 0:
                    digit += 1
                if (ty & mask) != 0:
                    digit += 2
                quadKey += str(digit)
            return quadKey

        return self.frame.mapproviders[self.frame.GetMapSrc()][1].format(x=x,y=y,z=z,q=quad_key(int(x),int(y),int(z)))

    def DownloadTile(self, tile):
        x, y, zoom = map(str, tile.tile)
        url=self.GetUrl(x,y,zoom)
        filename = self.frame.GetCacheDir() + "/" + x + "-" + y + "-" + zoom + ".png"
        useragent=self.frame.http_user_agent

        if sys.version_info.major >= 3:
            try:
                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', useragent)]
                urllib.request.install_opener(opener)
                url = urllib.request.urlretrieve(url, filename)
                return url
            except IOError as e:
                return False
        else:
            try:
                opener = urllib.FancyURLopener()
                opener.addheaders = [("User-agent", useragent)]
                opener.retrieve(url,filename)
                #url = urllib.urlretrieve(url, filename)
            except IOError as e:
                return False

    def run(self):
        while True:
            tile = tile_to_download.get()
            self.img = self.DownloadTile(tile)
            if(self.img is not False):
                evt = DownloadImageEvent(downloaded_tile=tile)
                wx.PostEvent(self.frame, evt)
            tile_to_download.task_done()'''

_gdebug=False
def debug(*str):
    if _gdebug:
        warnings.warn("debug:"+str,UserWarning)
        sys.stdout.flush()

class WxMapImage(object):
    def __init__(self):
        self.rotation=0
        self.scale=0
        self.anchor_x=0
        self.anchor_y=0
        self.hasalpha=0
        ##__GL specific stuff
        self.pixdata=''
        self.texid=0
        ##__wxImage specific stuff
        self.img=None  
        
    def __delete__(self):
        self.img.Destroy()
    
    def __makebuffers(self):
        self.rotation=0
        self.scale=1.0
        self.anchor_x=0
        self.anchor_y=0
        self.hasalpha=0
        if self.img.IsOk():
            self.w=self.img.GetWidth()
            self.h=self.img.GetHeight()
            self.hasalpha=self.img.HasAlpha()
            rgb=self.img.GetData()
            a=self.img.GetAlphaBuffer()
            if self.hasalpha:
                self.pixdata=bytearray(b'')
                for i in range(len(rgb)//3):
                    self.pixdata.append(rgb[3*i])
                    self.pixdata.append(rgb[3*i+1])
                    self.pixdata.append(rgb[3*i+2])
                    self.pixdata.append(a[i])
            else:
                self.pixdata=self.img.GetData()

    
    @classmethod
    def FromFile(cls,filename):
        obj=cls.__new__(cls)
        try:
            obj.img=wx.Image(filename,wx.BITMAP_TYPE_ANY)
        except:
            pass
        obj.__makebuffers()
        return obj

    @classmethod
    def FromBase64(cls,b64):
        obj=cls.__new__(cls)
        obj.img=wx.Image(BytesIO(base64.b64decode(b64)))
        obj.__makebuffers()
        return obj

    @classmethod
    def FromWxImage(cls,srcimg,rect=None):
        obj=cls.__new__(cls)
        if rect==None:
            obj.img=srcimg.GetSubImg(wx.Rect(0,0,srcimg.GetWidth(),srcimg.GetHeight()))
        else:
            obj.img=srcimg.GetSubImg(rect)
        obj.__makebuffers()
        return obj

    def AutoCenter(self):
        self.anchor_x=self.w/2
        self.anchor_y=self.h/2

    def Rotate(self, theta):
        self.rotation=theta

    def Scale (self, sf):
        self.scale=sf

class WxGLArtist(glcanvas.GLCanvas):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = kwargs.setdefault('style', wx.NO_FULL_REPAINT_ON_RESIZE) | wx.NO_FULL_REPAINT_ON_RESIZE
        glcanvas.GLCanvas.__init__(self, *args, **kwargs)
        self.context = glcanvas.GLContext(self)
        self.SetMinSize((250,250))
        self.width=250
        self.height=250
        self.inited=False                      # as the panel is not yet on screen, we can't set context. we have to wait
        self.pencolor=(1.0,1.0,1.0,1.0)
        self.brushcolor=(0.0,0.0,0.0,0.0)
        self.pensize=1.0
        self.usegl=True
        if hasGLUT:
            glutInit()
            self.font=GLUT_BITMAP_HELVETICA_12
        else:
            self.font=(wx.FONTFAMILY_SWISS,12)

    def SetPenColor(self,r,g,b,a):
        self.pencolor=(r,g,b,a)

    def SetBrushColor(self,r,g,b,a):
        self.brushcolor=(r,g,b,a)

    def SetLineWidth(self,size):
        self.pensize=size

    def Text(self,caption,x,y):
        if hasGLUT:
            glDisable(GL_TEXTURE_2D)
            glColor4f(*self.brushcolor)
            glRasterPos2i(int(x), int(y))
            for i in range(0,len(caption)):
                glutBitmapCharacter(self.font, ord(caption[i]))

    def SetFont(self,font):
        if hasGLUT:
            fontdict={'FIXED13':GLUT_BITMAP_8_BY_13,\
                      'FIXED15':GLUT_BITMAP_9_BY_15,\
                      'ROMAN10':GLUT_BITMAP_TIMES_ROMAN_10,\
                      'ROMAN24':GLUT_BITMAP_TIMES_ROMAN_24,\
                      'HELVETICA10':GLUT_BITMAP_HELVETICA_10,\
                      'HELVETICA12':GLUT_BITMAP_HELVETICA_12,\
                      'HELVETICA18':GLUT_BITMAP_HELVETICA_18}
            if font in fontdict:
                self.font=fontdict[font]
            else:
                self.font=fontdict['HELVETICA12']

    def Line(self,x1,y1,x2,y2):
        vertices=[x1,y1,x2,y2]
        self.Lines(vertices)

    def Lines(self,vertices):
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(self.pensize)
        vbo = glGenBuffers (1)
        glEnableClientState (GL_VERTEX_ARRAY)
        glDisableClientState (GL_TEXTURE_COORD_ARRAY)
        glDisableClientState (GL_COLOR_ARRAY)
        glBindBuffer (GL_ARRAY_BUFFER, vbo)
        glBufferData (GL_ARRAY_BUFFER,len(vertices)*4,(c_float*len(vertices))(*vertices), GL_STATIC_DRAW)
        glVertexPointer (2, GL_FLOAT, 0, ctypes.c_void_p(0*4))                           #size,type,stride,pointer to first vertex
        glLineWidth(self.pensize)
        glColor4f(*self.pencolor)
        glDrawArrays (GL_LINES, 0, len(vertices))
        glDeleteBuffers(1, GLuint(vbo))
        
    def RGBALines(self,vertices):
        #we suppose that vertices is an array [x,y,r,g,b,a,...]
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPolygonMode(GL_FRONT, GL_LINE)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT,GL_FASTEST)
        glLineWidth(self.pensize)
        vbo = glGenBuffers (1)
        glEnableClientState (GL_VERTEX_ARRAY)
        glEnableClientState (GL_COLOR_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glBindBuffer (GL_ARRAY_BUFFER, vbo)
        glBufferData (GL_ARRAY_BUFFER,len(vertices)*4,(c_float*len(vertices))(*vertices), GL_STATIC_DRAW)
        glVertexPointer (2, GL_FLOAT, 6*4, ctypes.c_void_p(0*4))                            #size,type,stride,pointer to first vertex
        glColorPointer (4,GL_FLOAT,6*4,ctypes.c_void_p(2*4))
        glLineWidth(self.pensize)
        glDrawArrays (GL_LINE_STRIP, 0, len(vertices)//6)
        glDeleteBuffers(1, GLuint(vbo))

    def Rect(self,l,t,r,b):
        vertices=[l,t,r,t,r,b,l,b]
        self.Polygon(vertices)

    def Circle(self,x,y,r):
        vertices=[]
        for i in range(30):
            vertices.append(r * math.cos(i*2*math.pi/30) + x)
            vertices.append(r * math.sin(i*2*math.pi/30) + y)
        self.Polygon(vertices)

    def Polygon(self,vertices):
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(self.pensize)
        vbo = glGenBuffers (1)
        glEnableClientState (GL_VERTEX_ARRAY)
        glDisableClientState (GL_TEXTURE_COORD_ARRAY)
        glDisableClientState (GL_COLOR_ARRAY)
        glBindBuffer (GL_ARRAY_BUFFER, vbo)
        glBufferData (GL_ARRAY_BUFFER,len(vertices)*4,(c_float*len(vertices))(*vertices), GL_STATIC_DRAW)
        glVertexPointer (2, GL_FLOAT, 0, ctypes.c_void_p(0*4))                            #size,type,stride,pointer to first vertex
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
        glColor4f(*self.brushcolor)
        glDrawArrays (GL_TRIANGLE_FAN, 0, len(vertices)//2)
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
        glLineWidth(self.pensize)
        glColor4f(*self.pencolor)
        glDrawArrays (GL_LINE_LOOP, 0, len(vertices)//2)
        glDeleteBuffers(1, GLuint(vbo))

    def Image(self,img,x,y):
        # Bug correction but awfull hack!!
        #savedtex=glGetIntegerv(GL_TEXTURE_BINDING_2D)
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        # end bug
        #that next part could be moved to nitialisation: we don't need to re-generate texture each time
        glEnable(GL_TEXTURE_2D)
        texid =glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        if img.hasalpha:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.w, img.h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img.pixdata)
        else:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.w, img.h, 0, GL_RGB, GL_UNSIGNED_BYTE, img.pixdata)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texid)
        glColor3f(1.0, 1.0, 1.0)
        glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
        # vertices=[x-img.anchor_x,y-img.anchor_y,0.0,0.0,\
                        # x-img.anchor_x, y+img.h-img.anchor_y,0.0,1.0,\
                        # x+img.w-img.anchor_x, y+img.h-img.anchor_y,1., 1.,\
                        # x+img.w-img.anchor_x, y-img.anchor_y,1., 0.]
        vertices=[-img.w/2,-img.h/2,0.0,0.0,\
                   -img.w/2,img.h/2,0.0,1.0,\
                   img.w/2,img.h/2,1., 1.,\
                   img.w/2,-img.h/2,1., 0.
                ]
        vbo = glGenBuffers(1)
        glEnableClientState(GL_VERTEX_ARRAY)
        glDisableClientState (GL_COLOR_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glBindBuffer (GL_ARRAY_BUFFER, vbo)
        glBufferData (GL_ARRAY_BUFFER,len(vertices)*4, \
                            (c_float*len(vertices))(*vertices), GL_STATIC_DRAW)
        glVertexPointer (2, GL_FLOAT, 4*4, ctypes.c_void_p(0*4))                      #size,type,stride,pointer to first vertex
        glTexCoordPointer(2,GL_FLOAT,4*4,ctypes.c_void_p(2*4))
        glPushMatrix()
        glTranslated(x+img.w/2,y+img.h/2,0)
        glRotated(img.rotation,0,0,1)
        glScaled(img.scale,img.scale,img.scale)
        glDrawArrays (GL_QUADS, 0, 4)
        glPopMatrix()
        glDeleteBuffers(1, GLuint(vbo))
        glDeleteTextures(GLuint(texid))
        #  Bug correction but awfull hack!!
        #glBindTexture(GL_TEXTURE_2D, savedtex)
        glPopAttrib()
        # end bug

    def LoadImageFromFile(self,path):
        return WxMapImage.FromFile(path)

    def LoadImageFromBase64(self,b64):
        return WxMapImage.FromBase64(b64)

    def LoadImageFromImage(self,img,rect=None):
        return WxMapImage.FromWxImage(img,rect)

    def MakeBuffer(self):
        self.SetCurrent(self.context)
        glEnable(GL_TEXTURE_2D)
        buff=glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, buff)
        tex=glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0,GL_RGBA,self.width, self.height,0,GL_RGBA,GL_UNSIGNED_INT,None)
        glTexEnvf( GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE )
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D,tex,0)
        return (buff,tex)

    def SizeBuffer(self,buff):
        self.SetCurrent(self.context)
        glBindFramebuffer(GL_FRAMEBUFFER_EXT,buff[0])
        glBindTexture(GL_TEXTURE_2D, buff[1])
        glTexImage2D(GL_TEXTURE_2D, 0,GL_RGBA,self.width, self.height,0,GL_RGBA,GL_UNSIGNED_INT,None)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(0,0,self.width, self.height)
        #gluOrtho2D(0,self.width,self.height,0)     # some pyopengl versions miss gluOrtho2D
        glOrtho(0,self.width,self.height,0,-1,1)
        return buff

    def UseBuffer(self,buff):
        self.SetCurrent(self.context)
        glBindFramebuffer(GL_FRAMEBUFFER, buff[0])
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(0, 0, self.width, self.height)
        #gluOrtho2D(0,self.width,self.height,0)     # some pyopengl versions miss gluOrtho2D
        glOrtho(0,self.width,self.height,0,-1,1)

    def BlitBuffer(self,srcbuffer,dstbuffer=(0,0),x=0,y=0):
        self.SetCurrent(self.context)
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        #crazy osx bug in pyopengl
        if sys.platform!='darwin':
            drawbuffer=glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING)
            readbuffer=glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dstbuffer[0])
        glBindFramebuffer(GL_READ_FRAMEBUFFER, srcbuffer[0])
        glBindTexture(GL_TEXTURE_2D,srcbuffer[0])
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
        glBegin(GL_QUADS)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        # preliminary work to enable partial zooming. but would require to also soom in each DrawOnscreen for each layer
        # abandonned feature
        #if False:
        #    hwidth=self.width/2
        #    hheight=self.height/2
        #    cx=hwidth
        #    cy=hheight
        #    glTexCoord2f(0., 1.);        glVertex2f(cx-hwidth, cy-hheight)
        #    glTexCoord2f(0., 0.);        glVertex2f(cx-hwidth, cy+hheight)
        #    glTexCoord2f(1., 0.);        glVertex2f(cx+hwidth, cy+hheight)
        #    glTexCoord2f(1., 1.);        glVertex2f(cx+hwidth, cy-hheight)
        glTexCoord2f(0., 1.);        glVertex2f(x, y)
        glTexCoord2f(0., 0.);        glVertex2f(x, x+self.height)
        glTexCoord2f(1., 0.);        glVertex2f(x+self.width, y+self.height)
        glTexCoord2f(1., 1.);        glVertex2f(x+self.width, y)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        if sys.platform!='darwin':
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, drawbuffer)
            glBindFramebuffer(GL_READ_FRAMEBUFFER, readbuffer)
        else:
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glPopAttrib()
        
    def SaveBuffer(self,buff,filename,imgtype=wx.BITMAP_TYPE_PNG):
        # try:
        #    from PIL import Image
        #    glBindFramebuffer(GL_FRAMEBUFFER, buff[0])
        #    glReadBuffer(GL_COLOR_ATTACHMENT0);
        #    rgba=glReadPixels(0,0,self.width,self.height,GL_RGB,GL_UNSIGNED_BYTE)
        #    image = Image.frombytes('RGBA', (self.width,self.height), rgba).transpose(Image.ROTATE_180).transpose(Image.FLIP_LEFT_RIGHT)
        #    image.save (filename)
        # except ImportError:
        #    print("unimplemented: missing pillow module")
        glBindFramebuffer(GL_FRAMEBUFFER, buff[0])
        glReadBuffer(GL_COLOR_ATTACHMENT0)
        rgb=glReadPixels(0,0,self.width,self.height,GL_RGB,GL_UNSIGNED_BYTE)
        img= wx.EmptyImage(self.width,self.height)
        img.SetData(rgb)
        img.Mirror(False).SaveFile(filename, imgtype)
        
    def ClearBuffer(self,buff=(0,0)):
        self.SetCurrent(self.context)
        glBindFramebuffer(GL_FRAMEBUFFER, buff[0])
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT)

    def StartDrawing(self):
        self.SetCurrent(self.context)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT)

    def DefaultBuffer(self):
        self.SetCurrent(self.context)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def EndDrawing(self):
        self.SetCurrent(self.context)
        self.SwapBuffers()

    def Resize(self,event):
        debug("renderer resize")
        self.width,self.height=event.GetSize()
        self.SetSize(wx.Size(self.width,self.height))

    def OnPaintGL(self,event):
        self.Draw(False)

class WxDCArtist(wx.Panel):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = kwargs.setdefault('style', wx.NO_FULL_REPAINT_ON_RESIZE) | wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__(self, *args, **kwargs)
        self.SetMinSize((250,250))
        self.width=250
        self.height=250
        self.inited=False                      # as the panel is not yet on screen, we can't set context. we have to wait
        self.pencolor=(1.0,1.0,1.0,1.0)
        self.brushcolor=(0.0,0.0,0.0,0.0)
        self.pensize=1.0
        self.usegl=False
        self.font=(wx.FONTFAMILY_SWISS,12)      #'HELVETICA12' for WxGLArtist
        #we maintain two variables,
        self._mainbuffer=wx.Bitmap.FromRGBA(32,32)
        self._curbuffer=self._mainbuffer
        self.SetBackgroundColour((0, 0, 0))

    def SetPenColor(self,r,g,b,a):
        self.pencolor=(r,g,b,a)

    def SetBrushColor(self,r,g,b,a):
        self.brushcolor=(r,g,b,a)

    def SetLineWidth(self,size):
        self.pensize=size

    def SetFont(self,font):
        fontdict={'FIXED13':(wx.FONTFAMILY_DEFAULT,13),\
                  'FIXED15':(wx.FONTFAMILY_DEFAULT,15),\
                  'ROMAN10':(wx.FONTFAMILY_ROMAN,10),\
                  'ROMAN24':(wx.FONTFAMILY_ROMAN,24),\
                  'HELVETICA10':(wx.FONTFAMILY_SWISS,10),\
                  'HELVETICA12':(wx.FONTFAMILY_SWISS,12),\
                  'HELVETICA18':(wx.FONTFAMILY_SWISS,18)}
        if font in fontdict:
            self.font=fontdict[font]
        else:
            self.font=fontdict['HELVETICA12']

    def Text(self,caption,x,y):
        dc=wx.GCDC(wx.MemoryDC(self._curbuffer))
        self._preparedc(dc)
        (width,height)=dc.GetTextExtent(caption)
        dc.DrawText(caption, x, y-height)

    def Line(self,x1,y1,x2,y2):
        dc=wx.GCDC(wx.MemoryDC(self._curbuffer))
        self._preparedc(dc)
        dc.DrawLine(x1,y1,x2,y2)

    def Lines(self,vertices):
        dc=wx.GCDC(wx.MemoryDC(self._curbuffer))
        self._preparedc(dc)
        for i in range(0,len(vertices)//4):
            dc.DrawLine(vertices[4*i],vertices[4*i+1],vertices[4*i+2],vertices[4*i+3])

    def RGBALines(self,vertices):
        dc=wx.GCDC(wx.MemoryDC(self._curbuffer))
        self._preparedc(dc)
        for i in range(0,len(vertices)//6-1):
                dc.SetPen(wx.Pen(wx.Colour(int(vertices[i*6+2]*255),int(vertices[i*6+3]*255),int(vertices[i*6+4]*255),int(vertices[i*6+5]*255)),self.pensize))
                dc.DrawLine(vertices[6*i],vertices[6*i+1],vertices[6*(i+1)],vertices[6*(i+1)+1])

    def Rect(self,l,t,r,b):
        dc=wx.GCDC(wx.MemoryDC(self._curbuffer))
        self._preparedc(dc)
        dc.DrawRectangle(l,t,(r-l),(b-t))

    def Circle(self,x,y,r):
        dc=wx.GCDC(wx.MemoryDC(self._curbuffer))
        self._preparedc(dc)
        dc.DrawCircle(x,y,r)

    def Polygon(self,vertices):
        points=[ (vertices[2*i],vertices[2*i+1]) for i in range(len(vertices)//2) ]
        dc=wx.GCDC(wx.MemoryDC(self._curbuffer))
        self._preparedc(dc)
        dc.DrawPolygon(points)

    def Image(self,img,x,y):
        dc=wx.GCDC(wx.MemoryDC(self._curbuffer))
        if img.rotation==0 and img.scale==1.0:
            dc.DrawBitmap(img.img.ConvertToBitmap(),x-img.anchor_x,y-img.anchor_y, False)
        else:
            dc.DrawBitmap(img.img.Scale(img.w*img.scale,img.h*img.scale)\
                            .Rotate(img.rotation*0.017453,wx.Point(img.anchor_x*img.scale,img.anchor_y*img.scale))\
                            .ConvertToBitmap(),x-img.anchor_x*img.scale,y-img.anchor_y*img.scale, False)

    def LoadImageFromFile(self,path):
        return WxMapImage.FromFile(path)

    def LoadImageFromBase64(self,b64):
        return WxMapImage.FromBase64(b64)

    def LoadImageFromImage(self,img,rect=None):
        return WxMapImage.FromWxImage(img,rect)

    def _buff2dc(self,buff=None):
        if buff!=None:
            dc=wx.GCDC(wx.MemoryDC(buff))
        else:
            dc=wx.GCDC(wx.MemoryDC(self._mainbuffer))
        return dc

    def _preparedc(self,dc):
        dc.SetPen(wx.Pen(wx.Colour(int(self.pencolor[0]*255),\
                                int(self.pencolor[1]*255),\
                                int(self.pencolor[2]*255),\
                                int(self.pencolor[3]*255)),\
                                self.pensize))
        dc.SetBrush(wx.Brush(wx.Colour(int(self.brushcolor[0]*255),\
                                    int(self.brushcolor[1]*255),\
                                    int(self.brushcolor[2]*255),\
                                    int(self.brushcolor[3]*255))))
        dc.SetTextForeground(wx.Colour(int(self.pencolor[0]*255),\
                                int(self.pencolor[1]*255),\
                                int(self.pencolor[2]*255),\
                                int(self.pencolor[3]*255)))
        dc.SetTextBackground(wx.Colour(int(self.brushcolor[0]*255),\
                                    int(self.brushcolor[1]*255),\
                                    int(self.brushcolor[2]*255),\
                                    int(self.brushcolor[3]*255)))
        dc.SetFont(wx.Font(self.font[1],self.font[0],wx.NORMAL,wx.FONTWEIGHT_NORMAL,False))

    def MakeBuffer(self):
        width=max(self.width,1)
        height=max(self.height,1)
        return wx.Bitmap.FromRGBA(width,height)

    def SizeBuffer(self,buff):
        return wx.Bitmap.FromRGBA(self.width,self.height)

    def UseBuffer(self,buff):
        self._curbuffer=buff

    def BlitBuffer(self,srcbuff,dstbuff=None,x=0,y=0):
        dc=self._buff2dc(dstbuff)
        dc.SetClippingRegion(0,0,self.width,self.height)
        dc.DrawBitmap(srcbuff, 0, 0,False)
        
    def SaveBuffer(self,buff,filename,imgtype=wx.BITMAP_TYPE_PNG):
        buff.SaveFile(filename,imgtype)
        
    def ClearBuffer(self,buff=None):
        dc=self._buff2dc(buff)
        dc.SetBackground(wx.Brush(wx.Colour(0,0,0,0)))
        dc.Clear()

    def DefaultBuffer(self):
        self._curbuffer=self._mainbuffer

    def StartDrawing(self):
        del self._mainbuffer
        self._mainbuffer=wx.Bitmap.FromRGBA(self.width, self.height)
        dc=wx.GCDC(wx.MemoryDC(self._mainbuffer))
        dc.SetBackground(wx.Brush(wx.Colour(0,0,0,255)))
        dc.Clear()

    def EndDrawing(self):
        if self._mainbuffer.IsOk() and self.IsShownOnScreen():
            wx.ClientDC(self).DrawBitmap(self._mainbuffer, 0, 0)

    def Resize(self,event):
        debug("renderer resize")
        self.width,self.height=event.GetSize()
        self.SetSize(wx.Size(self.width,self.height))

    def OnPaintDC(self,event):
        self.Draw(False)

class WxMapBase(wx.Panel):
    def __init__(self, parent,*args, **kwargs):
        self.localcache = kwargs.pop('localcache', None)
        self.usegl= kwargs.pop('usegl', None)
        self.numthreads= kwargs.pop('numthreads', DOWNLOAD_THREAD_NUM)
        wx.Panel.__init__(self, parent,*args, **kwargs)
        self.width, self.height=self.GetSize()
        # initialize renderer and pack it into panel
        self.sizer = wx.BoxSizer()
        if self.usegl and hasOpenGL:
            self.renderer=WxGLArtist(self)
        else:
            self.renderer=WxDCArtist(self)
        self.sizer.Add(self.renderer, 0, wx.EXPAND)
        self.SetSizerAndFit(self.sizer)
        # set initial parameters
        self.mapproviders=MAPSRC
        self.http_user_agent='Mozilla/5.0 (X11; Fedora; Linux) Gecko/20100101 Firefox/63.0'
        self.SetMapSrc(5)
        self.zoom = 2
        self.centerlat = 44.8404400
        self.centerlon = -0.5805000
        self.dragging=False
        self.inited=False
        self.layers=[]
        self.layerorder=1
        #create cursors
        self.stdcursor=wx.Cursor(wx.CURSOR_ARROW)
        self.handcursor=wx.Cursor(wx.CURSOR_BULLSEYE)
        #self.handcursor=wx.Cursor(wx.CURSOR_HAND)

        for i in range(self.numthreads):
            DT = DownloadThread(self)
            DT.name = str(i)
            DT.start()

        # event binding
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.renderer.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(EVT_DOWNLOAD_IMAGE,self.OnDownload)
        # other events are trapped by renderer
        self.renderer.Bind(wx.EVT_LEFT_DOWN,self.OnLeftMouseDown)
        self.renderer.Bind(wx.EVT_LEFT_UP,self.OnLeftMouseUp)
        self.renderer.Bind(wx.EVT_MOTION,self.OnMouseMotion)
        self.renderer.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftMouseDblClick)
        self.renderer.Bind(wx.EVT_RIGHT_DOWN,self.OnRightMouseDown)
        self.renderer.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        self.renderer.Bind(wx.EVT_ENTER_WINDOW,self.OnMouseEnter)
        self.renderer.Bind(wx.EVT_LEAVE_WINDOW,self.OnMouseLeave)
        #keyboard
        self.renderer.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)
        self.renderer.Bind(wx.EVT_KEY_UP,self.OnKeyUp)
        self.renderer.Bind(wx.EVT_CHAR,self.OnChar)
        self.renderer.Bind(wx.EVT_SIZE,self.OnSize)
        self.renderer.Bind(wx.EVT_ERASE_BACKGROUND,self.OnErase)
        # create scale layer
        self.scalelayer= WxScaleLayer(self)
        self.AppendLayer(self.scalelayer)

    def _calcbbox(self):
        self.width,self.height=self.ClientSize
        #calculate pixel coordinates of viewport
        self.center_x,self.center_y=LatLonToPixels(self.centerlat ,self.centerlon ,self.zoom)
        self.left=self.center_x-self.width/2
        self.right=self.center_x+self.width/2
        self.top=self.center_y-self.height/2
        self.bottom=self.center_y+self.height/2
        # calculate tile limits
        self.tile_left=int(math.floor(self.left/256))
        self.tile_right=int(math.ceil(self.right/256))
        self.tile_top=int(math.floor(self.top/256))
        self.tile_bottom=int(math.ceil(self.bottom/256))
        self.ori_x=self.tile_left*256-self.left
        self.ori_y=self.tile_top*256-self.top
        self.pixelscale=6378137*2*math.pi*math.cos(math.radians(self.centerlat))/(2**(self.zoom+8))
        #S=6372.7982*2*math.pi*cos(lat)/2^(z+8)
    ##
    ## public API starts here
    ##

    def LoadProviders(self, path):
        try:
            file=open(path,'r')
            self.mapproviders=[]
            for line in file.readlines():
                if line.startswith('#') or len(line.split(','))!=3:
                    continue
                name=line.split(',')[0]
                url=line.split(',')[1]
                cache=line.split(',')[2]
                self.AppendTileProvider(name.strip(' \t\n"'),url.strip(' \t\n"'),cache.strip(' \t\n"'))
        except IOError:
            warnings.warn("unable to open map providers",UserWarning)

    def AppendTileProvider(self,name,url,cache):
        self.mapproviders.append((name.strip(' \t\n"'),url.strip(' \t\n"'),cache.strip(' \t\n"')))

    def ShowScale(self):
        self.scalelayer.visible=True

    def HideScale(self):
        self.scalelayer.visible=False

    def GetMapSrc(self):
        return self.map_src

    def SetMapSrc(self,src):
        if type(src)==type(1):
            self.map_src=src
        elif type(src)==type('string'):
            self.map_src=[x[0] for x in self.mapproviders ].index(src)
        self.map_cache_dir=self.GetCacheDir()
        if not os.path.exists(self.GetCacheDir()):
            os.makedirs(self.GetCacheDir())

    def ListMapSrc(self):
        return [x[0] for x in self.mapproviders]

    def SetUserAgent(self,agent):
        self.http_user_agent=agent

    def GetCacheDir(self):
        old_app_name = wx.GetApp().GetAppName()
        wx.GetApp().SetAppName("WxMapwidget")
        if self.localcache==None:
            self.map_cache_dir = wx.StandardPaths.Get().GetUserDataDir()+os.sep+"cache"+os.sep+self.mapproviders[self.map_src][2]
        else:
            self.map_cache_dir = self.localcache+os.sep+"cache"+os.sep+self.mapproviders[self.map_src][2]
        wx.GetApp().SetAppName(old_app_name)
        return self.map_cache_dir

    def TruncCache(self,size=100*1048576,count=10000):
        file_paths = []
        cachesize=0
        for root, directories, files in os.walk(self.GetCacheDir()+os.sep+'..'+os.sep):
            for filename in files:
                filepath = os.path.join(root, filename)
                file_paths.append((filepath,os.path.getmtime(filepath),os.stat(filepath).st_size))
        #sort list and get the last size elements
        file_paths=sorted(file_paths, key= lambda tup: tup[1], reverse=True)
        #remove any file exceeding count
        for f in file_paths[count:]:
             os.remove(f[0])
        ##unfinished code. just does nothing
        #cachesize=sum([x[2] for x in file_paths])
        #while cachesize>maxbytes:
        #    file_paths.pop()
        #    cachesize=sum([x[2] for x in file_paths])

    def ScreenToGeo(self,x,y):
        return PixelsToLatLon(x+self.left,y+self.top,self.zoom)

    def GeoToScreen(self,lat,lon):
        tx,ty=LatLonToPixels(lat,lon,self.zoom)
        tx-=self.left
        ty-=self.top
        return tx,ty

    def EncloseGeoBbox(self,latmin,lonmin,latmax,lonmax):
        self.width=self.GetClientSize().width
        self.height=self.GetClientSize().height
        for z in range(0,22):
            t,l=LatLonToPixels(latmin,lonmin,z)
            b,r=LatLonToPixels(latmax,lonmax,z)
            if math.fabs(l-r)>self.width or math.fabs(b-t)>self.height:
                z=z-1
                break
        self.SetGeoZoomAndCenter(z,((latmin+latmax)/2,(lonmin+lonmax)/2))

    def SetGeoZoomAndCenter(self,zoom,center):
        self.zoom=zoom
        self.centerlat,self.centerlon=center
        self.Draw(True)
        self.Refresh()

    def GetGeoZoom(self):
        return self.zoom

    def GetGeoCenter(self):
        return (self.centerlat,self.centerlon)

    def AppendLayer(self,layer):
        self.layers.append(layer)

    def GetNamedLayer(self,name):
        for layer in self.layers:
            if layer.name==name:
                return layer

    def Translate(self,dx,dy):
        center_x,center_y=LatLonToPixels(self.centerlat,self.centerlon,self.zoom)
        center_x-=dx
        center_y-=dy
        self.centerlat,self.centerlon=PixelsToLatLon(center_x,center_y,self.zoom)
        self.Draw(True)

    def Zoom(self,zoominc,x,y):
        self.centerlat,self.centerlon=PixelsToLatLon(x+self.left,y+self.top,self.zoom)
        #make sure zoom is clamped between 0 and 22
        self.zoom=max(0,min(self.zoom+zoominc,22))
        #get new pixel coordinates for center, so that the same point stays at the same place
        center_x,center_y=LatLonToPixels(self.centerlat,self.centerlon,self.zoom)
        center_x+=self.width/2-x
        center_y+=self.height/2-y
        self.centerlat,self.centerlon=PixelsToLatLon(center_x,center_y,self.zoom)
        self.Draw(True)

    def GetPixelScale(self):
        return self.pixelscale
    # todo :
    # At present momment, it is the layer's responsability to call Draw() after handling event.
    # if several layers handle the same event (usualy not the case), this may result in several redraws.
    # this could be avoided by maintaining a dirty flag on map widget, and testing the flag after all layers have drawn
    # by default, layers are processed in normal order (bottom to top)

    def SetLayerProcessOrder(self,order):
        if order<0:
            self.layerorder=-1
        else:
            self.layerorder=1

    def OnLeftMouseDown(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnLeftMouseDown(event):return
        self.dragging=True
        self.x_dragori=event.GetX()
        self.y_dragori=event.GetY()
        self.SetCursor(self.handcursor)

    def OnLeftMouseUp(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnLeftMouseUp(event):return
        self.dragging=False
        self.SetCursor(self.stdcursor)

    def OnLeftMouseDblClick(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnLeftMouseDblClick(event):return

    def OnRightMouseDown(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnRightMouseDown(event):return

    def OnRightMouseUp(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnRightMouseUp(event):return

    def OnMouseWheel(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnMouseWheel(event):return
        if event.GetWheelRotation() > 0:
            self.Zoom(1,event.GetX(),event.GetY())
        else:
            self.Zoom(-1,event.GetX(),event.GetY())

    def OnMouseMotion(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnMouseMotion(event):return
        if self.dragging:
            self.Translate(event.GetX()-self.x_dragori,event.GetY()-self.y_dragori)
            self.x_dragori=event.GetX()
            self.y_dragori=event.GetY()

    def OnMouseEnter(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnMouseEnter(event):return
        self.SetFocus()                 # due to a bug in wxSplitterWindow

    def OnMouseLeave(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnMouseLeave(event):return

    def OnKeyUp(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnKeyUp(event):return

    def OnKeyDown(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnKeyDown(event):return
        if event.GetKeyCode()==wx.WXK_F10:
            self.Zoom(+1,self.width/2, self.height/2)
        if event.GetKeyCode()==wx.WXK_F11:
            self.Zoom(-1,self.width/2, self.height/2)
        if event.GetKeyCode()==wx.WXK_F5:
            self.Reload()

    def OnChar(self,event):
        for layer in self.layers[::self.layerorder]:
            if layer.OnChar(event):return

    def put_tile_in_queue(self, tile):
        if(tile.tile[2] == self.zoom):
            tile_to_download.put(tile)

    def Draw(self,updatebuffers=True):
        #the soft used to work without this exception handling! depends on wxPython version
        try:
            self.renderer.StartDrawing()
        except:
            warnings.warn("could not set context!! maybe next time",UserWarning)
            return
        if not self.inited:
            self.mapbuffer=self.renderer.MakeBuffer()
            self.layerbuffer=self.renderer.MakeBuffer()
            self.inited=True
        if updatebuffers:
            self._calcbbox()
            self.renderer.ClearBuffer(self.mapbuffer)
            self.renderer.UseBuffer(self.mapbuffer)
            # redraw map buffer
            for x in range(self.tile_left, self.tile_right):
                for y in range(self.tile_top, self.tile_bottom):
                    newtile=WxMapTile(self,x,y,self.zoom)
                    if newtile.DrawLocalTile(self.tile_left*256-self.ori_x,self.tile_top*256-self.ori_y):
                        pass
                    else:
                        #if(newtile.tile[2] == self.zoom):
                        #    tile_to_download.put(newtile)
                        #self.put_tile_in_queue(newtile)
                        t=Timer(QUEUE_WAIT, self.put_tile_in_queue,args=[newtile, ])
                        t.start()
            # redraw layer buffer
            self.renderer.UseBuffer(self.layerbuffer)
            self.renderer.ClearBuffer(self.layerbuffer)
            for layer in self.layers:
                layer.DrawOffscreen(None)
        # Blit the buffers
        self.renderer.BlitBuffer(self.mapbuffer)
        self.renderer.BlitBuffer(self.layerbuffer)
        self.renderer.DefaultBuffer()
        for layer in self.layers:
            layer.DrawOnscreen(None)
        self.renderer.EndDrawing()

    def Reload(self):
        for x in range(self.tile_left, self.tile_right):
            for y in range(self.tile_top, self.tile_bottom):
                os.remove(self.GetCacheDir() + os.sep+str(x)+"-"+str(y)+"-"+str(self.zoom)+".png")
        self.Draw(True)

    def OnSize(self,event):
        self.width, self.height = event.GetSize()
        self.renderer.Resize(event)
        if self.IsShownOnScreen():
            if self.inited:
                self.mapbuffer=self.renderer.SizeBuffer(self.mapbuffer)
                self.layerbuffer=self.renderer.SizeBuffer(self.layerbuffer)
            self.Draw(True)

    def OnPaint(self,event):
        self.Draw(False)

    def OnDownload(self,event):
        if (event.downloaded_tile is not None and (event.downloaded_tile.tile[2] == self.zoom)):
            self._calcbbox()
            self.renderer.UseBuffer(self.mapbuffer)
            newtile = event.downloaded_tile
            newtile.DrawLocalTile(self.tile_left*256-self.ori_x,self.tile_top*256-self.ori_y)
            self.Draw(False)
            self.Refresh()

    def OnErase(self,event):
        pass
    
    def CacheAll(self,maxzoom):
        lat1,lon1=self.ScreenToGeo(0,0)
        lat2,lon2=self.ScreenToGeo(self.width,self.height)
        zoom=self.zoom
        for z in range(self.zoom, maxzoom+1):
            start_x, start_y = tuple(int(x/256) for x in LatLonToPixels(lat1,lon1,z))
            stop_x, stop_y = tuple(int(x/256) for x in LatLonToPixels(lat2,lon2,z))
            # obviously, caching entire area will generate lots of tiles - just print what would be downloaded
            warnings.warn("\nzoom level:", z,"tile count: ", stop_x-start_x, " X ", stop_y-start_y," (",(stop_x-start_x)*(stop_y-start_y), "tiles)")
            warnings.warn("x range:", start_x, stop_x, " -- y range:", start_y, stop_y)
            for x in range(start_x,stop_x+1):
                for y in range(start_y, stop_y+1):
                    warnings.warn("downloading tile: {}/{}-{}-{}.png".format(self.GetCacheDir(),x,y,z))
    
class WxMapTile:
    def __init__(self, frame,x, y, zoom):
        self.tile = x, y, zoom
        self.frame = frame
        self.filename=self.frame.GetCacheDir() + "/" + str(x) + "-" + str(y) + "-" + str(zoom) + ".png"

    def DrawLocalTile(self, x_offset,y_offset):
        x, y, zoom = self.tile
        self.frame.renderer.SetPenColor(1.0,0.0,0.0,1.0)
        self.frame.renderer.SetLineWidth(1.0)
        if os.path.exists(self.filename):
            tile=WxMapImage.FromFile(self.frame.GetCacheDir() + "/" + str(x) + "-" + str(y) + "-" + str(zoom) + ".png")
            if tile.img.IsOk():
                self.frame.renderer.Image(tile,x * 256-x_offset, y * 256-y_offset)
                #self.frame.renderer.SetBrushColor(0.0,0.0,0.0,0.0)
                #self.frame.renderer.Rect(x*256-x_offset,y*256-y_offset,x*256-x_offset+256,y*256-y_offset+256)
                return True
        self.frame.renderer.SetBrushColor(0.8,0.8,0.8,1.0)
        self.frame.renderer.SetPenColor(0.0,0.0,0.0,1.0)
        self.frame.renderer.Rect(x*256-x_offset,y*256-y_offset,x*256-x_offset+256,y*256-y_offset+256)
        self.frame.renderer.SetPenColor(0.0,0.0,0.0,1.0)
        self.frame.renderer.SetBrushColor(0.0,0.0,0.0,1.0)
        self.frame.renderer.Text(str(x)+","+str(y), x*256-x_offset,y*256-y_offset)
        return False

#layers
class WxMapLayer(object):
    def __init__(self,parent,name="Generic layer"):
        self.visible=True
        self.parent=parent
        self.name=name
        self.active=True

    def Show(self):
        self.visible=True
        self.parent.Draw(False)

    def Hide(self):
        self.visible=False
        self.parent.Draw(False)

    def GetName(self):
        return self.name

    def GetOrder(self):
        idx=0
        for layer in self.parent.layers:
            if layer==self: return idx
            idx+=1

    def SetActive(self,active):
        self.active=active

    def DrawOffscreen(self,dc):pass
    def DrawOnscreen(self,dc):pass
    def OnLeftMouseDown(self,event):pass
    def OnLeftMouseUp(self,event):pass
    def OnLeftMouseDblClick(self,event):pass
    def OnRightMouseDown(self,event):pass
    def OnRightMouseUp(self,event):pass
    def OnMouseWheel(self,event):pass
    def OnMouseMotion(self,event):pass
    def OnMouseEnter(self,event):pass
    def OnMouseLeave(self,event):pass
    def OnKeyDown(self,event):pass
    def OnKeyUp(self,event):pass
    def OnChar(self, event):pass

class WxMapButton(object):
    def __init__(self,name,img,cb):
        self.name=name
        self.img=img
        self.rect=(0,0,self.img.w,self.img.h)
        self.selected=False
        self.cb=cb

    def Hit(self,x,y):
        return self.rect[0]<x<self.rect[2] and self.rect[1]<y<self.rect[3]

class WxToolLayer(WxMapLayer):
    def __init__(self, parent, name="Tool layer"):
        WxMapLayer.__init__(self,parent,name)
        self.tools=[]
        self.buttons=[]
        self.anchor_x=-5
        self.anchor_y=-5
        self.activetool=''
        self.padding=1
        self.colors=[(1.0,1.0,1.0,1.0),(0.9,0.9,0.9,0.9),(0.6,0.6,0.6,1.0),(0.6,0.6,0.6,0.6)]

    def __repack(self):
        dx=0
        dy=0
        for tool in self.tools:
            tool.rect=(-1*self.anchor_x+dx,\
                        -1*self.anchor_y+dy,\
                        -1*self.anchor_x+dx+tool.img.w,\
                        -1*self.anchor_y+dy+tool.img.h)
            dx+=0*(tool.img.w+self.padding)
            dy+=1*(tool.img.h+self.padding)

    def AppendTool(self,tool):
        self.tools.append(tool)
        self.__repack()

    def RemoveTool(self,name):
        for i in range(len(self.tools)):
            if self.tools[i].name==name:
                del self.tools[i]
        self.__repack()

    def SelectTool(self,name):
        for tool in self.tools:
            if tool.name!=name and not tool.selected:
                pass
            elif tool.name!=name and tool.selected:
                if tool.cb!=None:
                    tool.cb(False)
                tool.selected=False
            elif tool.name==name and not tool.selected:
                if tool.cb!=None:
                    tool.cb(True)
                tool.selected=True
        self.parent.Refresh()

    def DrawOffscreen(self,dc):
        pass

    def DrawOnscreen(self,dc):
        pen=self.parent.renderer
        for tool in self.tools:
            if tool.selected:
                pen.SetPenColor(*self.colors[0])
                pen.SetBrushColor(*self.colors[1])
            else:
                pen.SetPenColor(*self.colors[2])
                pen.SetBrushColor(*self.colors[3])
            pen.SetLineWidth(1.0)
            pen.Rect(tool.rect[0],tool.rect[1],tool.rect[2],tool.rect[3])
            pen.Image(tool.img,tool.rect[0],tool.rect[1])

    def OnLeftMouseDown(self,event):
        if self.active:
            for tool in self.tools:
                if tool.Hit(event.GetX(),event.GetY()):
                    self.SelectTool(tool.name)
                    self.parent.Draw(False)
                    return True

class WxScaleLayer(WxMapLayer):
    def __init__(self,parent,name="Scale layer"):
        WxMapLayer.__init__(self,parent,name)

    def DrawOnscreen(self,dc):
        self.parent._calcbbox()
        if self.visible:
            pixelscale=self.parent.pixelscale
            width,height=self.parent.GetClientSize()
            scalebarmeters=10**math.floor(math.log(width*pixelscale,10))
            scalebarpixels=scalebarmeters/pixelscale
            # reduce scale bar so it is not more than 150px
            while scalebarpixels>150:
                scalebarmeters/=2
                scalebarpixels/=2
            # adjust units to km or m
            if scalebarmeters>999.99:
                caption=str(scalebarmeters/1000)+ "km"
            else:
                caption=str(scalebarmeters)+ "m"
            pen=self.parent.renderer
            pen.SetLineWidth(4.0)
            pen.SetPenColor(1.0,1.0,1.0,1.0)
            pen.SetBrushColor(1.0,1.0,1.0,1.0)
            pen.Line(10,height-10,10+scalebarpixels,height-10)
            pen.SetFont('HELVETICA12')
            pen.Text(caption,10,height-25)

class WxPathLayer(WxMapLayer):
    def __init__(self,parent,name="Generic path layer"):
        WxMapLayer.__init__(self,parent,name)
        self.path=[]
        self.linewidth=2.0
        self.color=(1.0,1.0,1.0,1.0)
        self.pointwidth=3.0

    def SetPointWidth(self,width):
        self.pointwidth=width

    def SetPathColor(self, r,g,b,a):
        self.color=(r,g,b,a)

    def SetLineWidth(self,width):
        self.linewidth=width

    def GetPathLength(self):
        length=0
        if len(self.path)>1:
            for i in range(1,len(self.path)):
                lat1=self.path[i-1][0]
                lon1=self.path[i-1][1]
                lat2=self.path[i][0]
                lon2=self.path[i][1]
                length+=Haversine(lat1,lon1,lat2,lon2)[0]
        return length

    def AppendPoint(lat,lon):
        self.path.append((lat,lon))

    def DrawOffscreen(self,dc):
        pen=self.parent.renderer
        pen.SetLineWidth(self.linewidth)
        pen.SetPenColor(*self.color)
        pen.SetBrushColor(*self.color)
        pen.SetFont('HELVETICA12')
        for i in range(1,len(self.path)):
            x1,y1=self.parent.GeoToScreen(self.path[i-1][0],self.path[i-1][1])
            x2,y2=self.parent.GeoToScreen(self.path[i][0],self.path[i][1])
            pen.Line(x1,y1,x2,y2)
            pen.Circle(x2,y2,self.pointwidth)
        if len(self.path)>0:
            x1,y1=self.parent.GeoToScreen(self.path[0][0],self.path[0][1])
            pen.Circle(x1,y1,self.pointwidth)

    def OnLeftMouseDown(self,event):
        if self.active:
            self.path.append(self.parent.ScreenToGeo(event.GetX(),event.GetY()))
            self.parent.Draw(True)
            self.parent.Refresh()
            return True

    def OnRightMouseDown(self,event):
        if self.active:
            for i in range(len(self.path)):
                x,y=self.parent.GeoToScreen(self.path[i][0],self.path[i][1])
                if (x-event.GetX())**2+(y-event.GetY())**2<=self.pointwidth**2:
                    del self.path[i]
                    self.parent.Draw(True)
                    self.parent.Refresh()
                    return True

if __name__=='__main__':
    app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.
    frame = wx.Frame(None, wx.ID_ANY, "Hello World") # A Frame is a top-level window.
    mappanel=WxMapBase(frame,usegl=False)
    frame.Show(True)     # Show the frame.
    app.MainLoop()
