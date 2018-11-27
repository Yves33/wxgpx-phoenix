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

dirs="S|SSO|SO|OSO|O|ONO|NO|NNO|N|NNE|NE|ENE|E|ESE|SE|SSE"
direction_to_degrees={}
count=0
for entry in dirs.split('|'):
    direction_to_degrees[entry]=count*22.5
    count=count+1

wind_avg=10
wind_min=10
wind_max=10
wind_dir='0'
wind_units='kts'
(wind_avg,wind_max,wind_min,wind_units,wind_dir)=WxQuery("Enter wind characteristics",	\
				[('wxentry','Average speed',None,10,'float'),\
                 ('wxentry','Max speed',None,10,'float'),\
                 ('wxentry','Min speed',None,10,'float'),\
                 ('wxcombo','Units',"m/s|km/h|kts",'kts','str'),\
                 ('wxcombo','Direction speed',dirs,"O",'str')])   
if not gpx.has_field('wind_dir'):
    gpx.append_column('wind_dir','a5')
if not gpx.has_field('wind_avg'):
    gpx.append_column('wind_avg','float')
if not gpx.has_field('wind_mini'):
    gpx.append_column('wind_mini','float')
if not gpx.has_field('wind_maxi'):
    gpx.append_column('wind_maxi','float')
    
if wind_units=='kts':
    sf=0.514444
elif wind_units=='km/h':
    sf=0,277778
else:
    sf=1.0
gpx['wind_avg'].fill(wind_avg*sf)
gpx['wind_mini'].fill(wind_min*sf)
gpx['wind_maxi'].fill(wind_max*sf)
if wind_dir.isdigit():
    gpx['wind_dir'].fill(wind_dir)
elif wind_dir in dirs.split('|'):
    gpx['wind_dir'].fill(direction_to_degrees[wind_dir])

    #then set approriate units for display
    gpx.set_unit('wind_avg',wind_units)
    gpx.set_unit('wind_mini',wind_units)
    gpx.set_unit('wind_maxi',wind_units)
    sh.upd()
