import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
import wx

def idx2x(idx):
    return timeview.x_to_num(gpx[timeview.xaxis][idx])


# patches  
mypatches=[]
mypatches.append(patches.Rectangle((idx2x(1200),0),idx2x(2400)-idx2x(1200),25.0))
p=PatchCollection(mypatches, alpha=0.4)
timeview.ax1.add_collection(p)
# text
txt=timeview.ax1.text(idx2x(2400),12,'end',fontsize=12)
# annotations
annotation=timeview.ax1.annotate('local max', xy=(idx2x(1200),10), xytext=(idx2x(1200),20),
            arrowprops=dict(facecolor='black', shrink=0.05),
            fontsize=12
            )
sh.upd()
cmd=raw_input('Press enter to exit script:')
p.remove()
txt.remove()
annotation.remove()
sh.upd()