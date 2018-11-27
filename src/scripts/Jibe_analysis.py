import math
from wxmappanel.wxmappanel import Haversine                 # haversine is now included in map panel we don't need to re-define it

def dist_to_line(ax, ay, bx, by, cx, cy):    
    k = ((by-ay) * (cx-ax) - (bx-ax) * (cy-ay)) / ((by-ay)**2 + (bx-ax)**2)
    x4 = cx - k * (by-ay)
    y4 = cy + k * (bx-ax)
    return (x4,y4)


def jibecurve(t,wind,convolution):
    ax=gpx['lat'][t]
    ay=gpx['lon'][t]
    bx=ax+math.cos(math.radians(wind))  # 10 may not be enough. Not sure if this works at north pole
    by=ay+math.sin(math.radians(wind))
    x=[]
    y=[]
    ## print ("\n------------")  ## debugging purpose only you may check that all points are aligned in right direction
    for tt in range(t-convolution,t+convolution,2):
        px,py=dist_to_line(ax,ay,bx,by,gpx['lat'][tt],gpx['lon'][tt])
        px1,py1=dist_to_line(ax,ay,bx,by,gpx['lat'][tt+1],gpx['lon'][tt+1])
        x.append(px)
        y.append(py)
        x.append(px1)
        y.append(py1)
        ## print ("{px},{py},{px1},{py1}") ## debugging purpose only you may check that all points are aligned in right direction
    return Haversine(min(x),min(y),max(x),max(y))[0]
        
sh.clear()
# we could add an option to dump the BBOX coordinate
(winddirection,convolution,minspeed,sortkey,rev)=(90,10,3.5,"min speed",True)
(winddirection,convolution,minspeed,sortkey,rev)=WxQuery("Jibe detection parameters",    \
                [('wxentry','Wind Direction',None,winddirection,'float','in degrees, North id 0, West is 90, South 180'),\
                ('wxentry','convolution',None,convolution,'int','nuumber of points to use for data smoothing'),\
                ('wxentry','Minimal speed',None,minspeed,'float','ignore any jibe when convolved speed is below this value'),\
                ('wxcombo','Sort by','Time|TimeStamp|min speed|max speed|jibe radius',sortkey,'str'),\
                ('wxcheck','Desc',None,rev,'bool')]
                )
if not 'conv_speed' in gpx.get_header_names(): gpx.append_column('conv_speed','float')
if not 'tack' in gpx.get_header_names():       gpx.append_column('tack','float')
gpx.set_unit('conv_speed','kts')
gpx['conv_speed']=np.convolve(gpx[('speed',1)], np.ones(convolution)/convolution,mode='same')
gpx['tack']=np.sin(np.radians(gpx['course']-winddirection))

jibes=[]
zerocrossing=np.where(np.diff(np.sign(gpx['tack'])))[0]
for t in zerocrossing[0:]:
    if (t>convolution)   and  ( (gpx[('conv_speed',1)][t-convolution:t+convolution]>=minspeed).all()):
        jibes.append( (t,
                        gpx['time'][t],
                        np.min(gpx[('speed',1)][t-convolution:t+convolution]),
                        np.max(gpx[('speed',1)][t-convolution:t+convolution]),
                        jibecurve(t,(winddirection)%360,convolution)
                    ) )
sortnum='Time|TimeStamp|min speed|max speed|jibe radius'.split('|').index(sortkey)
print("Time (s), Timestamp, Min Speed, Max Speed, Jibe radius")
for j in sorted(jibes,key=lambda tup: tup[sortnum],reverse=rev):
    print(j)
