'''
haversine now returns a tupple(dist, course)
def dist2pt(idx1,idx2):
    lat1, lon1 = gpx['lat'][idx1],gpx['lon'][idx1]
    lat2, lon2 = gpx['lat'][idx2],gpx['lon'][idx2]
    dlat = np.radians(lat2-lat1)
    dlon = np.radians(lon2-lon1)
    radius = 6371000
    a = np.sin(dlat/2) * np.sin(dlat/2) + np.cos(np.radians(lat1)) \
            * np.cos(np.radians(lat2)) * np.sin(dlon/2) * np.sin(dlon/2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return radius * c

def course2pt(idx1,idx2):
    lat1,lat2 = np.radians(gpx['lat'][idx1]),np.radians(gpx['lat'][idx2])
    lon1,lon2 = np.radians(gpx['lon'][idx1]), np.radians(gpx['lon'][idx2])
    dlon = lon2-lon1
    b = np.arctan2(np.sin(dlon)*np.cos(lat2),np.cos(lat1) \
        *np.sin(lat2)-np.sin(lat1)*np.cos(lat2)*np.cos(dlon)) # course calc
    bd = np.degrees(b)
    br,bn = divmod(bd+360,360)      # the course remainder and final course
    return bn


sh.pyshell.interp.locals['course2pt']=course2pt
sh.pyshell.interp.locals['dist2pt']=dist2pt
'''
#print("This script is executed at application startup")
