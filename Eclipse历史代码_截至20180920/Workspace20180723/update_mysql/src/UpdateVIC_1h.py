# coding:utf-8

"""
"""

from sqlalchemy import create_engine
from coinapi_v1 import CoinAPIv1
import datetime as dt
import pandas as pd

test_key = 'EA8CF467-3ECD-42D6-A59E-97D908AEB57D'
api = CoinAPIv1(test_key)

# 直接更新到216生产环境vic_1h.1h
engine = create_engine('mysql+pymysql://' +
                       'ops:ops!@#9988@47.74.179.216:3308/vic_1h')
with engine.connect() as conn:
    # 日期格式调整
    UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.0000000Z"  # coinapi的日期格式
    LOCAL_FORMAT = "%Y-%m-%d %H:%M:%S"  # live的日期格式

    def time_format(inputT):
        return dt.datetime.strptime(inputT, UTC_FORMAT).strftime(LOCAL_FORMAT)

    # 需要更新的品种，每天分市场补全，对BINA--BTC--USDT，BINANCE_SPOT_BTC_USDT无数据，使用BITFINEX_SPOT_BTC_USD替换
    symbols = {
        'BINA--EOS--USDT': 'BITFINEX_SPOT_EOS_USD',
        'BINA--XRP--USDT': 'BITSTAMP_SPOT_XRP_USD',
        'BINA--ETC--USDT': 'BITFINEX_SPOT_ETC_USD',
        'BINA--BTC--USDT': 'BITSTAMP_SPOT_BTC_USD',
        'BINA--ETH--USDT': 'BITSTAMP_SPOT_ETH_USD',
        'BINA--BCC--USDT': 'BITSTAMP_SPOT_BCH_USD',
        'BINA--LTC--USDT': 'BITSTAMP_SPOT_LTC_USD',
        'BINA--DASH--USDT': 'KRAKEN_SPOT_DASH_USD',
        'BINA--BNB--USDT': 'BINANCE_SPOT_BNB_USDT',
        'OKEX--BTC--USDT': 'BITSTAMP_SPOT_BTC_USD',
        'OKEX--ETH--USDT': 'BITSTAMP_SPOT_ETH_USD',
        'OKEX--BCH--USDT': 'BITSTAMP_SPOT_BCH_USD',
        'OKEX--LTC--USDT': 'BITSTAMP_SPOT_LTC_USD',
        'OKEX--EOS--USDT': 'BITFINEX_SPOT_EOS_USD',
        'OKEX--XRP--USDT': 'BITSTAMP_SPOT_XRP_USD',
        'OKEX--ETC--USDT': 'BITFINEX_SPOT_ETC_USD',
        'OKEX--DASH--USDT': 'BITFINEX_SPOT_DASH_USD',
        'OKEX--OKB--USDT': 'OKEX_SPOT_OKB_USDT',
        'HUOBI--BTC--USDT': 'HUOBIPRO_SPOT_BTC_USDT',
        'HUOBI--ETH--USDT': 'HUOBIPRO_SPOT_ETH_USDT',
        'HUOBI--BCH--USDT': 'BITFINEX_SPOT_BCH_USD',
        'HUOBI--LTC--USDT': 'HUOBIPRO_SPOT_LTC_USDT',
        'HUOBI--EOS--USDT': 'HUOBIPRO_SPOT_EOS_USDT',
        'HUOBI--XRP--USDT': 'HUOBIPRO_SPOT_XRP_USDT',
        'HUOBI--ETC--USDT': 'HUOBIPRO_SPOT_ETC_USDT',
        'HUOBI--DASH--USDT': 'HUOBIPRO_SPOT_DASH_USDT',
        'HUOBI--HT--USDT': 'HUOBIPRO_SPOT_HT_USDT'
    }

    # 需要更新的时间段，补全间断，没有后接，待处理
    dateStart = '2018-05-31 00:00:00'
    dateEnd = '2018-08-15 14:00:00'

    with open('d:\\david_1h_20180815.csv', 'a') as f:  # append方式打开文档
        # csv存一份，sql更新一份
        s = 'ts,symbol,open,high,low,close,quantity\n'
        f.write(s)

        # 遍历每一个品种，先查日期是否间断，有则下载数据填充mysql
        for key in symbols.keys():
            # 取1h表的某key的ts列
            query = """
            SELECT DISTINCT ts FROM vic_1h.1h 
            WHERE symbol='%s' AND ts BETWEEN '%s' AND '%s' 
            ORDER BY ts;
            """ % (key, dateStart, dateEnd)
            df = pd.read_sql(sql=query, con=conn)

            # 选出间隔大于1h的ts值
            df['diff'] = df['ts'].diff(1) / pd.Timedelta('0 days 01:00:00')
            tsOut = list(df[df['diff'] > 1].index.values)

            for i in tsOut:
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
                        insert into vic_1h.1h(ts,symbol,open,high,low,close,quantity) value('%s','%s',%f,%f,%f,%f,%f)
                        """ % (ts, symbol, open, high, low, close, quantity)
                        conn.execute(sql)

                        s = str(f_data).replace('[', '').replace(']', '')
                        s = s.replace("'", '') + '\n'
                        f.write(s)
