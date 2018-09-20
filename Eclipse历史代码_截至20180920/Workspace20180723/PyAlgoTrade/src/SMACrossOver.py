from pyalgotrade import plotter
from pyalgotrade import strategy
from pyalgotrade.bar import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.technical import cross
from pyalgotrade.technical import ma
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
        df['Adj Close'] = df['Close']
        df.to_csv(symbol + '.csv', index=False)
        return symbol
    else:
        return symbol


class SMACrossOver(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod):
        super(SMACrossOver, self).__init__(feed)
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__sma = ma.SMA(self.__prices, smaPeriod)

    def getSMA(self):
        return self.__sma

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        # If RSI2 position was not opened, check if we should enter RSI2 long
        # position.
        if self.__position is None:
            if cross.cross_above(self.__prices, self.__sma) > 0:
                shares = int(self.getBroker().getCash() * 0.9 /
                             bars[self.__instrument].getPrice())
                # Enter RSI2 buy market order. The order is good till canceled.
                self.__position = self.enterLong(
                    self.__instrument, shares, True)
        # Check if we have to exit the position.
        elif not self.__position.exitActive() and cross.cross_below(self.__prices, self.__sma) > 0:
            self.__position.exitMarket()


def main(plot):
    symbol = sql_to_csv(True)

    instrument = symbol
    smaPeriod = 10

    # Download the bars.
    feed = GenericBarFeed(Frequency.DAY, None, None)
    feed.addBarsFromCSV(symbol, symbol + '.csv')

    strat = SMACrossOver(feed, instrument, smaPeriod)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)
        plt.getInstrumentSubplot(instrument).addDataSeries(
            "sma", strat.getSMA())

    strat.run()
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)
