#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

import json
import sys
import time

from david_http import HttpClient


class QyWeixin(HttpClient):
    corpid = 'wxf81392ac6d39f547'
    secrets = {}
    departments = {}
    userlist = {}

    def __init__(self, secret='kQZhhsJaiAsoDm69M2PehVrIIkLeAOeR3dbAGDyHnxk'):
        """
        """
        self.__headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def __check(self, secret):
        """
        """
        token = QyWeixin.secrets.get(secret)

        if token == None:
            return False

        diff = time.time() - token['timestamp']

        if diff < token['expires_in'] + 180:
            return True
        return False

    def __gettoken(self, secret):
        """
        """
        if(self.__check(secret)):
            return QyWeixin.secrets[secret]['access_token']

        QyWeixin.secrets[secret] = {}
        token = QyWeixin.secrets[secret]
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={0}&corpsecret={1}'
        url = url.format(QyWeixin.corpid, secret)
        resp = self.http_request(url, 'GET', None, {})

        if(not resp or resp['errcode'] != 0):
            raise Exception('get token fail: ' + str(resp))

        token['expires_in'] = resp['expires_in']
        token['access_token'] = resp['access_token']
        token['timestamp'] = time.time()

        return token['access_token']

    def getdepartment(self, secret):
        """
        """
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=' + access_token
        resp = self.http_request(url, 'GET', None, {})

        if(not resp or resp['errcode'] != 0):
            raise Exception('get department fail: ' + str(resp))

        return resp['department']

    def getuser(self, secret, departmentid):
        """
        """
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token={0}&department_id={1}&fetch_child=1'
        url = url.format(access_token, departmentid)
        resp = self.http_request(url, 'GET', None, {})

        if(not resp or resp['errcode'] != 0):
            raise Exception('get userlist fail: ' + str(resp))

        return resp['userlist']

    def getuserinfo(self, secret, departmentid):
        """
        """
        access_token = self.__gettoken(secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token={0}&department_id={1}&fetch_child=1'
        url = url.format(access_token, departmentid)
        resp = self.http_request(url, 'GET', None, {})
        if(not resp or resp['errcode'] != 0):
            raise Exception('get userlist fail: ' + str(resp))

        return resp['userlist']

    def getuserid(self, secret):
        """
        """
        userid = []
        departments = self.getdepartment(secret)
        for department in departments:
            users = self.getuser(secret, department['id'])
            userid += [user['userid'] for user in users]

        return userid

    def sendtxt(self, secret, agentid,  message, touser=None, toparty=None, totag=None):
        """
        """
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

        body = json.dumps(data)  # .decode('unicode-escape').encode("utf-8")

        resp = self.http_request(url, 'POST', body, self.__headers)

        return resp


if __name__ == "__main__":
    """
    """
    secret = 'xzNVWx-_Ub_HwDsWZn3ISOjtbRem56Izkg1ZMUW4z1g'
    agentid = 1000003
    message = 'test message'
    touser = 'David'
    toparty = 4

    qy = QyWeixin()

    print(qy.getdepartment(secret))
#     print(qy.sendtxt(secret, agentid, message, touser, toparty))
