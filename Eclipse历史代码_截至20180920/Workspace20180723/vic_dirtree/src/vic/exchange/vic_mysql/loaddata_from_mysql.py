# -*- coding: utf-8 -*-

import threading
import datetime
import logging
import time

import MySQLdb

from vic.core.struct import DateType
from vic.core.struct import Ticker
from vic.core.struct import Bar

class MysqlDataThread(threading.Thread):
    '''
        load data from mysql for market plugin
    '''
    def __init__(self, channels, queue, start_date, end_date, type=DateType.ON_MKT_TRADE, period=60):
        self.__channels = channels
        self.__queue = queue
        self.__mysql_conn = MySQLdb.connect(host='47.74.179.216', port=3308, user='ops', passwd='ops!@#9988', db='vic', charset='utf8')  
        self.__cursor = self.__mysql_conn.cursor()
        self.__timestamp = 0
        self.__start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d') 
        self.__end_date =  datetime.datetime.strptime(end_date, '%Y-%m-%d')
        self.__type = type
        self.__hash_callback = [i for i in range(0, 50)]
        self.__period = period
        self.__table = {60 : 'vic_1mk.1mk', 
                         300 : 'vic_5mk.5mk', 
                         3600:'vic_1h.1h', 
                         86400:'vic_1d.1d'}[period]
        super(MysqlDataThread, self).__init__()

    def getsymbols(self):
        return self.__channels
    
    def set_callback(self, type , callback):
        self.__hash_callback[type] = callback

    def __query(self, sql, callback):
        logging.info(sql)
        self.__cursor.execute(sql)
        while True:  
            row = self.__cursor.fetchone()  
            if row is None:
                break
            callback(row) 
    
    def timestamp(self, dt):
        return (int(time.mktime(dt.timetuple()))+3600*8) * 1000 

    def __kline(self):
        while self.__start_date < self.__end_date:
            str_start = self.__start_date.strftime('%Y-%m-%d')
            self.__start_date = self.__start_date + datetime.timedelta(days=1)
            str_end = self.__start_date.strftime('%Y-%m-%d')
            sql = 'select * from {0} where ts>\"{1}\" and ts<\"{2}\" and symbol in {3};'.format(self.__table, str_start, str_end, tuple(self.__channels))
            self.__query(sql, self.onkline)

    def __trade(self):
        while self.__start_date < self.__end_date:
            str_start = self.__start_date.strftime('%Y-%m-%d')
            self.__start_date = self.__start_date + datetime.timedelta(days=1)
            str_end = self.__start_date.strftime('%Y-%m-%d')
            sql = 'select * from vic_ticker.ticker where ts>\"{0}\" and ts<\"{1}\" and symbol in {2};'.format(str_start, str_end, tuple(self.__channels))
            self.__query(sql, self.onticker)

    def onticker(self, data):
        #ts | symbol   | price   | quantity | type
        if data[1] not in self.__channels:
            return
        group = data[1].split('--')[0]
        trade = {}
        trade['timestamp']  = self.timestamp(data[0])
        trade['id']         = '0'
        trade['direction']  = 'sell' if data[4]==1 else 'buy'
        trade['price']      = data[2]
        trade['symbol']     = data[1]
        trade['volume']     = data[3]
        trade['openinterest'] = 0
        self.__queue.append((DateType.ON_MKT_TRADE, group, Ticker(trade)))

    def onkline(self, data):
        #ts     | symbol    | open     | high | low  | close | quantity | turnover | openinterest
        if data[1] not in self.__channels:
            return
        group = data[1].split('--')[0]
        bar = {}
        bar['period']       = self.__period
        bar['timestamp']    = self.timestamp(data[0])
        bar['symbol']       = data[1]
        bar['open']         = data[2]
        bar['high']         = data[3]
        bar['low']          = data[4]
        bar['close']        = data[5]
        bar['volume']       = data[6]
        bar['amount']       = data[7]
        bar['openinterest'] = data[8]
        self.__queue.append((DateType.ON_MKT_KLINE, group, Bar(bar)))
        if(self.__timestamp and timestamp<bar['timestamp']):
            self.__queue().append((DateType.ON_TIMESTAMP, group, {'timestamp': self.__timestamp}))
            self.__timestamp = bar['timestamp']
    
    def start(self):
        self.set_callback(DateType.ON_MKT_TRADE, self.__trade)
        self.set_callback(DateType.ON_MKT_KLINE, self.__kline)
        super(MysqlDataThread, self).start()

    def stop(self):
        pass

    def run(self):
        self.__hash_callback[self.__type]()







