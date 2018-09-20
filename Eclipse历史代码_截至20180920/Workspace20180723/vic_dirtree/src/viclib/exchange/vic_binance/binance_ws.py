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

class BinaWs(WebSocket):
    def __init__(self, url, apiKey=None, secretKey=None):
        '''
            wss : wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade/ethbtc@trade
            wss : wss://stream.binance.com:9443/ws/btcusdt@trade
        '''
        self.api_key = apiKey
        self.secret_key = secretKey
        self.channels = [] 
        self.__timestamp = None
        super(BinaWs, self).__init__(url)

            
    def on_ping(self, ws, data):
        #¿ÉÒÔ¼ì²â³¬Ê±
        pass
    
    def on_message(self, ws, message):
        datas = json.loads(message)
        try:
            #logging.info(datas)
            if('stream' in datas.keys()):
                self.execute(datas['stream'], datas['data'])                  
            else:
                self.execute(datas['e'], datas)                  
        except Exception, e:
            logging.exception('%r----------->%r', e, datas)

    def onorder(self, key, data):
        logging.info('%r %r', key, data)
    
    
    def ontrade(self, key, data):
        logging.info('%r %r', key, data)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')
    wss = "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade/ethbtc@trade/ethbtc@depth5"
    #wss = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    
    apiKey   = "CeVAxLBcH1TrxcZxRRD0k2G1llJVFNpfsmNl96cRQKjZ2b01LC85zewyRCJwkOQu"
    
    apiSecret= "5PF53iyHXFAvEBNs2zt0p5qbLkInkDCg83430b34kIFYv4O9HvFKbmEDc2q2vsxd"

    ws = BinaWs(wss);                              
    
    ws.onchannel('btcusdt@trade', ws.ontrade)
    ws.onchannel('ethusdt@trade', ws.ontrade)
    ws.onchannel('ethbtc@trade',  ws.ontrade)
    ws.onchannel('ethbtc@depth5', ws.onorder)


    #ws.onLogin = 
    ws.signal()
    ws.connect(sslopt={"cert_reqs": ssl.CERT_NONE})                                                                           




