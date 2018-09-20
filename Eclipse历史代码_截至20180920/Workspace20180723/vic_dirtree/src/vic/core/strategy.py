# -*- coding: utf-8 -*-
import os
import time
import logging
import signal
from datetime import datetime

from livefeed import Feed
from livebroker import Broker
from struct import *

class StrategyBase(object):
    MARKET = 1
    TRADE = 2
    def __init__(self, queue):
        # 所有可交易列表 同时经过底层验证
        self.__instruments =   []
        # 所有行情列表 同时经过底层验证
        self.__instruments =   []
        # 接收行情交易数据的队列
        self.__queue = queue
        # 插件句柄线程
        self.__market_handle_thread = {}
        # 插件句柄线程
        self.__trade_handle_thread = {}
        # 一组broker以交易所key + 账户
        self.__group_brk = {}
        # 一组feed
        self.__group_feed = {}
        # 数据回调  数据类型1-50
        self.__hash_callback = [i for i in range(0, 50)]
    
    def get_deque(self):
        return self.__queue
    
    def signal_handler(self, sign, frame):
        logging.exception('recv signal %r', sign)

    def signal_handler_exit(self, sign, frame):
        self.stop()

    def init(self):
        self.set_callback(DateType.ON_TIMESTAMP,       self.__ontimestamp)
        self.set_callback(DateType.ON_MKT_TRADE,       self.__onticker)
        self.set_callback(DateType.ON_MKT_SNAP,        self.__onsnap)
        self.set_callback(DateType.ON_MKT_KLINE,       self.__onkline)
        self.set_callback(DateType.ON_MKT_ORDER_BOOK,  self.__onorderbook)
        self.set_callback(DateType.ON_ACCOUNT_BALANCE, self.__onbalance)
        self.set_callback(DateType.ON_ACCOUNT_TRADE,   self.__ontrade)
        self.set_callback(DateType.ON_ACCOUNT_ORDER,   self.__onorder)
        self.set_callback(DateType.ON_ACCOUNT_POSITION,self.__onposition)
        
        signal.signal(signal.SIGHUP,    self.signal_handler) # 1
        signal.signal(signal.SIGQUIT,   self.signal_handler) # 3
        signal.signal(signal.SIGALRM,   self.signal_handler) # 14
        signal.signal(signal.SIGTERM,   self.signal_handler) # 15
        signal.signal(signal.SIGCONT,   self.signal_handler) # 18
        
        signal.signal(signal.SIGINT,    self.signal_handler_exit) # 2
        signal.signal(signal.SIGUSR1,   self.signal_handler_exit) # 10
        signal.signal(signal.SIGUSR2,   self.signal_handler_exit) # 12

    def check(self, group, symbol):
        plugin = self.get_market_handle(group)
        if not plugin: return False
        return (symbol in plugin.getsymbols())
    
    def symbols(self):
        s = []
        for k in self.__market_handle_thread:
            s.extend(self.__market_handle_thread[k].getsymbols())
        return s 

    def set_callback(self, type, callback):
        self.__hash_callback[type] = callback

    def get_trade_handle(self, group):
        return self.__trade_handle_thread.get(group)
    
    def get_trade_handles(self):
        return self.__trade_handle_thread
    
    def get_market_handle(self, group):
        return self.__market_handle_thread.get(group)

    def get_market_handles(self):
        return self.__market_handle_thread

    def get_brk(self, group):
        return self.__group_brk.get(group)
    
    def get_group_brk(self):
        return self.__group_brk

    def get_feed(self, group):
        return self.__group_feed.get(group)
    
    def get_group_feed(self):

        return self.__group_feed

    def add_feed(self, group, maxlen=100):
        self.__group_feed[group] = Feed(group, maxlen)

    def add_brk(self, group):
        self.__group_brk[group] = Broker(group)
    
    def resample(self, period, callback):
        '''所有组都设置同样的周期'''
        for group in self.__group_feed:
            self.__group_feed[group].resample(period, callback)
    
    def register(self):
        for group in self.__group_feed:
            feed = self.__group_feed[group]
            plugin = self.__market_handle_thread[group]
            feed.register(plugin.getsymbols())
        for group in self.__group_brk:
            brk = self.__group_brk[group]
            plugin = self.__trade_handle_thread[group]
            brk.register(plugin.getsymbols())

    def set_handle_thread(self, **kwargs):
        '''
            type : StrategyBase.MARKET StrategyBase.TRADE
            group : the unique name of the plugin
            plugin : ws or http for trade and market
            maxlen: for martket data plugin
        '''
        type = kwargs.get('type')
        group = kwargs.get('group')
        plugin = kwargs.get('plugin')
        if(type == StrategyBase.MARKET):
            self.__market_handle_thread[group] = plugin
            self.add_feed(group, kwargs.get('maxlen'))
        elif(type == StrategyBase.TRADE):
            self.__trade_handle_thread[group] = plugin 
            self.add_brk(group)
        else:
            raise Exception('plugin type error.')

    def dispatch(self):
        data = ()
        try:
            data = self.__queue.popleft()
        except IndexError:
            return
        try:
            self.__hash_callback[data[0]](data[1], data[2])
        except Exception as e:
            logging.exception(e)
        return True

    def start(self):
        for key in self.__market_handle_thread:
            self.__market_handle_thread[key].start()
        for key in self.__trade_handle_thread:
            self.__trade_handle_thread[key].start()
        self.onstart()

    def stop(self):
        for key in self.__trade_handle_thread:
            try:
                self.__trade_handle_thread[key].stop()
            except Exception as e:
                logging.exception(e)
        for key in self.__market_handle_thread:
            try:
                self.__market_handle_thread[key].stop()
            except Exception as e:
                logging.exception(e)
        self.onend()
        os._exit(0)

    def join(self):
        for key in self.__market_handle_thread:
            self.__market_handle_thread[key].join()
        for key in self.__trade_handle_thread:
            self.__trade_handle_thread.join()

    def run(self):
        self.init()
        self.register()
        self.start()
        while True:
            if(self.dispatch()) :
                continue
            time.sleep(0.01)
                

    ############################invoked in feed and brk#################################################
    def __ontimestamp(self, group, data):
        self.get_feed(group).ontimestamp(data)
    
    def __onticker(self, group, data):
        self.get_feed(group).onticker(data, self.onticker)
   
    def __onkline(self, group, data):
        ''' data must contain period of the kline'''
        self.get_feed(group).onkline(data.period(), data)

    def __onsnap(self, group, data):
        self.get_feed(group).onsnap(data, self.onsnap)

    def __onorderbook(self, group, data):
        self.get_feed(group).onorderbook(data, self.onorderbook)
    
    
    def __ontrade(self, group, data):
        self.get_brk(group).ontrade(data, self.ontrade)

    def __onorder(self, group, data):
        self.get_brk(group).onorder(data, self.onorder)

    def __onposition(self, group, data):
        self.get_brk(group).onposition(data, self.onposition)

    def __onbalance(self, group, data):
        self.get_brk(group).onbalance(data, self.onbalance)
    
    ########################realize in subclass#########################################
    def onstart(self):
        pass

    def onend(self):
        pass

    #for market data
    def onticker(self, handle, group, data):
        pass

    def onorderbook(self, handle, group, data):
        pass

    def onsnap(self, handle, group, data):
        pass
    
    # for account trade
    def ontrade(self, handle, group, data):
        pass

    def onorder(self, handle, group, data):
        pass

    def onposition(self, handle, group, data):
        pass
    
    def onbalance(self, handle, group, data):
        pass


    def place_order(self, symbol, order_type, price_type, limit_price, order_quantity):
        '''
            order_type : OrderType
            price_type : PriceType
            limit_price : float
            order_quantity : float
        '''
        group = symbol.split('--')[0]
        order = self.get_trade_handle(group).submitOrder(symbol, order_type, price_type, limit_price, order_quantity)
        if(order is None):
            return False
        self.__onorder(group, order)
        return order

    def cancel_order(self, orderid, symbol):
        group = symbol.split('--')[0]
        handle = self.get_trade_handle(group)
        return handle.cancelOrder(symbol, orderid)

    def buy_limit(self, symbol, price, quantity):
        return self.place_order(symbol, OrderType.Buy, PriceType.Limit, price, quantity)

    def sell_limit(self, symbol, price, quantity):
        return self.place_order(symbol, OrderType.Sell, PriceType.Limit, price, quantity)

    def buy_market(self, symbol, quantity):
        return self.place_order(symbol, OrderType.Buy, PriceType.Market, 0, quantity)

    def sell_market(self, symbol, quantity):
        return self.place_order(symbol, OrderType.Sell, PriceType.Market, 0, quantity)

    def buy_ice_limit(self, symbol, price, quantity):
        return self.place_order(symbol, OrderType.Buy, PriceType.Limit, price, quantity)

    def sell_ice_limit(self, symbol, price, quantity):
        return self.place_order(symbol, OrderType.Sell, PriceType.Limit, price, quantity)
   




