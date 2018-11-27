import numpy as np
import datetime
import dateutil.parser
from dateutil.relativedelta import *

[hh,mm,ss]=WxQuery("Time shift data",	\
				[('wxentry','Hours',None,0,'int'), \
				('wxentry','Minutes',None,0,'int'), \
				('wxentry','Secondes',None,0,'int')] \
				)
if gpx!=None:
	for idx in range (gpx.get_row_count()):
		time=dateutil.parser.parse(gpx['time'][idx]) + relativedelta(hours=hh,minutes=mm, seconds=ss)
		gpx['time'][idx]=time.strftime ("%Y-%m-%dT%H:%M:%SZ")
	sh.upd()