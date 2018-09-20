#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

import os
import time
import winsound

from david_okex_http import OkexHttp
from david_okexft_http import OkexftHttp
from david_qyapi_weixin import *
import datetime as dt


def sendWatchingMsg(msg='test'):
    AGENG_ID = 5
    SECRET = "nVzt0pYQWNFccZiGcpjHLKSG5TqxB6T3_KgMhqXHGMU"
    TO_USER = "david"
    TOPARTY = 4

    qy = QyWeixin()

    qy.sendtxt(SECRET, AGENG_ID, msg, TO_USER, TOPARTY)


def token_watching(token='btc_usdt', price=5988.46, direction='down'):
    """
    about : 实现的是当前价高于或低于给定的某个价位时，打印出信息，后期加上推送企业微信功能。
    """
    apikey = 'cdffc016-fdea-4e97-a200-39de74f0021a'
    apisecret = '4277FB3395F1590ABC1FC8218B8CC1DF'
    url = "https://www.okex.com/api/v1"

    http = OkexHttp(url, apikey, apisecret)

    if direction == 'down':
        if float(http.ticker(token)['ticker']['last']) <= price:
            msg = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S') + '\t%s\tcp:%s\twp:%s\t%s' % (
                token, http.ticker(token)['ticker']['last'], str(price), direction)

#             sendWatchingMsg(msg)
            winsound.PlaySound("dingdong.wav", winsound.SND_ASYNC)
            print(msg)

    elif direction == 'up':
        if float(http.ticker(token)['ticker']['last']) >= price:
            msg = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S') + '\t%s\tcp:%s\twp:%s\t%s' % (
                token, http.ticker(token)['ticker']['last'], str(price), direction)

#             sendWatchingMsg(msg)
            winsound.PlaySound("dingdong.wav", winsound.SND_ASYNC)
            print(msg)


def tokenft_watching(token='eth_usd', price=315.6429, type='quarter', direction='up'):
    """
    """
    apikey = 'cdffc016-fdea-4e97-a200-39de74f0021a'
    apisecret = '4277FB3395F1590ABC1FC8218B8CC1DF'
    url = "https://www.okex.com/api/v1"

    http = OkexftHttp(url, apikey, apisecret)

    if direction == 'down':
        if float(http.future_ticker(token, type)['ticker']['last']) <= price:
            msg = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S') + '\t%s\tcp:%s\twp:%s\t%s' % (
                token, http.future_ticker(token, type)['ticker']['last'], str(price), direction)

#             sendWatchingMsg(msg)
            winsound.PlaySound("dingdong.wav", winsound.SND_ASYNC)
            print(msg)

    elif direction == 'up':
        if float(http.future_ticker(token, type)['ticker']['last']) >= price:
            msg = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S') + '\t%s\tcp:%s\twp:%s\t%s' % (
                token, http.future_ticker(token, type)['ticker']['last'], str(price), direction)

#             sendWatchingMsg(msg)
            winsound.PlaySound("dingdong.wav", winsound.SND_ASYNC)
            print(msg)


if __name__ == '__main__':
    """
    """
    while True:
        time.sleep(5)
        try:
            print(dt.datetime.now())
            token_watching('btc_usdt', 6311, 'up')
#             token_watching('btc_usdt', 6050, 'up')
#             token_watching('btc_usdt', 6020, 'up')

#             tokenft_watching('eth_usd', 0, 'quarter', 'up')
#
#             tokenft_watching('eth_usd', 314.0567, 'quart', 'up')
#             tokenft_watching('ltc_usd', 58.0808, 'quart', 'up')
#             tokenft_watching('bch_usd', 567.3150, 'quart', 'up')
#             tokenft_watching('eos_usd', 4.6649, 'quart', 'up')
#             tokenft_watching('xrp_usd', 0.2970, 'quart', 'up')
        except Exception as e:
            print(e)
            continue
