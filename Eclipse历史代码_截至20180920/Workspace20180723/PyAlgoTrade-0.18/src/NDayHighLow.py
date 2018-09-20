"""
@date:2018-08-24
@author:David
"""
from pyalgotrade import plotter, dataseries
from pyalgotrade import strategy
from pyalgotrade import technical
from pyalgotrade.bar import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.broker.backtesting import TradePercentage
from pyalgotrade.dataseries import DataSeries
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import returns as rets
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import trades
from pyalgotrade.technical.cross import cross_above, cross_below
from pyalgotrade.technical.ma import SMA
from sqlalchemy.engine import create_engine
from sympy.printing.pretty.pretty_symbology import sup
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def mysqlToCsv(label=True, database='vic_1h', table='1h', instrument='BINA--BTC--USDT'):
    """
    """
    if label:
        try:
            engine = create_engine(
                'mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/david'
            )
            con = engine.connect()
            sql = """select ts,high as High,open as Open,low as Low,close as Close,quantity as Volume 
            from %s.%s where symbol='%s' and ts between '2018-07-29 08:00:00' and '2018-08-01 08:00:00' order by ts;
            """ % (database, table, instrument)
            df = pd.read_sql(sql, con)
            df.rename(columns={'ts': 'Date Time'}, inplace=True)
            df['Adj Close'] = df['Close']
            df.to_csv(instrument + '.csv', index=False)
            con.close()
            return True
        except Exception as e:
            print(e)
            return False
    else:
        return True


class myStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument):
        super(myStrategy, self).__init__(feed)
        self.__instrument = instrument
        self.__high = feed[instrument].getHighDataSeries()
        self.__low = feed[instrument].getLowDataSeries()
        self.ncp5 = []
        self.ncp55 = []
        self.counter = 0

    def __ncp5(self):
        return (max(self.__high[- 6:-1]) / min(self.__low[-6:-1]) - 1) * 100

    def __ncp55(self):
        return (max(self.__high[- 16:-6]) / min(self.__low[-16:-6]) - 1) * 100

    def onBars(self, bars):
        if len(self.__high) < 55:
            return
        self.ncp5.append(self.__ncp5())
        self.ncp55.append(self.__ncp55())

        if self.__ncp5() > self.__ncp55():
            print(bars[self.__instrument].getDateTime())
            self.counter += 1


def mainPlot():
    instrument = 'BINA--BTC--USDT'
    if mysqlToCsv(label=True, database='vic_5mk', table='5mk', instrument=instrument):
        feed = GenericBarFeed(Frequency.MINUTE * 5, None, None)
        feed.addBarsFromCSV(instrument, instrument + '.csv')

    strat = myStrategy(feed, instrument)
    strat.run()
    plt.plot(strat.ncp5)
    plt.plot(strat.ncp55)
    plt.show()
    print(strat.counter)


if __name__ == '__main__':
    mainPlot()
