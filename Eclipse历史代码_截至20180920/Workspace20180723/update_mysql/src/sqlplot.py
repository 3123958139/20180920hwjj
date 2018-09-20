# coding:utf-8

"""
@date:20180822
@author: David
"""

from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import pandas as pd


engine = create_engine('mysql+pymysql://' +
                       'ops:ops!@#9988@47.74.249.179:3308/david')

symbols = ['BINA--EOS--USDT', 'BINA--XRP--USDT', 'BINA--BTC--USDT',
           'BINA--ETH--USDT', 'BINA--BCC--USDT', 'BINA--LTC--USDT',
           'BINA--EOS--BTC', 'BINA--XRP--BTC', 'BINA--ETC--BTC',
           'BINA--ETH--BTC', 'BINA--BCC--BTC', 'BINA--LTC--BTC']

with engine.connect() as con:
    for s in symbols:
        sql = "select ts,close from %s.%s where symbol = '%s' order by ts" % (
            'vic_1d', '1d', s)
#         sql = "select ts,close from %s.%s where symbol = '%s' order by ts" % (
#             'vic_1h', '1h', s)
        df = pd.read_sql(sql, con)
        df.set_index('ts', inplace=True)
        df.plot()
        plt.title(s)
        plt.show()
