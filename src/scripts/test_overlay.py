from scripts import liboverlay

def makeoverlay(name='Overlay'):
	ovl=mapview.GetNamedLayer(name)
	if (ovl==None):
		mapview.AppendLayer(liboverlay.WxOverlayLayer(mapview,name))
		ovl=mapview.GetNamedLayer(name)
	return ovl

ovl=makeoverlay()
ovl.Add(('pen',2))
ovl.Add(('pencolor',0.0,0.0,1.0,1.0))
ovl.Add(('screen',))
#ovl.Add(('rect',50,50,150,150))
#ovl.Add(('circle',150,150,50))
#ovl.Add(('line',50,50,150,150))
ovl.Add(('lines',50,50,150,50,150,150,50,50))
#ovl.Add(('polygon',50,50,150,50,150,150,50,50))
#ovl.Add(('text',"Screen",116.02, 300.36))
ovl.Add(('pen',3))
ovl.Add(('geo',))
ovl.Add(('brushcolor',1.0,0.0,0.0,0.5))
ovl.Add(('rect',gpx['lat'].min(),gpx['lon'].min(),gpx['lat'].max(),gpx['lon'].max()))
ovl.Add(('brushcolor',0.0,1.0,0.0,0.5))
ovl.Add(('circle',gpx['lat'].min(),gpx['lon'].min(),250))
#ovl.Add(('line',gpx['lat'].min(),gpx['lon'].min(),gpx['lat'].max(),gpx['lon'].max()))
#ovl.Add(('text',"Hello_world",gpx['lat'].min(),gpx['lon'].min()))
#ovl.Add(('polygon',gpx['lat'].min(),gpx['lon'].min(),\
#                    gpx['lat'].min(),gpx['lon'].max(),\
#                    gpx['lat'].max(),gpx['lon'].max()
#                    ))
#ovl.clear()
mapview.Draw(True)
cmd=raw_input('Press enter to exit script:')
#todo delete overlay and remove it from list

