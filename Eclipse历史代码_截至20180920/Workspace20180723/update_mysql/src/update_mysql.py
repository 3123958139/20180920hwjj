#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

"""
1、数据库链接
标签：测试 或 生产
2、数据的补全
开始日期、结束日期：给定一个标签，或者从头补齐，或者补齐中间
品种的字典：给定一个标签，或者遍历数据库，或者手动给定  
    
3、数据的合成
"""

from sqlalchemy import create_engine as ce

from coinapi_v1 import CoinAPIv1 as ca
from datetime.datetime import strftime, strptime
import datetime as dt
import pandas as pd


class UpdateMySQL(object):
    """
    """

    def __init__(self, db=179):
        """
        @常量和全局变量放在这
        """
        self._APIKEY = 'EA8CF467-3ECD-42D6-A59E-97D908AEB57D'
        self._api = ca(self._APIKEY)

        self._UTCTIMEFORMAT = "%Y-%m-%dT%H:%M:%S.0000000Z"  # coinapi的日期格式
        self._LOCALTIMEFORMAT = "%Y-%m-%d %H:%M:%S"  # live的日期格式

        self._period = {'1mk': '0 days 00:01:00'}

        if db == 179:  # 使用179测试环境david库
            self._engine = ce('mysql+pymysql://' +
                              'ops:ops!@#9988@47.74.249.179:3308/david')
            self._conn = self._engine.connect()

    def utctime_to_localtime(self, utcTimeStr=''):
        """
        """
        return strptime(utcTimeStr, self._UTCTIMEFORMAT).strftime(self._LOCALTIMEFORMAT)

    def get_symbol_pairs(self, symbols=[''], exchange='BITFINEX_SPOT'):
        """
        @排除平台币
        """
        pairs = dict()
        try:
            for symbol in symbols:
                key = symbol

                symbolTail = symbol[-4:]
                symbolHead = symbol[:4]

                # change the tail
                if symbolTail == 'USDT':
                    symbol = symbol[:-1]

                # change the head
                if symbolHead == 'BINA':
                    pairs[key] = (exchange + symbol[4:]).replace('--', '_')
                if symbolHead == 'OKEX':
                    pairs[key] = (exchange + symbol[4:]).replace('--', '_')
                if symbolHead == 'HUOB':
                    pairs[key] = (exchange + symbol[5:]).replace('--', '_')
        except Exception as e:
            raise e

        return pairs

    def update_mysql_data(self, period='1mk', symbol='BINA--EOS--USDT', start='2018-05-31 00:00:00', end='2018-08-01 00:00:00'):
        """
        """
        query = """
        SELECT DISTINCT ts FROM david.%s 
        WHERE symbol='%s' AND ts BETWEEN '%s' AND '%s' 
        ORDER BY ts;
        """ % (period, start, end)
        df = pd.read_sql(query, self._conn)

        df['diff'] = df['ts'].diff(1) / pd.Timedelta(self._period[period])
        missingTsIndex = list(df[df['diff'] > 1].index.values)

        for i in missingTsIndex:
                # 间断期的起止ts值，去头去尾，中间才是缺少的日期段
            start, end = df['ts'].ix[i - 1: i].values

            if ((end - start) / pd.Timedelta('0 days 01:00:00')) > 1:
                print('1 symbol:%s\t' % key, 'local time -\t',
                      str(start)[:19], str(end)[:19])

                start = start + \
                    pd.Timedelta('0 days 01:00:00') - \
                    pd.Timedelta('0 days 08:00:00')  # 去头，再减去8小时
                end = end - pd.Timedelta('0 days 01:00:00') - \
                    pd.Timedelta('0 days 08:00:00')  # 去尾，再减去8小时

                # coinapi参数是19位，'2018-01-01T08:00:00'
                downLoadStart = str(start)[:10] + 'T' + str(start)[-8:]
                downLoadEnd = str(end)[:10] + 'T' + str(end)[-8:]

                print('2 symbol:%s\t' % key, '  utc time -\t',
                      downLoadStart, downLoadEnd)

                name = symbols[key]
                try:
                    data = api.ohlcv_historical_data(name,
                                                     {'period_id': '1HRS', 'time_start': downLoadStart, 'time_end': downLoadEnd})
                    if data:
                        pass
                    else:
                        print(data)

                except Exception as e:
                    print(e)
                    continue

                for s in data:

                    ts = (dt.datetime.strptime(
                        s['time_period_start'], UTC_FORMAT) + pd.Timedelta('0 days 08:00:00')).strftime(LOCAL_FORMAT)  # 加上8小时
                    symbol = key
                    open = s['price_open']
                    high = s['price_high']
                    low = s['price_low']
                    close = s['price_close']
                    quantity = s['volume_traded']

                    f_data = [ts, symbol, open, high, low, close, quantity]
                    print(f_data)

                    sql = """
                        insert into david.1h(ts,symbol,open,high,low,close,quantity) value('%s','%s',%f,%f,%f,%f,%f)
                        """ % (ts, symbol, open, high, low, close, quantity)
                    conn.execute(sql)

                    s = str(f_data).replace('[', '').replace(']', '')
                    s = s.replace("'", '') + '\n'
                    f.write(s)

    def finished(self):
        """
        : 清场动作，如关闭engine等
        """
        self._conn.close()
