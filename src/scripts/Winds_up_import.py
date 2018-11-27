import os
import numpy as np
import datetime
import dateutil.parser
from dateutil.relativedelta import *
from lxml import objectify,etree
# we could download directly from winds-up. for that, we would need to 
# parse correct date from gpx file
# provide an exhaustive list of the spots with correcponding url
# import urllib.request
# opener = urllib.request.build_opener()
# tree = ET.parse(opener.open(url))
# after changing script name, generate columns from user input

# dirs="S|SSO|SO|OSO|O|ONO|NO|NNO|N|NNE|NE|ENE|E|ESE|SE|SSE"
# direction_to_degrees={}
# count=0
# for entry in dirs.split('|'):
    # direction_to_degrees[entry]=count*22.5
    # count=count+1
direction_to_degrees={ "N":180,\
                      "NO":135,\
                      "NW":135,\
                      "O":90,\
                      "W":90,\
                      "SO":45,\
                      "SW":45,\
                      "S":0,\
                      "SE":315,\
                      "E":270,\
                      "NE":225
                      }
srcfile=None
[srcfile]=WxQuery("Load html file",	\
				[('wxfile','Get html file','HTML file (*.htm,*.html)|*.htm;*.html',"C:\\",'str')])
if srcfile!=None:
    meas=[]
    html = etree.parse(srcfile,parser=etree.HTMLParser(encoding='iso-8859-1',recover=True))
    #time;direction;average;skip;mini;maxi
    for e in html.xpath('//div[@id="moreInfos"]/table[@class="tableau hover"]//td')[6:]:
        if e.text!=None:
            #print e.sourceline,":",e.text.encode('utf-8')
            meas.append(e.text.encode('utf-8'))
        else:
            imgs=e.xpath('img/@src')
            if len(imgs)>0:
                #print e.sourceline,":",e.xpath('img/@src')[0]
                img=e.xpath('img/@src')[0].encode('utf-8')
                meas.append(img.split("/")[-1][:-4])
    #todo check that length%5=0
    #we now loop though our values file
    if not gpx.has_field('wind_dir'):
        gpx.append_column('wind_dir','float')
    if not gpx.has_field('wind_avg'):
        gpx.append_column('wind_avg','float')
    if not gpx.has_field('wind_mini'):
        gpx.append_column('wind_mini','float')
    if not gpx.has_field('wind_maxi'):
        gpx.append_column('wind_maxi','float')
    for idx in range (0,(len(meas)//5)-1):
        tmp1=gpx['time'][0][:-9]+meas[idx*5][-5:]+":00Z"
        tmp2=gpx['time'][0][:-9]+meas[(idx+1)*5][-5:]+":00Z"
        indices=np.where((tmp1>=gpx['time']) & (gpx['time']>=tmp2))
        if indices[0].size>0:
            #in order to cope with our standard settings, we convert wind speed to m/s
            gpx['wind_dir'][indices]=direction_to_degrees[ str(meas[idx*5+1]) ]
            gpx['wind_avg'][indices]=float(meas[idx*5+2])*0.514444
            gpx['wind_mini'][indices]=float(meas[idx*5+3])*0.514444
            gpx['wind_maxi'][indices]=float(meas[idx*5+4])*0.514444
    #then set approriate units for display
    gpx.set_unit('wind_avg','kts')
    gpx.set_unit('wind_mini','kts')
    gpx.set_unit('wind_maxi','kts')
    sh.upd()
