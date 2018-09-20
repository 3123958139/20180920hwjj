# coding:utf-8

# anaconda包
import logging
from queue import Queue
import sys
import time

# vic.core包
from vic.core.livebroker import Broker
from vic.core.livefeed import Feed
from vic.core.strategy import StrategyBase
from vic.core.struct import Bar, DateType

# vic.exchenge包
from vic.exchange.vic_binance.binance_http_thread import BinaHttpThread
from vic.exchange.vic_binance.binance_ws_thread import BinaWsThread
from vic.exchange.vic_bitmex.bitmex_http_thread import BitmexHttpThread
from vic.exchange.vic_bitmex.bitmex_ws_thread import BitmexWsThread
from vic.exchange.vic_huobi.huobi_http_thread import HuobiHttpThread
from vic.exchange.vic_huobi.huobi_ws_thread import HuobiWsThread
from vic.exchange.vic_okex.okex_http_thread import OkexHttpThread
from vic.exchange.vic_okex.okex_ws_thread import OkexWsThread
from vic.exchange.vic_okex.okexft_http_thread import OkexftHttpThread
from vic.exchange.vic_okex.okexft_ws_thread import OkexftWsThread

# vics.lib包
from vics.lib.conf import VConf
from vics.lib.mysql_pool import MysqlPool


class Strategy(StrategyBase):
    """
    Strategy继承基类StrategyBase，重写方法。
    """

    def __init__(self, queue):
        """
        super()函数是用于调用父类的一个方法。
        """
        super(Strategy, self).__init__(queue)

    def init(self):
        """
        """
        super(Strategy, self).init()
        self.resample(1 * 60,  self.onbar)
        self.resample(5 * 60, self.onbar)
        self.resample(60 * 60, self.onbar)
        self.resample(24 * 60 * 60, self.onbar)

    def onorder(self, handle, group, data):
        """
        %s的意义是字符串，%r的意义是使用repr，而不是str，
        %r用来做 debug比较好，因为它会显示变量的原始数据raw data，而其它的符号则是用来向用户显示输出的。
        >>> print '%s, %s'%('one', 'two')
        one, two
        >>> print '%r, %r'%('one', 'two')
        'one', 'two'
        """
        logging.info('%r %r %r', group, data.symbol(), data)

    def ontrade(self, handle, group, data):
        pass

    def onposition(self, handle, group, data):
        pass

    def onbalance(self, handle, group, data):
        pass

    def onsnap(self, handle, group, data):
        pass

    def onticker(self, handle, group, data):
        pass

    def onorderbook(self, handle, group, data):
        pass

    def onbar(self, handle, group, period, data):
        pass

    def onend(self):
        pass

    def onstart(self):
        pass


if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(asctime)s[%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s'
    )
    conf = VConf()
    queue = Queue.deque()
    strategy = Strategy(queue)
    exchanges = [
        #('okex', 'OKEX', OkexWsThread, OkexHttpThread, '13651401725'),
        #('okexft', 'OKEXFT', OkexftWsThread,OkexftHttpThread, '13651401725'),
        #('huobi', 'HUOBI', HuobiWsThread, HuobiHttpThread, '13692179756'),
        #('binance', 'BINA', BinaWsThread, BinaHttpThread, '741822598@qq.com'),
        #('bitmex', 'BITM', BitmexWsThread, BitmexHttpThread, '741822598@qq.com'),
    ]
    for exch in exchanges:
        http = conf.get_http(exch[0])
        wss = conf.get_wss(exch[0])
        apikey = conf.get_apikey(exch[0], exch[4])
        secret = conf.get_secret(exch[0], exch[4])

        channels = conf.get_channels(exch[1])
        logging.info(channels)
        wsthread = exch[2](wss, channels, None, None, queue, exch[1])
        httpthread = exch[3](http, wss, channels, apikey,
                             secret, queue, exch[1])
        strategy.set_handle_thread(
            type=Strategy.MARKET, group=exch[1], plugin=wsthread, maxlen=100)
        strategy.set_handle_thread(
            type=Strategy.TRADE, group=exch[1], plugin=httpthread)
    strategy.run()
