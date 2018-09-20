# -*- coding: utf-8 -*-

import Queue

#must at top
from  pyalgotrade import logger
logger.log_format  = '%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s'
logging = logger.getLogger()

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade import bar 


import vic.exchange.vic_coinigy.wsclient 
import vic.exchange.vic_coinigy.httpclient 

import vic.exchange.livepyalgo.broker as broker
import vic.exchange.livepyalgo.livebroker as livebroker
import vic.exchange.livepyalgo.livefeed as livefeed

from lib.mysql_pool import MysqlPool


import pdb

channels_conf = "../conf/market-channels.txt"
mysql = MysqlPool('127.0.0.1', 3308, 'ops', 'ops!@#9988', 'vic_ticker', 'utf8')

def readChannels(path):
    channels = []
    file = open(path) 
    while True:
        lines = file.readlines(10000)
        if not lines : break
        for line in lines:
            channels.append(line.strip())
    file.close()
    logging.debug(channels)
    return channels


class Strategy(strategy.BaseStrategy):
    def __init__(self, feed, brk):
        super(Strategy, self).__init__(feed, brk)
        self.__OrderBook = {}
        
        # Subscribe to order book update events to get bid/ask prices to trade.
        # feed.getOrderBookUpdateEvent().subscribe(self.__onOrderBookUpdate)

        # 1 minute 
        self.resampleBarFeed(1*60,     self.onBarsFrequency)
        # 5 minute
        self.resampleBarFeed(5*60,     self.onBarsFrequency)
        # 1 hours
        self.resampleBarFeed(1*60*60,  self.onBarsFrequency)
        #1 days
        self.resampleBarFeed(24*60*60, self.onBarsFrequency)
        
        self.__kline = {}

        #数据库加载对应周期的kline到self.__kline
    
    def __onOrderBookUpdate(self, orderBookUpdate):
        self.__OrderBook[orderBookUpdate.getInstrument()] = orderBookUpdate 
        logging.info("Order book updated. instrument:%s, Best bid: %s. Best ask: %s" % (orderBookUpdate.getInstrument(), len(orderBookUpdate.getBidPrices()), len(orderBookUpdate.getAskPrices())))

    def onEnterOk(self, position):
        pass

    def onEnterCanceled(self, position):
        pass

    def onExitOk(self, position):
        pass

    def onExitCanceled(self, position):
        pass

    def onBars(self, bars):
        try:
            symbol = bars.getInstruments()[0]
            bar = bars[symbol]
               
            self.__ticker.append((bar.getDateTime().strftime('%Y-%m-%d %H:%M:%S.%f'), symbol.split('coinigy-')[1], bar.getPrice(), bar.getVolume(), 1 if bar.isBuy() else 2))

            #logging.info('symbol: %r,  frequency: %r, volume: %r' %(symbol, bar.getFrequency(), bar.getVolume())) 

        except Exception as e:
            logging.error('%r', e)
        except:
            logging.error('Exception caught!')


    def onBarsFrequency(self, dt, bars):
        #这里需要划分交易所
        try:
            k = []
            Frequency = None
            for key in bars.keys():
                bar = bars[key]
                Frequency = bar.getFrequency()
                
                #更新self.__kline
                k = self._kline[Frequency].get(key)
                
            
        except Exception as e: 
            logging.error('%r', e)


#市场品种有持仓才能交易
def main():
    feedqueue = Queue.Queue()
    feed    = livefeed.LiveTradeFeed(feedqueue)
    brk = broker.PaperTradingBroker(1000, feed)
    
    wss      = "wss://sc-02.coinigy.com/socketcluster/"
    apiKey   = "d0bcf5456624692ffb43f5c2de1f5706"
    apiSecret= "386a90a299e974326933f03e2bf3e0c1"
    #channels = ['KRKN--ETH--USD', 'BITF--ETH--USD', 'BITF--BTC--USD', 'BMEX--XBT--USD','BITF--ETH--USD', 'BITF--LTC--USD', 'BITF--BTC--USD', 'BITS--USD--BTC']
    channels = readChannels(channels_conf)
    coinigyws = vic.exchange.vic_coinigy.wsclient.WebSocketClient(wss, apiKey, apiSecret, channels, feedqueue, 'coinigy')
    feed.setExchange('coinigy', coinigyws, channels)
   
    strat   = Strategy(feed, brk)
    strat.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error('main exit %r', e)
    mysql.dispose()

