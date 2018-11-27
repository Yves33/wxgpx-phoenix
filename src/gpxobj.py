#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-#
import os,sys

from lxml import objectify,etree
import numpy as np
import numpy.lib.recfunctions as npr
import math
import re
import string
import datetime
import dateutil.parser
import zipfile
import pickle

from fitparse import FitFile

#units. only ascii chars, utf8 fails
units={   'SI'  :('System International units (m, s)',1.0),\
          'm'   :('meters',1.0),\
          's'   :('seconds',1.0),\
          'm/s' :('meters/second',1.0),\
          's/m' :('seconds/meter',1.0),\
          'km'  :('kilometer',1.0/1000),\
          'mi'  :('international mile',1.0/1609.344),\
          'nq'  :('nautic mile',1.0/1852.0),\
          'km/h':('kilometer per hour',3.6),\
          'mph' :('miles per hour',2.23693629),\
          'kts' :('knots',1.94384449),\
          'min/km':('minute per kilometer',16.6666667),\
          'min/mi':('minute per mile',26.8224),\
          'min' :('minutes',1/60.00),\
          'hr'  :('hours',1/3600),\
          'deg'   :('degrees',1.0)}

# scale and units are dictionnaries indexed by column keys
# d is an np.array

class GpxObj:
    def __init__(self):
        self.speedunit=0
        self.distunit=0
        self.scale={}
        self.unit={}
        self.offset={}
        self.d=None
        self.finename=None

    def __getitem__(self,tup):
        if not isinstance(tup, tuple):
            return self.d[tup]                      # don't bother...
        else:
            tup=tup+(False,False)                   # make sure our tuple has at least 3 items
            key,scaled,ok=tup[0],tup[1],tup[2]
            if not ok and not scaled:
                return self.d[key]
            if not ok and scaled:
                return self.d[key]*self.scale[key]
            if ok and not scaled:
                return self.d[key][np.where(self.d['ok']==True)]
            if ok and scaled:
                return self.d[key][np.where(self.d['ok']==True)]*self.scale[key]
            ## by the way, you can filter your data using something like
            #self.d['ok'][np.where(self.d[('speed',1,0)]>x,yz)]=0

    def __setitem__(self,key,value):
        self.d[key]=value

    def __repr__(self):
        print(self.d)

    def open_gpx(self, filename):
        #print(filename)
        self.gpxdoc = etree.parse(filename)
        self.filename=filename
        self.parse_trkpts()

    def close_gpx(self):
        self.gpxdoc = None
        del self.d
        del self.scale
        del self.unit

    def save_gpx(self,filename,fields=None,indices=None):
        self.save_xml(filename,fields,indices)

    def open_npz(self,filename):
        loadeddata=np.load(filename)
        self.d=loadeddata['d']
        self.unit=dict(zip(list(loadeddata['keys']),list(loadeddata['unit'])))
        self.scale=dict(zip(list(loadeddata['keys']),list(loadeddata['scale'])))

    def save_npz(self,filename):
        if False:
            keys = np.array(list(self.unit.keys()))
            unit = np.array(list(self.unit.values()))
            scale = np.array(list(self.scale.values()))
            np.savez(filename,keys=keys,unit=unit,scale=scale,d=self.d)
        else:
        ## the same filtering out unwanted columns (starting with underscore: private data for plugins)
            exportedkeys=[k for k in self.unit.keys() if not k.startswith('_')]
            keys = np.array([k for k in exportedkeys if not k.startswith('idx')])
            unit = np.array([self.unit[k] for k in exportedkeys])
            scale = np.array([self.scale[k] for k in exportedkeys])
            d =self.d[[k for k in exportedkeys+['ok']]]
            np.savez(filename,keys=keys,unit=unit,scale=scale,d=d)

    def get_trkseg_count(self):
        return sum(1 for _ in self.gpxdoc.iter('{*}trkseg'))

    def get_trkpt_count(self,seg=-1):
        if seg == -1:
            return sum(1 for _ in self.gpxdoc.iter('{*}trkpt'))
        else:
            return sum(1 for _ in self.gpxdoc.findall('.//{*}trkseg')[seg].findall('.//{*}trkpt'))

    def get_trkpt_elements(self):
        types=[]
        pt=self.gpxdoc.find('.//{*}trkpt')
        #we try to determine the type of element by trying to convert to int, then float, then text
        for child in pt.findall('.//{*}*'):
            #print(child)
            if re.sub(r'\{.*?\}', '', child.tag) in ['extensions','TrackPointExtension'] :
                continue
            try:
                x=int(child.text)
                types.append((re.sub(r'\{.*?\}', '', child.tag),'int'))
            except  ValueError:
                try:
                    x=float(child.text)
                    types.append((re.sub(r'\{.*?\}', '', child.tag),'float'))
                except  ValueError:
                    # specially for time, you may encounter points with 1/10 of seconds,
                    # in which case the Z will disappear, which will prevent correct computations
                    # another solution woul be to enzure the last charater of 'time' field is always 'Z'
                    types.append((re.sub(r'\{.*?\}', '', child.tag),'a'+str(len(child.text)+5)))
                pass
        return types

    def get_trkpt_element_names(self):
        tags=self.get_trkpt_elements()
        nam,typ=zip(*tags)
        return nam

    def get_trkpt_element_types(self):
        tags=self.get_trkpt_elements()
        nam,typ=zip(*tags)
        return typ

    def parse_trkpts(self,keys=None,trkseg=-1):
        if (keys==None) or (len(keys) == 0):
            keys=self.get_trkpt_elements()
        row=self.get_trkpt_count(trkseg)
        self.d=np.ones(row,dtype={'names':['ok'],'formats':['bool']})
        for key,typ in ([('lat','float'),('lon','float')]+keys):
            self.d=npr.rec_append_fields(self.d,key,np.zeros(row),typ)
            self.scale[key]=1.0
            self.unit[key]="SI"
        idx=0
        for trkpt in self.gpxdoc.iter('{*}trkpt'):
            self.d['lat'][idx] = float(trkpt.get('lat'))        # lat and lon are the only mandatory elements
            self.d['lon'][idx] = float(trkpt.get('lon'))        # lat and lon are the only mandatory elements
            for child in trkpt.findall('.//{*}*'):
                key=re.sub(r'\{.*?\}', '', child.tag)
                if key in self.d.dtype.names:
                    typ=dict(keys)[key]
                    if typ=='float':
                        self.d[key][idx]=float(child.text)
                    elif typ=='int':
                        self.d[key][idx]=int(child.text)
                    else:
                        self.d[key][idx]=child.text
            idx+=1
        self.append_column('idx','int')
        self['idx']=np.arange(self.get_row_count())

    def append_column(self,key,typ):
        self.d=npr.rec_append_fields(self.d,key,np.zeros(self.d.shape[0]),typ)
        self.scale[key]=1.0
        self.unit[key]="SI"

    def drop_column(self,key):
        self.d=npr.rec_drop_fields(self.d,key)
        del self.scale[key]
        del self.unit[key]

    def move_column(self, oldkey, newkey):
        headers=list(self.d.dtype.names)
        headers[headers.index(oldkey)]=newkey
        self.d.dtype.names=tuple(headers)
        self.scale[newkey]=self.scale.pop(oldkey)
        self.unit[newkey]=self.unit.pop(oldkey)

    def append_row(self, values):
        self.d = np.append(self.d, values)

    def drop_row(self,rownum):
        self.d=np.delete(self.d, (rownum), axis=0)
        self['idx']=np.arange(self.get_row_count())

    def get_last_row_idx(self):
        return (self.get_row_count()-1)

    def get_last_col_idx(self):
        return (self.get_col_count()-1)

    def get_headers(self):
        return self.d.dtype

    def get_header_names(self):
        res=[]
        for (name,typ) in self.get_headers().descr:
            res.append(name)
        return res

    def get_header_types(self):
        res=[]
        for (name,typ) in self.get_headers().descr:
            res.append(typ)
        return res

    def has_field(self,field):
        return str(field) in self.get_header_names()

    def get_col_count(self):
        return len(self.get_header_names())

    def get_row_count(self):
        (r,)=self.d.shape
        return r

    def set_unit(self,key,value):
        try:
            self.unit[key]=value
            self.scale[key]=units[value][1]
        except KeyError:
            self.unit[key]= ""
            self.scale[key]=1.0

    def get_unit(self,key):
        try:
            return (self.unit[key],units[self.unit[key]][0],units[self.unit[key]][1])
        except KeyError:
            return ("","",1.0)

    def get_unit_sym(self,key):
        try:
            return self.unit[key]
        except KeyError:
            return ""

    def get_unit_desc(self,key):
        try:
            return units[self.unit[key]][0]
        except KeyError:
            return ""

    def get_scale(self,key):
        try:
            return self.scale[key]
        except KeyError:
            return 1.0

    def set_scale(self, key, value):
        try:
            self.scale[key]=value
        except KeyError:
            self.scale[key]= 1.0

    def duration(self):
        d=np.zeros(self.get_row_count())
        for i in range(1,self.get_row_count()):
            #t1=datetime.datetime.strptime(self['time'][i-1],"%Y-%m-%dT%H:%M:%SZ")
            #t2=datetime.datetime.strptime(self['time'][i],"%Y-%m-%dT%H:%M:%SZ")
            t1=dateutil.parser.parse(self['time'][i-1])
            t2=dateutil.parser.parse(self['time'][i])
            d[i] =(t2-t1).total_seconds()
        return d

    def hv_distance(self):
        # vectorized version
        d=np.zeros(self.get_row_count())
        lat2=self.d['lat'] * np.pi / 180.0
        lon2=self.d['lon'] * np.pi / 180.0
        lat1=np.roll(self.d['lat'],1) * np.pi / 180.0
        lon1=np.roll(self.d['lon'],1) * np.pi / 180.0
        # haversine formula #### Same, but atan2 named arctan2 in numpy
        dlon = (lon2 - lon1)
        dlat = (lat2 - lat1)
        a = (np.sin(dlat/2))**2 + np.cos(lat1) * np.cos(lat2) * (np.sin(dlon/2.0))**2
        c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0-a))
        c[0]=0.0
        return 6371000 * c
        #loop version much slower than above vectorized version
        #d=np.zeros(self.get_row_count())
        #for i in range(1,self.get_row_count()):
        #    lat1, lon1 = self['lat'][i-1],self['lon'][i-1]
        #    lat2, lon2 = self['lat'][i],self['lon'][i]
        #    dlat = math.radians(lat2-lat1)
        #    dlon = math.radians(lon2-lon1)
        #    radius = 6371000    #meters
        #    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        #        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        #    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        #    d[i] = radius * c
        #return d

    def hv_course(self):
        #vectorized version
        d=np.zeros(self.get_row_count())
        lat2=self.d['lat'] * np.pi / 180.0
        lon2=self.d['lon'] * np.pi / 180.0
        lat1=np.roll(self.d['lat'],1) * np.pi / 180.0
        lon1=np.roll(self.d['lon'],1) * np.pi / 180.0
        # vectorized haversine formula
        dlon = (lon2 - lon1)
        dlat = (lat2 - lat1)
        b=np.arctan2(np.sin(dlon)*np.cos(lat2),np.cos(lat1)*np.sin(lat2)-np.sin(lat1)*np.cos(lat2)*np.cos(dlon))
        bd=b*180/np.pi
        return np.mod((360+b*180/np.pi),360)
        #loop version much slower than above vectorized version
        #d=np.zeros(self.get_row_count())
        #for i in range(1,self.get_row_count()):
        #    lat1 = math.radians(self['lat'][i-1])
        #    lat2 = math.radians(self['lat'][i])
        #    lon1 = math.radians(self['lon'][i-1])
        #    lon2 = math.radians(self['lon'][i])
        #    dlon = lon2-lon1
        #    b = math.atan2(math.sin(dlon)*math.cos(lat2),math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(dlon)) # course calc
        #    bd = math.degrees(b)
        #    br,bn = divmod(bd+360,360)      # the course remainder and final course
        #    d[i] = bn
        #return d

    def hv_speed(self,skipnan=True):
        # numpy vectorized version. we have to caclulate duration,  and hence parse datetime, which is slooowww!
        # if you already have a duration column then simply calculate hv_distance()/gpx['duration']
        if 'time' in self.get_header_names():
            d=self.hv_distance()/self.duration()
            if skipnan:
                d[0]=d[1]
                #d[0]=0.0
            return d
        #loop version
        #d=np.zeros(self.get_row_count())
        #if not 'time' in self.get_header_names():
        #    return d
        #for i in range(1,self.get_row_count()):
        #    lat1, lon1 = self['lat'][i-1],self['lon'][i-1]
        #    lat2, lon2 = self['lat'][i],self['lon'][i]
        #    #t1=datetime.datetime.strptime(self['time'][i-1],"%Y-%m-%dT%H:%M:%SZ")
        #    #t2=datetime.datetime.strptime(self['time'][i],"%Y-%m-%dT%H:%M:%SZ")
        #    t1=dateutil.parser.parse(self['time'][i-1])
        #    t2=dateutil.parser.parse(self['time'][i])
        #    dlat = math.radians(lat2-lat1)
        #    dlon = math.radians(lon2-lon1)
        #    dt =(t2-t1).total_seconds()
        #    radius = 6371000    #meters
        #    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        #        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        #    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        #    if dt!=0:
        #        d[i] = radius * c/dt
        #return d


    def hv_slope(self,conv=10,skipnan=False):
        if not self.has_field('ele'):
            return np.zeros(self.get_row_count())
        d=np.zeros(self.get_row_count())
        #can't compute slope without convolving data a lot!
        vert=(1.0)*np.convolve(self[('ele',0,0)], np.ones((conv,))/conv)[(conv-1):]
        horiz=(1.0)*np.convolve(self.hv_distance(), np.ones((conv,))/conv)[(conv-1):]
        slope=np.ediff1d(vert,to_begin=0)/horiz
        if skipnan:
            slope[np.where(~np.isfinite(slope))]=0.0
        return slope

    def hv_nearest(self, lat, lon):
        d=np.zeros(self.get_row_count())
        for i in range(0,self.get_row_count()):
            lat1, lon1 = lat,lon
            lat2, lon2 = self['lat'][i],self['lon'][i]
            dlat = math.radians(lat2-lat1)
            dlon = math.radians(lon2-lon1)
            radius = 6371000    #meters
            a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
                * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            d[i] = radius * c
        return np.argmin(d)

    def hv_pace(self,dist,ahead=False):
        d=np.cumsum(self.hv_distance())
        t=np.cumsum(self.duration())
        r=np.empty(self.get_row_count())
        r[:]=np.nan
        if ahead:
            for i in range (0,len(d)):
                idx=np.where(d>d[i]+dist)
                try:
                    j=idx[0][0]
                    r[i]=(t[j]-t[i])/dist
                except IndexError:
                    pass
        else:
            first=np.where(d>dist)
            for i in range (first[0][0],len(d)):
                idx=np.where(d>d[i]-dist)
                try:
                    j=idx[0][0]
                    r[i]=(t[i]-t[j])/dist
                except IndexError:
                    pass
        return r

    def sort_asc(self,key):
        self.d=self[self[key].argsort()]

    def sort_desc(self,key):
        self.d=self[self[key].argsort()][::-1]
        # as explained below
        # data[:,n] -- get entire column of index n
        # argsort() -- get the indices that would sort it
        # data[data[:,n].argsort()] -- get data array sorted by n-th column
        # should be feasible with
        # data[data[col].argsort()]

    def get_top_n(self,key,n):
        return self[self[key].argsort()][::-1][n:]
        #sort array, in descending order ("[::-1]) and return the first n ([5:])

    def ok(self):
        return np.where(self['ok']==True)

    def discard(self):
        return np.where(self['ok']==False)

    def nanmean(self,a):
        #quick hack as nanmean gives inmprobable results
        return np.ma.masked_invalid(a).mean()
        
    def open_fit(self,filename):
        self.filename=filename
        a = FitFile(filename)
        a.parse()
        records = list(a.get_messages(name='record'))
        row= len(records)
        if row!=0:
            keys=[]
            self.d=np.ones(row,dtype={'names':['ok'],'formats':['bool']})
            #parse first record
            for field in records[0]:
                if field.type.name=='date_time':
                    keys.append((field.name,'a20'))
                else:
                    keys.append((field.name,'float'))
            for key,typ in (keys):
                #some files edited by fitfiletools (https://www.fitfiletools.com/) (eg remover) may have some strange structure, with twice the same field!
                try:
                    self.d=npr.rec_append_fields(self.d,key,np.zeros(row),typ)
                    self.scale[key]=1.0
                    self.unit[key]="SI"
                except:
                    pass
        idx=0
        for r in a.get_messages(name='record'):
            for f in r.fields:
                if f.type.name=='date_time':
                    self.d[f.name][idx]=f.value.isoformat()+'Z'
                else:
                    try:
                        self.d[f.name][idx]=float(f.value)
                    except:
                        #print("invalid data", f.name, idx,f.data)
                        self.d[f.name][idx]=-1.0
            idx+=1
        #we now have to convert lat and lon
        self.d['position_lat']/=11930464.71
        self.d['position_long']/=11930464.71
        #new version of fitparse gives speed in mm/s
        self.d['speed']/=1000
        self.move_column('position_lat','lat')
        self.move_column('position_long','lon')
        self.move_column('altitude','ele')
        self.move_column('timestamp','time')
        self.append_column('idx','int')
        self['idx']=np.arange(self.get_row_count())

    def save_xml(self,filename,fields=None,indices=None):
        # todo: in order to be gpx compliant, any data other than ele, time, speed, course, geoidheight, hdop, vdop, pdop, magmar, sat,...
        # should be embedded in an xml tag
        # see http://www.topografix.com/gpx_manual.asp to get a full list of allowed optional info for trkpt
        # optional='name|desc|url|urlname|time|course|speed|ele|magvar|geoidheight|cmt|src|sym|type|fix|sat|hdop|vdop|pdop|ageofdgpsdata|dgpsid'.split('|')
        # <trkpt lat="43.963912" lon="4.594150">
        # <ele>-7.8</ele>
        # <time>2013-10-25T18:10:05Z</time>
        # <extensions><gpxtpx:TrackPointExtension>
        # <gpxtpx:hr>255</gpxtpx:hr>
        # <gpxtpx:atemp>288.15</gpxtpx:atemp>
        # </gpxtpx:TrackPointExtension></extensions>
        # </trkpt>
        if fields==None:
            fields=self.get_header_names()
        if indices==None:
            indices=range(0,self.get_row_count())
        optional='name|desc|url|urlname|time|course|speed|ele|magvar|geoidheight|cmt|src|sym|type|fix|sat|hdop|vdop|pdop|ageofdgpsdata|dgpsid'.split('|')
        #extensions='hr|pwr|power|distance|cad|atemp|wtemp|cal'
        # remove fields which are automatically generated when a file is opened, as well as lat and lon which are properties and not elements
        if 'ok' in fields: fields.remove('ok')
        if 'idx' in fields: fields.remove('idx')
        if 'lat' in fields: fields.remove('lat')
        if 'lon' in fields: fields.remove('lon')
        header = '''<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.0"\n\tcreator="wxgpgpsport"\n\txmlns="http://www.topografix.com/GPX/1/0"\n\txmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">\n<trk>\n<trkseg\n>\n'''
        footer='''</trkseg>\n</trk>\n</gpx>'''
        f=open(filename,'w')
        f.write(header)
        print(fields)
        for idx in indices:
            f.write('<trkpt lat="{}" lon="{}">\n'.format(self.d['lat'][idx],self.d['lon'][idx]))
            # two passes are required, first for optional params, then for extra params that should be treadted as an extension
            # optional parameters
            for h in fields:
                if h in self.get_header_names() and h in optional:
                    f.write('<{}>{}</{}>\n'.format(h,self.d[h][idx],h))
            # extensions
            if len (set(fields)-set(optional))>0:
                f.write('<extensions>\n<gpxtpx:TrackPointExtension>\n')
                for h in fields:
                    if h in self.get_header_names() and h not in optional:
                        f.write('<{}>{}</{}>\n'.format('gpxtpx:'+h,self.d[h][idx],'gpxtpx:'+h))
                f.write('</gpxtpx:TrackPointExtension>\n</extensions>\n')
            f.write('</trkpt>\n')
        f.write(footer)
        f.close()

