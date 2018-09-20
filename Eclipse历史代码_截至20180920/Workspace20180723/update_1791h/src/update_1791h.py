# coding:utf-8

"""
@Company : HWJJ
@Date    : 20180810
@Author  : David
"""

from sqlalchemy import create_engine

from coinapi_v1 import CoinAPIv1
import datetime as dt
import list2dict as l2d
import pandas as pd


# key1和key2似乎互斥，流量不能叠加，不知道为什么
test_key = 'EA8CF467-3ECD-42D6-A59E-97D908AEB57D'  # key1
# test_key = '778C65A3-E842-4C10-B5FF-C1AF0F56E78E'  # key2
# test_key = 'F998EBA9-86E5-411A-B434-45D51B6FCBFE'  # key3
api = CoinAPIv1(test_key)


# 使用179地址的david库1h表做测试
engine = create_engine('mysql+pymysql://' +
                       'ops:ops!@#9988@47.74.249.179:3308/david')  # ?charset=utf8&autocommit=true
with engine.connect() as conn:
    # 日期格式调整
    UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.0000000Z"  # coinapi的日期格式
    LOCAL_FORMAT = "%Y-%m-%d %H:%M:%S"  # live的日期格式

    def time_format(inputT):
        return dt.datetime.strptime(inputT, UTC_FORMAT).strftime(LOCAL_FORMAT)

    # 需要更新的品种，每天分市场补全，对BINA--BTC--USDT，BINANCE_SPOT_BTC_USDT无数据，使用BITFINEX_SPOT_BTC_USD替换
    df = pd.read_csv('symbols.csv')
    symbols = l2d.list2dict(list(df['symbol'].values),
                            exchange='BITFINEX_SPOT')

    # 需要更新的时间段，补全间断，没有后接，待处理
    dateStart = '2018-05-31 00:00:00'
    dateEnd = '2018-08-01 00:00:00'

    with open('d:\\update_1791h.csv', 'a') as f:  # append方式打开文档
        # csv存一份，sql更新一份
        s = 'ts,symbol,open,high,low,close,quantity\n'
        f.write(s)

        # 遍历每一个品种，先查日期是否间断，有则下载数据填充mysql
        for key in symbols.keys():
            # 取1h表的某key的ts列
            query = """
            SELECT DISTINCT ts FROM david.1h 
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
                        insert into david.1h(ts,symbol,open,high,low,close,quantity) value('%s','%s',%f,%f,%f,%f,%f)
                        """ % (ts, symbol, open, high, low, close, quantity)
                        conn.execute(sql)

                        s = str(f_data).replace('[', '').replace(']', '')
                        s = s.replace("'", '') + '\n'
                        f.write(s)
