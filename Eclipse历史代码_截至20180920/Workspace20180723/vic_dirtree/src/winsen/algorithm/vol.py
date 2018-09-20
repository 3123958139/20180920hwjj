# *-* coding:utf8 *-*
def avgVol(bar, maxLen=12):
    #最近12根的平均成交量
    if len(bar["volume"]) < maxLen:
        return 0
    volume = bar["volume"][-maxLen:]
    volSum = 0.0 
    for i in range(maxLen):
        vol  = float(volume[i])
        volSum += vol
        thisVol = round(volSum / maxLen, 1)
    return thisVol
