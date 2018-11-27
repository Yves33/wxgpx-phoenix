import os
mydir=WxQuery("Choose directory to process",[('wxdir','Choose',None,"C:\\",'str')])
for f in os.listdir(mydir[0]):
    if f.endswith('fit'):
        app.OpenFile(mydir[0]+os.sep+f)
        gpx=app.gpx             #mandatory line! as we opened a new gpx file, we need to relink it to gpx shell variable
        print (px['speed'].mean())
        #sh.run("any script")
        #app.SaveFile('where/you/should/save.ext)