# coding:utf-8
import list2dict as l2d

import pandas as pd

df = pd.read_csv('symbols.csv')
symbols = list(df['symbol'].values)

d = l2d.list2dict(symbols)
print(d)