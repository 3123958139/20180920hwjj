# -*- coding: utf-8 -*-
import time
import sys
import json
import logging
import signal
import hashlib
import hmac

from vic.exchange.common._websocket import WebSocket

class BitmexWs(WebSocket):
    def __init__(self, url, apiKey=None, secretKey=None):
        self.api_key = apiKey
        self.secret_key = secretKey
        self.channels = [] 
        self.acks = {} 
        self.subcribeall = None
        super(BitmexWs, self).__init__(url)

    def on_open(self, ws):
        super(BitmexWs, self).on_open(ws)
        
        #如果实时获取账户成交 订单推送则需要登录
        if(self.api_key and self.secret_key):
            self.login()
        else:
            self.subcribeall(self)
        
    def onLogin(self, ws, data):
        if 'success' not in  data.keys() and data['success']!=True:
            logging.error("auth error : %r ",  data)
            time.sleep(3)
            self.login()
        else:
            logging.info("auth ok : %r", data)
            self.subcribeall(self);
     
    def login(self):
        #{"op": "authKey", "args": ["<APIKey>", <nonce>, "<signature>"]}
        nonce = int(round(time.time()) + 10)
        handshakeobject = json.loads('{}')
        handshakeobject["op"] = "authKey"                                           
        paramsobject = json.loads('[]')
        paramsobject.append(self.api_key)
        paramsobject.append(nonce)
        paramsobject.append(self.__sign(nonce))
        handshakeobject["args"] = paramsobject                                     
        #{"event":"login","parameters":{"api_key":"xxx","sign":"xxx"}}
        self.ws.send(json.dumps(handshakeobject, sort_keys=True))                         
        #logging.info('login ' + json.dumps(handshakeobject))

    def __sign(self, nonce):
        message = ('GET' + '/realtime' + str(nonce) + '').encode('utf-8')
        signature = hmac.new(self.secret_key.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
        return signature 
     
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            #logging.info(data)
            if 'table' in data.keys(): 
                channel = data['table']
                self.execute(channel, data['data'])
            elif 'subscribe' in data.keys():
                self.onsubcribe(ws, data) 
            elif 'request' in data.keys():
                self.onsubcribe(ws, data) 
            else:
                logging.info('--------------------------------->%r', data)
        except Exception, e:
            logging.exception('%r', e)

    def subcribe(self, channel):
        subscribeobject = json.loads('{}')                             
        subscribeobject["op"] = "subscribe"
        subscribeobject["args"] = [channel]
        self.ws.send(json.dumps(subscribeobject, sort_keys=True))      
        self.channels.append(channel)                                  
        #self.send("{'event':'addChannel','channel':'ok_sub_spot_bch_btc_ticker'}")

    def send(self, data):
        self.send(data)


    def onsubcribe(self, ws, data):
        '''{u'subscribe': u'orderBook10', u'request': {u'args': [u'orderBook10'], u'op': u'subscribe'}, u'success': True}'''
        if('success' not in data.keys() or not data['success']):
            logging.error('subcribe fail: %r.', data)
            self.subcribe(data['request']['args'][0])
        else:
            logging.info('subcribe OK: %r.', data)
            if(data['request']['op'] == 'authKey'):
                self.onLogin(ws, data)

#self.send("{'event':'addChannel','channel':'ok_sub_spotusd_btc_ticker','binary':'true'}")
#
#self.send("{'event':'addChannel','channel':'ok_sub_spot_bch_btc_ticker'}")
#
#self.send("{'event':'addChannel','channel':'ok_sub_spot_bch_btc_deals'}")


def onorder(key, data):
    logging.info('%r %r', key, data)


def ontrade(key, data):
    for item in data:
        logging.info('%r %r', key, item)

def oninstrument(key, data):
    for item in data:
        if 'state' in item and item['state']=='Open':
            if item['symbol'] == 'XBT7D_U110':
                logging.info(item)
            ins = {}
            ins['rootSymbol'] = item['rootSymbol']
            ins['symbol'] = item['symbol']
            ins['underlying'] = item['underlying']
            ins['state'] = item['state']
            ins['settle'] = item['settle']
            logging.info('%r %r', key, ins)



def subcribe(socket):
    #socket.subcribe('trade')
    socket.subcribe('instrument')
    #socket.subcribe('orderBook10')
    
    socket.onchannel('trade', ontrade)
    socket.onchannel('instrument', oninstrument)
    socket.onchannel('orderBook10', onorder)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')
    wss = "wss://www.bitmex.com/realtime"
    apikey    = 'xShYIkq6c964NqKMH7cP1f3j'
    apisecret = 'ehWvEyF80IkmkwTJbB5-DiLSlJP8k6WWJiEXyhIdmYaskrBR'

    ws = BitmexWs(wss);                              
    #ws = BitmexWs(wss, apiKey, apiSecret);                              
    
    #ws.onLogin = 
    ws.subcribeall = subcribe
    ws.signal()
    ws.connect()                                                                           




