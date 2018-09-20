# -*- coding:utf-8 -*- 
#author: winsen.HUANG 
#wechat: winsentess 
#time:   2018-05-10 23:26

# calculate twap value
def twap(bar, maxLen=12):
    close = bar["close"][-maxLen:]
    high  = bar["high"][-maxLen:]
    low   = bar["low"][-maxLen:]
    priceSum = 0.0
    for i in range(maxLen):
        highPrice  = float(high[i])
        lowPrice   = float(low[i])
        closePrice = float(close[i])
        price = (highPrice + lowPrice + closePrice) / 3.0
        priceSum += price
    twapPrc = round(priceSum / maxLen, 4)

    return twapPrc


if __name__ == "__main__":
    a = [1,2,3,4,5,6,7]
    print(a[-2:])
