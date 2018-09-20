# coding:utf-8
'''
from coinapi_v1 import CoinAPIv1

test_key = 'EA8CF467-3ECD-42D6-A59E-97D908AEB57D'  # key1
# test_key = '778C65A3-E842-4C10-B5FF-C1AF0F56E78E'  # key2
# test_key = 'F998EBA9-86E5-411A-B434-45D51B6FCBFE'  # key3
api = CoinAPIv1(test_key)

data = api.ohlcv_historical_data('BITFINEX_SPOT_ETC_USD', {'period_id': '1HRS',
                                                           'time_start': '2018-06-05T10:00:00',
                                                           'time_end': '2018-06-05T12:00:00'})
print(data)
'''
import datetime

from coinapi_v1 import CoinAPIv1


test_key = 'EA8CF467-3ECD-42D6-A59E-97D908AEB57D'

api = CoinAPIv1(test_key)
exchanges = api.metadata_list_exchanges()

print('Exchanges')
for exchange in exchanges:
    print('Exchange ID: %s' % exchange['exchange_id'])
    print('Exchange website: %s' % exchange['website'])
    print('Exchange name: %s' % exchange['name'])