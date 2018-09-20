#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8


"""
@date: 20180820
@author: David
"""

from builtins import Exception

from sqlalchemy import create_engine

import datetime as dt
import pandas as pd

PATH_TB = "\\\\192.168.1.67\\CryphtoFund\\DATA\\TB\\"

symDict = {
    'BCH': 'OKEX--BCH--USDT',
    'BTC': 'OKEX--BTC--USDT',
    'DASH': 'OKEX--DASH--USDT',
    'EOS': 'OKEX--EOS--USDT',
    'ETC': 'OKEX--ETC--USDT',
    'ETH': 'OKEX--ETH--USDT',
    'LTC': 'OKEX--LTC--USDT',
    'XRP': 'OKEX--XRP--USDT'
}

engine = create_engine(
    'mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/vic_5mk')
with engine.connect() as conn:
    for k in symDict.keys():
        try:
            query = "SELECT ts as datetime,open,high,low,close,quantity as volume FROM vic_5mk.5mk WHERE symbol='%s' AND ts>'2018-06-07 00:00:00' ORDER BY ts;" % (
                symDict[k])
            df = pd.read_sql(query, conn)
            df.set_index('datetime', inplace=True)
            ohlc_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            df = df.resample('30T', how=ohlc_dict, closed='left', label='left')
            df.to_csv(PATH_TB + k + '.csv', index=True, header=None)
            print(k + ' is OK.')

        except Exception as e:
            print(e)
            continue
