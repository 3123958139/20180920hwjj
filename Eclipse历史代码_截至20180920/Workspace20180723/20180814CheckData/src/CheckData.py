from unittest.mock import inplace

import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


df = pd.read_csv('BCH.csv')
df2 = pd.read_csv('BCH (2).csv')

df3 = pd.merge(df[['datetime', 'open']],
               df2[['datetime', 'open']],
               on=['datetime'])

df3['x'] = (df3['open_x'] - df3['open_x'].shift(1)) / df3['open_x'].shift(1)
df3['y'] = (df3['open_y'] - df3['open_y'].shift(1)) / df3['open_y'].shift(1)
df3['diff'] = df3['x'] - df3['y']
df3['datetime'] = df3['datetime'].map(
    lambda x: dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
df3.set_index('datetime', inplace=True)

df3['diff'].plot()
plt.show()
print(df3)
