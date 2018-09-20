# -*- coding:utf8 -*-

def updateSignalPos(d, symbol, qty, signalPrc, direction):
    """
    update strategy signal dictionary.
    """
    if symbol in d.keys():
        if d[symbol]["qty"] <> qty:
            d[symbol]["qty"] = qty 
            d[symbol]["signalPrc"] = signalPrc
            d[symbol]['direction'] = direction
        else:
            d[symbol] = {}
            d[symbol]["qty"] = qty 
            d[symbol]["signalPrc"] = signalPrc
            d[symbol]['direction'] = direction
    return d

