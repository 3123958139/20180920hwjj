from vic.core.strategy import StrategyBase
from vic.core.livebroker import Broker
from vic.core.livefeed import Feed
from vic.core.struct import DateType
from vic.core.struct import Bar

from  vic.exchange.vic_okex.okex_ws_thread         import OkexWsThread
from  vic.exchange.vic_okex.okex_http_thread       import OkexHttpThread
from  vic.exchange.vic_huobi.huobi_ws_thread       import HuobiWsThread
from  vic.exchange.vic_huobi.huobi_http_thread     import HuobiHttpThread
from  vic.exchange.vic_binance.binance_ws_thread   import BinaWsThread
from  vic.exchange.vic_binance.binance_http_thread import BinaHttpThread
from  vic.exchange.vic_okex.okexft_ws_thread       import OkexftWsThread
from  vic.exchange.vic_okex.okexft_http_thread     import OkexftHttpThread
from  vic.exchange.vic_bitmex.bitmex_ws_thread     import BitmexWsThread
from  vic.exchange.vic_bitmex.bitmex_http_thread   import BitmexHttpThread

from vics.lib.mysql_pool import MysqlPool


class Strategy(StrategyBase):
    def __init__(self, queue):
        super(Strategy, self).__init__(queue)
    
    def init(self):
        super(Strategy, self).init()
        self.resample(1*60,  self.onbar)
        self.resample(5*60, self.onbar)
        self.resample(60*60, self.onbar)
        self.resample(24*60*60, self.onbar)

    def onorder(self, handle, group, data):
        logging.info('%r %r', group, data)

    def ontrade(self, handle, group, data):
        logging.info('%r %r', group, data)

    def onposition(self, handle, group, data):
        pass

    def onbalance(self, handle, group, data):
        logging.info('%r %r', group, data)
    
    def onsnap(self, handle, group, data):
        logging.info('%r', data)

    def onticker(self, handle, group, data):
        #logging.info('%r %r %r %r %r %r', data['symbol'][-1], data['tradeid'][-1], data['price'][-1], data['volume'][-1], data['side'][-1], data['timestamp'][-1])
        pass

    def onorderbook(self, handle, group, data):
        pass
        #logging.info('%r %r', group, data)

    def onbar(self, handle, group, period, data):
        logging.info('%r %r %r %r %r %r %r %r %r', group, period, data['symbol'][-1], data['timestamp'][-1], data['high'][-1], data['open'][-1], data['low'][-1], data['close'][-1], data['volume'][-1])
        #self.get_trade_handle('OKEX').submitOrder(self, symbol, order_type, price_type, limit_price, order_quantity):

    def onstart(self):
        ''' 这里表示插件启动之后开始接收插件行情 此时加载历史行情(ticker/kline)
            如果是kline 每组时间推送完毕 推送一个时间戳结束
            append/pop
            这里appendleft()
            self.get_deque().appendleft((DateType.ON_MKT_KLINE, 'OKEX', {kline period:60}))
            self.get_deque().appendleft((DateType.ON_TIMESTAMP, 'OKEX', {'timestamp' : 1332344344344}))
        '''
        #等待60s让行接收1min中的trade数据衔接
        #time.sleep(60)
        logging.info('start load data.')
        mysql = MysqlPool('47.74.179.216', 3308, 'ops', 'ops!@#9988', 'vic', 'utf8')
        datas = mysql.getAll('select symbol, unix_timestamp(ts) as timestamp, high, low, open, close, quantity as volume, turnover as amount, openinterest  from vic_1mk.1mk where symbol like "BITM--%" and ts>"2018-05-07 05:41:00"; ')
        if not datas : return
        timestamp = 0
        datas = list(datas)
        datas.reverse()
        for data in datas:
            group = data['symbol'].split('--')[0]
            if not self.check(group, data['symbol']) : continue
            data['period'] = 60
            data['timestamp'] = (data['timestamp'] + 8*3600) * 1000
            self.get_deque().appendleft((DateType.ON_MKT_KLINE, group, Bar(data)))
            if(timestamp and timestamp<data['timestamp']): 
                self.get_deque().appendleft((DateType.ON_TIMESTAMP, group, {'timestamp': timestamp}))
            timestamp = data['timestamp']
        mysql.dispose()
        logging.info('load history data ok.')

if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(asctime)s[%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s'
    )

    queue = Queue.deque()
    strategy = Strategy(queue)
  
    http        = "https://www.okex.com/api/v1"
    wss         = 'wss://real.okex.com:10440/websocket/okexapi'
    apiKey      = "db98cb7e-71c4-442d-bf45-8c6ab05a4c1c"
    apiSecret   = "4A5F6437B9DE1A2B16E80FC0018C8515"
    channels    = ['OKEXFT--BTC--TW', 'OKEXFT--LTC--TW', 'OKEXFT--ETH--TW', 'OKEXFT--ETC--TW', 'OKEXFT--BCH--TW', 'OKEXFT--BTC--NW', 'OKEXFT--LTC--NW', 'OKEXFT--ETH--NW', 'OKEXFT--ETC--NW', 'OKEXFT--BCH--NW', 'OKEXFT--BTC--TQ', 'OKEXFT--LTC--TQ', 'OKEXFT--ETH--TQ', 'OKEXFT--ETC--TQ', 'OKEXFT--BCH--TQ']
    okexftws    = OkexftWsThread(wss, channels, None, None, queue, 'OKEXFT')
    okexfthttp  = OkexftHttpThread(http, wss, channels, apiKey, apiSecret, queue, 'OKEXFT')
    strategy.set_handle_thread(type=Strategy.MARKET, group='OKEXFT', plugin=okexftws, maxlen=100)
    strategy.set_handle_thread(type=Strategy.TRADE, group='OKEXFT', plugin=okexfthttp, bit={})

 
    strategy.run()





