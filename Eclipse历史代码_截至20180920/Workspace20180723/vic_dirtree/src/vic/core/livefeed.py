# -*- coding: utf-8 -*-

import time
import logging

from struct import MINNUM

class Bars(object):
    def __init__(self, period, callback, maxlen):
        self.maxlen = maxlen
        self.period = period
        self.callback = callback
        self.last_push_time = 0
        self.data = {}

class Feed(object):
    '''
        1. 不支持ticker历史 + 实时kline
        2. 历史k线 + 实时k线/实时ticker(实时ticker合成新周期的 new)
            历史k线加载完毕之后 更新行情时间为整点, 然后可以接收处理整点的行情
        3. ticker历史 + 实时ticker  (根据ticker时间过滤 可以完全衔接的)
        4. kline 一批k线更新后 在更新时间戳
    '''
    def __init__(self, name, maxlen=100):
        # 一组有时序品种行情
        self.__group_name = name 
        self.__maxlen = maxlen
        # 数据列表 bars[60] = {}    bars[-1] = 
        self.__bars = {}
        # 快照数据
        self.__snap = {}
        # ticker 
        self.__tickers = Bars(-1, None, maxlen)
        # 是否补齐k线  策略端需要补齐  存储不要补齐
        self.__fill_kline_flag = True
        # market time 
        self.__cur_timestamp = 0

    def register(self, symbols):
        ''' run after resample'''
        for period in self.__bars:
            for symbol in symbols:
                self.__bars[period].data[symbol] = dict()
                self.__bars[period].data[symbol]['symbol'] = list()
                self.__bars[period].data[symbol]['timestamp'] = list()
                self.__bars[period].data[symbol]['open'] = list()
                self.__bars[period].data[symbol]['high'] = list()
                self.__bars[period].data[symbol]['low'] = list()
                self.__bars[period].data[symbol]['close'] = list()
                self.__bars[period].data[symbol]['volume'] = list()
                self.__bars[period].data[symbol]['amount'] = list()
                self.__bars[period].data[symbol]['openinterest'] = list()
                self.__snap[symbol] = {}
        for symbol in symbols:
            self.__tickers.data[symbol] = dict() 
            self.__tickers.data[symbol]['tradeid'] = list() 
            self.__tickers.data[symbol]['symbol'] = list() 
            self.__tickers.data[symbol]['price'] = list() 
            self.__tickers.data[symbol]['volume'] = list() 
            self.__tickers.data[symbol]['amount'] = list() 
            self.__tickers.data[symbol]['side'] = list() 
            self.__tickers.data[symbol]['timestamp'] = list() 

    def resample(self, period, callback, maxlen=-1):
        if -1 == maxlen:
            maxlen = self.__maxlen
        self.__bars[period] = Bars(period, callback, maxlen)

    def ontimestamp(self, data):
        '''根据这个时间检查生成各种周期的k线'''
        self.__cur_timestamp = data['timestamp']

    def onsnap(self, data, callback):
        '''更新快照 以合约为key'''
        self.__snap[data['symbol']].update({data})
        callback(self, self.__group_name, self.__snap[data['symbol']])

    def onticker(self, data, callback):
        '''
            需要保证这里收到的数据是顺序递增的
        '''
        if(self.__cur_timestamp > data.timestamp()):
            #logging.error('datatime of the ticker {0} is less then market time {1} .'.format( data.timestamp(), self.__cur_timestamp))
            #return
            raise Exception('datatime of the ticker {0} is less then market time {1} .'.format( data.timestamp(), self.__cur_timestamp))
        
        tickers = self.__tickers.data[data.symbol()]
        self.__add_ticker(tickers, data)
        self.__shift_ticker(tickers, self.__tickers.maxlen)
        callback(self, self.__group_name, tickers)
      
        p = data.price()
        
        for period in self.__bars:
            timekey = self.__getklinekey(period, data.timestamp())
            bars = self.__bars[period].data[data.symbol()]
            if(len(bars['timestamp']) == 0):
                self.__add_kline(bars, timekey, data.symbol(), p, p, p, p, data.volume(), data.amount(), data.openinterest())
            elif(timekey == bars['timestamp'][-1]):
                #logging.info('__update_kline: %r %r %r %r', period, timekey,  data.timestamp(), bars['timestamp'][-1])
                self.__update_kline(bars, p, p, p, p, data.volume(), data.amount(), data.openinterest())
            elif(timekey > bars['timestamp'][-1]):
                #logging.info('__add_kline: %r %r %r %r %r %r', data.symbol(), period, timekey,  self.__bars[period].last_push_time, data.timestamp(), bars['timestamp'][-1])
                if(self.__bars[period].last_push_time+period < timekey) : 
                    self.__bars[period].last_push_time = timekey-period
                    self.__checknow(period)
                self.__add_kline(bars, timekey, data.symbol(), p, p, p, p, data.volume(), data.amount(), data.openinterest())
            else:
                raise Exception('datatime of the ticker is less the last kline.')

    def onkline(self, period, data):
        '''由kline来更新'''
        for key in self.__bars:
            if(key < period) : continue
            timekey = self.__getklinekey(key, data.timestamp())
            bars = self.__bars[key].data[data.symbol()]
            if(len(bars['timestamp']) == 0):
                self.__add_kline(bars, timekey, data.symbol(), data.open(), data.high(), data.low(), data.close(), data.volume(), data.amount(), data.openinterest())
            elif(timekey == bars['timestamp'][-1]):
                self.__update_kline(bars, data.open(), data.high(), data.low(), data.close(), data.volume(), data.amount(), data.openinterest())
            elif(timekey > bars['timestamp'][-1]):
                if(self.__bars[key].last_push_time+key < timekey) : 
                    self.__bars[key].last_push_time = timekey-key
                    self.__checknow(key)
                self.__add_kline(bars, timekey, data.symbol(), data.open(), data.high(), data.low(), data.close(), data.volume(), data.amount(), data.openinterest())
            else:
                raise Exception('datatime of the ticker is less the last kline.')

    def onorderbook(self, data, callback):
        '''暂时直接回调'''
        callback(self, self.__group_name, data)

    def __checknow(self, period):
        '''补齐所有合约 回调最后一个周期'''
        timekey = self.__getklinekey(period, self.__cur_timestamp)
        data = self.__bars[period].data
        for symbol in data:
            if(len(data[symbol]['timestamp']) == 0) : continue
            self.__fill_kline(data[symbol], symbol, period, timekey)
            self.__shift_bars(data[symbol], self.__bars[period].maxlen)
            self.__bars[period].callback(self, self.__group_name, period, data[symbol])
    
    def __shift_bars(self, data, maxlen):
         while(len(data['symbol']) > maxlen):
            data['symbol'].pop(0)
            data['timestamp'].pop(0)
            data['open'].pop(0)
            data['high'].pop(0)
            data['low'].pop(0)
            data['close'].pop(0)
            data['volume'].pop(0)
            data['amount'].pop(0)
            data['openinterest'].pop(0)

    def __shift_ticker(self, data, maxlen):
         while(len(data['symbol']) > maxlen):
             data['symbol'].pop(0)
             data['tradeid'].pop(0)
             data['price'].pop(0)
             data['volume'].pop(0)
             data['amount'].pop(0)
             data['side'].pop(0)
             data['timestamp'].pop(0)

    def __fill_kline(self, bars, symbol, period, timekey):
        '''
            补齐最后一根到  当前时间戳之间的 不包含当前时间戳对应的
            中间补齐的不走回调 一般情况下不会有很多补齐 
        '''
        if(not self.__fill_kline_flag) : return
        diff = timekey - bars['timestamp'][-1]
        if(diff <= period) : return
        while(diff > period): 
            p = bars['close'][-1]
            diff -= period
            self.__add_kline(bars, timekey-diff, symbol, p, p, p, p, 0, 0, 0)

    def __getklinekey(self, period, timestamp):
        '''支持一般的周期'''
        return int(timestamp/1000) / period * period

    def __add_ticker(self, bars, data):
        bars['tradeid'].append(data.id())
        bars['symbol'].append(data.symbol())
        bars['price'].append(data.price())
        bars['volume'].append(data.volume())
        bars['amount'].append(data.amount())
        bars['side'].append(data.side())
        bars['timestamp'].append(data.timestamp())
        #logging.info('%r %r', self.__cur_timestamp, data.timestamp())
        self.__cur_timestamp = data.timestamp()
    
    def __add_kline(self, bars, timekey, symbol, open, high, low, close, volume, amount, openinterest):
        bars['symbol'].append(symbol)
        bars['timestamp'].append(timekey)
        bars['open'].append(open)
        bars['high'].append(high)
        bars['low'].append(low)
        bars['close'].append(close)
        bars['volume'].append(volume)
        bars['amount'].append(amount)
        bars['openinterest'].append(openinterest)
        #logging.info('%r %r %r %r %r %r %r', bars['symbol'][-1], bars['timestamp'][-1], bars['high'][-1], bars['open'][-1], bars['low'][-1], bars['close'][-1], bars['volume'][-1])

    def __update_kline(self, bars, open, high, low, close, volume, amount, openinterest):
        if(bars['open'][-1] < MINNUM):
            bars['open'][-1] = open
        if(high > bars['high'][-1]):
            bars['high'][-1] = high
        if(low < bars['low'][-1] and low > 0):
            bars['low'][-1] = low
        bars['close'][-1]   = close
        bars['volume'][-1]  += volume
        bars['amount'][-1]  += amount
        bars['openinterest'][-1]+= openinterest
 
    

