# -*- coding: utf-8 -*-

import sys
import logging
import Queue
import datetime
import MySQLdb

from vic.core.strategy import StrategyBase
from vic.core.struct import  schedule
from vic.exchange.vic_okex.okex_ws_thread         import OkexWsThread
from vic.exchange.vic_huobi.huobi_ws_thread       import HuobiWsThread
from vic.exchange.vic_binance.binance_ws_thread   import BinaWsThread
from vic.exchange.vic_okex.okexft_ws_thread       import OkexftWsThread
from vic.exchange.vic_okex.okexzs_ws_thread       import OkexzsWsThread
from vic.exchange.vic_bitmex.bitmex_ws_thread     import BitmexWsThread

from vics.lib.conf import VConf
from vics.lib.mysql_pool  import MysqlPool

class Strategy(StrategyBase):
    def __init__(self, queue):
        self.__maptable = {60:'1mk', 300: '5mk', 3600:'1h', 86400:'1d'}
        self.__tickers = []
        self.__bars = {}
        self.__mysql = MysqlPool('47.74.249.179', 3308, 'ops', 'ops!@#9988', 'vic')
        #self.__mysql = MysqlPool('47.74.179.216', 3308, 'ops', 'ops!@#9988', 'vic')
        super(Strategy, self).__init__(queue)

    def init(self):
        for period in self.__maptable:
            self.resample(period,     self.onbar)
            self.__bars[period] = []
        super(Strategy, self).init()

    def __query(self, sql, data):
        try:
            self.__mysql.insertMany(sql, data)
            while data : 
                data.pop()
        except MySQLdb.IntegrityError:
            while data : 
                data.pop()
        except MySQLdb.OperationalError as e:
            logging.error('%r\n%r', sql, e)
        except AttributeError as e:
            logging.error('%r\n%r', sql, e)
        except Exception as e:
            logging.exception('%r\n%r', sql, e)

    def __insert_ticker(self, args):
        if len(self.__tickers) < 1 : return
        sql =  'insert into vic_ticker.ticker values(%s, %s, %s, %s, %s, %s)'
        self.__query(sql, self.__tickers)

    def __insert_bar(self, args):
        for p in self.__bars:
            if len(self.__bars[p]) < 1 : continue
            sql =  'insert into vic_' + self.__maptable[p] + '.' + self.__maptable[p] + ' values(%s, %s, %s, %s, %s, %s, %s, %s, %s)' 
            self.__query(sql, self.__bars[p])
    
    def strtime(self, t):
        return datetime.datetime.fromtimestamp(t)

    def onticker(self, handle, group, data):
        l = []
        l.append(self.strtime(data['timestamp'][-1]/1000))
        l.append(data['symbol'][-1])
        l.append(data['price'][-1])
        l.append(data['volume'][-1])
        l.append(data['side'][-1])
        l.append(data['tradeid'][-1])
        self.__tickers.append(tuple(l))
        #logging.info('%r %r %r', self.strtime(data['timestamp'][-1]/1000), data['timestamp'][-1], data['symbol'][-1])

    def onbar(self, handle, group, period, data):
        l = []
        l.append(self.strtime(data['timestamp'][-1]))
        l.append(data['symbol'][-1])
        l.append(data['high'][-1])
        l.append(data['open'][-1])
        l.append(data['low'][-1])
        l.append(data['close'][-1])
        l.append(data['volume'][-1])
        l.append(data['amount'][-1])
        l.append(data['openinterest'][-1])
        self.__bars[period].append(tuple(l))
        #logging.info('%r %r %r %r %r %r %r %r %r', group, period, data['symbol'][-1], data['timestamp'][-1], data['high'][-1], data['open'][-1], data['low'][-1], data['close'][-1], data['volume'][-1])
    
    def onstart(self):
        schedule(10, self.__insert_ticker, [])
        schedule(30, self.__insert_bar, [])
    
    def onend(self):
        for ticker in self.__tickers:
            logging.error('insert into vic_ticker.ticker values %r', str(ticker))
        for p in self.__bars:
            for bar in self.__bars[p]:
                logging.error('insert into vic_%r.%r values %r', self.__maptable[p], self.__maptable[p], str(bar))
        logging.info('stop ok.')

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
                    ('okex', 'OKEX', OkexWsThread), 
                    ('okexft', 'OKEXFT', OkexftWsThread),
                    ('okexft', 'OKEXZS', OkexzsWsThread),
                    ('huobi', 'HUOBI', HuobiWsThread), 
                    ('binance', 'BINA', BinaWsThread),
                    ('bitmex', 'BITM', BitmexWsThread),
                ]
    for exch in exchanges:
        http = conf.get_http(exch[0])
        wss = conf.get_wss(exch[0])
        channels = conf.get_channels(exch[1])
        logging.info(channels)
        wsthread    = exch[2](wss, channels, None, None, queue, exch[1])
        strategy.set_handle_thread(type=Strategy.MARKET, group=exch[1], plugin=wsthread, maxlen=100)
    strategy.run()











