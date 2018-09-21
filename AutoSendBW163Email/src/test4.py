import pandas as pd
df = pd.DataFrame([['2018-05-01 00:00', 15951.0, 300.904267, 49.600000],
                   ['2018-05-01 00:15', 16075.0, 300.904267, 49.600000],
                   ['2018-05-01 00:30', 15977.0, 300.904267, 49.600000],
                   ['2018-05-01 01:00', 15868.0, 298.889333, 298.889333]],
                  columns=['Date_time', 'current_demand', 'Temp_Mean', 'humidity_Mean'])

df['Date_time'] = pd.to_datetime(df['Date_time'])

grouper = pd.Grouper(key='Date_time', freq='15T')

res = df.groupby(grouper).first().ffill().reset_index()

dif = sorted(list(set(res['Date_time'].astype(str).values) -set(df['Date_time'].astype(str).values)))
print dif