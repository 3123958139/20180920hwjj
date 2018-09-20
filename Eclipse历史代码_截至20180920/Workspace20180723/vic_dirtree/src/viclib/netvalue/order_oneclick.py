#!/usr/bin/env python
#coding=utf-8

#from vic.exchange.vic_binance.binance_http import BinaHttp

import time
from vic.exchange.vic_binance.binance_http import BinaHttp
from vic.exchange.vic_huobi.huobi_http import HuobiHttp
from vic.exchange.vic_okex.okex_http import OkexHttp
from vic.exchange.vic_okex.okexft_http import OkexftHttp

from lib.okex_risk_netvalue import OkexService
from lib.bina_risk_netvalue import BinanService
from lib.huobi_risk_netvalue import HuobiService
from lib.common import config_data, log_info, log_exception, timestamp2str, \
     current_strtime, before_after_timestamp, get_symbol, config_error_code_msg

conf = config_data()

def bina_order(currency, to_currency, quantity, price, type='LIMIT', side='BUY'):
    """币安一键下单"""
    url       = conf.get('BINA_URL')
    apiKey    = conf.get('BINA_APIKEY')
    apiSecret = conf.get('BINA_APISECRET')

    symbol = get_symbol(currency, to_currency, 'bina')
    http   = BinaHttp(url, apiKey, apiSecret)
    bs     = BinanService(url, apiKey, apiSecret)

    http.place_order(symbol, quantity, price, type, side)
    msg, status_code, json = http.msg, http.status_code, http.json

    if status_code != 200:
        log_info(u'币安下单:%s, 失败!' % symbol)
        log_info(u'### error:%s'% json)
        if json.get('msg') == 'Invalid quantity.':
            log_info(u'下单数量不正确，或者余额不足')
        return False

    log_info(u'%s  下单价格:%s, 下单量:%s, 成功!'% (symbol, price, quantity))
    return True


def bina_cancel_order(currency, to_currency):
    """币安一键撤单"""

    symbol      = get_symbol(currency, to_currency, 'bina')
    error_msg   = {}
    success_msg = {}

    url       = conf.get('BINA_URL')
    apiKey    = conf.get('BINA_APIKEY')
    apiSecret = conf.get('BINA_APISECRET')
    http = BinaHttp(url, apiKey, apiSecret)
    order_list = http.openorders()
    print(order_list)

    error_list, success_list = [], []

    if not order_list:
        log_info(u'币安无单可撤!')
        return False

    for order in order_list:
        orderId = order.get('orderId')
        http.cancel_order(symbol, orderId)
        status_code = http.status_code
        if status_code != 200:
            error_msg['orderId'] = orderId
            error_list.append(error_msg)
            log_info(u'币安撤单失败!, orderId:%s'% orderId)
        else:
            success_msg['orderId'] = orderId
            success_list.append(success_msg)
            log_info(u'币安撤单成功!, orderId:%s'% orderId)

    if len(error_list) > 0:
        return False

    return True


def huobi_order(currency, to_currency, amount, price=0, type='sell-limit', is_cancel=False):
    """火币一键下单"""

    url       = conf.get('HUOBI_URL')
    apiKey    = conf.get('HUOBI_APIKEY')
    apiSecret = conf.get('HUOBI_APISECRET')

    symbol    = get_symbol(currency, to_currency, 'huobi')
    http      = HuobiHttp(url, apiKey, apiSecret)
    hs        = HuobiService(url, apiKey, apiSecret)

    user = http.accounts()
    if not user or user.get('status') != u'ok':
        log_info(u'获取用户账户信息失败')
        return False

    user_data = user['data']
    data_list = [http.balance(data['id'])['data'] for data in user_data]
    uid_list  = [http.balance(data['id'])['data'].get('id') for data in user_data]
    order_list, order_data = [], {}
    for data in data_list:
        user_type    = data.get('type')
        state        = data.get('state')
        uid          = data.get('id')
        balance_list = data['list']

        for b in balance_list:
            currency = b.get('currency')
            balance  = float(b.get('balance'))
            price    = float(price)
            b_type   = b.get('type')
            amount   = balance if is_cancel else amount
            if symbol.startswith('%s'% currency) is False:
                # 不是要下单的币种的账户
                continue

            if balance <= 0:
                log_info(u'### 余额小于下单价格')
                continue

            if b_type == 'frozen':
                # 过滤掉冻结
                continue

            log_info(u'### 下单币种:%s, 成交币种:%s, 余额:%s, 下单价格:%s, 订单量:%s,  账户类型:%s'% (currency, to_currency,'%.6f' % balance, price, amount, b_type))

            source    = 'margin-api' if user_type == 'margin' else 'api'
            hs.place_order(uid, symbol, '%s' % amount, '%s' % price, type, source)
            status_code, msg, json = http.status_code, http.msg, http.json

            if status_code != 200:
                log_info(u'uid:%s  火币下单失败!'% uid)
                log_info(u'### error_msg:%s'% msg)
            elif json.get('status') == 'error':
                log_info(u'### 火币下单失败! uid:%s, http.status_code:%s, error_msg:%s' % (uid, status_code, json.get('err-msg')))
            else:
                order_data['uid']       = data.get('uid')
                order_list.append(order_data)
                log_info(u'火币下单: %s, 成功!' % symbol)

    if len(order_list) <= 0:
        log_info(u'火币下单失败, 没有合适的账户可以下单')

    return True


