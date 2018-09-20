# *-* coding:utf8 *-*

def initOrder(symbols):
    d = {}
    isOrderTag = {}
    for sym in symbols:
        d[sym]=[]
        isOrderTag[sym] = False
    return d, isOrderTag

def initDict(symbols):
    v = {}
    for sym in symbols:
        v[sym] = 0 
    return v

def initTag(symbols):
    tag = {}
    for sym in symbols:
        tag[sym] = False
    return tag

def initSignal(symbols):
    signal = {}
    for sym in symbols:
        signal[sym] = {}
        signal[sym]["direction"] = ""
        signal[sym]["qty"] = 0
        signal[sym]["signalPrc"] = 0
    return signal
