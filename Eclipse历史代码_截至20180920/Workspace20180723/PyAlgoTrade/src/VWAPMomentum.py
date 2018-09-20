#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

from unittest.mock import inplace

from pyalgotrade import plotter
from pyalgotrade import strategy
from pyalgotrade.bar import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.technical import vwap
from sqlalchemy.engine import create_engine

import pandas as pd


# export mysql data to csv file.
def sql_to_csv(label=True, symbol='BINA--BTC--USDT'):
    if label:
        engine = create_engine(
            'mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/vic_5mk')
        con = engine.connect()
        sql = """select ts,high as High,open as Open,low as Low,close as Close,quantity as Volume from %s.%s where symbol='%s' order by ts;
        """ % ('vic_1d', '1d', symbol)
        df = pd.read_sql(sql, con)
        df.rename(columns={'ts': 'Date Time'}, inplace=True)
        df.to_csv(symbol + '.csv', index=False)
        return symbol
    else:
        return symbol


class VWAPMomentum(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, vwapWindowSize, threshold):
        super(VWAPMomentum, self).__init__(feed)
        self.__instrument = instrument
        self.__vwap = vwap.VWAP(feed[instrument], vwapWindowSize)
        self.__threshold = threshold

    def getVWAP(self):
        return self.__vwap

    def onBars(self, bars):
        vwap = self.__vwap[-1]
        if vwap is None:
            return

        shares = self.getBroker().getShares(self.__instrument)
        price = bars[self.__instrument].getClose()
        notional = shares * price

        if price > vwap * (1 + self.__threshold) and notional < 1000000:
            self.marketOrder(self.__instrument, 100)
        elif price < vwap * (1 - self.__threshold) and notional > 0:
            self.marketOrder(self.__instrument, -100)


def main(plot):
    symbol = sql_to_csv(False)
    instrument = symbol
    vwapWindowSize = 5
    threshold = 0.01

    # Download the bars.
    feed = GenericBarFeed(Frequency.DAY, None, None)

    feed.addBarsFromCSV(symbol, symbol + '.csv')

    strat = VWAPMomentum(feed, instrument, vwapWindowSize, threshold)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)
        plt.getInstrumentSubplot(instrument).addDataSeries(
            "vwap", strat.getVWAP())

    strat.run()
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)
