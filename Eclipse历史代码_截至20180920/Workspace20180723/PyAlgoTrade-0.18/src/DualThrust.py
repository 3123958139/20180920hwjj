from pyalgotrade import plotter
from pyalgotrade import strategy
from pyalgotrade.bar import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.stratanalyzer import sharpe
from sqlalchemy.engine import create_engine
import pandas as pd

"""
@date:2018-08-24
@author:David
"""


def sql_to_csv(label=True, database='vic_5mk', table='5mk', instrument='BINA--BTC--USDT'):
    """q导出mysql数据到csv，其中csv需要根据pyalgotrade的数据格式调整字段，如果本地无该csv则下载，有则label设为False直接使用本地csv
    """
    if label:
        try:
            engine = create_engine(
                'mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/david'
            )
            con = engine.connect()
            sql = """select ts,high as High,open as Open,low as Low,close as Close,quantity as Volume 
            from %s.%s where symbol='%s' and ts>'2018-01-01 08:00:00' order by ts;
            """ % (database, table, instrument)
            df = pd.read_sql(sql, con)
            df.rename(columns={'ts': 'Date Time'}, inplace=True)
            df['Adj Close'] = df['Close']
            df.to_csv(instrument + '.csv', index=False)
            con.close()
            return instrument
        except Exception as e:
            print(e)
            return instrument
    else:
        return instrument


class DualThrust(strategy.BacktestingStrategy):
    """q策略逻辑：https://www.v2ex.com/t/360405
    TB代码：http://blog.sina.com.cn/s/blog_53f0769d0102x1zq.html
    """

    def __init__(self, feed, instrument):
        """
        """
        super(DualThrust, self).__init__(feed)
        self.__instrument = instrument
        self.__open = feed[instrument].getOpenDataSeries()
        self.__high = feed[instrument].getHighDataSeries()
        self.__low = feed[instrument].getLowDataSeries()
        self.__close = feed[instrument].getCloseDataSeries()
        # 策略参数
        self.__k1 = 0.5
        self.__k2 = 0.5
        self.__mday = 5
        self.__nday = 5
        self.__lots = 5
        self.__offset = 0
        # 用于存储上下轨数据
        self.__buyposition = []
        self.__sellposition = []

    def get_high(self):
        """
        """
        return self.__high

    def get_low(self):
        """
        """
        return self.__low

    def get_buy_position(self):
        """q上轨线
        """
        return self.__buyposition

    def get_sell_position(self):
        """q下轨线
        """
        return self.__sellposition

    def onBars(self, bars):
        """q一根bar就是一个事件，一根bar只含当前时点的数据，如果需要更早的数据，使用self里面的全序列
        """
        if len(self.__high) < max(self.__mday, self.__nday):
            return

        bar = bars[self.__instrument]

        hh = max(self.__high[-self.__mday:])
        hc = max(self.__close[-self.__mday:])
        ll = min(self.__low[-self.__mday:])
        lc = min(self.__close[-self.__mday:])

        sellrange = max((hh - lc), (hc - ll))

        hh = max(self.__high[-self.__nday:])
        hc = max(self.__close[-self.__nday:])
        ll = min(self.__low[-self.__nday:])
        lc = min(self.__close[-self.__nday:])

        buyrange = max((hh - lc), (hc - ll))

        selltrig = self.__k2 * sellrange
        buytrig = self.__k1 * buyrange

        sellposition = selltrig
        buyposition = buytrig

        self.__sellposition.append(sellposition)
        self.__buyposition.append(buyposition)

        if len(self.__buyposition) < 2:
            return

        # 当价格向上突破上轨时，如果当时持有空仓，则先平仓，再开多仓；如果没有仓位，则直接开多仓；
        # 当价格向下突破下轨时，如果当时持有多仓，则先平仓，再开空仓；如果没有仓位，则直接开空仓；
        shares = self.getBroker().getShares(self.__instrument)
        if shares == 0 and bar.getHigh() >= self.__buyposition[-2] + bar.getOpen():
            self.marketOrder(self.__instrument, 10)
        elif shares == 0 and bar.getLow() <= bar.getOpen() - self.__sellposition[-2]:
            self.marketOrder(self.__instrument, -10)
        elif shares > 0 and bar.getLow() <= bar.getOpen() - self.__sellposition[-2]:
            self.marketOrder(self.__instrument, -20)
        elif shares < 0 and bar.getHigh() >= self.__buyposition[-2] + bar.getOpen():
            self.marketOrder(self.__instrument, 20)
        shares = self.getBroker().getShares(self.__instrument)
        print(bar.getDateTime(), self.__instrument, shares)


def main(plot):
    """
    """
    # 初始化常量
    instrument = 'BINA--BTC--USDT'
    # 数据
    # 1、从mysql导出csv数据
    # 2、指定数据频率
    # 3、读入csv给feed
    sql_to_csv(False)
    feed = GenericBarFeed(Frequency.MINUTE * 5, None, None)
    feed.addBarsFromCSV(instrument, instrument + '.csv')

    # 评价器
    # 1、初始化一个sharpratio评价器
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    # 注入
    # 1、实例化一个策略
    # 2、注入评价器
    strat = DualThrust(feed, instrument)
    strat.attachAnalyzer(sharpeRatioAnalyzer)
    if plot:
        plt = plotter.StrategyPlotter(strat, True, True, True)
#         plt.getInstrumentSubplot(instrument).addDataSeries(
#             "High", strat.get_high())
#         plt.getInstrumentSubplot(instrument).addDataSeries(
#             "Low", strat.get_low())
#         plt.getInstrumentSubplot(instrument).addDataSeries(
#             "BuyPosition", strat.get_buy_position())
#         plt.getInstrumentSubplot(instrument).addDataSeries(
#             "SellPosition", strat.get_sell_position())
    strat.run()
    plt.plot()
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))


if __name__ == "__main__":
    main(True)
