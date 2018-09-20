# coding=utf-8
from pyalgotrade import strategy
from pyalgotrade.bar import Frequency
from pyalgotrade.barfeed.csvfeed import GenericBarFeed

# 构建一个策略


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument):
        super(MyStrategy, self).__init__(feed)
        self.__instrument = instrument

    def onBars(self, bars):
        bar = bars[self.__instrument]
        self.info(bar.getClose())


# 获得回测数据，我们用本地数据
feed = GenericBarFeed(Frequency.DAY, None, None)
feed.addBarsFromCSV("fd", "fd.csv")

# 把策略跑起来
myStrategy = MyStrategy(feed, "fd")
myStrategy.run()
