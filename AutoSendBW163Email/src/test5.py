def ___get_currency_price(list_currency=['BTC', 'EOS', 'ETH', 'XRP', 'BCH', 'LTC']):
                import urllib.request
                cur_price_dict = {}
                headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}
                for cur in list_currency:                    
                    req = urllib.request.Request(url='https://www.okex.com/api/v1/ticker.do?symbol=%s_usdt' % cur.lower(), headers=headers) 
                    cur_data = eval(urllib.request.urlopen(req).read())
                    print(cur_data)
                    cur_price_dict[cur] = float(cur_data['ticker']['buy'])
                return cur_price_dict

print(___get_currency_price())