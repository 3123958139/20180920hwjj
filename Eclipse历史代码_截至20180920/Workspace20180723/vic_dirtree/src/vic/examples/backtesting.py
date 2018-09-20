# -*- coding: utf-8 -*-

import sys
import logging
import Queue
import time

from vic.core.strategy import StrategyBase
from vic.exchange.vic_mysql.loaddata_from_mysql import MysqlDataThread

class Strategy(StrategyBase):
    def __init__(self, queue):
        super(Strategy, self).__init__(queue)
    
    def init(self):
        super(Strategy, self).init()
        self.resample(10,  self.onbar_10sec)
        self.resample(60, self.onbar_60sec)

    def onorder(self, handle, group, data):
        logging.info('%r %r', group, data)

    def ontrade(self, handle, group, data):
        logging.info('%r %r', group, data)

    def onposition(self, handle, group, data):
        pass

    def onbalance(self, handle, group, data):
        logging.info('%r %r', group, data)
    
    def onsnap(self, handle, group, data):
        logging.info('%r', data)

    def onticker(self, handle, group, data):
        #logging.info('%r %r %r %r %r %r', data['symbol'][-1], data['tradeid'][-1], data['price'][-1], data['volume'][-1], data['side'][-1], data['timestamp'][-1])
        pass

    def onorderbook(self, handle, group, data):
        pass
        #logging.info('%r %r', group, data)

    def onbar_10sec(self, handle, group, period, data):
        logging.info('%r %r %r %r %r %r %r %r %r', group, period, data['symbol'][-1], data['timestamp'][-1], data['high'][-1], data['open'][-1], data['low'][-1], data['close'][-1], data['volume'][-1])

    def onbar_60sec(self, handle, group, period, data):
        logging.info('%r %r %r %r %r %r %r %r %r', group, period, data['symbol'][-1], data['timestamp'][-1], data['high'][-1], data['open'][-1], data['low'][-1], data['close'][-1], data['volume'][-1])
    
    def onstart(self):
        pass

if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(asctime)s[%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s'
    )

    queue = Queue.deque()
    strategy = Strategy(queue)
    
    #数据库数据时序是安组的(交易所)
    channels = ['OKEXFT--ETH--TQ', 'OKEXFT--EOS--TQ']
    datathread = MysqlDataThread(channels, queue, '2018-05-08', '2018-05-11')
    strategy.set_handle_thread(type=Strategy.MARKET, group='OKEXFT', plugin=datathread, maxlen=100)

    strategy.run()









