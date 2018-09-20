# -*- coding: utf-8 -*-

import logging
import threading
import Queue
import time

from vic.core.struct import DateType
from huobi_ws import HuobiWs


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
        return self.get()['id']

    def price(self):
        """Returns the trade price."""
        return float(self.get()['price'])
    
    def volume(self):
        return float(self.get()['amount']) 

    def amount(self):
        """Returns the trade amount."""
        return self.price() * self.volume()

    def isbuy(self):
        """Returns True if the trade was a buy."""
        return self.get()['direction'] == 'buy'

    def issell(self):
        """Returns True if the trade was a sell."""
        return self.get()['direction'] == 'sell'

    def side(self):
        return 1 if self.isbuy() else 2
    
    def openinterest(self):
        return 0


#统一broker ask1=bid1
class OrderBookUpdate:
    """An order book update event."""
    def __init__(self, instrument, _dict):
        self.__dateTime = _dict['ts']
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

class HuobiWsThread(threading.Thread):
    def __init__(self, wss, channels, apiKey=None, apiSecret=None, queue=None, exchangekey='HUOBI'):
        super(HuobiWsThread, self).__init__()
        self.__wss = wss
        self.__apikey = apiKey
        self.__apisecret = apiSecret
        self.socket = None
        self.__tradingday = None
        self.__queue = queue
        if queue is None :  
            self.__queue = Queue.deque()
        self.__echname =  exchangekey
        self.__channels = []
        self.__last_tradeid = {}
        self.__channels_old = channels 
        for channel in channels:
            self.__channels.append(self.bb2hb(channel))
            self.__last_tradeid[channel] = 0
        self.daemon  = True
        self.__now_time = 0
        logging.info(exchangekey + ' init ok')
    
    def getsymbols(self):
        return self.__channels_old

    def getchannels(self):
        return self.__channels

    def getQueue(self):
        return self.__queue

    def hb2bb(self, c):
        ''' btcusdt----> HB--BTC--USDT'''
        #末尾是这三个 USDT BTC ETH  USDT必须在后面
        n = -3
        if(c.find('usdt') > 0) : n = -4
        return (self.__echname + '--' + c[:n].upper() + '--' +  c[n:].upper())
    
    def bb2hb(self, c):
        '''HUOBI--BTC--USDT ----> btcusdt'''
        return c.replace(self.__echname+'--', '').replace('--','').lower()
    
    def __start(self):
        self.socket = HuobiWs(self.__wss, self.__apikey, self.__apisecret)
        self.socket.subcribeall = self.subcribe 
        self.socket.connect()
 
    def ontrade(self, key, data):
        #logging.info("key : %r, data: %r",  key, data['tick']['id'])
        trades = data['tick']['data']
        instrument  = self.hb2bb(key.replace('.trade.detail', '').replace('market.', ''))
        #logging.info("%r %r", key, instrument)
        for item in trades:
            if(self.__last_tradeid.get(instrument) > item['id']): 
                continue
            item['symbol'] = instrument
            __datetime = item['ts']
            if(self.__now_time > __datetime):
                __datetime = self.__now_time
            else:
                self.__now_time = __datetime
            self.__queue.append((DateType.ON_MKT_TRADE, self.__echname, Ticker(__datetime, item)))
            self.__last_tradeid[instrument] = item['id']
            #logging.info('__datetime:%r %r', instrument,  __datetime)
    
    def onorder(self, key, data):
        #{u'timestamp': 1522246671491, u'bids': [[u'0.0567', u'0.01']], u'asks': [[u'0.05712111', u'1.218962']}
        #logging.info("key : %r, data: %r",  key, data)
        instrument = self.hb2bb(key.replace('.depth.step1', '').replace('market.', ''))
        self.__queue.append((DateType.ON_MKT_ORDER_BOOK, self.__echname, OrderBookUpdate(instrument,  data['tick'])))
   
    def onkline(self, key, data):
        instrument = self.hb2bb(key.replace('.kline.1day', '').replace('market.', ''))

    def subcribe(self, socket):
        '''
            market.$symbol.kline.$period
            market.$symbol.depth.$type
            market.$symbol.trade.detail
            这个是快照
            market.$symbol.detail
        '''
        for channel in self.__channels:
            channel = 'market.' + channel
            #订阅成交
            socket.subcribe(channel+'.trade.detail')     
            socket.onchannel(channel+'.trade.detail', self.ontrade) 
            #订阅order step0 ----> step5
            socket.subcribe(channel+'.depth.step1')     
            socket.onchannel(channel+'.depth.step1', self.onorder)
            #订阅1day 
            socket.subcribe(channel+'.kline.1day')     
            socket.onchannel(channel+'.kline.1day', self.onkline)

    def start(self):
        super(HuobiWsThread, self).start()
   
    def stop(self):
        self.socket.stop()

    def run(self):
        #线程循环
        self.__start()


if __name__ == "__main__":
    wss = "wss://api.huobipro.com/ws"
    apiKey   = "3af5ee91-4bc1407b-d68cd6a5-7291b"
    apiSecret= "319c3ea1-88eeb820-a80d5ae8-3f93b"

    channels = ['HUOBI--BTC--USDT', 'HUOBI--ETC--BTC', 'HUOBI--LTC--BTC']
    ws = HuobiWsThread(wss, channels);
    ws.start()

    while True:
        #logging.info('main thread')
        time.sleep(3)


    
