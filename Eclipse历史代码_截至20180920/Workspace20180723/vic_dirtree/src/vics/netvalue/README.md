# 工具使用说明
1. ip=47.74.249.178
2. cd /home/ops/dreamy/vics/vics/risk_netvalue  && python oneclick_sh.py XXX

# 币安一键下单
如： python oneclick_sh.py  bina_order -c eth -tc usdt -q 10 -p 1

## 说明
1. -c, -tc, -ct  是短参数
2. eth, usdt 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-tc     | varchar  | 交易币种
-q      | varchar  | 交易数量
-p      | varchar  | 交易价格


# 币安一键撤单
如： python oneclick_sh.py  bina_cancel_order -c eth -tc usdt

## 说明
1. -c, -tc, -ct  是短参数
2. eth, usdt 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-tc     | varchar  | 交易币种


# 火币一键下单
如： python oneclick_sh.py  huobi_order -c iota -tc usdt -q 3 -p 3 -o 'sell-limit'

## 说明
1. -c, -tc, -ct, -q, -p, -o  是短参数
2. eth, usdt 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-tc     | varchar  | 交易币种
-q      | varchar  | 交易数量
-p      | varchar  | 交易价格
-o      | varchar  | 订单类型 buy-market:市价买, sell-market:市价卖, buy-limit:限价买, sell-limit:限价卖, buy-ioc:IOC买单, sell-ioc:IOC卖单


# 火币一键撤单
如： python oneclick_sh.py  huobi_cancel_order -c eth -tc usdt

## 说明
1. -c, -tc, -ct  是短参数
2. eth, usdt 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-tc     | varchar  | 交易币种


# okex一键下单
如： python oneclick_sh.py  okex_order -c eth -tc usdt  -a 1 -p 1 -tt buy

## 说明
1. -c, -tc, -a, -p, -tt是短参数
2. eth, usdt, 1, 1, buy 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-tc     | varchar  | 交易币种
-a      | varchar  | 交易数量
-p      | varchar  | 交易价格
-tt     | varchar  | 卖类型：限价单(buy/sell) 市价单(buy_market/sell_market)


# okex一键撤单
如： python oneclick_sh.py  okex_cancel_order -c eth -tc usdt

## 说明
1. -c, -tc, -ct  是短参数
2. eth, usdt 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-tc     | varchar  | 交易币种


# okex合约一键下单
如： python oneclick_sh.py  okexft_order -c eth -tc usd -ct this_week -tt 1 -p 400 -q 1

## 说明
1. -c, -tc, -a, -p, -tt是短参数
2. eth, usdt, 1, 1, buy 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-tc     | varchar  | 交易币种
-ct     | varchar  | 合约类型: this_week:当周 next_week:下周 quarter:季度
-tt     | varchar  | 交易类型: 1:开多; 2：开空; 3:平多; 4：平空
-p      | varchar  | 交易价格
-q      | varchar  | 交易数量


# okex合约一键撤单
如： python oneclick_sh.py  okex_future_cancel -c eth -tc usdt -ct this_week

## 说明
1. -c, -tc, -ct  是短参数
2. eth, usdt, this_week 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-tc     | varchar  | 交易币种
-ct     | varchar  | 合约类型: this_week:当周 next_week:下周 quarter:季度




# 账户一键减仓
如：python accounts_sh.py onekey_reduce -c eth -m 1/3 -t bina

## 说明
1.-c, -m, -t  是短参数
2. eth, 1/3, bina 是对应参数的值

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | 币种
-m      | varchar  | 减仓的倍数
-t      | varchar  | 减仓的交易所: bina:币安 huobi:火币 okex:okex collect:三个交易所




