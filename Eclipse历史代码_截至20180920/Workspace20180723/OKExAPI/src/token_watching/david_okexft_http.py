#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

import sys

from david_http import HttpClient


class OkexftHttp(HttpClient):
    def __init__(self, url, apikey, apisecret):
        """
        """
        super(OkexftHttp, self).__init__(url, apikey, apisecret)

    def future_ticker(self, symbol, contract_type):
        """
        GET : 获取OKEx合约行情
        symbol : btc_usd ltc_usd eth_usd etc_usd bch_usd
        contract_type : this_week/next_week/quarter
        return : {
            date: '1411627632',
            ticker: {...}
        }
        """
        return self.http_get_request('future_ticker.do', symbol=symbol, contract_type=contract_type)


if __name__ == "__main__":
    apikey = 'cdffc016-fdea-4e97-a200-39de74f0021a'
    apisecret = '4277FB3395F1590ABC1FC8218B8CC1DF'
    url = "https://www.okex.com/api/v1"

    http = OkexftHttp(url, apikey, apisecret)

    print(http.future_ticker('btc_usd', 'this_week'))
