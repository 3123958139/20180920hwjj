# -*- coding: utf-8 -*-
import time
import sys
import json
import logging
import signal
import StringIO
import gzip

from vic.exchange.common._websocket import WebSocket

#基于请求id的回调
#兼容请求 和 push
class HuobiWs(WebSocket):
    def __init__(self, url, apiKey=None, secretKey=None):
        self.api_key = apiKey
        self.secret_key = secretKey
        self.channels = [] 
        self.acks = {} 
        self.subcribeall = None
        self.__timestamp = None
        super(HuobiWs, self).__init__(url)

    def getreqid(self):
        return str(time.time())

    def on_open(self, ws):
        super(HuobiWs, self).on_open(ws)
        
        #如果实时获取账户成交 订单推送则需要登录
        #if(self.api_key and self.secret_key):
        #    self.login()
        #else:
        self.subcribeall(self)
        
    #def onLogin(self, ws, data):
    #    if not data['result']:
    #        logging.error("auth error : %r ",  data)
    #        time.sleep(3)
    #        self.login()
    #    else:
    #        logging.info("auth ok : %r", data)
    #        self.subcribeall(self);
     
    #def login(self):
    #    handshakeobject = json.loads('{}')
    #    handshakeobject["event"] = "login"                                           
    #    paramsobject = json.loads('{}')
    #    paramsobject['api_key'] = self.api_key
    #    paramsobject['sign'] = self.__sign({'api_key': self.api_key})
    #    handshakeobject["parameters"] = paramsobject                                     
    #    #{"event":"login","parameters":{"api_key":"xxx","sign":"xxx"}}
    #    self.ws.send(json.dumps(handshakeobject, sort_keys=True))                         
     
    def on_ping(self, ws, data):
        subscribeobject = json.loads('{}')
        subscribeobject['pong'] = data['ping']
        self.__timestamp = data['ping']
        self.ws.send(json.dumps(subscribeobject))      
    
    def on_message(self, ws, message):
        try:
            stream = StringIO.StringIO(message)
            datastr = gzip.GzipFile(fileobj=stream).read()
            data = json.loads(datastr)
            
            if('ping' in data.keys()):
                self.on_ping(ws, data)
            elif('id' in data.keys()):
                self.execute(data['id'], data) 
                self.delchannel(data['id'])
            else:
                channel = data['ch']
                self.execute(channel, data)                  
        except Exception, e:
            logging.exception('%r', e)

    #def __sign(self, params):
    #    sign = ''
    #    for key in sorted(params.keys()):
    #        sign += key + '=' + str(params[key]) +'&'
    #    data = sign + 'secret_key=' + self.secret_key
    #    return  hashlib.md5(data.encode("utf8")).hexdigest().upper()

    def subcribe(self, channel):
        subscribeobject = json.loads('{}')                             
        subscribeobject["sub"] = channel
        subscribeobject["id"] = 'subcribe'
        self.ws.send(json.dumps(subscribeobject, sort_keys=True))      
        self.channels.append(channel)
        self.onchannel(subscribeobject['id'], self.onsubcribe)
        #self.send("{'req':'reqid','req':'ok_sub_spot_bch_btc_ticker'}")
        
        #logging.info(json.dumps(subscribeobject, sort_keys=True))

    def unsubcribe(self, channel):
        subscribeobject = json.loads('{}')                             
        subscribeobject["unsub"] = channel
        subscribeobject["id"] = 'unsubcribe'
        self.ws.send(json.dumps(subscribeobject, sort_keys=True))      
        self.channels.append(channel)                                  
        self.onchannel(subscribeobject['id'], self.onunsubcribe)
        #self.send("{'id':'reqid','req':'ok_sub_spot_bch_btc_ticker'}")
    
    def request(self, channel, callback=None):
        subscribeobject = json.loads('{}')                             
        subscribeobject["req"] = channel
        subscribeobject["id"] = self.getreqid()
        self.ws.send(json.dumps(subscribeobject, sort_keys=True))      
        self.channels.append(channel)                                  
        self.onchannel(subscribeobject['id'], callback)
        #self.send("{'id':'reqid','req':'ok_sub_spot_bch_btc_ticker'}")
    
    def onsubcribe(self, ws, data):
        status = data['status']
        if(status == 'ok'):
            logging.info('subcribe %s OK.', data['subbed'])
        else:
            logging.exception('subcribe fail:', data)
             
    def onunsubcribe(self, ws, data):
        status = data['status']
        if(status == 'ok'):
            logging.info('subcribe %s OK.', data['subbed'])
        else:
            logging.exception('subcribe fail:', data)
         

def onorder(key, data):
    return
    logging.info('%r %r', key, data)


def ontrade(key, data):
    logging.info('%r %r', key, data)


def onkline(key, data):
    logging.info('%r %r', key, data)

def subcribe(socket):
    ''' 
        market.$symbol.kline.$period
        market.$symbol.depth.$type
        market.$symbol.trade.detail
        market.$symbol.detail
    '''
    socket.subcribe('market.btcusdt.trade.detail')
    socket.subcribe('market.btcusdt.depth.step0')
    socket.onchannel('market.btcusdt.trade.detail', ontrade)
    socket.onchannel('market.btcusdt.depth.step0', onorder)
    
    #socket.request('market.btcusdt.kline.60min', onkline)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')
    wss = "wss://api.huobipro.com/ws"
    apiKey   = "3af5ee91-4bc1407b-d68cd6a5-7291b"                                    
    apiSecret= "319c3ea1-88eeb820-a80d5ae8-3f93b"                                        


    ws = HuobiWs(wss);                              
    
    #ws.onLogin = 
    ws.subcribeall = subcribe
    ws.signal()
    ws.connect()                                                                           




