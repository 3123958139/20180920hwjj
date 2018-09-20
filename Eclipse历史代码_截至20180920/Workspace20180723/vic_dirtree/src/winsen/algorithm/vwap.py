# -*- coding:utf-8 -*-
#author: winsen.HUANG
#wechat: winsentess
#time:   2018-05-10 23:26

# calculate vwap value
def calc_vwap(marketDataTable):
    n = len(marketDataTable) - 1
    total_sum = 0.0
    volume_sum = 0
    for i in range(1, n + 1):
        high_price = float(marketDataTable[i][9])
        low_price = float(marketDataTable[i][10])
        price = (high_price + low_price) / 2
        volume = int(marketDataTable[i][11])
        total_sum += price * volume
        volume_sum += volume

    return total_sum / volume_sum
