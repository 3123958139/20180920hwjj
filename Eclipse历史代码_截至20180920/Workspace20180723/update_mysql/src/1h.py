# coding:utf-8

"""
@date:20180815
@author: David
"""

from datetime import datetime as dt
import datetime
from sqlalchemy import create_engine
from coinapi_v1 import CoinAPIv1
import pandas as pd


class UpdateVIC(object):
    """
    """

    def __init__(self, config, fixperiod):
        """
        """
        self._config = config
        self._database = self._config['mysql']['database']
        self._table = self._config['mysql']['table']
        self._symbols = self._config['symbolpairs']
        self._start = self._config['time']['start']
        self._end = self._config['time']['end']
        self._fixperiod = fixperiod
        self._UTCTIMEFORMAT = "%Y-%m-%dT%H:%M:%S.0000000Z"
        self._LOCALTIMEFORMAT = "%Y-%m-%d %H:%M:%S"
        self._api = CoinAPIv1(self._config['coinapi']['apikey'])
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

    def localtime_to_utctime(self, localTimeStr):
        """
        """
        utc = dt.strptime(localTimeStr, self._LOCALTIMEFORMAT)
        utc = utc - pd.Timedelta('0 days 08:00:00')
        return str(utc)[:10] + 'T' + str(utc)[-8:]

    def update_vic_init(self):
        """
        """
        apiStart = self.localtime_to_utctime(self._start)
        apiEnd = self.localtime_to_utctime(self._end)

        with self._engine.connect() as conn:
            for t in [apiStart, apiEnd]:
                print('update_vic_init:[utctime]\t' + t)
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
                            print(data)

                    except Exception as e:
                        print(e)
                        continue

                    for s in data:
                        sqlTs = (dt.strptime(s['time_period_start'], self._UTCTIMEFORMAT) +
                                 pd.Timedelta('0 days 08:00:00')).strftime(self._LOCALTIMEFORMAT)
                        sqlSymbol = key
                        sqlOpen = s['price_open']
                        sqlHigh = s['price_high']
                        sqlLow = s['price_low']
                        sqlClose = s['price_close']
                        sqlQuantity = s['volume_traded']
                        sqlTurnover = 0.0
                        sqlOpeninterest = 0.0

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

    def update_vic_data(self):
        """
        """
        with self._engine.connect() as conn:
            with open('d:\\' + self._fixperiod + '.csv', 'a') as f:
                s = 'ts,symbol,open,high,low,close,quantity,turnover,openinterest\n'
                f.write(s)
                for key in self._symbols.keys():
                    query = """
                    SELECT DISTINCT ts FROM %s.%s 
                    WHERE symbol='%s' AND ts BETWEEN '%s' AND '%s' 
                    ORDER BY ts;
                    """ % (self._database, self._table, key, self._start, self._end)
                    df = pd.read_sql(sql=query, con=conn)
                    fixperiod = self._config['timedelta'][self._fixperiod]
                    timeDelta = pd.Timedelta(fixperiod)
                    df['diff'] = df['ts'].diff(1) / timeDelta
                    missingTs = list(df[df['diff'] > 1].index.values)
                    for i in missingTs:
                        start, end = df['ts'].ix[i - 1: i].values

                        if ((end - start) / timeDelta) > 1:
                            print('1 symbol:%s\t' % key,
                                  'local time -\t', str(start)[:19], str(end)[:19])
                            start = start + \
                                timeDelta - \
                                pd.Timedelta('0 days 08:00:00')
                            end = end - \
                                timeDelta - \
                                pd.Timedelta('0 days 08:00:00')
                            apiStart = str(start)[:10] + 'T' + str(start)[-8:]
                            apiEnd = str(end)[:10] + 'T' + str(end)[-8:]
                            print('2 symbol:%s\t' % key,
                                  '  utc time -\t', apiStart, apiEnd)
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
                                    print(data)

                            except Exception as e:
                                print(e)
                                continue

                            for s in data:
                                sqlTs = (dt.strptime(s['time_period_start'], self._UTCTIMEFORMAT) +
                                         pd.Timedelta('0 days 08:00:00')).strftime(self._LOCALTIMEFORMAT)
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
    """
    config = {
        'coinapi': {
            # 收费'AA8D14FA-FFCC-406F-BD17-E7E391D22FD6'
            # 免费'EA8CF467-3ECD-42D6-A59E-97D908AEB57D',
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
            'start': '2018-08-01 16:00:00',
            'end': '2018-09-03 20:00:00'  # datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        'symbolpairs': {
            'BINA--EOS--USDT': 'BITFINEX_SPOT_EOS_USD',
            'BINA--XRP--USDT': 'BITFINEX_SPOT_XRP_USD',
            'BINA--BTC--USDT': 'BITFINEX_SPOT_BTC_USD',
            'BINA--ETH--USDT': 'BITFINEX_SPOT_ETH_USD',
            'BINA--BCC--USDT': 'BITFINEX_SPOT_BCH_USD',
            'BINA--LTC--USDT': 'BITFINEX_SPOT_LTC_USD',
            'BINA--EOS--BTC': 'BITFINEX_SPOT_EOS_BTC',
            'BINA--XRP--BTC': 'BITFINEX_SPOT_XRP_BTC',
            'BINA--ETC--BTC': 'BITFINEX_SPOT_ETC_BTC',
            'BINA--ETH--BTC': 'BITFINEX_SPOT_ETH_BTC',
            'BINA--BCC--BTC': 'BITFINEX_SPOT_BCH_BTC',
            'BINA--LTC--BTC': 'BITFINEX_SPOT_LTC_BTC',

            'OKEX--EOS--USDT': 'BITFINEX_SPOT_EOS_USD',
            'OKEX--XRP--USDT': 'BITFINEX_SPOT_XRP_USD',
            'OKEX--BTC--USDT': 'BITFINEX_SPOT_BTC_USD',
            'OKEX--ETH--USDT': 'BITFINEX_SPOT_ETH_USD',
            'OKEX--BCC--USDT': 'BITFINEX_SPOT_BCH_USD',
            'OKEX--LTC--USDT': 'BITFINEX_SPOT_LTC_USD',
            'OKEX--EOS--BTC': 'BITFINEX_SPOT_EOS_BTC',
            'OKEX--XRP--BTC': 'BITFINEX_SPOT_XRP_BTC',
            'OKEX--ETC--BTC': 'BITFINEX_SPOT_ETC_BTC',
            'OKEX--ETH--BTC': 'BITFINEX_SPOT_ETH_BTC',
            'OKEX--BCC--BTC': 'BITFINEX_SPOT_BCH_BTC',
            'OKEX--LTC--BTC': 'BITFINEX_SPOT_LTC_BTC',

            'HUOBI--EOS--USDT': 'BITFINEX_SPOT_EOS_USD',
            'HUOBI--XRP--USDT': 'BITFINEX_SPOT_XRP_USD',
            'HUOBI--BTC--USDT': 'BITFINEX_SPOT_BTC_USD',
            'HUOBI--ETH--USDT': 'BITFINEX_SPOT_ETH_USD',
            'HUOBI--BCC--USDT': 'BITFINEX_SPOT_BCH_USD',
            'HUOBI--LTC--USDT': 'BITFINEX_SPOT_LTC_USD',
            'HUOBI--EOS--BTC': 'BITFINEX_SPOT_EOS_BTC',
            'HUOBI--XRP--BTC': 'BITFINEX_SPOT_XRP_BTC',
            'HUOBI--ETC--BTC': 'BITFINEX_SPOT_ETC_BTC',
            'HUOBI--ETH--BTC': 'BITFINEX_SPOT_ETH_BTC',
            'HUOBI--BCC--BTC': 'BITFINEX_SPOT_BCH_BTC',
            'HUOBI--LTC--BTC': 'BITFINEX_SPOT_LTC_BTC'


            #             'HUOBI--IOTA--USDT': 'KRAKEN_SPOT_IOTA_USD',
            #             'HUOBI--ADA--USDT': 'KRAKEN_SPOT_ADA_USD',
            #             'HUOBI--ZIL--USDT': 'KRAKEN_SPOT_ZIL_USD',
            #             'HUOBI--ELA--USDT': 'KRAKEN_SPOT_ELA_USD',
            #             'HUOBI--NAS--USDT': 'KRAKEN_SPOT_NAS_USD',
            #             'HUOBI--VEN--USDT': 'KRAKEN_SPOT_VEN_USD',
            #             'HUOBI--NEO--USDT': 'KRAKEN_SPOT_NEO_USD',
            #             'HUOBI--HT--USDT': 'KRAKEN_SPOT_HT_USD',
            #             'BINA--IOTA--USDT': 'BINANCE_SPOT_IOTA_USDT',
            #             'BINA--ADA--USDT': 'BINANCE_SPOT_ADA_USDT',
            #             'BINA--XLM--USDT': 'BINANCE_SPOT_XLM_USDT',
            #             'BINA--VET--USDT': 'BINANCE_SPOT_VET_USDT',
            #             'BINA--NEO--USDT': 'BINANCE_SPOT_NEO_USDT',
            #             'BINA--BNB--USDT': 'BINANCE_SPOT_BNB_USDT',
            #             'OKEX--IOTA--USDT': 'OKEX_SPOT_IOTA_USDT',
            #             'OKEX--ADA--USDT': 'OKEX_SPOT_ADA_USDT',
            #             'OKEX--ZIL--USDT': 'OKEX_SPOT_ZIL_USDT',
            #             'OKEX--ABT--USDT': 'OKEX_SPOT_ABT_USDT',
            #             'OKEX--XLM--USDT': 'OKEX_SPOT_XLM_USDT',
            #             'OKEX--ZRX--USDT': 'OKEX_SPOT_ZRX_USDT',
            #             'OKEX--NAS--USDT': 'OKEX_SPOT_NAS_USDT',
            #             'OKEX--SC--USDT': 'OKEX_SPOT_SC_USDT',
            #             'OKEX--NEO--USDT': 'OKEX_SPOT_NEO_USDT',
            #             'OKEX--OKB--USDT': 'OKEX_SPOT_OKB_USDT'
        }
    }
    obj = UpdateVIC(config=config, fixperiod='1h')
#     obj.update_vic_init()
    for i in range(1):
        obj.update_vic_data()
