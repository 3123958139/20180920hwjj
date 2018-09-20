# -*- coding: utf-8 -*-
import websocket
from threading import Timer
import logging
import signal
import os
import sys

class WebSocket(object):
    def __init__(self, url):
        self.url = url
        self.enablereconnection = True
        self.delay = 3
        self.ws =  None
        self.onConnected =  self.onconnected
        self.onDisconnected = self.ondisconnect
        self.onConnectError =  self.onconnecterror
        self.heartbeat = 10
        self.timeout = 30 
        self.data_time = 0 
        self.map = {}
        super(WebSocket, self).__init__()
        self.sslopt = None
        self.http_proxy_host = None
        self.http_proxy_port = None
    
    def signal(self):
        '''作为主线程运行时  调用这个接收键盘中断'''
        signal.signal(signal.SIGINT, self.ctlc)

    def ctlc(self, signum, frame):
        logging.info('%r %r', signum, frame)
        os._exit(-1)

    def on(self, key, function):
        self.map[key] = function

    def onchannel(self, key, function):
        self.map[key] = function
    
    def delchannel(self, key):
        try:
            del self.map[key]
        except Exception, e:
            pass
        
    def execute(self, key, object):
        if key in self.map:
            function = self.map[key]
            if function is not None:
                function(key, object)

    def connect(self, sslopt=None, http_proxy_host=None, http_proxy_port=None):
        
        self.sslopt = sslopt
        self.http_proxy_host = http_proxy_host
        self.http_proxy_port = http_proxy_port

        # websocket.enableTrace(True)                                                                         
        self.ws = websocket.WebSocketApp(self.url,
                                         on_ping=self.on_ping,
                                         on_pong=self.on_pong,
                                         on_message=self.on_message,                                          
                                         on_error=self.on_error,                                              
                                         on_close=self.on_close)                                              
        self.ws.on_open = self.on_open 
        self.ws.run_forever(sslopt=sslopt, ping_interval=15, ping_timeout=14, http_proxy_host=http_proxy_host, http_proxy_port=http_proxy_port)  
    
    def stop(self):
        logging.info('close')
        return self.ws.close()

    def setBasicListener(self, onConnected, onDisconnected, onConnectError):
        self.onConnected = onConnected
        self.onDisconnected = onDisconnected
        self.onConnectError = onConnectError

    def reconnect(self):
        Timer(self.delay, self.connect, (self.sslopt, self.http_proxy_host, self.http_proxy_port)).start()

    def setdelay(self, delay):
        self.delay = delay

    def setreconnection(self, enable):
        self.enablereconnection = enable

    def on_ping(self, ws):
        pass

    def on_pong(self, ws, data):
        pass

    def on_error(self, ws, error):
        if self.onConnectError is not None:
            self.onConnectError(self, error)
            # self.reconnect()

    def on_close(self, ws):
        if self.onDisconnected is not None:
            self.onDisconnected(self)
        if self.enablereconnection:
            self.reconnect()

    def on_open(self, ws):
        if self.onConnected is not None:
            self.onConnected(self)
    
    def on_message(self, ws, message):
        raise NotImplementedError('Not Implemented.') 
    
    def onconnected(self, ws):
        logging.info('connected')

    def ondisconnect(self, ws):
        logging.info('missing connect')

    def onconnecterror(self, ws, error):
        logging.info('connect error:%r', error)
    
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s') 
    ws = WebSocket('----');
    ws.connect()