def huobi_cancel_order(currency, to_currency, start_date=None, end_date=None, _from=None, direct=None, size=1000000):
    """火币一键撤单"""

    url       = conf.get('HUOBI_URL')
    apiKey    = conf.get('HUOBI_APIKEY')
    apiSecret = conf.get('HUOBI_APISECRET')
    symbol    = get_symbol(currency, to_currency, 'huobi')

    http = HuobiHttp(url, apiKey, apiSecret)
    states = 'pre-submitted,submitted,partial-filled,partial-canceled'
    http.orders(symbol, states=states, start_date=start_date, end_date=end_date, _from=_from, direct=direct, size=size)
    json = http.json
    if not json:
        log_info(u'火币撤销订单失败')
        return False

    order_id_list = [int(id.get('id')) for id in json['data'] if json and json.get('data')]
    order_id_list = map(lambda id:'%s' % id, list(set(order_id_list)))

    if len(order_id_list) <= 0:
        log_info(u'火币%s, 近期没有可撤消的订单'% symbol)
        return False

    order_ids   = {'order-id':order_id_list}
    order_num   = len(order_id_list)
    cancel_time = int(order_num/50) if order_num > 50 else 1 # 由于一次不能撤单超过50个，所以要分次数撤销
    calcel_num  = 0

    for ct in range(cancel_time):
        #log_info(u'### calcel_num:%s, order_ids:%s'% (calcel_num, order_ids))
        begin     = calcel_num*50
        end       = (calcel_num+1)*50

        order_ids = {'order-ids':order_id_list[begin:end]}
        print('### order_ids:%s'% order_ids)
        http.cancel_orders(order_ids)
        print('### json:%s'% http.json)

        json_data = http.json['data']
        if json_data:
            success   = json_data.get('success')
            log_info(u'火币撤单成功的订单id有:%s' % success)
        else:
            log_info(u'火币无单可撤')

        time.sleep(1)
        calcel_num += 1

    return True


def okex_order(currency, to_currency, amount, price=0, tradetype='sell', order_type=''):
    """okex币币一键下单"""

    url       = conf.get('OKEX_URL')
    apiKey    = conf.get('OKEX_APIKEY')
    apiSecret = conf.get('OKEX_APISECRET')

    http      = OkexHttp(url, apiKey, apiSecret)
    oks       = OkexService(url, apiKey, apiSecret)
    symbol    = get_symbol(currency, to_currency, 'okex')

    log_info(u'下单价格:%s, tradetype:%s, amount:%s' % (price, tradetype, amount))
    http.addorder(symbol, tradetype, price, amount)
    status_code, json = http.status_code, http.json

    # 获取错误码的信息
    error_code = json.get('error_code')
    file = "../conf/okex_error_code.txt"
    msg = config_error_code_msg(error_code, file)

    log_info(u'### json:%s'% json)
    if status_code != 200 or msg:
        log_info(u'okex下单: %s, 失败!' % symbol)
        log_info(msg)
        return False

    log_info(u'okex下单: %s, 成功!' % symbol)
    return True


