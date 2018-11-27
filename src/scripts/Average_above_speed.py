'''
    This script calculates the average speed, total distance and total time
    for points where speed is greater than a user specified value.
'''
Buffer=""
[filter]=WxQuery("Please specify filter for speed ({})".format(gpx.get_unit_sym('speed')),[('wxentry','Enter threshold',None,1,'float')])
avg_speed=gpx[('speed',1)][np.where(gpx[('speed',1)]>filter)].mean()
tot_dist=gpx[('deltaxy',1)][np.where(gpx[('speed',1)]>filter)].sum()
tot_time=gpx[('deltat',1)][np.where(gpx[('speed',1)]>filter)].sum()
Buffer+="#################################\n"
Buffer+="Average speed for points above {} {} ({}): {}\n".format(filter,\
                                                            gpx.get_unit_sym('speed'),\
                                                            gpx.get_unit_sym('speed'),\
                                                            avg_speed)
Buffer+="Total distance for points above {} {} ({}): {}\n".format(filter,\
                                                            gpx.get_unit_sym('speed'),\
                                                            gpx.get_unit_sym('deltaxy'),\
                                                            tot_dist)
Buffer+="Total time for points above {} {} ({}): {}\n".format(filter,\
                                                            gpx.get_unit_sym('speed'),\
                                                            gpx.get_unit_sym('deltat'),\
                                                            tot_time)
Buffer+="#################################\n"
print(Buffer)