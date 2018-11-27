import os
import numpy as np
import datetime
import dateutil.parser
from dateutil.relativedelta import *
import math
windspeed=''
winddir=''
boatspeed=''
boatdir=''
headers=[x for x in gpx.get_header_names() if not x in ['ok','time','duration','idx','ele','magvar','lat','lon','slope']]
(windspeed,winddir,boatspeed,boatdir)=WxQuery("Apparent wind and VMG calculation",	\
				[('wxcombo','column for wind speed','|'.join(headers),'wind_avg','str'),\
                 ('wxcombo','column for wind direction','|'.join(headers),'wind_dir','str'),\
                 ('wxcombo','column for boat speed','|'.join(headers),'speed','str'),\
                 ('wxcombo','column for boat direction','|'.join(headers),'course','str')])   
if not gpx.has_field('app_wind_dir'):
    gpx.append_column('app_wind_dir','float')
if not gpx.has_field('app_wind_avg'):
    gpx.append_column('app_wind_avg','float')
#loop version
#Apparent wind angle is given by ArcTan((SIN(TWA)*TWS)/(BS+COS(TWA)*TWS));
#Apparent wind speed is given by SQRT((SIN(TWA)*TWS)^2+(BS+COS(TWA)*TWS)^2)
for i in range(0, gpx.get_row_count()):
    # tws true wind speed
    # bs  boat speed
    # twa true wind angle (0=fully upwind; 180=fully downwind)
    # awa apparent wind angle
    # aws apparent wind speed
    tws=gpx[windspeed][i]        # our wind direction is reversed. compared to usual conventions
    bs=gpx[boatspeed][i]
    twa=(gpx[boatdir][i]-gpx[winddir][i]+180)%360
    twa=twa/180.0*math.pi
    awa=math.atan((math.sin(twa)*tws)/(bs+math.cos(twa)*tws))
    aws=math.sqrt((math.sin(twa)*tws)**2+(bs+math.cos(twa)*tws)**2)
    gpx['app_wind_avg'][i]=aws
    if (gpx[boatdir][i]-twa)>0:
        gpx['app_wind_dir'][i]=(gpx[boatdir][i]-awa*180/math.pi)+180
    else:
        gpx['app_wind_dir'][i]=(gpx[boatdir][i]+awa*180/math.pi)+180
sh.upd()
