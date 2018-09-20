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
        # config
        self._config = config

        self._database = self._config['mysql']['database']
        self._table = self._config['mysql']['table']

        self._symbols = self._config['symbolpairs']

        self._start = self._config['time']['start']
        self._end = self._config['time']['end']

        self._fixperiod = fixperiod

        # 从coinapi获取的str时间是utc格式转为local格式
        self._UTCTIMEFORMAT = "%Y-%m-%dT%H:%M:%S.0000000Z"  # coinapi的日期格式utc
        self._LOCALTIMEFORMAT = "%Y-%m-%d %H:%M:%S"  # mysql的日期格式local

        # coinapi的数据接口
        self._api = CoinAPIv1(self._config['coinapi']['apikey'])

        # 'mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/david'
        self._engine = create_engine(
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

    def utc_to_local(self, utcTimeStr):
        """
        @: 把coinapi的str时间由utc格式转为local格式
        """
        return dt.strptime(utcTimeStr, self._UTCTIMEFORMAT).strftime(self._LOCALTIMEFORMAT)

    def localtime_to_utctime(self, localTimeStr=''):
        """
        @: local时间转为utc时间，减去8小时时差，再做成coinapi时间参数格式
        """
        utc = dt.strptime(
            localTimeStr, self._LOCALTIMEFORMAT) - pd.Timedelta('0 days 08:00:00')
        return str(utc)[:10] + 'T' + str(utc)[-8:]

    def update_vic_init(self):
        """
        @: 首先根据给定的起止时间更新时间头时间尾记录，确保头尾不缺失
        """
        apiStart = self.localtime_to_utctime(self._start)
        apiEnd = self.localtime_to_utctime(self._end)

        with self._engine.connect() as conn:
            for t in [apiStart, apiEnd]:  # 先补齐日期头再补齐日期尾
                print('update_vic_init')
                for key in self._symbols.keys():  # 遍历品种字典
                    try:
                        name = self._symbols[key]
                        data = self._api.ohlcv_historical_data(
                            name,
                            {
                                'period_id': self._config['coinapi']['period'][self._fixperiod],
                                'time_start': t,
                                'time_end': t
                            }
                        )
                        if data:
                            pass
                        else:
                            print(data)  # 如果返回数据为空则打印空值出来查看

                    except Exception as e:
                        print(e)
                        continue

                    for s in data:
                        sqlTs = (dt.strptime(s['time_period_start'], self._UTCTIMEFORMAT) +
                                 pd.Timedelta('0 days 08:00:00')).strftime(self._LOCALTIMEFORMAT)  # 加上8小时
                        sqlSymbol = key
                        sqlOpen = s['price_open']
                        sqlHigh = s['price_high']
                        sqlLow = s['price_low']
                        sqlClose = s['price_close']
                        sqlQuantity = s['volume_traded']
                        sqlTurnover = 0.0  # 实际为null，需求是换为0
                        sqlOpeninterest = 0.0  # 实际为null，需求是换为0

                        print([sqlTs, sqlSymbol, sqlOpen, sqlHigh,
                               sqlLow, sqlClose, sqlQuantity, sqlTurnover, sqlOpeninterest])
                        try:
                            sql = """
                            insert into %s.%s(ts,symbol,open,high,low,close,quantity,turnover,openinterest) value('%s','%s',%f,%f,%f,%f,%f,%f,%f)
                            """ % (self._database, self._table, sqlTs, sqlSymbol, sqlOpen, sqlHigh, sqlLow, sqlClose, sqlQuantity, sqlTurnover, sqlOpeninterest)
                            conn.execute(sql)
                        except Exception as e:
                            print(e)
                            continue

    def update_vic_1d(self):
        """
        @: 根据起止时间补全中间缺失数据
        """
        with self._engine.connect() as conn:
            # 'd:\\1d.csv'
            with open('d:\\' + self._fixperiod + '.csv', 'a') as f:
                # csv存一份，sql更新一份
                s = 'ts,symbol,open,high,low,close,quantity,turnover,openinterest\n'
                f.write(s)

                # 遍历每一个品种，先查日期是否间断，有则下载数据填充mysql
                for key in self._symbols.keys():
                    # 得到某key的ts列为df
                    query = """
                    SELECT DISTINCT ts FROM %s.%s 
                    WHERE symbol='%s' AND ts BETWEEN '%s' AND '%s' 
                    ORDER BY ts;
                    """ % (self._database, self._table, key, self._start, self._end)
                    df = pd.read_sql(sql=query, con=conn)

                    # 选出缺失的ts值，相邻ts算差值再除以周期，大于1的是缺失的ts止点
                    timeDelta = pd.Timedelta(
                        self._config['timedelta'][self._fixperiod]
                    )  # 对应周期的时间delta
                    df['diff'] = df['ts'].diff(1) / timeDelta
                    missingTs = list(df[df['diff'] > 1].index.values)
                    for i in missingTs:
                        # 间断期的起止ts值，去头去尾，中间才是缺少的日期段
                        start, end = df['ts'].ix[i - 1: i].values

                        if ((end - start) / timeDelta) > 1:
                            # 打印缺失的local时间段
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
                            # 打印缺失的utc时间段
                            print('2 symbol:%s\t' % key,
                                  '  utc time -\t', apiStart, apiEnd)
                            # 下载数据
                            try:
                                name = self._symbols[key]
                                data = self._api.ohlcv_historical_data(
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
                                    print(data)  # 如果返回数据为空则打印空值出来查看

                            except Exception as e:
                                print(e)
                                continue

                            for s in data:

                                sqlTs = (dt.strptime(s['time_period_start'], self._UTCTIMEFORMAT) +
                                         pd.Timedelta('0 days 08:00:00')).strftime(self._LOCALTIMEFORMAT)  # 加上8小时
                                sqlSymbol = key
                                sqlOpen = s['price_open']
                                sqlHigh = s['price_high']
                                sqlLow = s['price_low']
                                sqlClose = s['price_close']
                                sqlQuantity = s['volume_traded']
                                sqlTurnover = 0.0  # 实际为null，需求是换为0
                                sqlOpeninterest = 0.0  # 实际为null，需求是换为0

                                f_data = [sqlTs, sqlSymbol, sqlOpen, sqlHigh, sqlLow,
                                          sqlClose, sqlQuantity, sqlTurnover, sqlOpeninterest]
                                print(f_data)

                                sql = """
                                insert into %s.%s(ts,symbol,open,high,low,close,quantity,turnover,openinterest) value('%s','%s',%f,%f,%f,%f,%f,%f,%f)
                                """ % (self._database, self._table, sqlTs, sqlSymbol, sqlOpen, sqlHigh, sqlLow, sqlClose, sqlQuantity, sqlTurnover, sqlOpeninterest)
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
            'ip': '47.74.179.216',  # 216 生产环境
            'port': '3308',
            'database': 'vic_1d',  # 216 数据库vic_1d
            'table': '1d'  # 1d
        },
        'timedelta': {
            '1d': '1 days 00:00:00'  # 1d
        },
        'time': {
            'start': '2018-05-23 08:00:00',  # 开始日期
            'end': '2018-08-16 08:00:00'  # 结束日期
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
        'OKEX--BTC--USDT': 'BITFINEX_SPOT_BTC_USD',
        'OKEX--ETH--USDT': 'BITFINEX_SPOT_ETH_USD',
        'OKEX--BCH--USDT': 'BITFINEX_SPOT_BCH_USD',
        'OKEX--LTC--USDT': 'BITFINEX_SPOT_LTC_USD',
        'OKEX--EOS--USDT': 'BITFINEX_SPOT_EOS_USD',
        'OKEX--XRP--USDT': 'BITFINEX_SPOT_XRP_USD',
        'HUOBI--BTC--USDT': 'HUOBIPRO_SPOT_BTC_USDT',
        'HUOBI--ETH--USDT': 'HUOBIPRO_SPOT_ETH_USDT',
        'HUOBI--BCH--USDT': 'HUOBIPRO_SPOT_BCH_USDT',
        'HUOBI--LTC--USDT': 'HUOBIPRO_SPOT_LTC_USDT',
        'HUOBI--EOS--USDT': 'HUOBIPRO_SPOT_EOS_USDT',
        'HUOBI--XRP--USDT': 'HUOBIPRO_SPOT_XRP_USDT'
    }
    obj = UpdateVIC_1D(config=config, fixperiod='1d')  # 1d
#     obj.update_vic_init()

    obj.update_vic_1d()
