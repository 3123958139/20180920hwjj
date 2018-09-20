# -*- coding: utf-8 -*-

import logging, sys, json,os
import signal
import threading
import Queue
import time

from vic.core.struct import DateType
from okex_ws import OkexWs


#统一trade
class Ticker:
    """A trade event."""

    def __init__(self, dateTime, _dict):
        self.__dict = _dict
        self.__dateTime = dateTime

    def get(self):
        return self.__dict

    def timestamp(self):
        """Returns the :class:`datetime.datetime` when this event was received."""
        return self.__dateTime

    def symbol(self):
        return self.get()[5]

    def id(self):
        """Returns the trade id."""
        return self.get()[0]

    def price(self):
        """Returns the trade price."""
        return float(self.get()[1])

    def volume(self):
        """Returns the trade amount."""
        return float(self.get()[2])

    def amount(self):
        """Returns the trade amount."""
        return self.price() * self.volume()

    def isbuy(self):
        """Returns True if the trade was a buy."""
        return self.get()[4] == 'bid'

    def issell(self):
        """Returns True if the trade was a sell."""
        return self.get()[4] == 'ask'
 
    def side(self):
        return 1 if self.isbuy() else 2
    
    def openinterest(self):
        return 0


#统一broker ask1=bid1
class OrderBookUpdate:
    """An order book update event."""
    def __init__(self, instrument, _dict):
        self.__dateTime = _dict['timestamp'] 
        self.__instrument = instrument
        self.__ask = _dict['asks']
        self.__bid = _dict['bids'] 
        self.__ask.reverse();

    def symbol(self):
        return self.__instrument

    def timestamp(self):
        """Returns the :class:`datetime.datetime` when this event was received."""
        return self.__dateTime

    def bid_prices(self):
        """Returns a list with the top 20 bid prices."""
        return [float(bid[0]) for bid in self.__bid]

    def bid_volumes(self):
        """Returns a list with the top 20 bid volumes."""
        return [float(bid[1]) for bid in self.__bid]

    def ask_prices(self):
        """Returns a list with the top 20 ask prices."""
        return [float(ask[0]) for ask in self.__ask]

    def ask_volumes(self):
        """Returns a list with the top 20 ask volumes."""
        return [float(ask[1]) for ask in self.__ask]

class OkexzsWsThread(threading.Thread):
    ''''okex 期货端'''
    def __init__(self, wss, channels, apiKey=None, apiSecret=None, queue=None, exchangekey='OKEXZS'):
        super(OkexzsWsThread, self).__init__()
        self.__wss = wss
        self.__apikey = apiKey
        self.__apisecret = apiSecret
        self.socket = None
        self.__tradingday = None
        self.__queue = queue
        if queue is None: self.__queue = Queue.deque()
        self.__echname =  exchangekey
        self.__channels = []
        self.__channels_old = channels
        for channel in channels:
            self.__channels.append(self.ft2ok(channel))
        self.daemon  = True
        self.__now_time = 0

    def getsymbols(self):          
        return self.__channels_old 

    def getchannels(self):
        return self.__channels

    def getQueue(self):
        return self.__queue

    def ok2ft(self, c):
        try:
            symbol = c.replace('_index', '')
            return (self.__echname + '--' + symbol.upper())
        except Exception, e:
            logging.exception(e)
    
    def ft2ok(self, c):
        '''转换为小写 --变为_  去除交易所前缀'''
        k = c.replace(self.__echname+'--', '')
        return k.lower() + '_index'
    
    def __start(self):
        self.socket = OkexWs(self.__wss, self.__apikey, self.__apisecret)
        self.socket.subcribeall = self.subcribe 
        self.socket.connect()

    def onindex(self, key, data):
        #ok_sub_futureusd_btc_index {u'usdCnyRate': u'6.289', u'timestamp': u'1524119366651', u'futureIndex': u'8195.84'}
        #logging.info('%r %r', key, data)
        instrument = self.ok2ft(key.replace('ok_sub_futureusd_', ''))
        index = []
        index.append(data['timestamp'])
        index.append(data['futureIndex'])
        index.append('0')
        index.append('')
        index.append('')
        index.append(instrument)
        __datetime = int(data['timestamp']) / 1000

        if __datetime < self.__now_time:
            __datetime = self.__now_time
        else:
            self.__now_time = __datetime
        #logging.info(index)
        self.__queue.append((DateType.ON_MKT_TRADE, self.__echname, Ticker(__datetime*1000, index)))

    def subcribe(self, socket):
        try:
            for channel in self.__channels:
                channel = 'ok_sub_futureusd_' + channel
                socket.subcribe(channel+'_index')     
                socket.onchannel(channel+'_index', self.onindex)
        except Exception, e:
            logging.exception(e)
    

    def onLogin(self, ws, data):
        if not data['result']:
            logging.exception("auth error : %r ",  data)
            time.sleep(3)
            self.login()
        else:
            logging.info("auth ok : %r", data)
            self.subcribeall(ws);
         
    def start(self):
        super(OkexzsWsThread, self).start()
   
    def stop(self):
        self.socket.stop()

    def run(self):
        #线程循环
        self.__start()


if __name__ == "__main__":
    wss      = 'wss://real.okex.com:10440/websocket/okexapi'
    #apikey    = 'db98cb7e-71c4-442d-bf45-8c6ab05a4c1c'
    #apisecret = '4A5F6437B9DE1A2B16E80FC0018C8515'

    channels = ['OKEXZS--BTC']
    #channels = ['OKEXZS--BTC--TW']
    #ws = OkexzsWsThread(wss, channels, apiKey, apiSecret);
    ws = OkexzsWsThread(wss, channels);
    ws.start()

    while True:
        logging.info('main thread')
        time.sleep(3)


    
