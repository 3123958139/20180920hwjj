# -*- coding: utf-8 -*-
# @Date    : 2018-03-06 15:40:03
# @Author  : DreamyZhang
# @QQ      : 775745576

import sys
import json
import logging
import time
import hashlib
import requests
import urllib

class HttpClient(object):
    def __init__(self, url, apikey, apisecret):
        self.__apikey = apikey 
        self.__apisecret = apisecret
        self.__url = url
        self.getheader = {"Content-type" : "application/x-www-form-urlencoded",}
        self.postheader = {"Content-type" : "application/x-www-form-urlencoded",}
    
    def getApiKey(self):
        return self.__apikey

    def getApiSecret(self):
        return self.__apisecret
    
    def getUrl(self):
        return self.__url

    def __sign(self, params): 
        data = sorted(params.items(), key=lambda d: d[0], reverse=False)
        data = urllib.urlencode(data) + '&secret_key=' + self.__apisecret
        return  hashlib.md5(data.encode("utf8")).hexdigest().upper()     

    def http_post_request(self, method, query=None, **args):
        ''' for okex '''
        url = '{url}/{method}'.format(url=self.__url, method=method)
        data = {}
        data.update(**args)
        if query is not None: data.update(query)
        data['sign']  = self.__sign(data)

        return self.http_request(url, 'POST', data, self.postheader)

    def http_get_request(self, method, query=None, **args):
        ''' for okex'''
        data = {}
        data.update(**args)
        if query is not None: data.update(query)
        url = '{url}/{method}?{params}'.format(url=self.__url, method=method, params=urllib.urlencode(data))
        return self.http_request(url, 'GET', None, self.getheader)
        
    def http_request(self, url, method, data, headers, timeout=5):
        try_times = 0
        while try_times < 2:
            try_times += 1
            response = None
            try:
                if(method == 'POST'):
                    #data will in body
                    response = requests.post(url, data=data, headers=headers, timeout=timeout)
                elif(method == 'GET'):
                    #data will in query string
                    response = requests.get(url, data=data, headers=headers, timeout=timeout)
                elif(method == 'PUT'):
                    #data will in body
                    response = requests.put(url, data=data, headers=headers, timeout=timeout)
                elif(method == 'DELETE'):
                    #will in request  
                    response = requests.delete(url, data=data, headers=headers, timeout=timeout)
                else:
                    raise Exception('http method ' + method + ' not realized!')
               
                #if response.status_code == 200:
                return response.json()
                #logging.info('%r %r\n data:%r\n headers:%r\n response:%r\n\n', method, url, data, headers, response.json())
            except BaseException as e:
                logging.error('%r %r\n data:%r\n headers:%r\n resp:%r\n Exception:%r\n\n', method, url, data, headers, response and response.json() or None, e)
            time.sleep(1)
        return None
    

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')
    http = HttpClient('', '', '')








