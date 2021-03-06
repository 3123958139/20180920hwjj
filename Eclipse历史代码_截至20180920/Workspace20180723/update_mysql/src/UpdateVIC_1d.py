# coding:utf-8

"""
@date:20180815
@author: David
"""

from datetime import datetime as dt

from sqlalchemy import create_engine

from coinapi_v1 import CoinAPIv1
import pandas as pd


class UpdateVIC_1D(object):
    """
    """

    def __init__(self, config={}, fixperiod=''):
        """
        """
        self._config = config

        self._database = self._config['mysql']['database']
        self._table = self._config['mysql']['table']

        self._symbols = self._config['symbolpairs']

        self._start = self._config['time']['start']
        self._end = self._config['time']['end']

        self._fixperiod = fixperiod

    def update_vic_1d(self):
        """
        """
        # coinapi的数据接口
        apikey = self._config['coinapi']['apikey']
        api = CoinAPIv1(apikey)

        # 'engine': 'mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/david',
        engine = create_engine(
            'mysql+pymysql://' +
            self._config['mysql']['user'] +
            ':' +
            self._config['mysql']['password'] +
            '@' +
            self._config['mysql']['ip'] +
            ':' +
            self._config['mysql']['port'] +
            '/' +
            self._database
        )

        # 从coinapi获取的str时间是utc格式转为local格式
        UTCTIMEFORMAT = "%Y-%m-%dT%H:%M:%S.0000000Z"  # coinapi的日期格式utc
        LOCALTIMEFORMAT = "%Y-%m-%d %H:%M:%S"  # mysql的日期格式local

        def time_format(utcTimeStr):
            return dt.strptime(utcTimeStr, UTCTIMEFORMAT).strftime(LOCALTIMEFORMAT)

        # 从mysql查询最新的日期更新config中的end
        query = """
        select distinct ts from %s.%s order by ts desc limit 1;
        """ % (self._database, self._table)
        self._end = engine.execute(query).fetchall()[
            0]._row[0].strftime(LOCALTIMEFORMAT)

        # 更新
        with engine.connect() as conn:
            # 'd:\\1d.csv'
            with open('d:\\' + self._fixperiod + '.csv', 'a') as f:
                # csv存一份，sql更新一份
                s = 'ts,symbol,open,high,low,close,quantity\n'
                f.write(s)

                # 遍历每一个品种，先查日期是否间断，有则下载数据填充mysql
                for key in self._symbols.keys():
                    # 某key的ts列
                    query = """
                    SELECT DISTINCT ts FROM %s.%s 
                    WHERE symbol='%s' AND ts BETWEEN '%s' AND '%s' 
                    ORDER BY ts;
                    """ % (self._database, self._table, key, self._start, self._end)
                    df = pd.read_sql(sql=query, con=conn)

                    # 选出缺失的ts值
                    timeDelta = pd.Timedelta(
                        self._config['timedelta'][self._fixperiod]
                    )
                    df['diff'] = df['ts'].diff(1) / timeDelta  # 二者的差是周期的倍数
                    missingTs = list(df[df['diff'] > 1].index.values)
                    for i in missingTs:
                        # 间断期的起止ts值，去头去尾，中间才是缺少的日期段
                        start, end = df['ts'].ix[i - 1: i].values

                        if ((end - start) / timeDelta) > 1:
                            print('1 symbol:%s\t' % key,
                                  'local time -\t', str(start)[:19], str(end)[:19])
                            # 去头一个周期，再减去8小时
                            start = start + \
                                timeDelta - \
                                pd.Timedelta('0 days 08:00:00')
                            # 去尾一个周期，再减去8小时
                            end = end - \
                                timeDelta - \
                                pd.Timedelta('0 days 08:00:00')

                            # coinapi参数是19位，'2018-01-01T08:00:00'
                            apiStart = str(start)[:10] + 'T' + str(start)[-8:]
                            apiEnd = str(end)[:10] + 'T' + str(end)[-8:]

                            print('2 symbol:%s\t' % key,
                                  '  utc time -\t', apiStart, apiEnd)

                            name = self._symbols[key]
                            try:
                                data = api.ohlcv_historical_data(
                                    name,
                                    {
                                        'period_id': self._config['coinapi']['period'][self._fixperiod],
                                        'time_start': apiStart,
                                        'time_end': apiEnd
                                    }
                                )
                                if data:
                                    pass
                                else:
                                    print(data)

                            except Exception as e:
                                print(e)
                                continue

                            for s in data:

                                sqlTs = (dt.strptime(s['time_period_start'], UTCTIMEFORMAT) +
                                         pd.Timedelta('0 days 08:00:00')).strftime(LOCALTIMEFORMAT)  # 加上8小时
                                sqlSymbol = key
                                sqlOpen = s['price_open']
                                sqlHigh = s['price_high']
                                sqlLow = s['price_low']
                                sqlClose = s['price_close']
                                sqlQuantity = s['volume_traded']

                                f_data = [sqlTs, sqlSymbol, sqlOpen,
                                          sqlHigh, sqlLow, sqlClose, sqlQuantity]
                                print(f_data)

                                sql = """
                                insert into %s.%s(ts,symbol,open,high,low,close,quantity) value('%s','%s',%f,%f,%f,%f,%f)
                                """ % (self._database, self._table, sqlTs, sqlSymbol, sqlOpen, sqlHigh, sqlLow, sqlClose, sqlQuantity)
                                conn.execute(sql)

                                s = str(f_data).replace(
                                    '[', '').replace(']', '')
                                s = s.replace("'", '') + '\n'
                                f.write(s)


if __name__ == '__main__':
    """
    @note:主要修改这个config
    """
    config = {
        'coinapi': {
            'apikey': 'EA8CF467-3ECD-42D6-A59E-97D908AEB57D',
            'period': {
                '1d': '1DAY'  # 1d
            }
        },
        'mysql': {
            'user': 'ops',
            'password': 'ops!@#9988',
            'ip': '47.74.249.179',  # 216 生产环境
            'port': '3308',
            'database': 'david',  # 216 数据库
            'table': '1d'  # 1d
        },
        'timedelta': {
            '1d': '1 days 00:00:00'  # 1d
        },
        'time': {
            'start': '2018-05-23 08:00:00',
            'end': '2018-08-15 08:00:00'
        },
        'symbolpairs': {}
    }
    config['symbolpairs'] = {
        'BINA--EOS--USDT': 'BITFINEX_SPOT_EOS_USD',
        'BINA--XRP--USDT': 'BITFINEX_SPOT_XRP_USD',
        'BINA--BTC--USDT': 'BITFINEX_SPOT_BTC_USD',
        'BINA--ETH--USDT': 'BITFINEX_SPOT_ETH_USD',
        'BINA--BCC--USDT': 'BITFINEX_SPOT_BCH_USD',
        'BINA--LTC--USDT': 'BITFINEX_SPOT_LTC_USD',
        'OKEX--BTC--USDT': 'OKEX_SPOT_BTC_USDT',
        'OKEX--ETH--USDT': 'OKEX_SPOT_ETH_USDT',
        'OKEX--BCH--USDT': 'OKEX_SPOT_BCH_USDT',
        'OKEX--LTC--USDT': 'OKEX_SPOT_LTC_USDT',
        'OKEX--EOS--USDT': 'OKEX_SPOT_EOS_USDT',
        'OKEX--XRP--USDT': 'OKEX_SPOT_XRP_USDT',
        'HUOBI--BTC--USDT': 'HUOBIPRO_SPOT_BTC_USDT',
        'HUOBI--ETH--USDT': 'HUOBIPRO_SPOT_ETH_USDT',
        'HUOBI--BCH--USDT': 'HUOBIPRO_SPOT_BCH_USDT',
        'HUOBI--LTC--USDT': 'HUOBIPRO_SPOT_LTC_USDT',
        'HUOBI--EOS--USDT': 'HUOBIPRO_SPOT_EOS_USDT',
        'HUOBI--XRP--USDT': 'HUOBIPRO_SPOT_XRP_USDT',
    }
    obj = UpdateVIC_1D(config=config, fixperiod='1d')  # 1d
    obj.update_vic_1d()
