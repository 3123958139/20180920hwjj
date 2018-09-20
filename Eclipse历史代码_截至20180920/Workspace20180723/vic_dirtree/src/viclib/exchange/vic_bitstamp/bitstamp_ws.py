# -*- coding: utf-8 -*-
import time
import sys
import json
import logging
import signal
import StringIO
import gzip

from websocket._ssl_compat import ssl
from vic.exchange.common._websocket import WebSocket

class BitstampWs(WebSocket):
    def __init__(self, url, apiKey=None, secretKey=None):
        '''
            wss : wss://ws.pusherapp.com/app/de504dc5763aeef9ff52?protocol=7&client=js&version=2.1.6&flash=false
        '''
        self.api_key = apiKey
        self.secret_key = secretKey
        self.channels = [] 
        self.__timestamp = None
        self.subcribeall = None
        super(BitstampWs, self).__init__(url)

    def on_open(self, ws):
        super(BitstampWs, self).on_open(ws)
        self.subcribeall(self)

    def on_message(self, ws, message):
        datas = json.loads(message)
        
        logging.info(datas)
        
        return 
        if datas.event == 'pusher:connection_established':
            pass
        elif datas.event == 'pusher:error':
            pass
        elif datas.event == 'pusher:ping':
            pass
        elif datas.event == 'pusher:pong':
            pass
        else:
            self.execute(datas['e'], datas) 

        try:
            logging.info(datas)
            #if('stream' in datas.keys()):
            #    self.execute(datas['stream'], datas['data'])                  
            #else:
            #    self.execute(datas['e'], datas)                  
        except Exception, e:
            logging.exception('%r----------->%r', e, datas)

    def subcribe(self, channel):
        subscribeobject = json.loads('{}')
        subscribeobject["event"] = 'pusher:subscribe'
        subscribeobject["data"] = {"channel": channel}
        self.ws.send(json.dumps(subscribeobject, sort_keys=True))
        self.channels.append(channel)
        self.onchannel(channel, self.onsubcribe)

    def onsubcribe(self, ws, data):
        logging.info('%r', data)
        status = data['status']
        if(status == 'ok'):
            logging.info('subcribe %s OK.', data['subbed'])
        else:
            logging.exception('subcribe fail:', data)


def ontrade(self, key, data):
    logging.info('%r %r', key, data)

def subcribe(socket):
    socket.subcribe('live_trades')
    socket.onchannel('live_trades', ontrade)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')
    wss = "wss://ws.pusherapp.com/app/de504dc5763aeef9ff52?protocol=7&client=js&version=2.1.6&flash=false"

    apiKey   = "CeVAxLBcH1TrxcZxRRD0k2G1llJVFNpfsmNl96cRQKjZ2b01LC85zewyRCJwkOQu"
    apiSecret= "5PF53iyHXFAvEBNs2zt0p5qbLkInkDCg83430b34kIFYv4O9HvFKbmEDc2q2vsxd"

    ws = BitstampWs(wss);                              

    ws.subcribeall = subcribe

    #ws.onLogin = 
    ws.signal()
    ws.connect(sslopt={"cert_reqs": ssl.CERT_NONE})                                                                           




