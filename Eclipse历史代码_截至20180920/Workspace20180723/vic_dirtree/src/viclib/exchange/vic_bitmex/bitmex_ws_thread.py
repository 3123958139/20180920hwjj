# -*- coding: utf-8 -*-

import logging, sys, json,os
import signal
import threading
import Queue
import time

from vic.core.struct import DateType 
from vic.core.struct import OrderBook 

from bitmex_ws import BitmexWs



class Ticker:
    """A trade event."""

    def __init__(self, dateTime, _dict):
        self.__dict = _dict
        self.__dateTime = dateTime

    def get(self):
        return self.__dict

    def timestamp(self):
        return self.__dateTime

    def symbol(self):
        return self.get()[5]

    def id(self):
        return self.get()[0]

    def price(self):
        return float(self.get()[1])

    def volume(self):
        return float(self.get()[2])

    def amount(self):
        return self.price() * self.volume()

    def isbuy(self):
        return self.get()[4] == 'Buy'

    def issell(self):
        return self.get()[4] == 'Sell'

    def side(self):
        return 1 if self.isbuy() else 2
    
    def openinterest(self):
        return 0

class BitmexWsThread(threading.Thread):
    def __init__(self, wss, channels, apiKey=None, apiSecret=None, queue=None, exchangekey='BITM'):
        super(BitmexWsThread, self).__init__()
        self.__wss = wss
        self.__apikey = apiKey
        self.__apisecret = apiSecret
        self.socket = None
        self.__tradingday = None
        self.__queue = queue
        if queue is None : 
            self.__queue = Queue.deque()
        self.__echname =  exchangekey
        self.__channels = channels
        self.daemon  = True
        self.__map_symbol = {}
        self.__symbol_infos = {}

    def getsymbols(self):          
        return self.__channels 

    def getQueue(self):
        return self.__queue

    def bm2ft(self, c):
        '''交易所转换本地'''
        return self.__map_symbol.get(c) 
    
    def ft2bm(self, c):
        '''本地转换交易所'''
        return self.__map_symbol.get(c)
    
    def __start(self):
        self.socket = BitmexWs(self.__wss, self.__apikey, self.__apisecret)
        self.socket.subcribeall = self.subcribe 
        self.socket.connect()
 
    def tradedatetime(self, t):
        tm = time.strptime(t, '%Y-%m-%dT%H:%M:%S.%fZ')
        return (int(time.mktime(tm)) + 3600*8) * 1000
    
    def ontrade(self, key, data):
        #[[{u'homeNotional': 9, u'trdMatchID': u'36df660a-25ab-f1e9-ded6-b68961089d5f', u'timestamp': u'2018-04-19T02:21:42.498Z', u'price': 0.1126, u'foreignNotional': 1.0134, u'grossValue': 101340000, u'side': u'Buy', u'tickDirection': u'ZeroPlusTick', u'symbol': u'BCHM18', u'size': 9}]]
        for item in data:
            #logging.info('%r %r', key, self.bm2ft(item['symbol']))
            #区分指数 和 正常的. 指数的id是timestamp    正常交易id是trdMatchID
            #多交易所区分tradeid 框架用到
            #item[0]     = self.__echname + item[0]
            instrument = self.bm2ft(item['symbol'])
            if(instrument is None):
                continue
            trade = []
            trade.append(item['trdMatchID']) #指数没有 这里需要全转化为时间戳
            trade.append(item['price'])
            trade.append(item['size'])     #指数没有
            trade.append(item['timestamp'])
            trade.append(item['side'])     #指数没有
            trade.append(instrument)
            __datetime = self.tradedatetime(item['timestamp']) 
            #logging.info('%r %r %r %r', key, instrument, item['symbol'], __datetime)
            self.__queue.append((DateType.ON_MKT_TRADE, self.__echname, Ticker(__datetime, trade)))
    
    def onorder(self, key, data):
        #{u'timestamp': u'2018-04-19T06:41:04.709Z', u'symbol': u'XBTUSD', u'bids': [[u'0.0567', u'0.01']], u'asks': [[u'0.05712111', u'1.218962']}
        for item in data:
            instrument = self.bm2ft(item['symbol'])
            if(instrument is None):
                continue
            item['timestamp'] = self.tradedatetime(item['timestamp'])
            #logging.info('%r %r %r %r', key, instrument, item['symbol'], item['timestamp'])
            self.__queue.append((DateType.ON_MKT_ORDER_BOOK, self.__echname, OrderBook(instrument, item)))
   
    def oninstrument(self, key, data):
        for item in data:
            if 'state' in item and item['state']=='Open':
                param = {}
                param['rootSymbol'] = item['rootSymbol']
                param['symbol']     = item['symbol']
                param['underlying'] = item['underlying']
                param['state']      = item['state']
                param['listing']    = item['listing']
                param['expiry']     = item['expiry']
                param['type']        = item['typ']
                self.__add_instrument(param['type'], param['symbol'], param['underlying'], param['expiry'])
                self.__symbol_infos[item['symbol']] = param 

    def __add_instrument(self, type, symbol, underlying, expiry):
        end = ''
        if type == 'FFCCSX':  #期货合约
            end = time.strftime('%b', time.strptime(expiry, '%Y-%m-%dT%H:%M:%S.%fZ'))
        elif type == 'FFWCSX': #永续合约
            end = 'USD'
        elif type == 'OCECCS': #BITM--XBT--7D_U110 期权
            logging.info('option instrument : %r %r %r %r', symbol, underlying, type, expiry)
            return
        else:
            logging.error('unknow instrument: %r %r %r %r', symbol, underlying, type, expiry)
            return
        key = '--'.join((self.__echname, underlying.upper(), end.upper()))
        logging.info('future instrument: %r %r %r %r', key, symbol, underlying, type)
        if end and key in self.__channels:
            self.__map_symbol[symbol] = key 
            self.__map_symbol[key] = symbol
            logging.info(self.__map_symbol)

    def subcribe(self, socket):
        socket.subcribe('instrument')
        socket.subcribe('trade')
        socket.subcribe('orderBook10')
        socket.onchannel('trade', self.ontrade)
        socket.onchannel('instrument', self.oninstrument)
        socket.onchannel('orderBook10', self.onorder)
    
    def start(self):
        super(BitmexWsThread, self).start()
   
    def stop(self):
        self.socket.stop()

    def run(self):
        #线程循环
        self.__start()


if __name__ == "__main__":
    wss = "wss://www.bitmex.com/realtime"
    apikey    = 'xShYIkq6c964NqKMH7cP1f3j'
    apisecret = 'ehWvEyF80IkmkwTJbB5-DiLSlJP8k6WWJiEXyhIdmYaskrBR'

    #订阅会返回所有行情
    channels = ['BITM--ETH--BTC', 'BITM--ETC--BTC', 'BITM--LTC--BTC']
    #ws = BitmexWsThread(wss, channels, apiKey, apiSecret);
    ws = BitmexWsThread(wss, channels);
    ws.start()

    while True:
        logging.info('main thread')
        time.sleep(3)


    
