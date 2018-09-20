# coding:utf-8
import datetime as dt
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import tushare as ts


df = ts.get_k_data('002237')
df = df[['date', 'close']]

# 日期格式由str调整为datetime64
df['date'] = df['date'].map(lambda x: dt.datetime.strptime(x, '%Y-%m-%d'))

date = df['date']
close = df['close']

fig, ax = plt.subplots(1, 1)
ax.plot(date, close, lw=2.5)

fig.suptitle('Close Price of 002237', fontsize=18, ha='center')

# figure的外框显示设置
ax.spines['top'].set_visible(False)
ax.spines['bottom'].set_visible(True)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)

plt.grid(True, 'major', 'y', ls='--', lw=.5, c='k', alpha=.3)
plt.tick_params(axis='both', which='both', bottom=True, top=False,
                labelbottom=True, left=False, right=False, labelleft=True)

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # 日期格式
plt.xticks(rotation=60)  # 日期旋转

close_argmax = df['close'].values.argmax()
close_argmin = df['close'].values.argmin()

# 最高点，最低点画竖线
plt.axvline(df['date'][close_argmax], c='r', lw=2.5)
plt.axvline(df['date'][close_argmin], c='r', lw=2.5)

plt.show()
