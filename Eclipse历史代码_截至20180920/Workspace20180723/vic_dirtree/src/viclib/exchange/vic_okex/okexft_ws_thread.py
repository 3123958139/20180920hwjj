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

class OkexftWsThread(threading.Thread):
    ''''okex 期货端'''
    def __init__(self, wss, channels, apiKey=None, apiSecret=None, queue=None, exchangekey='OKEXFT'):
        super(OkexftWsThread, self).__init__()
        self.__wss = wss
        self.__apikey = apiKey
        self.__apisecret = apiSecret
        self.socket = None
        self.__queue = queue
        if queue is None: self.__queue = Queue.deque()
        self.__echname =  exchangekey
        self.__contract_type = {'TW': 'this_week', 'NW': 'next_week', 'TQ':'quarter'}
        self.__contract_type.update({'this_week': 'TW', 'next_week': 'NW', 'quarter':'TQ'})
        self.__last_tradeid = {}
        self.__channels = []
        self.__channels_old = channels
        for channel in channels:
            self.__channels.append(self.ft2ok(channel))
            #logging.info(self.__channels)
            self.__last_tradeid[channel] = 0
        self.daemon  = True
        self.__now_time = 0
        #启动程序前面len(self.__channels)跳过
        self.__trade_count = 0
        self.__start_skip = len(self.__channels)+10

    def getsymbols(self):          
        return self.__channels_old 

    def get_ontract_type(self):
        return self.__contract_type

    def getchannels(self):
        return self.__channels

    def getQueue(self):
        return self.__queue

    def ok2ft(self, c):
        try:
            symbol = c.split('_')[0]
            contract_type = c[len(symbol)+1:].replace('depth_', '').replace('_20', '').replace('trade_', '')
            key = (self.__echname + '--' + symbol.upper() + '--' + self.__contract_type[contract_type])
            return key
        except Exception, e:
            logging.exception(e)
    
    def ft2ok(self, c):
        '''转换为小写 --变为_  去除交易所前缀'''
        k = c.replace(self.__echname+'--', '').split('--')
        contract_type = self.__contract_type[k[1]] if len(k)>1 else ''
        return (k[0].lower(), contract_type) 
    
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
        
        #logging.info('%r %r', t, tradetime)
        #logging.info('%r %r %r', tradetime, self.__now_time, t)
        if(tradetime < self.__now_time):
            tradetime = self.__now_time
        else:
            self.__now_time = tradetime
        
        #logging.info('%r %r', t, tradetime)
        return tradetime*1000
    
    def ontrade(self, key, data):
        self.__trade_count += 1
        if self.__trade_count < self.__start_skip:
            return
        #ok_sub_futureusd_btc_trade_quarter [u'598538291544087', u'8127.99', u'58.0', u'16:56:09', u'ask']
        instrument  = self.ok2ft(key.replace('ok_sub_futureusd_', ''))
        for item in data:
            if(self.__last_tradeid.get(instrument) > int(item[0])): continue
            item.append(instrument)
            __datetime = self.tradedatetime(item[3]) 
            if len(item)>6: #兼容安张 和 和币种记价
                item[5] = instrument
            #logging.info('__datetime: %r %r', __datetime, item)
            self.__queue.append((DateType.ON_MKT_TRADE, self.__echname, Ticker(__datetime, item)))
            self.__last_tradeid[instrument] = int(item[0])
    
    def onorder(self, key, data):
        #ok_sub_futureusd_btc_depth_this_week_20
        instrument = self.ok2ft(key.replace('ok_sub_futureusd_', ''))
        #logging.info(" %r", instrument)
        if('asks' not in data.keys()): 
            logging.info(data)
            return
        self.__queue.append((DateType.ON_MKT_ORDER_BOOK, self.__echname, OrderBookUpdate(instrument, data)))
     
    def on_account_trade(self, key, data):
        logging.info('key: %r,  order: %r', key, data)

    def on_account_userinfo(self, key, data):
        logging.info('key: %r,  order: %r', key, data)

    def on_account_position(self, key, data):
        logging.info('key: %r,  order: %r', key, data)
        
    def subcribe(self, socket):
        try:
            for channel in self.__channels:
                channel, contract_type = channel
                channel = 'ok_sub_futureusd_' + channel
                #订阅成交
                socket.subcribe(channel+'_trade_'+contract_type)     
                socket.onchannel(channel+'_trade_'+contract_type, self.ontrade)     

                #订阅order _depth_1 ----> _depth_200
                socket.subcribe(channel+'_depth_'+contract_type+'_20')     
                socket.onchannel(channel+'_depth_'+contract_type+'_20', self.onorder)     
        except Exception, e:
            logging.exception(e)
        ##订阅账户order
        #socket.subcribe('ok_sub_futureusd_trades') 
        #socket.onchannel('ok_sub_futureusd_trades', self.on_account_trade) 
        #
        ##订阅账户权益变动
        #socket.subcribe('ok_sub_futureusd_userinfo')     
        #socket.onchannel('ok_sub_futureusd_userinfo', self.on_account_userinfo) 
    
        ##订阅账户权益变动
        #socket.subcribe('ok_sub_futureusd_positions')     
        #socket.onchannel('ok_sub_futureusd_positions', self.on_account_positions) 
    

    def onLogin(self, ws, data):
        if not data['result']:
            logging.exception("auth error : %r ",  data)
            time.sleep(3)
            self.login()
        else:
            logging.info("auth ok : %r", data)
            self.subcribeall(ws);
         
    def start(self):
        super(OkexftWsThread, self).start()
   
    def stop(self):
        self.socket.stop()

    def run(self):
        #线程循环
        self.__start()


if __name__ == "__main__":
    wss      = 'wss://real.okex.com:10440/websocket/okexapi'
    #apikey    = 'db98cb7e-71c4-442d-bf45-8c6ab05a4c1c'
    #apisecret = '4A5F6437B9DE1A2B16E80FC0018C8515'

    channels = ['OKEXFT--ETC--TQ']
    #channels = ['OKEXFT--BTC--TW']
    #ws = OkexftWsThread(wss, channels, apiKey, apiSecret);
    ws = OkexftWsThread(wss, channels);
    ws.start()

    while True:
        logging.info('main thread')
        time.sleep(3)


    