def okexft_order(currency, to_currency, contract_type, tradetype, price, amount, match_price=0):
    """okex合约下单"""
    url       = conf.get('OKEX_URL')
    apiKey    = conf.get('OKEX_APIKEY')
    apiSecret = conf.get('OKEX_APISECRET')
    symbol    = get_symbol(currency, to_currency, 'okex')

    ft_http = OkexftHttp(url, apiKey, apiSecret)
    #print(ft_http.future_trade('eth_usd', 'this_week', '1', '400', '1'))
    ft_http.future_trade(symbol, contract_type, '%s'% tradetype , '%s'% price, '%s'% amount, '%s'% match_price)

    #获取错误码的信息
    file = "../conf/okexws_error_code.txt"
    status_code, json = ft_http.status_code, ft_http.json
    error_code = json.get('error_code')
    msg = config_error_code_msg(error_code, file)
    json = ft_http.json

    if status_code != 200 or msg:
        log_info(u'okex合约下单: %s, 失败!' % symbol)
        log_info(msg)
        return False

    log_info(u'okex合约下单: %s, 成功!' % symbol)
    return True


def okex_cancel_order(currency, to_currency):
    """okex币币一键撤单"""

    url       = conf.get('OKEX_URL')
    apiKey    = conf.get('OKEX_APIKEY')
    apiSecret = conf.get('OKEX_APISECRET')
    http      = OkexHttp(url, apiKey, apiSecret)
    symbol    = get_symbol(currency, to_currency, 'okex')

    # 订单id列表
    order_history = http.order_history(symbol)
    order_list    = order_history['orders']
    order_id_list = [order.get('order_id') for order in order_list]

    status_code = http.status_code
    if len(order_id_list) <= 0:
        log_info(u'无单可撤!')

    for order_id in order_id_list:
        http.cancelorder(symbol, order_id)
        log_info(u'订单id为:%s, 撤单成功!'% order_id)
        time.sleep(0.5)

        # 获取错误码的信息
        json       = http.json
        error_code = json.get('error_code')
        file       = "../conf/okexws_error_code.txt"
        msg        = config_error_code_msg(error_code, file)

        if msg:
            log_info(u'订单id为:%s, 撤单失败. %s' % (order_id, msg))

    return True


def okex_future_cancel(currency, to_currency, contract_type):
    """okex取消合约订单"""

    url       = conf.get('OKEX_URL')
    apiKey    = conf.get('OKEX_APIKEY')
    apiSecret = conf.get('OKEX_APISECRET')
    ft_http   = OkexftHttp(url, apiKey, apiSecret)
    symbol    = get_symbol(currency, to_currency, 'okex')

    # 订单id列表
    data = ft_http.future_order_info(symbol, contract_type, '-1')
    order_list    = data['orders']
    order_id_list = [str(order.get('order_id')) for order in order_list]

    if len(order_id_list) <= 0:
        log_info(u'无单可撤!')

    order_num = len(order_id_list)
    for num in range(order_num):
        order_id = order_id_list[num]
        print('### order_id:%s'% order_id)
        ft_http.future_cancel(symbol, contract_type, order_id)
        time.sleep(0.5) # 访问频率 4次/2秒

        # 获取错误码的信息
        json       = ft_http.json
        error_code = json.get('error_code')
        file       = "../conf/okexws_error_code.txt"
        msg        = config_error_code_msg(error_code, file)

        if msg:
            log_info(u'订单id:%s, 撤单失败!' % order_id)
            log_info(msg)
        else:
            log_info(u'订单id: %s, 撤单成功!'% order_id)


def bina_clean_up():
    """币安清仓"""

    url       = conf.get('BINA_URL')
    apiKey    = conf.get('BINA_APIKEY')
    apiSecret = conf.get('BINA_APISECRET')

    http   = BinaHttp(url, apiKey, apiSecret)
    bs     = BinanService(url, apiKey, apiSecret)
    account  = http.account()
    balances = account.get('balances')
    for b in balances:
        asset  = b.get('asset')
        free   = float(b.get('free'))
        locked = float(b.get('locked'))

        if asset == 'usdt':
            continue

        if locked > 0:
            bina_cancel_order(asset, 'usdt')

        if free > 0:
            if asset not in bs.conf_currency_tousdt_list():
                continue # 过滤不是币安配置文件的币种

            # 获取symbol最新价格
            symbol       = get_symbol(asset, 'usdt', 'bina')
            lp           = http.latest_price(symbol)
            latest_price = float(lp.get('price')) # symbol最新价格
            bina_order(asset, 'usdt', round(free, 2), latest_price, 'LIMIT', 'SELL')

    return True


