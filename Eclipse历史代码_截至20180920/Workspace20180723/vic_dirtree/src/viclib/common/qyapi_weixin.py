# -*- coding: UTF-8 -*-

import time
import sys
import logging
import json

from vic.exchange.common.http import HttpClient


class QyWeixin(HttpClient):
    # 企业微信号对应id
    corpid = 'wxf81392ac6d39f547'
    # 全局的secret对应的token存储
    secrets = {}
    #部门列表
    departments = {}
    #用户列表
    userlist = {}

    def __init__(self, secret='kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk'):
        '''secret通讯录的'''
        self.__headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
        }
    def __check(self, secret):
        ''' 检查secret的token是不是过期了'''
        token = QyWeixin.secrets.get(secret)
        if token == None:
            return False
        diff = time.time()-token['timestamp']
        if diff < token['expires_in']+180:
            return True
        return False

    def __gettoken(self, secret):
        '''获取secret对应的有效的token'''
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
        '''获取部门信息
            secret : kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk (4通讯录的)
        '''
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token='+access_token
        resp = self.http_request(url, 'GET', None, {})
        if(not resp or resp['errcode']!=0):
            raise Exception('get department fail: ' + str(resp))
        return resp['department']

    def getuser(self, secret, departmentid):
        ''' 获取用户列表
            secret : kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk (通讯录的)
        '''
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token={0}&department_id={1}&fetch_child=1'
        url = url.format(access_token, departmentid)
        resp = self.http_request(url, 'GET', None, {})
        if(not resp or resp['errcode']!=0):
            raise Exception('get userlist fail: ' + str(resp))
        return resp['userlist']
    
    def getuserinfo(self, secret, departmentid):
        ''' 获取用户详细信息
        '''
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token={0}&department_id={1}&fetch_child=1'
        url = url.format(access_token, departmentid)
        resp = self.http_request(url, 'GET', None, {})
        if(not resp or resp['errcode']!=0):
            raise Exception('get userlist fail: ' + str(resp))
        return resp['userlist']
    

    def getuserid(self, secret):

        ''' 获取所有用户的详细信息
            secret : kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk (通讯录的)
        '''
        userid = []
        departments = self.getdepartment(secret)
        for department in departments:
            users = self.getuser(secret, department['id'])
            userid += [user['userid'] for user in users]
        return userid

    def sendtxt(self, secret, agentid,  message, touser=None, toparty=None, totag=None):
        ''' 发送文本消息给secret对应的应用
            toparty touser totag 不能同时为空
            access_token: 对应应用的
            int agentid : 对应应用的
            message     : 消息内容，最长不超过2048个字节
            touser      : 成员ID列表（消息接收者，多个接收者用‘|’分隔，最多支持1000个）。特殊情况：指定为@all，则向该企业应用的全部成员发送
            toparty     : 部门ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
            totag       : 标签ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
            return      : {
                errcode  0  0表示成功 
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
    
    #获取userid  和 department id
    #print(qy.getuserid(secret))
    #print(qy.getdepartment(secret))







