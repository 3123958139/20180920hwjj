# coding:utf-8

"""
@date:20180815
@author: David
"""

from datetime import datetime as dt
from sqlalchemy import create_engine
from coinapi_v1 import CoinAPIv1
import pandas as pd


class UpdateVIC(object):
    """对数据库进行补全
    """

    def __init__(self, config, fixperiod):
        """全局变量和常量
        """
        self._config = config
        self._database = self._config['mysql']['database']
        self._table = self._config['mysql']['table']
        self._symbols = self._config['symbolpairs']
        self._start = self._config['time']['start']
        self._end = self._config['time']['end']
        # 补全的周期
        self._fixperiod = fixperiod
        # coinapi的日期格式utc
        # mysql的日期格式local
        self._UTCTIMEFORMAT = "%Y-%m-%dT%H:%M:%S.0000000Z"
        self._LOCALTIMEFORMAT = "%Y-%m-%d %H:%M:%S"
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
        self._nullTs = {
            'BINA--EOS--USDT': [],
            'BINA--XRP--USDT': [],
            'BINA--BTC--USDT': [],
            'BINA--ETH--USDT': [],
            'BINA--BCC--USDT': [],
            'BINA--LTC--USDT': [],
            'BINA--EOS--BTC': [],
            'BINA--XRP--BTC': [],
            'BINA--ETC--BTC': [],
            'BINA--ETH--BTC': [],
            'BINA--BCC--BTC': [],
            'BINA--LTC--BTC': [],

            'OKEX--EOS--USDT': [],
            'OKEX--XRP--USDT': [],
            'OKEX--BTC--USDT': [],
            'OKEX--ETH--USDT': [],
            'OKEX--BCC--USDT': [],
            'OKEX--LTC--USDT': [],
            'OKEX--EOS--BTC': [],
            'OKEX--XRP--BTC': [],
            'OKEX--ETC--BTC': [],
            'OKEX--ETH--BTC': [],
            'OKEX--BCC--BTC': [],
            'OKEX--LTC--BTC': [],

            'HUOBI--EOS--USDT': [],
            'HUOBI--XRP--USDT': [],
            'HUOBI--BTC--USDT': [],
            'HUOBI--ETH--USDT': [],
            'HUOBI--BCC--USDT': [],
            'HUOBI--LTC--USDT': [],
            'HUOBI--EOS--BTC': [],
            'HUOBI--XRP--BTC': [],
            'HUOBI--ETC--BTC': [],
            'HUOBI--ETH--BTC': [],
            'HUOBI--BCC--BTC': [],
            'HUOBI--LTC--BTC': []
        }

    def localtime_to_utctime(self, localTimeStr):
        """local时间转为utc时间，减去8小时时区，再做成coinapi日期参数格式
        """
        utc = dt.strptime(localTimeStr, self._LOCALTIMEFORMAT)
        utc = utc - pd.Timedelta('0 days 08:00:00')
        return str(utc)[:10] + 'T' + str(utc)[-8:]

    def update_vic_init(self):
        """首先根据给定的起止时间更新时间头时间尾记录，确保头尾不缺失
        """
        apiStart = self.localtime_to_utctime(self._start)
        apiEnd = self.localtime_to_utctime(self._end)
        with self._engine.connect() as conn:
            # 先补齐日期头再补齐日期尾
            for t in [apiStart, apiEnd]:
                print('update_vic_init:[utctime]\t' + t)
                # 遍历品种字典
                for key in self._symbols.keys():
                    try:
                        name = self._symbols[key]
                        periodId = self._config['coinapi']['period'][self._fixperiod]
                        data = self._api.ohlcv_historical_data(
                            name,
                            {
                                'period_id': periodId,
                                'time_start': t,
                                'time_end': t
                            }
                        )
                        if data:
                            pass
                        else:
                            # 如果返回数据为空则打印空值出来查看
                            print(data)
                    except Exception as e:
                        print(e)
                        continue
                    for s in data:
                        # 加上8小时
                        sqlTs = (dt.strptime(s['time_period_start'], self._UTCTIMEFORMAT) +
                                 pd.Timedelta('0 days 08:00:00')).strftime(self._LOCALTIMEFORMAT)
                        sqlSymbol = key
                        sqlOpen = s['price_open']
                        sqlHigh = s['price_high']
                        sqlLow = s['price_low']
                        sqlClose = s['price_close']
                        sqlQuantity = s['volume_traded']
                        # 实际为null，需求是换为0
                        sqlTurnover = 0.0
                        sqlOpeninterest = 0.0
                        print([sqlTs, sqlSymbol, sqlOpen, sqlHigh,
                               sqlLow, sqlClose, sqlQuantity, sqlTurnover, sqlOpeninterest])
                        # 可能表里有数据了会报错，但不影响，后续优化
                        try:
                            sql = """
                            insert into %s.%s(ts,symbol,open,high,low,close,quantity,turnover,openinterest) value('%s','%s',%f,%f,%f,%f,%f,%f,%f)
                            """ % (self._database, self._table, sqlTs, sqlSymbol, sqlOpen, sqlHigh, sqlLow, sqlClose, sqlQuantity, sqlTurnover, sqlOpeninterest)
                            conn.execute(sql)
                        except Exception as e:
                            print(e)
                            continue

    def update_vic_data(self):
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
                    fixperiod = self._config['timedelta'][self._fixperiod]
                    timeDelta = pd.Timedelta(fixperiod)
                    df['diff'] = df['ts'].diff(1) / timeDelta
                    missingTs = list(df[df['diff'] > 1].index.values)
                    fillTs = list(set(missingTs) - set(self._nullTs[key]))
                    for i in fillTs:
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
                                periodId = self._config['coinapi']['period'][self._fixperiod]
                                data = self._api.ohlcv_historical_data(
                                    name,
                                    {
                                        'period_id': periodId,
                                        'time_start': apiStart,
                                        'time_end': apiEnd
                                    }
                                )
                                if data:
                                    pass
                                else:
                                    self._nullTs[key].append(i)
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
                                sqlTurnover = 0.0
                                sqlOpeninterest = 0.0
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
    @note: api周期清单
    Second    1SEC, 2SEC, 3SEC, 4SEC, 5SEC, 6SEC, 10SEC, 15SEC, 20SEC, 30SEC
    Minute    1MIN, 2MIN, 3MIN, 4MIN, 5MIN, 6MIN, 10MIN, 15MIN, 20MIN, 30MIN
    Hour      1HRS, 2HRS, 3HRS, 4HRS, 6HRS, 8HRS, 12HRS
    Day       1DAY, 2DAY, 3DAY, 5DAY, 7DAY, 10DAY
    Month     1MTH, 2MTH, 3MTH, 4MTH, 6MTH
    Year      1YRS, 2YRS, 3YRS, 4YRS, 5YRS
    """
    # 主要修改这个config
    # 注意先注释掉执行语句，确定好config再说
    config = {
        'coinapi': {
            # 免费'EA8CF467-3ECD-42D6-A59E-97D908AEB57D'
            # 付费'AA8D14FA-FFCC-406F-BD17-E7E391D22FD6'
            'apikey': 'AA8D14FA-FFCC-406F-BD17-E7E391D22FD6',
            'period': {
                '1h': '1HRS'
            }
        },
        'mysql': {
            'user': 'ops',
            'password': 'ops!@#9988',
            'ip': '47.74.179.216',
            'port': '3308',
            'database': 'vic_1h',
            'table': '1h'
        },
        'timedelta': {
            '1h': '0 days 01:00:00'
        },
        'time': {
            'start': '2018-01-01 08:00:00',
            'end': '2018-09-21 08:00:00'
        },
        'symbolpairs': {# 尝试BITFINEX和KRAKEN，补补全且缺失不到则fillna
            'BINA--EOS--USDT': 'KRAKEN_SPOT_EOS_USD',
            'BINA--XRP--USDT': 'KRAKEN_SPOT_XRP_USD',
            'BINA--BTC--USDT': 'KRAKEN_SPOT_BTC_USD',
            'BINA--ETH--USDT': 'KRAKEN_SPOT_ETH_USD',
            'BINA--BCC--USDT': 'KRAKEN_SPOT_BCH_USD',
            'BINA--LTC--USDT': 'KRAKEN_SPOT_LTC_USD',
            'BINA--EOS--BTC': 'KRAKEN_SPOT_EOS_BTC',
            'BINA--XRP--BTC': 'KRAKEN_SPOT_XRP_BTC',
            'BINA--ETC--BTC': 'KRAKEN_SPOT_ETC_BTC',
            'BINA--ETH--BTC': 'KRAKEN_SPOT_ETH_BTC',
            'BINA--BCC--BTC': 'KRAKEN_SPOT_BCH_BTC',
            'BINA--LTC--BTC': 'KRAKEN_SPOT_LTC_BTC',

            'OKEX--EOS--USDT': 'KRAKEN_SPOT_EOS_USD',
            'OKEX--XRP--USDT': 'KRAKEN_SPOT_XRP_USD',
            'OKEX--BTC--USDT': 'KRAKEN_SPOT_BTC_USD',
            'OKEX--ETH--USDT': 'KRAKEN_SPOT_ETH_USD',
            'OKEX--BCC--USDT': 'KRAKEN_SPOT_BCH_USD',
            'OKEX--LTC--USDT': 'KRAKEN_SPOT_LTC_USD',
            'OKEX--EOS--BTC': 'KRAKEN_SPOT_EOS_BTC',
            'OKEX--XRP--BTC': 'KRAKEN_SPOT_XRP_BTC',
            'OKEX--ETC--BTC': 'KRAKEN_SPOT_ETC_BTC',
            'OKEX--ETH--BTC': 'KRAKEN_SPOT_ETH_BTC',
            'OKEX--BCC--BTC': 'KRAKEN_SPOT_BCH_BTC',
            'OKEX--LTC--BTC': 'KRAKEN_SPOT_LTC_BTC',

            'HUOBI--EOS--USDT': 'KRAKEN_SPOT_EOS_USD',
            'HUOBI--XRP--USDT': 'KRAKEN_SPOT_XRP_USD',
            'HUOBI--BTC--USDT': 'KRAKEN_SPOT_BTC_USD',
            'HUOBI--ETH--USDT': 'KRAKEN_SPOT_ETH_USD',
            'HUOBI--BCC--USDT': 'KRAKEN_SPOT_BCH_USD',
            'HUOBI--LTC--USDT': 'KRAKEN_SPOT_LTC_USD',
            'HUOBI--EOS--BTC': 'KRAKEN_SPOT_EOS_BTC',
            'HUOBI--XRP--BTC': 'KRAKEN_SPOT_XRP_BTC',
            'HUOBI--ETC--BTC': 'KRAKEN_SPOT_ETC_BTC',
            'HUOBI--ETH--BTC': 'KRAKEN_SPOT_ETH_BTC',
            'HUOBI--BCC--BTC': 'KRAKEN_SPOT_BCH_BTC',
            'HUOBI--LTC--BTC': 'KRAKEN_SPOT_LTC_BTC'
        }
    }
    # 1h
    obj = UpdateVIC(config=config, fixperiod='1h')  # 1h
#     obj.update_vic_init()
    for i in range(2):
        obj.update_vic_data()
