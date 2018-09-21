#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

"""
@date:20180826
@author: David
"""

from sqlalchemy import create_engine
import pandas as pd


class CheckIfMissing(object):
    """
    """

    def __init__(self, symbols, timeDelta, dataBase, table, start, end):
        """
        """
        self._engine = create_engine(
            'mysql+pymysql://ops:ops!@#9988@47.74.179.216:3308/david'
#                         'mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/david'
        )
        self._symbols = symbols
        self._timeDelta = timeDelta
        self._dataBase = dataBase
        self._table = table
        self._start = start
        self._end = end

    def check_if_missing(self):
        """
        """
        with self._engine.connect() as con:
            for symbol in self._symbols:
                sql = """SELECT DISTINCT ts FROM %s.%s 
                    WHERE symbol='%s' AND ts BETWEEN '%s' AND '%s' 
                    ORDER BY ts;
                    """ % (self._dataBase, self._table, symbol, self._start, self._end)
                df = pd.read_sql(sql, con)
                df['diff'] = df['ts'].diff(1) / pd.Timedelta(self._timeDelta)
                missingTsDF = df[df['diff'] > 1]
                missingTsSum = missingTsDF['diff'].sum() - len(missingTsDF)
                print(symbol, '\n',
                      missingTsDF, '\n',
                      '总缺失记录条数 \t', missingTsSum, '\n', '*' * 80, '\n')


if __name__ == '__main__':
    symbols = [
        'BINA--EOS--USDT',
        'BINA--XRP--USDT',
        'BINA--BTC--USDT',
        'BINA--ETH--USDT',
        'BINA--BCC--USDT',
        'BINA--LTC--USDT',
        'BINA--EOS--BTC',
        'BINA--XRP--BTC',
        'BINA--ETC--BTC',
        'BINA--ETH--BTC',
        'BINA--BCC--BTC',
        'BINA--LTC--BTC',

        'OKEX--EOS--USDT',
        'OKEX--XRP--USDT',
        'OKEX--BTC--USDT',
        'OKEX--ETH--USDT',
        'OKEX--BCC--USDT',
        'OKEX--LTC--USDT',
        'OKEX--EOS--BTC',
        'OKEX--XRP--BTC',
        'OKEX--ETC--BTC',
        'OKEX--ETH--BTC',
        'OKEX--BCC--BTC',
        'OKEX--LTC--BTC',

        'HUOBI--EOS--USDT',
        'HUOBI--XRP--USDT',
        'HUOBI--BTC--USDT',
        'HUOBI--ETH--USDT',
        'HUOBI--BCC--USDT',
        'HUOBI--LTC--USDT',
        'HUOBI--EOS--BTC',
        'HUOBI--XRP--BTC',
        'HUOBI--ETC--BTC',
        'HUOBI--ETH--BTC',
        'HUOBI--BCC--BTC',
        'HUOBI--LTC--BTC'
    ]
#     # 1d表
#     print('1d', '-' * 78)
#     timeDelta = '1 days 00:00:00'
#     obj = CheckIfMissing(symbols, timeDelta,
#                          'vic_1d', '1d', '2018-01-01 08:00:00', '2018-09-21 08:00:00')
#     obj.check_if_missing()
#     # 1h表
#     print('1h', '-' * 78)
#     timeDelta = '0 days 01:00:00'
#     obj = CheckIfMissing(symbols, timeDelta,
#                          'vic_1h', '1h', '2018-01-01 08:00:00', '2018-09-21 08:00:00')
#     obj.check_if_missing()
    # 5mk表
    print('5mk', '-' * 77)
    timeDelta = '0 days 00:05:00'
    obj = CheckIfMissing(symbols, timeDelta, 'vic_5mk', '5mk', '2018-01-01 08:00:00', '2018-09-21 08:00:00')
    obj.check_if_missing()
#     # 1mk表
#     print('1mk', '-' * 77)
#     timeDelta = '0 days 00:01:00'
#     obj = CheckIfMissing(symbols, timeDelta,
#                          'vic_5mk', '5mk', '2018-01-01 08:00:00', '2018-09-13 16:00:00')
#     obj.check_if_missing()
