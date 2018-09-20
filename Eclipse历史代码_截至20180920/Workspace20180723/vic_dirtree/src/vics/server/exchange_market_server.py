# -*- coding: utf-8 -*-
import logging
import sys
import time
from websocket_server import WebsocketServer


class Server(object):
    def __init__(self, ip, port):
        self.__ip = ip
        self.__port = port
        self.__server = None

    def __new_client(self, client, server):
        logging.info(client)
        logging.info(server.clients)
    
    def __client_left(self, client, server):
        logging.info(client)
        logging.info(server.clients)
    
    def __recv_ping(self, client, data=''):
        self.__send_msg_client(client, str({'timestamp' : int(1000 * time.time())}))

    def __message_received(self, client, server, message):
        if not message:
            self.__recv_ping(client, message)
        logging.info(client)
        logging.info(message)
        self.__send_msg(message)

    def __run(self):
        try:
            self.__server = WebsocketServer(self.__ip, self.__port) 
            self.__server.set_fn_new_client(self.__new_client)            
            self.__server.set_fn_client_left(self.__client_left)              
            self.__server.set_fn_message_received(self.__message_received)    
            self.__server.run_forever()
        except Exception as e:
            logging.exception(e)
            self.__server = None
   
    def __send_msg_client(self, client, message):
        if self.__server:
            self.__server.send_message(client, message)

    def __send_msg(self, message):
        if self.__server:
            self.__server.send_message_to_all(message)

    def start(self):
        #while True:
        self.__run()

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s') 
    Server(9990, '0.0.0.0').start()
