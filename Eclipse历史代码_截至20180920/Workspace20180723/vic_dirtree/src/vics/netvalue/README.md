# ����ʹ��˵��
1. ip=47.74.249.178
2. cd /home/ops/dreamy/vics/vics/risk_netvalue  && python oneclick_sh.py XXX

# �Ұ�һ���µ�
�磺 python oneclick_sh.py  bina_order -c eth -tc usdt -q 10 -p 1

## ˵��
1. -c, -tc, -ct  �Ƕ̲���
2. eth, usdt �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-tc     | varchar  | ���ױ���
-q      | varchar  | ��������
-p      | varchar  | ���׼۸�


# �Ұ�һ������
�磺 python oneclick_sh.py  bina_cancel_order -c eth -tc usdt

## ˵��
1. -c, -tc, -ct  �Ƕ̲���
2. eth, usdt �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-tc     | varchar  | ���ױ���


# ���һ���µ�
�磺 python oneclick_sh.py  huobi_order -c iota -tc usdt -q 3 -p 3 -o 'sell-limit'

## ˵��
1. -c, -tc, -ct, -q, -p, -o  �Ƕ̲���
2. eth, usdt �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-tc     | varchar  | ���ױ���
-q      | varchar  | ��������
-p      | varchar  | ���׼۸�
-o      | varchar  | �������� buy-market:�м���, sell-market:�м���, buy-limit:�޼���, sell-limit:�޼���, buy-ioc:IOC��, sell-ioc:IOC����


# ���һ������
�磺 python oneclick_sh.py  huobi_cancel_order -c eth -tc usdt

## ˵��
1. -c, -tc, -ct  �Ƕ̲���
2. eth, usdt �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-tc     | varchar  | ���ױ���


# okexһ���µ�
�磺 python oneclick_sh.py  okex_order -c eth -tc usdt  -a 1 -p 1 -tt buy

## ˵��
1. -c, -tc, -a, -p, -tt�Ƕ̲���
2. eth, usdt, 1, 1, buy �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-tc     | varchar  | ���ױ���
-a      | varchar  | ��������
-p      | varchar  | ���׼۸�
-tt     | varchar  | �����ͣ��޼۵�(buy/sell) �м۵�(buy_market/sell_market)


# okexһ������
�磺 python oneclick_sh.py  okex_cancel_order -c eth -tc usdt

## ˵��
1. -c, -tc, -ct  �Ƕ̲���
2. eth, usdt �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-tc     | varchar  | ���ױ���


# okex��Լһ���µ�
�磺 python oneclick_sh.py  okexft_order -c eth -tc usd -ct this_week -tt 1 -p 400 -q 1

## ˵��
1. -c, -tc, -a, -p, -tt�Ƕ̲���
2. eth, usdt, 1, 1, buy �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-tc     | varchar  | ���ױ���
-ct     | varchar  | ��Լ����: this_week:���� next_week:���� quarter:����
-tt     | varchar  | ��������: 1:����; 2������; 3:ƽ��; 4��ƽ��
-p      | varchar  | ���׼۸�
-q      | varchar  | ��������


# okex��Լһ������
�磺 python oneclick_sh.py  okex_future_cancel -c eth -tc usdt -ct this_week

## ˵��
1. -c, -tc, -ct  �Ƕ̲���
2. eth, usdt, this_week �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-tc     | varchar  | ���ױ���
-ct     | varchar  | ��Լ����: this_week:���� next_week:���� quarter:����




# �˻�һ������
�磺python accounts_sh.py onekey_reduce -c eth -m 1/3 -t bina

## ˵��
1.-c, -m, -t  �Ƕ̲���
2. eth, 1/3, bina �Ƕ�Ӧ������ֵ

param   | type     | desc
--------|----------|---------------------
-c      | varchar  | ����
-m      | varchar  | ���ֵı���
-t      | varchar  | ���ֵĽ�����: bina:�Ұ� huobi:��� okex:okex collect:����������




