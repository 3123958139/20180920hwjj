# -*- coding:utf-8 -*-

#基金规模
FUND_ASSET = 700000

#仓位控制比率
POSITION_RATIO = 0.1

#趋势策略数量
STRATEGY_NUMBER = 10.0

#交易品种数量
SYMBOL_NUMBER = 6.0

#单位交易资金
UNIT_AMOUNT = FUND_ASSET * POSITION_RATIO / STRATEGY_NUMBER / SYMBOL_NUMBER


"""XRP币安交易所数据库没有数据，暂时调整至HUOBI"""
SYMBOL_ALLOCATE = {"OKEXFT":{"BTC": 0.06,
                             "EOS": 0.06,
                             "ETH": 0.06,
                             "XRP": 0.06,
                             "BCH": 0.03,
                             "LTC": 0.03
                           },

               "HUOBI":{"BTC": 0.06,
                        "EOS": 0.06,
                        "ETH": 0.06,
                        "XRP": 0.06,
                        "BCH": 0.03,
                        "LTC": 0.03
                       },

                "BINA":{"BTC": 0.08,
                        "EOS": 0.08,
                        "ETH": 0.08,
                        "XRP": 0.08,
                        "BCC": 0.04,
                        "LTC": 0.04
                       }
                }


def allocate(sym_allocate_dict, unit_amount):
    d = {}
    for exchange in sym_allocate_dict.keys():
        tmp = sym_allocate_dict[exchange]
        d[exchange] = {}
        for k in tmp.keys():
            d[exchange][k] = tmp[k] * unit_amount
    return d

#每个交易所每个品种的资金
STRATEGY_UNIT_AMOUNT = FUND_ASSET * POSITION_RATIO / STRATEGY_NUMBER
UNIT_AMOUNT = allocate(SYMBOL_ALLOCATE, STRATEGY_UNIT_AMOUNT) 

if __name__ == "__main__":
    #策略资金单位资金
    STRATEGY_UNIT_AMOUNT = FUND_ASSET * POSITION_RATIO / STRATEGY_NUMBER

    #OKEX
    UNIT_AMOUNT = allocate(SYMBOL_ALLOCATE, STRATEGY_UNIT_AMOUNT) 
    print("STRATEGY_UNIT_AMOUNT:%r" % STRATEGY_UNIT_AMOUNT)
    print("UNIT_AMOUNT:%r" % UNIT_AMOUNT)
