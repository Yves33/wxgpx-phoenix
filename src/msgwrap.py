#!usr/bin/env python
# -*- coding: iso-8859-1 -*-#
# msgwrap is a simple wrapper around several message dispatching interfaces
# supported interfaces are :
#   + pydisptach
#   + pypubsub
#   + wx.lib.pubsub
#   + smokesignal

#import sys
#this could be determined dynamically with try:except:
#__backend__='pydispatch'
#__backend__='wxpubsub'
#__backend__='pypubsub'
#__backend__='smokesignal'

backends=[]
try:
    import pydispatch
    backends.append('pydispatch')
except ImportError:
    pass
try:
    import wx.lib.pubsub
    backends.append('wxpubsub')
except ImportError:
    pass
try:
    import pubsub
    backends.append('pypubsub')
except ImportError:
    pass
try:
    import smokesignal
    backends.append('smokesignal')
except ImportError:
    pass
        
assert len(backends)>0,"Could not find suitable signal backend \nPlease install either PubSub or Pydispatcher or SmokeSignal"
__backend__=backends[0]
print("Using %s signal backend" % __backend__)

if __backend__=='pydispatch':
    from pydispatch import dispatcher 
    def register(callback,signal):
        dispatcher.connect(callback, signal=signal, sender=dispatcher.Any)

    def message(signal,*args,**kwargs):
        dispatcher.send(signal,*args,**kwargs)



elif __backend__=='wxpubsub':
    try:
        from wx.lib.pubsub import setupkwargs       #deprecated in pubsub 4.x
    except ImportError:
        pass
    from wx.lib.pubsub import pub
    def register(callback,signal):
        pub.subscribe(callback,signal)

    def message(signal,*args,**kwargs):
        pub.sendMessage(signal,*args,**kwargs)

elif __backend__=='pypubsub':
    try:
        from pubsub import setupkwargs
    except ImportError:
        pass
    from pubsub import pub
    
    def register(callback,signal):
        pub.subscribe(callback,signal)

    def message(signal,*args,**kwargs):
        pub.sendMessage(signal,*args,**kwargs)

elif __backend__=='smokesignal':
    #untested
    import smokesignal
    def message(signal,*args,**kwargs):
        smokesignal.emit(signal,*args,**kwargs)

    def register(callback,signal):
        smokesignal.on(signal, callback)