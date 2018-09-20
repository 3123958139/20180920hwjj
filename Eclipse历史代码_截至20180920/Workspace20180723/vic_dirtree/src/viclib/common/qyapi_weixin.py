# -*- coding: UTF-8 -*-

import time
import sys
import logging
import json

from vic.exchange.common.http import HttpClient


class QyWeixin(HttpClient):
    # ��ҵ΢�źŶ�Ӧid
    corpid = 'wxf81392ac6d39f547'
    # ȫ�ֵ�secret��Ӧ��token�洢
    secrets = {}
    #�����б�
    departments = {}
    #�û��б�
    userlist = {}

    def __init__(self, secret='kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk'):
        '''secretͨѶ¼��'''
        self.__headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
        }
    def __check(self, secret):
        ''' ���secret��token�ǲ��ǹ�����'''
        token = QyWeixin.secrets.get(secret)
        if token == None:
            return False
        diff = time.time()-token['timestamp']
        if diff < token['expires_in']+180:
            return True
        return False

    def __gettoken(self, secret):
        '''��ȡsecret��Ӧ����Ч��token'''
        if(self.__check(secret)):
            return QyWeixin.secrets[secret]['access_token']
        QyWeixin.secrets[secret] = {}
        token = QyWeixin.secrets[secret]
        url ='https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={0}&corpsecret={1}'
        url = url.format(QyWeixin.corpid, secret)
        resp = self.http_request(url, 'GET', None, {})
        if(not resp or resp['errcode']!=0):
            raise Exception('get token fail: ' + str(resp))
        token['expires_in']     = resp['expires_in']
        token['access_token']   = resp['access_token']
        token['timestamp']      = time.time()
        return token['access_token']

    def getdepartment(self, secret):
        '''��ȡ������Ϣ
            secret : kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk (4ͨѶ¼��)
        '''
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token='+access_token
        resp = self.http_request(url, 'GET', None, {})
        if(not resp or resp['errcode']!=0):
            raise Exception('get department fail: ' + str(resp))
        return resp['department']

    def getuser(self, secret, departmentid):
        ''' ��ȡ�û��б�
            secret : kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk (ͨѶ¼��)
        '''
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token={0}&department_id={1}&fetch_child=1'
        url = url.format(access_token, departmentid)
        resp = self.http_request(url, 'GET', None, {})
        if(not resp or resp['errcode']!=0):
            raise Exception('get userlist fail: ' + str(resp))
        return resp['userlist']
    
    def getuserinfo(self, secret, departmentid):
        ''' ��ȡ�û���ϸ��Ϣ
        '''
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token={0}&department_id={1}&fetch_child=1'
        url = url.format(access_token, departmentid)
        resp = self.http_request(url, 'GET', None, {})
        if(not resp or resp['errcode']!=0):
            raise Exception('get userlist fail: ' + str(resp))
        return resp['userlist']
    

    def getuserid(self, secret):

        ''' ��ȡ�����û�����ϸ��Ϣ
            secret : kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk (ͨѶ¼��)
        '''
        userid = []
        departments = self.getdepartment(secret)
        for department in departments:
            users = self.getuser(secret, department['id'])
            userid += [user['userid'] for user in users]
        return userid

    def sendtxt(self, secret, agentid,  message, touser=None, toparty=None, totag=None):
        ''' �����ı���Ϣ��secret��Ӧ��Ӧ��
            toparty touser totag ����ͬʱΪ��
            access_token: ��ӦӦ�õ�
            int agentid : ��ӦӦ�õ�
            message     : ��Ϣ���ݣ��������2048���ֽ�
            touser      : ��ԱID�б���Ϣ�����ߣ�����������á�|���ָ������֧��1000���������������ָ��Ϊ@all���������ҵӦ�õ�ȫ����Ա����
            toparty     : ����ID�б�����������á�|���ָ������֧��100������touserΪ@allʱ���Ա�����
            totag       : ��ǩID�б�����������á�|���ָ������֧��100������touserΪ@allʱ���Ա�����
            return      : {
                errcode  0  0��ʾ�ɹ� 
                errmsg :
                ...
            }
        '''
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + access_token
        
        data = {}
        data['msgtype'] = 'text'
        data['agentid'] = agentid
        data['text'] = {'content': message}
        if touser:
            data['touser'] = touser
        if toparty:
            data['toparty'] = toparty
        data['safe'] = 0
       
        body = json.dumps(data).decode('unicode-escape').encode("utf-8")

        resp = self.http_request(url, 'POST', body, self.__headers)
       
        return resp

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s[%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s'
    )

    secret = 'xzNVWx-_Ub_HwDsWZn3ISOjtbRem56Izkg1ZMUW4z1g'
    agentid = 1000003
    message = 'test'
    touser  = 'Dreamy|Simons|winsen|rickon|jason'
    toparty = 4
    qy = QyWeixin()

    print(qy.sendtxt(secret, agentid, message, touser, toparty))
    
    #��ȡuserid  �� department id
    #print(qy.getuserid(secret))
    #print(qy.getdepartment(secret))







