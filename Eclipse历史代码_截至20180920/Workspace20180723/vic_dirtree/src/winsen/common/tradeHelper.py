# *-* coding:utf8 *-*

from numpy import floor

OKEXFT = "OKEXFT"
OKEX   = "OKEX"
MARGINRATIO = 0.5
NOT_ENOUGH_MSG      = "[%s] 策略[%s] 品种[%s]余额不足."
NOT_ENOUGH_USDT_MSG = "[%s] 策略[%s] 交易所[%s] USDT余额不足."
DB_POS_ERR_MSG      = "[%s] 策略[%s] 获取数据库持仓失败."
FILLED_MSG          = "[%s] 策略[%s] 周期[%s] 品种[%s] 方向[%s] 量[%s] 成交."
INIT_MSG            = "[%s] 策略[%s] 周期[%s] 品种[%s]开始监控."
END_MSG             = "[%s] 策略[%s] 周期[%s] 品种[%s]已停止."
CANCEL_ORDER_MSG    = "[%s] 策略[%s] 周期[%s] 品种[%s] 尝试撤单[%s]."
LOAD_DATA_OK        = "[%s] 策略[%s] 周期[%s] 成功加载历史数据."
START_LOAD_DATA     = "[%s] 策略[%s] 周期[%s] 开始加载历史数据."
NOT_IN_CAPITAL_MSG  = "[%s] 策略[%s] 周期[%s] 品种[%s]不在资产配置内."
STRATEGY_ALIVE_MSG  = "[%s] strategy=%s period=%s is alive."
NOT_IN_SIGANL       = "[%s] 策略[%s] 周期[%s] 品种[%s]不在监控范围."
NOT_ENOUGH_MARGIN   = "[%s] 策略[%s] 周期[%s] 品种[%s]保证金不足." 
SUBMIT_MSG          = "[%s] 策略[%s] 周期[%s] 品种[%s] SUBMITTED."
CANCEL_MSG          = "[%s] 策略[%s] 周期[%s] 品种[%s] CANCELLED."
TRADED_MSG          = "[%s] 策略[%s] 周期[%s] 品种[%s] TRADED."
PART_FILLED_MSG     = "[%s] 策略[%s] 周期[%s] 品种[%s] PARTIALLY FILLED."
UPDATE_DB_MSG       = "[%s] 策略[%s] 周期[%s] 品种[%s] UPDATE DATABASE."
QTY_PRECISE         = 2
FEE_RATIO           = 0.003


def usdtCash(group, balance):
    """
    """
    key = group + "--USDT"
    if key in balance.keys():
        return floor(100 * balance[key].available()) / 100.0 
    else:
        return 0

def dealBalance(abbr, balance):
    """
    处理balance,补全为0的情况
    若不为0,则向下保留两位小数
    """
    if abbr in balance.keys():
        thisBalance = floor(100 * balance[abbr].available()) / 100.0
    else:
        thisBalance = 0

    return thisBalance



def okexFtrSym(abbr):
    """
    """
    ftrSym = abbr.lower() + "_usd"
    return ftrSym

def relateSymbol(group, data):
    """相关代码处理"""
    symbol = data.symbol()
    if "--" in symbol:
        abbr = symbol.split("--")[1]
        balanceAbbr = group + "--" + abbr
    else:
        abbr = symbol
        balanceAbbr = group + "--" + symbol
    return symbol, abbr, balanceAbbr

def multiplier(symbol):
    '''
    每张合约的价值
    '''
    if "BTC" in symbol.upper(): 
        base = 100
    else: 
        base = 10
    return base

def qty2piece(symbol, price, qty):
    """
    将交易数量转换为合约张数
    """
    base = multiplier(symbol)
    piece = abs(qty) * price / base
    piece = max(1, int(piece))
    return piece

def piece2qty(symbol, price, piece, leverage=10):
    """
    将合约张数转换为数量
    """
    base = multiplier(symbol)
    qty = abs(piece) * base / price / leverage
    return qty


def mapSymbol(group, symbol, period="TQ"):
    """OKEX Exchange symbol convert"""
    if group not in OKEXFT:
        return symbol

    if group == OKEXFT:
        mirrorSymbol = OKEX + "--" + symbol.split("--")[1] + "--USDT"
    else:
        mirrorSymbol = OKEXFT + "--" + symbol.split("--")[1] + "--" + period 
    return mirrorSymbol


def getFuturePosition(okexHttp, symbol):
    '''
    获取指定品种的期货持仓
    RETURN:DICTIONARY
    {'quarter': {u'sell_available': 0, 
                 u'create_date': 1527589732000, 
                 u'contract_id': 201806290010035, 
                 u'buy_price_avg': 115.969, 
                 u'sell_price_cost': 0, 
                 u'sell_price_avg': 0, 
                 u'symbol': 
                 u'ltc_usd', 
                 u'buy_profit_real': -0.00023713, 
                 u'sell_amount': 0, 
                 u'sell_profit_real': -0.00023713, 
                 u'buy_amount': 11, 
                 u'buy_price_cost': 115.969, 
                 u'contract_type': u'quarter', 
                 u'lever_rate': 10, 
                 u'buy_available': 11}, 
    'this_week': None, 
    'next_week': None}

    '''
    symbol = symbol.lower() + "_usd"
    future = {}
    termList = ["this_week", "next_week", "quarter"]
    for t in termList:
        tmp = okexHttp.future_position(symbol, t)
        if tmp["result"]:
            if len(tmp["holding"]) > 0:
                future[t] = tmp["holding"][0]
            else:
                future[t] = None
        else:
            future[t] = None
    return future


def futureHolding(http, ftrSym, side="short", term="quarter"):
    """
    side: "long"/"short"
    term: "quarter" "this_week", "next_week"
    """
    if side == "long":
        directionAmount = "buy_amount"
    else:
        directionAmount = "sell_amount"

    futures = getFuturePosition(http, ftrSym)
    if futures[term] is not None:
        qty = futures[term][directionAmount]
    else:
        qty = 0

    return qty


def orderQtyConvert(order, dbQty, volume):
    """
    dbQty:数据库持仓
    order:
    volume:
    """
    if order.isbuy():
        volume = volume*(1-FEE_RATIO) 
        dbQty = dbQty + volume
    elif order.issell():
        dbQty = dbQty - volume
        volume = -volume
    return round(dbQty, QTY_PRECISE), volume

def orderSideConvert(order):
    """
    """
    if order.isbuy():
        return "buy"
    elif order.issell():
        return  "sell"

def okexCheck(group):
    """
    """
    if group in [OKEXFT]:
        return True
    else:
        return False


def mySpread(data):
    """
    """
    ask = data.ask_prices()[0]
    bid = data.bid_prices()[0]
    spread = round(abs(ask/bid)-1, 4) 
    return ask, bid, spread


def groupConvert(group):
    """
    """
    if group == OKEX:
        return OKEXFT
    else:
        return group

def transferSiganlQty(group, symbol, signalDict):
    """
    """
    if group == OKEXFT:
        symbol = mapSymbol(group, symbol)
    qty = signalDict[symbol]["qty"]
    return qty


def doubleMapSymbol(group, symbol):
    """
    """
    if group == OKEX:
        spotSymbol   = symbol
        mirrorSymbol = mapSymbol(group, symbol)
    elif group == OKEXFT:
        mirrorSymbol = symbol
        spotSymbol   = mapSymbol(group, symbol)
    return spotSymbol, mirrorSymbol


def qtyPrecise(symbol, qty):
    """
    """
    if "BTC" not in symbol.upper():
        return max(round(qty, QTY_PRECISE))
