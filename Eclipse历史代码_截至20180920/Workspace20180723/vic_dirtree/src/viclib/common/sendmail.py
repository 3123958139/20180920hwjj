# -*- coding: UTF-8 -*-

import datetime  
import os  
import smtplib  
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart  
from email.header import Header

class Email:  
    def __init__(self, _from, _passwd, _to=[], _cc=[]):  
        self.__from     = _from
        self.__passwd   = _passwd  
        self.__port = 465
        self.__address = 'smtp.exmail.qq.com'
        self.__to       = _to
        self.__cc       = _cc  
        
    def set_debug(self, debug):
        '''参数值为1表示开启调试模式,参数值为0关闭调试模式'''
        self.__smtp.set_debuglevel(debug)

    def sendmail(self, title, message, to=[], cc=[], files=[], images=[]):  
        server = smtplib.SMTP_SSL(self.__address, self.__port)  
        server.login(self.__from, self.__passwd)
        mime = MIMEMultipart()  
        if to : self.__to = to
        if cc : self.__cc = cc
        if files : self.__add_files(files, mime)
        if images : self.__add_images(images, mime)
        self.__add_content(message, mime)
        
        mime["Subject"] = Header(title, 'utf-8')
        mime["From"] = self.__from
        mime["To"] = ';'.join(self.__to)
        mime["Cc"] = ";".join(self.__cc)  
        
        server.sendmail("<{0}>".format(self.__from), self.__to+self.__cc, mime.as_string())  
        server.close() 

    def __add_images(self, filenames, mime):
        for filename in filenames:
            self.__add_image(filename.encode('utf8'), mime)
       
    def __add_files(self, filenames, mime):
        for filename in filenames:
            self.__add_file(filename.encode('utf8'), mime)

    def __add_image(self, filename, mime):
        '''  mime : MIMEMultipart '''
        name = filename[filename.rfind('/')+1:]
        fp = open(filename, 'rb')
        content = MIMEImage(fp.read())
        fp.close()
        content.add_header('Content-ID', name)
        mime.attach(content)
        return filename 

    def __add_file(self, filename, mime):
        '''  mime : MIMEMultipart '''
        name = filename[filename.rfind('/')+1:]
        fp = open(filename, 'rb')
        content = MIMEText(fp.read(), 'base64', 'utf-8')
        fp.close()
        content["Content-Type"] = 'application/octet-stream'
        content["Content-Disposition"] = 'attachment; filename="' + name + '"'
        mime.attach(content)

    def __add_content(self, message, mime):
        '''  mime : MIMEMultipart '''
        content = MIMEText(message, "plain", 'utf-8')
        mime.attach(content) 
  
if __name__=="__main__":
    mail = Email('dreamy.zhang@invesmart.cn', 'tm7409TTA')  
    mail.sendmail('title', 'test', ['dreamy.zhang@invesmart.cn'], ['dreamy.zhang@invesmart.cn'], ['./a.txt', u'交易所接入规划(1).xlsx'])

    
    
    
    
    
    
    
    
    
    
    
    
    
    
