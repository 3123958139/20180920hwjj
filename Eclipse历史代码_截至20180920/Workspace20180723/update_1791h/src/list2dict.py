# coding:utf-8

"""
@Company : HWJJ
@Date    : 20180810
@Author  : David

When given a list of MySQL's symbols,
change every MySQL's symbol into CoinAPI's symbol,
and then return the pairs of them as a dict.

Example:

When given
    ['BINA--ADA--BTC']
and 
    'BITFINEX_SPOT'
we will get
    {'BINA--ADA--BTC':'BITFINEX_SPOT_ADA_USD'}
"""


def list2dict(symbols=[], exchange='BITFINEX_SPOT'):
    """
    params:
        symbols   - list of MySQL's symbols
        exchange - data source  
    return:
        dict of pairs of MySQL's symbols and CoinAPI's symbols
    """
    pairs = dict()
    for symbol in symbols:
        key = symbol

        symbolTail = symbol[-4:]
        symbolHead = symbol[:4]

        # change the tail
        if symbolTail == 'USDT':
            symbol = symbol[:-1]

        # change the head
        if symbolHead == 'BINA':
            pairs[key] = (exchanges + symbol[4:]).replace('--', '_')
        if symbolHead == 'OKEX':
            pairs[key] = (exchanges + symbol[4:]).replace('--', '_')
        if symbolHead == 'HUOB':
            pairs[key] = (exchanges + symbol[5:]).replace('--', '_')

    return pairs


if __name__ == '__main__':
    symbols = ['BINA--ADA--BTC', 'BINA--ADA--USDT']

    pairs = list2dict(symbols)
    for k in pairs.keys():
        print(k, pairs[k])
