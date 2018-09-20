# coding:utf-8
from sqlalchemy import create_engine
from coinapi_v1 import CoinAPIv1
import datetime as dt
import pandas as pd


# test_key = 'EA8CF467-3ECD-42D6-A59E-97D908AEB57D'
test_key = '778C65A3-E842-4C10-B5FF-C1AF0F56E78E'
api = CoinAPIv1(test_key)

#  使用179地址的test库1h表做测试
engine = create_engine('mysql+pymysql://' +
                       'ops:ops!@#9988@47.74.249.179:3308/test')  # ?charset=utf8&autocommit=true
with engine.connect() as conn:
    # 日期格式调整
    UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.0000000Z"
    LOCAL_FORMAT = "%Y-%m-%d %H:%M:%S"

    def time_format(inputT):
        return dt.datetime.strptime(inputT, UTC_FORMAT).strftime(LOCAL_FORMAT)

    # 需要更新的品种
    symbols = {'BINA--BTC--USDT': 'BINANCE_SPOT_BTC_USDT'}
#                'BINA--ETH--USDT': 'BINANCE_SPOT_ETH_USDT',
#                'BINA--BCC--USDT': 'BINANCE_SPOT_BCC_USDT',
#                'BINA--LTC--USDT': 'BINANCE_SPOT_LTC_USDT',
#                'BINA--EOS--USDT': 'BINANCE_SPOT_EOS_USDT',
#                'BINA--XRP--USDT': 'BINANCE_SPOT_XRP_USDT',
#                'BINA--ETC--USDT': 'BINANCE_SPOT_ETC_USDT',
#                'BINA--DASH--USDT': 'BINANCE_SPOT_DASH_USDT',
#                'BINA--BNB--USDT': 'BINANCE_SPOT_BNB_USDT',
#                'OKEX--BTC--USDT': 'OKEX_SPOT_BTC_USDT',
#                'OKEX--ETH--USDT': 'OKEX_SPOT_ETH_USDT',
#                'OKEX--BCH--USDT': 'OKEX_SPOT_BCH_USDT',
#                'OKEX--LTC--USDT': 'OKEX_SPOT_LTC_USDT',
#                'OKEX--EOS--USDT': 'OKEX_SPOT_EOS_USDT',
#                'OKEX--XRP--USDT': 'OKEX_SPOT_XRP_USDT',
#                'OKEX--ETC--USDT': 'OKEX_SPOT_ETC_USDT',
#                'OKEX--DASH--USDT': 'OKEX_SPOT_DASH_USDT',
#                'OKEX--OKB--USDT': 'OKEX_SPOT_OKB_USDT',
#                'HUOBI--BTC--USDT': 'HUOBIPRO_SPOT_BTC_USDT',
#                'HUOBI--ETH--USDT': 'HUOBIPRO_SPOT_ETH_USDT',
#                'HUOBI--BCH--USDT': 'HUOBIPRO_SPOT_BCH_USDT',
#                'HUOBI--LTC--USDT': 'HUOBIPRO_SPOT_LTC_USDT',
#                'HUOBI--EOS--USDT': 'HUOBIPRO_SPOT_EOS_USDT',
#                'HUOBI--XRP--USDT': 'HUOBIPRO_SPOT_XRP_USDT',
#                'HUOBI--ETC--USDT': 'HUOBIPRO_SPOT_ETC_USDT',
#                'HUOBI--DASH--USDT': 'HUOBIPRO_SPOT_DASH_USDT',
#                'HUOBI--HT--USDT': 'HUOBIPRO_SPOT_HT_USDT'}

    # 需要更新的时间段，补全间断，没有后接，待处理
    dateStart = '2018-06-01 00:00:00'
    dateEnd = '2018-08-01 00:00:00'

    with open('d:\\test_1h.csv', 'w') as f:
        # 遍历每一个品种，先查日期是否间断，有则下载数据填充mysql
        for key in symbols.keys():
            #  取1h表的某key的ts列
            query = """
            SELECT DISTINCT ts FROM test.1h 
            WHERE symbol='%s' AND ts BETWEEN '%s' AND '%s' 
            ORDER BY ts;
            """ % (key, dateStart, dateEnd)
            df = pd.read_sql(sql=query, con=conn)

            # 选出间隔大于1h的ts值
            df['diff'] = df['ts'].diff(1) / pd.Timedelta('0 days 01:00:00')
            tsOut = list(df[df['diff'] > 1].index.values)

            # csv存一份，sql更新一份
            s = 'ts,symbol,open,high,low,close,quantity\n'
            f.write(s)

            for i in tsOut:
                # 间断期的起止ts值
                start, end = df['ts'].ix[i - 1: i].values

                # coinapi参数是19位
                downLoadStart = str(start)[:19]
                downLoadEnd = str(end)[:19]

                print('symbol:%s\t' % key +
                      'tsDelta:\t' + downLoadStart + '\t-\t' + downLoadEnd)

                name = symbols[key]
                try:
                    data = api.ohlcv_historical_data(name,
                                                     {'period_id': '1HRS', 'time_start': downLoadStart, 'time_end': downLoadEnd})
                except Exception as e:
                    print(e)
                    continue

                for s in data:  # 去头去尾[1:-1]，因为头尾在mysql里面已经存在
                    print(s)

                    ts = time_format(s['time_period_start'])
                    symbol = key
                    open = s['price_open']
                    high = s['price_high']
                    low = s['price_low']
                    close = s['price_close']
                    quantity = s['volume_traded']

                    sql = """
                    insert into test.1h(ts,symbol,open,high,low,close,quantity) value('%s','%s',%d,%d,%d,%d,%d)
                    """ % (ts, symbol, open, high, low, close, quantity)
                    conn.execute(sql)

                    f_data = [ts, symbol, open, high, low, close, quantity]
                    s = str(f_data).replace('[', '').replace(']', '')
                    s = s.replace("'", '') + '\n'
                    f.write(s)
