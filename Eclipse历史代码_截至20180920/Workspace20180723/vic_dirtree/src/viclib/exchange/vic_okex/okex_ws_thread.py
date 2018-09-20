# -*- coding: utf-8 -*-

import logging, sys, json,os
import signal
import threading
import Queue
import time

from vic.core.struct import DateType
from okex_ws import OkexWs


#断线 重启去数据库获取最大tradeid 最大tradeid针对到合约上


#统一trade
class Ticker(object):
    """A trade event."""

    def __init__(self, dateTime, _dict):
        self.__dict = _dict
        self.__dateTime = dateTime

    def get(self):
        return self.__dict

    def timestamp(self):
        """Returns the :class:`int(time.time()*1000)` when this event was received."""
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
        """amount is default 0"""
        return float(self.get()[2]) 

    def amount(self):
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
        """Returns the :class:`int(time.time() * 1000)` when this event was received."""
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

class OkexWsThread(threading.Thread):
    def __init__(self, wss, channels, apiKey=None, apiSecret=None, queue=None, exchangekey='OKEX'):
        super(OkexWsThread, self).__init__()
        self.__wss = wss
        self.__apikey = apiKey
        self.__apisecret = apiSecret
        self.socket = None
        self.__queue = queue
        # 极少情况出现一个乱序ticker  这里保证时序
        self.__now_time = 0
        if queue is None : 
            self.__queue = Queue.deque()
        self.__echname =  exchangekey
        self.__channels_old = channels
        self.__channels = []
        self.__last_tradeid = {}
        for channel in channels:
            self.__channels.append(self.bb2ok(channel))
            self.__last_tradeid[channel] = 0
        self.daemon  = True
        logging.info(exchangekey + ' init ok')
        #启动程序前面len(self.__channels)跳过 因为他的时间不对
        self.__trade_count = 0
        self.__start_skip = len(self.__channels)+10


    def getsymbols(self):
        return self.__channels_old

    def getchannels(self):
        return self.__channels

    def getQueue(self):
        return self.__queue

    def ok2bb(self, c):
        '''转换大写  _变换为-- 增加交易所前缀'''
        return (self.__echname +'--' +  c.replace('_', '--').upper())
    
    def bb2ok(self, c):
        '''转换为小写 --变为_  去除交易所前缀'''
        return c.replace(self.__echname+'--', '').replace('--','_').lower()
    
    def __start(self):
        self.socket = OkexWs(self.__wss, self.__apikey, self.__apisecret)
        self.socket.subcribeall = self.subcribe 
        self.socket.connect()
 
    def tradedatetime(self, t):
        '''
            可以纠正误差23小时的时间戳 如果收到跨天左右的时间不能正确处理
        '''
        second = int(t[0:2])*3600 + int(t[3:5])*60 + int(t[6:])
        now = int(time.time())
        day = now - (now + 3600*8) % 86400
        tradetime =  day + second
        
        #2018-03-29 00:00:00 now ----> 2018-03-29 23:59:59 tradetime 
        if(tradetime-now > 3600*23):
            tradetime = tradetime - 86400
        #2018-03-28 23:59:59   now --> 2018-03-28 00:00:00 tradetime
        elif(now-tradetime > 3600*23):
            tradetime = tradetime + 86400
        
        #logging.info('%r %r %r', tradetime, self.__now_time, t)
        if(tradetime < self.__now_time):
            tradetime = self.__now_time
        else:
            self.__now_time = tradetime
       
        return tradetime*1000
    
    def ontrade(self, key, data):
        self.__trade_count += 1
        if self.__trade_count < self.__start_skip:
            return
        #[[u'194932676', u'0.00202124', u'38.75135', u'22:04:59', u'ask']]
        #logging.info("key : %r, data: %r",  key, data)
        instrument  = self.ok2bb(key.replace('_deals', '').replace('ok_sub_spot_', ''))
        for item in data:
            if(self.__last_tradeid.get(instrument) > int(item[0])): continue
            #多交易所区分tradeid 框架用到
            #item[0]     = self.__echname + item[0]
            item.append(instrument)
            __datetime = self.tradedatetime(item[3]) 
            #logging.info('__datetime: %r %r %r %r', __datetime, self.__now_time, item[3], item[5])
            self.__queue.append((DateType.ON_MKT_TRADE, self.__echname, Ticker(__datetime, item)))
            #logging.info('%r', len(self.__queue))
            self.__last_tradeid[instrument] = int(item[0])
    
    def onorder(self, key, data):
        #{u'timestamp': 1522246671491, u'bids': [[u'0.0567', u'0.01']], u'asks': [[u'0.05712111', u'1.218962']}
        #logging.info("key : %r, data: %r",  key, data)
        instrument = self.ok2bb(key.replace('_depth_20', '').replace('ok_sub_spot_', ''))
        #logging.info("key : " + instrument)
        if('asks' not in data.keys()): 
            logging.info(data)
            return
        self.__queue.append((DateType.ON_MKT_ORDER_BOOK, self.__echname, OrderBookUpdate(instrument, data)))
   
    def on_account_order(self, key, data):
        logging.info('key: %r,  order: %r', key, data)

    def on_account_balance(self, key, data):
        logging.info('key: %r,  order: %r', key, data)

    #ok_sub_spot_
    def subcribe(self, socket):
        for channel in self.__channels:
            channel = 'ok_sub_spot_' + channel
            #订阅成交
            socket.subcribe(channel+'_deals')     
            socket.onchannel(channel+'_deals', self.ontrade) 
            #订阅order _depth_1 ----> _depth_200
            socket.subcribe(channel+'_depth_20')     
            socket.onchannel(channel+'_depth_20', self.onorder)
            ##订阅账户order
            #socket.subcribe(channel+'_order')     
            #socket.onchannel(channel+'_order', self.on_account_order) 
            ##订阅账户权益变动
            #socket.subcribe(channel+'_balance')     
            #socket.onchannel(channel+'_balance', self.on_account_balance) 
    
    def onLogin(self, ws, data):
        if not data['result']:
            logging.error("auth error : %r ",  data)
            time.sleep(3)
            self.login()
        else:
            logging.info("auth ok : %r", data)
            self.subcribeall(ws);
         
    def start(self):
        super(OkexWsThread, self).start()
   
    def stop(self):
        self.socket.stop()

    def run(self):
        #线程循环
        self.__start()


if __name__ == "__main__":
    wss = "wss://real.okex.com:10441/websocket"
    apikey    = 'db98cb7e-71c4-442d-bf45-8c6ab05a4c1c'
    apisecret = '4A5F6437B9DE1A2B16E80FC0018C8515'

    channels = ['OKEX--ETH--BTC', 'OKEX--ETC--BTC', 'OKEX--LTC--BTC']
    channels = ['OKEX--BTC--USDT', 'OKEX--ETH--USDT', 'OKEX--ETC--USDT', 'OKEX--BCH--USDT', 'OKEX--LTC--USDT', 'OKEX--NEO--USDT', 'OKEX--XUC--USDT', 'OKEX--EOS--USDT', 'OKEX--XRP--USDT', 'OKEX--BTG--USDT', 'OKEX--OMG--USDT', 'OKEX--ZEC--USDT', 'OKEX--BTM--USDT', 'OKEX--TRX--USDT', 'OKEX--DASH--USDT', 'OKEX--QTUM--USDT']
    #ws = OkexWsThread(wss, channels, apiKey, apiSecret);
    ws = OkexWsThread(wss, channels);
    ws.start()

    while True:
        logging.info('main thread')
        time.sleep(3)


    
