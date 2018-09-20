# -*- coding: utf-8 -*-
import logging
import sys
 
from vic.exchange.common._websocket import WebSocket 

#��ܻᷢ��ping ��server  server�ظ�pong
#�ͻ��˷�ping ����˻�pong  ping pong��־�ǰ�ͷ�� ������Դ�����
class Client(WebSocket):
    def __init__(self):
        super(Client, self).__init__('ws://127.0.0.1:9990')

    def on_message(self, ws, message):
        logging.info(message)
    
    def onconnected(self, ws):
        self.ws.send(u'test')      

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s') 
    
    client = Client()
    client.signal()
    client.connect()


