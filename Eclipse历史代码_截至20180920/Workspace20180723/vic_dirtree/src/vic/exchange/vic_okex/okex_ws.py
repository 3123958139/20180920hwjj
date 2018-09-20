# -*- coding: utf-8 -*-
import time
import sys
import json
import logging
import signal
import hashlib

from vic.exchange.common._websocket import WebSocket

class OkexWs(WebSocket):
    def __init__(self, url, apiKey=None, secretKey=None):
        self.api_key = apiKey
        self.secret_key = secretKey
        self.channels = [] 
        self.acks = {} 
        self.subcribeall = None
        super(OkexWs, self).__init__(url)
    
    def on_pong(self, ws, data):
        self.ws.send("{'event':'ping'}")

    def on_open(self, ws):
        super(OkexWs, self).on_open(ws)
        
        #如果实时获取账户成交 订单推送则需要登录
        if(self.api_key and self.secret_key):
            self.login()
        else:
            self.subcribeall(self)
        
    def onLogin(self, ws, data):
        if not data['result']:
            logging.error("auth error : %r ",  data)
            time.sleep(3)
            self.login()
        else:
            logging.info("auth ok : %r", data)
            self.subcribeall(self);
     
    def login(self):
        handshakeobject = json.loads('{}')
        handshakeobject["event"] = "login"                                           
        paramsobject = json.loads('{}')
        paramsobject['api_key'] = self.api_key
        paramsobject['sign'] = self.__sign({'api_key': self.api_key})
        handshakeobject["parameters"] = paramsobject                                     
        #{"event":"login","parameters":{"api_key":"xxx","sign":"xxx"}}
        self.ws.send(json.dumps(handshakeobject, sort_keys=True))                         
        #logging.info('login ' + json.dumps(handshakeobject))

    def on_message(self, ws, message):
        try:
            datas = json.loads(message)
            #logging.info('--------------------------------->%r', datas)
            for data in datas:
                if 'channel' not in data:
                    #logging.info(datas)
                    continue
                channel = data['channel']
                obj    = data['data'] 
                if(channel == 'login'):
                    self.onLogin(self.ws, obj)
                elif(channel == 'addChannel'):
                    self.onsubcribe(self.ws, obj)
                else:
                    self.execute(channel, obj)                  
        except Exception, e:
            logging.exception('%r', e)

    def __sign(self, params):
        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) +'&'
        data = sign + 'secret_key=' + self.secret_key
        return  hashlib.md5(data.encode("utf8")).hexdigest().upper()

    def subcribe(self, channel):
        #logging.info(channel)
        subscribeobject = json.loads('{}')                             
        subscribeobject["event"] = "addChannel"
        subscribeobject["channel"] = channel
        self.ws.send(json.dumps(subscribeobject, sort_keys=True))      
        self.channels.append(channel)                                  
        #self.send("{'event':'addChannel','channel':'ok_sub_spot_bch_btc_ticker'}")

    def onsubcribe(self, ws, data):
        '''{u'result': True, u'channel': u'ok_sub_spot_ltc_btc_balance'}'''
        if(not data['result']):
            logging.error('subcribe %s fail.', data)
            if data.get('channel'):
                self.subcribe(channel)
        else:
            logging.info('subcribe %s OK.', data['channel'])

#self.send("{'event':'addChannel','channel':'ok_sub_spotusd_btc_ticker','binary':'true'}")
#
#self.send("{'event':'addChannel','channel':'ok_sub_spot_bch_btc_ticker'}")
#
#self.send("{'event':'addChannel','channel':'ok_sub_spot_bch_btc_deals'}")


def onticker(key, data):
    #logging.info('%r %r', key, data)
    pass

def ontrade(key, data):
    logging.info('%r %r', key, data)


def subcribe(socket):
    socket.subcribe('ok_sub_spot_usd_btc_ticker')
    socket.subcribe('ok_sub_spot_bch_btc_ticker')
    socket.subcribe('ok_sub_spot_bch_btc_deals')
    socket.onchannel('ok_sub_spotusd_btc_ticker', onticker)
    socket.onchannel('ok_sub_spot_bch_btc_ticker', onticker)
    socket.onchannel('ok_sub_spot_bch_btc_deals', ontrade)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')
    wss = "wss://real.okex.com:10441/websocket"
    apikey    = 'db98cb7e-71c4-442d-bf45-8c6ab05a4c1c'
    apisecret = '4A5F6437B9DE1A2B16E80FC0018C8515'

    ws = OkexWs(wss);                              
    #ws = OkexWs(wss, apiKey, apiSecret);                              
    
    #ws.onLogin = 
    ws.subcribeall = subcribe
    ws.signal()
    ws.connect()                                                                           




