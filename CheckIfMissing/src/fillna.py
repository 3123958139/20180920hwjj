#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

"""
@date:20180826
@author: David
"""

from sqlalchemy import create_engine
import pandas as pd


class FillNa(object):
    """
    """

    def __init__(self, symbols, timedelta, database, table, start, end):
        """
        """
        self._engine = create_engine(
            'mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/david'
        )
        self._symbols = symbols
        self._timedelta = timedelta
        self._database = database
        self._table = table
        self._start = start
        self._end = end

    def fill_na(self):
        """
        """
        with self._engine.connect() as con:
            for symbol in self._symbols:
                sql = """SELECT DISTINCT ts FROM %s.%s 
                    WHERE symbol='%s' AND ts BETWEEN '%s' AND '%s' 
                    ORDER BY ts;
                    """ % (self._database, self._table, symbol, self._start, self._end)
                df = pd.read_sql(sql, con)
                df['diff'] = df['ts'].diff(1) / pd.Timedelta(timedelta)
                missingTsDF = df[df['diff'] > 1]
                for t, n in missingTsDF.values:
                    sql = """SELECT DISTINCT * FROM %s.%s 
                    WHERE symbol='%s' AND ts = '%s';
                    """ % (self._database, self._table, symbol, str(t - pd.Timedelta(5 * int(n), unit='m')))
                    df = pd.read_sql(sql, con)
                    for i in range(1, int(n)):
                        ts = str(t - pd.Timedelta(5 * int(n), unit='m') +
                                 pd.Timedelta(5 * i, unit='m'))
                        symbol = df['symbol'].values[0]
                        open = df['open'].values[0]
                        high = df['high'].values[0]
                        low = df['low'].values[0]
                        close = df['close'].values[0]
                        quantity = df['quantity'].values[0]
                        turnover = 0.0
                        openinterest = 0.0

                        print([ts, symbol, open, high, low, close,
                               quantity, turnover, openinterest])

#                         try:
#                             sql = """
#                             insert into %s.%s(ts,symbol,open,high,low,close,quantity,turnover,openinterest) value('%s','%s',%f,%f,%f,%f,%f,%f,%f)
#                             """ % (self._database, self._table, ts, symbol, open, high, low, close, quantity, turnover, openinterest)
#                             con.execute(sql)
#                         except Exception as e:
#                             print(e)
#                             continue


if __name__ == '__main__':
    print('5mk', '-' * 77)
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
    timedelta = pd.Timedelta(5, unit='m')
    obj = FillNa(symbols, timedelta,
                 'vic_5mk', '5mk', '2018-01-01 08:00:00', '2018-09-21 08:00:00')
    obj.fill_na()
