# coding:utf-8
try:
    import pandas as pd
    from sqlalchemy import create_engine
    import matplotlib.pyplot as plt
    import time
    import poplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    import email
    import smtplib
    import datetime
    from email.header import Header
    import seaborn as sns
except Exception as e:
    print(e)
    pass


class AutoSendBW163Email(object):
    '''实现每天的净值更新及净值图生成并由163邮箱发送给客户
    '''

    def __init__(self):
        self._engine = create_engine('mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/david?charset=utf8&autocommit=true')

    def _start(self):
        self._con = self._engine.connect()

    def _xls_to_mysql(self, xls='BW1_NETVALUE.xlsx', sheetName='BW1'):
        '''临时性的将excel的数据导入到mysql，只做一次
        '''
        df = pd.read_excel(io=xls, sheet_name=sheetName)
        df.to_sql('BW1_NETVALUE', con=self._con, schema='david', index=False, if_exists='replace', chunksize=500)

    def _update_sql_netvalue(self, given={}, day='2018-09-20 00:00:00'):
        '''这个函数用于更新当天记录的
        '''
        # 首先看given是否空，非空指手动给记录，空值则根据数据表进行合成更新，
        # day改造为当前18:00:00前最近的记录，
        # BW1_BASE_DATA用于更新BTC_USDT。
        if len(given) > 0:
            # update ......
            return given
        if day:
            day = day[:10]+' 18:00:00'
        else:
            import datetime
            day = datetime.datetime.now().strftime('%Y-%m-%d 18:00:00')
        
        INVESTMENT_CHANGE = 0.0
        SHARE_CHANGE      = 0.0
        
        # 根据BW1_BASE_DATA计算最近一条usdt总额和btc总额
        query = """SELECT ts, total_account_usdtvalue FROM david.BW1_STAT WHERE ts = 
        (SELECT ts FROM david.BW1_STAT WHERE ts < '%s' ORDER BY ts DESC LIMIT 1);
        """ % day
        df = pd.read_sql(query, self._con)
        DATE        = df['ts'].astype(str).values[0][:10]+' 00:00:00'
        ASSET_TOTAL = df['total_account_usdtvalue'].values[0]

        query = """
        SELECT
	        AVG( usdt / btc ) AS btc_usdt
        FROM
	        david.BW1_BASE_DATA 
        WHERE
            usdt > 1000 
            AND ts = '%s';
        """ % df['ts'].astype(str).values[0]
        df = pd.read_sql(query, self._con)
        BTC_USDT = df['btc_usdt'].values[0]       

        df = pd.read_sql_table('BW1_NETVALUE', self._con, schema='david')
        SHARE_TOTAL      = df['share_change'].sum()+SHARE_CHANGE
        INVESTMENT_TOTAL = df['investment_change'].sum()+INVESTMENT_CHANGE
        MANAGEMENT_FEE   = df['asset_net'].values[-1]*2/100/365
        ASSET_NET        = ASSET_TOTAL-df['management_fees'].sum()-MANAGEMENT_FEE
        UNITNET_USDT     = ASSET_NET/ASSET_TOTAL
        UNITNET_BTC      = BTC_USDT/df[df['date']=='2018-04-23 00:00:00']['btc_usdt'].values[0]
        PROFIT_DAY       = UNITNET_USDT/df['btc_usdt'].values[-1]-1
        PROFIT_TOTAL     = (UNITNET_USDT-df[df['date']=='2018-04-23 00:00:00']['unitnet_usdt'].values[0])*100

        # 如果是手动更新，可以直接写一条记录出来或者在
        sql_update_data = [DATE, UNITNET_USDT, UNITNET_BTC, PROFIT_DAY, PROFIT_TOTAL, INVESTMENT_TOTAL, INVESTMENT_CHANGE, SHARE_TOTAL, SHARE_CHANGE, ASSET_TOTAL, ASSET_NET, MANAGEMENT_FEE, BTC_USDT]
        print('[DATE, UNITNET_USDT, UNITNET_BTC, PROFIT_DAY, PROFIT_TOTAL, INVESTMENT_TOTAL, INVESTMENT_CHANGE, SHARE_TOTAL, SHARE_CHANGE, ASSET_TOTAL, ASSET_NET, MANAGEMENT_FEE, BTC_USDT]\n', sql_update_data)




    def _fill_sql_netvalue(self, day=''):
        '''该函数用于填充期间缺失的
        '''
        # 思路是假设传入的day是current day，然后调用函数进行更新
        self._update_sql_netvalue(day)

        

    def _get_sql_unitnet(self):
        '''提取date、unitnet_usdt、unitnet_btc出来画图
        '''
        # 使用pandas的grouper填充缺失日期段,
        # 然后两个df做差得到缺失的日期list，
        # 然后根据缺失date调用函数进行填充，注意这里要求顺序填充，如果上一根填充出错就停止，
        # 最后最后才读取完整的unitnet。
        query = """SELECT date FROM david.BW1_NETVALUE ORDER BY date;
        """
        df = pd.read_sql(query, self._con)
        df['date'] = pd.to_datetime(df['date'])
        grouper = pd.Grouper(key='date', freq='1D')
        df_ffill = df.groupby(grouper).first().ffill().reset_index()
        date_lost = sorted(list(set(df_ffill['date'].astype(str).values)-set(df['date'].astype(str).values)))

        if len(date_lost) > 0:
            for d in date_lost:
                try:
                    self._fill_sql_netvalue(d)
                except Exception as e:
                    raise e

        query = """SELECT date, unitnet_usdt, unitnet_btc FROM david.BW1_NETVALUE ORDER BY date;
        """
        return pd.read_sql(query, self._con)

    def _plot(self):
        '''
        '''
        # 从mysql读取净值，
        # 设置date为index，
        # 画图修改好格式，        
        sns.set_style("whitegrid")
        df = self._get_sql_unitnet()
        df.set_index('date', inplace=True)
        df.plot(title='Net Value of BW1')
        plt.savefig('BW1_NETVALUE_PIC.png')

    def _send_163email(self):
        # ��ǰ����
        now = datetime.datetime.now().strftime("%Y.%m.%d")
        # ��������
        _user = "m18807739832@163.com"
        _pwd = "test123456"
        # �����¼
        sent = smtplib.SMTP_SSL('smtp.163.com', 465)
        sent.login(_user, _pwd)

        def add_image(path, imgid):
            '''
            '''
            with open(path, 'rb') as img:
                msg_image = MIMEImage(img.read())
                msg_image.add_header('Content-ID', imgid)
            return msg_image

        content = MIMEMultipart('related')
        attach_img = add_image('BW1_NETVALUE_PIC.jpg', 'BW1')
        attach_img['Content-Disposition'] = 'attachment;filename="BW1_NETVALUE_PIC.jpg"'.decode(
            'utf-8').encode('gb18030')
        content.attach(attach_img)
        attach_txt = MIMEText(
            """Dear All,\nBelows are net charts of BW fund today, please review the attachment!""")
        content.attach(attach_txt)
        try:
            to = ['winsen.huang@invesmart.cn']
            content['Subject'] = now + ' Net charts of BW fund'
            content['From'] = 'm18807739832@163.com'
            content['To'] = ','.join(to)
            sent.sendmail('m18807739832@163.com', to, content.as_string())
            sent.close()
        except Exception as e:
            print(e)

    def _end(self):
        self._con.close()

    def main(self):
        self._start()
        # self._update_sql_netvalue()
        self._plot()
        # self._send_163email()
        self._end()


if __name__ == '__main__':
    obj = AutoSendBW163Email()
    obj.main()
