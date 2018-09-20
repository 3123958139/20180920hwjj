from pyalgotrade import plotter
from pyalgotrade import strategy
from pyalgotrade.bar import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.technical import bollinger
from sqlalchemy.engine import create_engine
import pandas as pd


def sql_to_csv(label=True, symbol='BINA--BTC--USDT'):
    '''export mysql data to csv file.
    '''
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


class BBands(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, bBandsPeriod):
        super(BBands, self).__init__(feed)
        self.__instrument = instrument
        self.__bbands = bollinger.BollingerBands(
            feed[instrument].getCloseDataSeries(), bBandsPeriod, 2)

    def getBollingerBands(self):
        return self.__bbands

    def onBars(self, bars):
        lower = self.__bbands.getLowerBand()[-1]
        upper = self.__bbands.getUpperBand()[-1]
        if lower is None:
            return

        shares = self.getBroker().getShares(self.__instrument)
        bar = bars[self.__instrument]
        if shares == 0 and bar.getClose() < lower:
            sharesToBuy = int(self.getBroker().getCash(False) / bar.getClose())
            self.marketOrder(self.__instrument, sharesToBuy)
        elif shares > 0 and bar.getClose() > upper:
            self.marketOrder(self.__instrument, -1 * shares)


def main(plot):
    symbol = sql_to_csv(True)
    instrument = symbol
    bBandsPeriod = 40

    # Download the bars.
    feed = GenericBarFeed(Frequency.DAY, None, None)
    feed.addBarsFromCSV(symbol, symbol + '.csv')

    strat = BBands(feed, instrument, bBandsPeriod)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, True, True)
        plt.getInstrumentSubplot(instrument).addDataSeries(
            "upper", strat.getBollingerBands().getUpperBand())
        plt.getInstrumentSubplot(instrument).addDataSeries(
            "middle", strat.getBollingerBands().getMiddleBand())
        plt.getInstrumentSubplot(instrument).addDataSeries(
            "lower", strat.getBollingerBands().getLowerBand())

    strat.run()
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)
