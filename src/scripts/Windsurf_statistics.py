### calcultae best points
import datetime
savedsel=np.copy(gpx['ok'])                                                                 # save selection, as we will modify it

#todo: push all these measurments in an array! and copy to clipboard
#date|hour|distance|duration|avg speed|duration (>10kts)|distance (>10kts)|avg speed (>10kts)|best 1s|best 10s|best 100|best 500
print("Average speed : {:3.2f} kts".format(gpx['speed'][np.where(gpx['ok']==True)].mean() *1.94384))
print("Distance :  {:3.2f} km".format(gpx['deltaxy'][np.where(gpx['ok']==True)].sum()/1000))
print("Duration :",str(datetime.timedelta(seconds=gpx['deltat'][np.where(gpx['ok']==True)].sum())))
print("Date:",gpx['time'][1])
print("Location : lat:",gpx['lat'].mean(), " -- lon:",gpx['lon'].mean())
print("Average speed above 10 kts: {:3.2f} kts".format(gpx['speed'][np.where((gpx['speed']>5.1444)&(gpx['ok']==True))].mean() *1.94384))
print("Distance above 10 kts:  {:3.2f} km".format(gpx['deltaxy'][np.where((gpx['speed']>5.1444)&(gpx['ok']==True))].sum()/1000))
print("Duration above 10 kts:",str(datetime.timedelta(seconds=gpx['deltat'][np.where((gpx['speed']>5.1444)&(gpx['ok']==True))].sum())))

values=[]
print("\n5 best instant measurments:")
buffer=np.copy(gpx[('speed',1)])
for count in range (0,5):
    value=np.max(buffer[gpx['ok']])                                                                                 #get max speed from enabled points
    idx=np.where(buffer == value)[0][0]                                                                             #get the idx of value
    print(count," best measurment at",gpx['time'][idx][11:19],":","{:3.2f}".format(value), " ",gpx.get_unit_sym('speed'))  #print results
    gpx['ok'][idx]=False                                                                                            #disable point
    values.append(value)                                                                                            #save value
gpx['ok'][:]=savedsel[:]

print("\n5 best 10 measurments average:")
buffer=np.convolve(gpx[('speed',1)],np.ones(10)/10,mode='same')
for count in range (0,5):
    value=np.max(buffer[gpx['ok']])                                                                                 #get max speed from enabled points
    idx=np.where(buffer == value)[0][0]                                                                             #get the idx of value
    print(count," best measurment at",gpx['time'][idx][11:19], ":","{:3.2f}".format(value), " ",gpx.get_unit_sym('speed'))  #print results
    gpx['ok'][idx-5:idx+5]=False                                                                                    #disable point
    values.append(value)                                                                                            #save value
gpx['ok'][:]=savedsel[:]

# calculating the best 500m is a little bit more tricky.
# the procedure could be modified using the 'idx' column that was recently added to the array
print("\n5 best 500m (at least):")
buffer=gpx.hv_pace(500)
for count in range (0,5):
    value=np.nanmin(buffer[gpx['ok']])                                                        #get max pace for enabled points
    locidx=np.nanargmin(buffer[gpx['ok']])                                                    #get the indice of that max pace
    time=gpx[('duration',1,1)][locidx]                                                        #get the time for this point
    idx=np.where(gpx['duration'] == time)[0][0]                                               #get the real index of this point
    s2=np.where(gpx['distance']>500+gpx['distance'][idx])[0][0]                               #get earliest new run
    s1=np.where(gpx['distance']<gpx['distance'][idx]-500)[0][-1]                              #get start of the run
    dist=gpx['distance'][idx]-gpx['distance'][s1]                                             #compute run distance
    dur=gpx['duration'][idx]-gpx['duration'][s1]                                              #compute run duration
    print(count," 500 meter run at",gpx['time'][idx][11:19], ":","{:3.1f}".format(dist), " m in ","{:3.0f}".format(dur),"s (","{:3.2f}".format(dist/dur*gpx.get_scale('speed')),gpx.get_unit_sym('speed'),")")
    gpx['ok'][s1:s2]=False                                                                    #disable points
    values.append(dist/dur*gpx.get_scale('speed'))                                                                #save value
gpx['ok'][:]=savedsel[:]                                                                      #restore selection

summary=""
#date
summary+=str(gpx['time'][1][0:10])
#time
summary+="\t"+str(gpx['time'][1][11:19])
#average speed in knots
summary+="\t{:3.2f}".format(gpx['speed'][np.where(gpx['ok']==True)].mean() *gpx.get_scale('speed'))
#atotal distance in km
summary+="\t{:3.2f}".format(gpx['deltaxy'][np.where(gpx['ok']==True)].sum()/1000)
#total duration
summary+="\t"+str(datetime.timedelta(seconds=gpx['deltat'][np.where(gpx['ok']==True)].sum()))
#average speed above 10 knots (5.1444 m/s)
summary+="\t{:3.2f}".format(gpx['speed'][np.where((gpx['speed']>5.1444)&(gpx['ok']==True))].mean() *gpx.get_scale('speed'))
#distance above 10 knots (5.1444 m/s)
summary+="\t{:3.2f}".format(gpx['deltaxy'][np.where((gpx['speed']>5.1444)&(gpx['ok']==True))].sum()/1000)
#duration above 10 knots (5.1444 m/s)
summary+="\t"+str(datetime.timedelta(seconds=gpx['deltat'][np.where((gpx['speed']>5.1444)&(gpx['ok']==True))].sum()))
#VMax
summary+="\t{:3.2f}".format(values[0])
#best 10 seconds
summary+="\t{:3.2f}".format(values[5])
#best 500
summary+="\t{:3.2f}".format(values[10])
#save value
print("Date\tTime\tAvg Speed\tDistance\tDuration\tAvg speed(>10kts)\tDistance (>10kts)\tDuration (>10kts)\tVMax\tBest 10s\tBest 500m"
print(summary)
sh.copy(summary)
