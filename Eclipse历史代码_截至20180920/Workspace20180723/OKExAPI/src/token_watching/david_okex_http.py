#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

from david_http import HttpClient


class OkexHttp(HttpClient):
    """
    """

    def __init__(self, url, apikey, apisecret):
        """
        """
        super(OkexHttp, self).__init__(url, apikey, apisecret)

    def ticker(self, symbol):
        """
        """
        return self.http_get_request('ticker.do', symbol=symbol)


if __name__ == "__main__":
    apikey = 'cdffc016-fdea-4e97-a200-39de74f0021a'
    apisecret = '4277FB3395F1590ABC1FC8218B8CC1DF'
    url = "https://www.okex.com/api/v1"

    http = OkexHttp(url, apikey, apisecret)

    print(http.ticker('btc_usdt'))