def huobi_clean_up():
    """火币清仓"""

    url       = conf.get('HUOBI_URL')
    apiKey    = conf.get('HUOBI_APIKEY')
    apiSecret = conf.get('HUOBI_APISECRET')
    http      = HuobiHttp(url, apiKey, apiSecret)

    # 账户id列表
    accounts_data = http.accounts()['data']
    accounts_id_list = [a.get('id') for a in accounts_data]
    for id in accounts_id_list:
        balance      = http.balance(id)
        balance_list = balance['data']['list']
        for b in balance_list:
            currency = b.get('currency')
            balance  = float(b.get('balance'))
            type     = b.get('type')
            if currency == 'usdt' or balance <= 0:
                continue # 如果是usdt或者余额不大于0的就循环下一个

            log_info('### currency:%s, balance:%s, type:%s'% (currency, balance, type))
            symbol = get_symbol(currency, 'usdt', 'huobi')
            if type == 'frozen':
                huobi_cancel_order(currency, 'usdt')

            kline = http.kline(symbol, '1min', 1)
            kline_low  = kline['data'][0]['low']
            huobi_order(currency,
                        'usdt',
                        round(balance, 3),
                        kline_low,
                        True)

    return True


def okex_clean_up(file_name=''):
    """okex清仓"""

    url       = conf.get('OKEX_URL')
    apiKey    = conf.get('OKEX_APIKEY')
    apiSecret = conf.get('OKEX_APISECRET')
    http      = OkexHttp(url, apiKey, apiSecret)
    oks       = OkexService(url, apiKey, apiSecret)
    ft_http   = OkexftHttp(url, apiKey, apiSecret)

    funds = http.userinfo()['info']['funds']
    free          = oks.free_data()
    freezed_data  = oks.freezed_data()
    currency_list = oks.currency_list()
    log_info('### funds:%s'% funds)
    log_info('### freezed_data:%s'% freezed_data)
    taobao_currency_list = []
    if file_name:
        file = '%s'% file_name
        with open(file, 'r') as f:
            data      = f.read()
            data      = data.replace('\r', '')
            data_list = data.split('\n')
            for d in data_list:
                d_list = re.split(r'[\s\,]+', d)
                key   = d_list[0].lower()
                if key == c:
                    taobao_currency_list.append(c)

    for c in currency_list:
        if c == 'usdt':
            continue # 如果是usdt就循环下一个

        if c in taobao_currency_list:
            continue # 套保的资金不清仓

        symbol          = get_symbol(currency, to_currency, 'okex')
        free_balance    = free.get(c)
        freezed_balance = freezed_data.get(c)
        if freezed_balance > 0:
            okex_cancel_order(c, 'usdt')

        if free_balance > 0:
            # ft_ticker  = ft_http.future_ticker(symbol, 'this_week')['ticker']
            # high_price = ft_ticker()['high']
            ticker     = http.ticker(symbol)['ticker']
            high_price = ticker['high']
            okex_order(c, 'usdt', free_balance, high_price, 'sell')

    return True




if __name__ == "__main__":

    currency    = 'eth'
    to_currency = 'usdt'

    quantity = 10
    price = 1

    #url       = conf.get('BINA_URL')
    #apiKey    = conf.get('BINA_APIKEY')
    #apiSecret = conf.get('BINA_APISECRET')
    #http      = BinaHttp(url, apiKey, apiSecret)
    #order_list = http.openorders()
    #print(order_list)

    #bina_order('eth', 'usdt', 10, 1)
    #bina_cancel_order('eth', 'usdt')
    #url      = conf.get('OKEX_URL')
    #apiKey   = conf.get('OKEX_APIKEY')
    #apiSecret= conf.get('OKEX_APISECRET')
    #ft_http   = OkexftHttp(url, apiKey, apiSecret)

    #huobi_order('eth', 'usdt', 0.1, 706.38) # currency, to_currency, amount, price
    #huobi_cancel_order('iota', 'usdt')
    #start_date = '2018-01-01'
    #end_date   = '2018-05-09'
    #huobi_cancel_order(currency, to_currency, '2018-01-01', '2018-05-09')

    #tradetype   = 'buy'
    #amount      = 0.001
    #price       = 0.1
    #okex_order('eth', 'usdt', 0.01, '500', 'sell') # currency, to_currency, amount, price, tradetype
    #contract_type = 'quarter'
    #tradetype     = 2 # 1:开多; 2：开空; 3:平多; 4：平空
    #ordertype = 'sell'
    #okexft_order('eth', 'usdt', 'quarter', 1, 0, 10) # currency, to_currency, contract_type, tradetype, price, amount
    #okex_cancel_order('eth', 'usdt')
    #okex_future_cancel('eth', 'usdt', 'quarter')
    #bina_clean_up()
    #huobi_clean_up()
    #okex_clean_up()
