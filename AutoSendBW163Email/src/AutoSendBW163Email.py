import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

df = pd.read_excel('BW_NETVALUE.xlsx')
df.set_index('date')
df[['unitnet_usdt', 'unitnet_btc']].plot()
plt.show()

print(df.head())
