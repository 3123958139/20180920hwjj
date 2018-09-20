# -*- coding: utf-8 -*-

import qconf_py as conf
import socket
import MySQLdb

class VConf(object):
    ''' get config from mysql'''
    def __init__(self):
        self.__root = '/vic/'
        self.__mysql_conn = MySQLdb.connect(host='47.74.179.216', port=3308, user='ops', passwd='ops!@#9988', db='vic', charset='utf8')
        self.__cursor = self.__mysql_conn.cursor()

    def gethostname(self):
        return socket.gethostname()
    
    def get_conf(self, key):
        return conf.get_conf(key) 

    def get_batch_conf(self, key):
        return conf.get_batch_conf(key)
    
    def get_try(self, key1, key2):
        try:
            return self.get_conf(key1)
        except Exception as e:
            return self.get_conf(key2)

    def __query(self, sql, callback):
        self.__cursor.execute(sql)
        while True:
            row = self.__cursor.fetchone()
            if row is None : break
            callback(row)

    def get_http(self, key):
        return self.get_conf(self.__root + key + '/http')

    def get_wss(self, key):
        return self.get_conf(self.__root + key + '/wss')

    def get_apikey(self, key, user):
        path1 = self.__root + key + '/accounts/' + user + '/apikey'
        path2 = self.__root + key + '/accounts/' + user + '/' + self.gethostname() + '/apikey'
        return self.get_try(path1, path2)

    def get_secret(self, key, user):
        path1 = self.__root + key + '/accounts/' + user + '/secret'
        path2 = self.__root + key + '/accounts/' + user + '/' + self.gethostname() + '/secret'
        return self.get_try(path1, path2)

    def get_accounts(self, key):
        ''' return ['okex', 'bina']'''
        path = self.__root + key + '/accounts'
        self.get_batch_conf(path)

    def get_channels(self, key):
        ''' get symbols from db '''
        sql = 'select * from vic.vic_symbols where exchange="' + key + '"'
        channels = []
        def ondata(data) : channels.append(data[2]) 
        self.__query(sql, ondata)
        return channels

if __name__ == "__main__":
    logging.basicConfig(
            stream=sys.stdout,
            level=logging.DEBUG,
            format='%(asctime)s[%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s'
    )
    conf = VConf()

    key = 'OKEX'
    logging.info('%r', conf.get_http(key.lower()))
    logging.info('%r', conf.get_wss(key.lower()))
    logging.info(conf.get_apikey(key.lower(), '13651401725'))
    logging.info(conf.get_secret(key.lower(), '13651401725'))
    
    logging.info(conf.get_channels(key))






