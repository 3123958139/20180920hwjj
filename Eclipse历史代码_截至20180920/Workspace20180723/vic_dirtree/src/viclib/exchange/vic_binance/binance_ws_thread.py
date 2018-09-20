# -*- coding: utf-8 -*-

import logging, sys, json,os
import signal
import threading
import Queue
import time
from websocket._ssl_compat import ssl


from vic.core.struct import DateType
from binance_ws import BinaWs


#断线 重启去数据库获取最大tradeid 最大tradeid针对到合约上


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
        return self.get()['symbol']

    def id(self):
        """Returns the trade id."""
        return self.get()['t']

    def price(self):
        """Returns the trade price."""
        return float(self.get()['p'])
    
    def volume(self):
        return float(self.get()['q']) 

    def amount(self):
        """Returns the trade amount."""
        return self.price() * self.volume()

    def isbuy(self):
        """Returns True if the trade was a buy."""
        return self.get()['m']

    def issell(self):
        """Returns True if the trade was a sell."""
        return not self.get()['m']
    
    def side(self):
        return 1 if self.isbuy() else 2
    
    def openinterest(self):
        return 0


#统一broker ask1=bid1
class OrderBookUpdate:
    """An order book update event."""
    def __init__(self, instrument, _dict):
        self.__dateTime = _dict['t']
        self.__instrument = instrument
        self.__ask = _dict['asks']
        self.__bid = _dict['bids'] 
        #self.__ask.reverse();

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

class BinaWsThread(threading.Thread):
    def __init__(self, wss, channels, apiKey=None, apiSecret=None, queue=None, exchangekey='BINA'):
        super(BinaWsThread, self).__init__()
        self.__apikey = apiKey
        self.__apisecret = apiSecret
        self.socket = None
        self.__queue = queue
        if queue is None : 
            self.__queue = Queue.deque()
        self.__echname =  exchangekey
        self.__channels = []
        self.__channels_old = channels
        self.__last_tradeid = {}
        for channel in channels:
            self.__channels.append(self.bb2hb(channel))
            self.__last_tradeid[channel] = 0
         
        self.daemon  = True
        self.__wss = wss
        logging.info(exchangekey + ' init ok.')
        self.__now_time = 0 #tick的时间

    def getsymbols(self):
        return self.__channels_old

    def getwss(self):
        return self.__wss

    def onwss(self):
        ''' override in the subclass'''
        channels = [s+'@trade' for s in self.__channels] + [s+'@depth5' for s in self.__channels]
        s = self.__wss + '/stream?streams=' + '/'.join(channels)
        #logging.info('wss : %r', s)
        return s

    def onchannels(self):
        ''' override in the subclass'''
        for channel in self.__channels:
            self.socket.onchannel(channel+'@trade', self.ontrade)
            self.socket.onchannel(channel+'@depth5', self.onorder)
       
    def getchannels(self):
        return self.__channels

    def getQueue(self):
        return self.__queue

    def hb2bb(self, c):
        ''' btcusdt----> BINA--BTC--USDT'''
        #末尾是这三个 USDT BTC ETH BNB  USDT必须在后面
        n = -3
        if(c.find('usdt') > 0) : n = -4
        return (self.__echname+'--' + c[:n].upper() + '--' +  c[n:].upper())
    
    def bb2hb(self, c):
        '''BINA--BTC--USDT ----> btcusdt'''
        return c.replace(self.__echname+'--', '').replace('--','').lower()
    
    def __start(self):
        self.socket = BinaWs(self.onwss(), self.__apikey, self.__apisecret)
        self.onchannels()
        self.socket.connect(sslopt={"cert_reqs": ssl.CERT_NONE})
 
    def ontrade(self, key, data):
        #logging.info("key : %r, data: %r",  key, data)
        instrument  = self.hb2bb(key.replace('@trade', ''))
        #logging.info("%r %r", key, instrument)
        
        if(self.__last_tradeid.get(instrument) > data['t']): return
        
        data['symbol'] = instrument
        __datetime = data['T']

        if(self.__now_time > __datetime):
            __datetime = self.__now_time
        else:
            self.__now_time = __datetime

        #logging.info('__datetime: %r %r', __datetime,  instrument)
        self.__queue.append((DateType.ON_MKT_TRADE, self.__echname, Ticker(__datetime, data)))
        self.__last_tradeid[instrument] = data['t']

    def onorder(self, key, data):
        #{u'timestamp': 1522246671491, u'bids': [[u'0.0567', u'0.01']], u'asks': [[u'0.05712111', u'1.218962']}
        #logging.info("key : %r, data: %r",  key, data)
        instrument  = self.hb2bb(key.replace('@depth5', ''))
        #logging.info("%r %r", key, instrument)
        data['t'] = self.__now_time
        self.__queue.append((DateType.ON_MKT_ORDER_BOOK, self.__echname, OrderBookUpdate(instrument,  data)))
   
    def onkline(self, key, data):
        instrument = self.hb2bb(key.replace('.kline.1day', '').replace('market.', ''))

    def start(self):
        super(BinaWsThread, self).start()
   
    def stop(self):
        self.socket.stop()

    def run(self):
        #线程循环
        self.__start()


if __name__ == "__main__":
    wss = "wss://stream.binance.com:9443"
    apiKey   = "CeVAxLBcH1TrxcZxRRD0k2G1llJVFNpfsmNl96cRQKjZ2b01LC85zewyRCJwkOQu"
    apiSecret= "5PF53iyHXFAvEBNs2zt0p5qbLkInkDCg83430b34kIFYv4O9HvFKbmEDc2q2vsxd"

    channels = ['BINA--BTC--USDT', 'BINA--ETC--BTC', 'BINA--LTC--BTC']
    #ws = BinaWsThread(wss, channels, apiKey, apiSecret);
    ws = BinaWsThread(wss, channels);
    ws.start()

    while True:
        #logging.info('main thread')
        time.sleep(3)


    
