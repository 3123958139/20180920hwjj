#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

"""
实现OKEx的实时价格监控预警，
注意这里使用的是我自己的api，
"""

import time

from python.OkcoinSpotAPI import OKCoinSpot
import datetime as dt


# 初始化apikey、secretkey、url
# 请求：国内账号为、 www.okcoin.cn，国外帐号www.okcoin.com
apikey = 'cdffc016-fdea-4e97-a200-39de74f0021a'
secretkey = '4277FB3395F1590ABC1FC8218B8CC1DF'
okcoinRESTURL = 'https://www.okex.com/api/v1'

# 现货api
okcoinSpot = OKCoinSpot(okcoinRESTURL, apikey, secretkey)


def price_warning(token='btc_usd', price=5988.46, direction='down'):
    """
    when current price is lower than the price given,
    it prints a message.
    """
    ticker = okcoinSpot.ticker(token)
    if direction == 'down':
        print(dt.datetime.now(), '%s' % ticker['ticker']['buy'])
        if float(ticker['ticker']['buy']) <= price:
            print(dt.datetime.now(), '%s %s %s' %
                  (token, str(price), direction))


while True:
    time.sleep(5)
    try:
        price_warning('btc_usd', 6311, 'up')
#         price_warning('ltc_usd', 55.0544, 'down')
#         price_warning('eth_usd', 303.8658, 'down')
#         price_warning('bch_usd', 537.1636, 'down')
#         price_warning('eos_usd', 4.8327, 'down')
#         price_warning('xrp_usd', 0.2873, 'down')
    except Exception as e:
        print(e)
        continue
