# coding: utf-8

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
import datetime

# 设置smtplib所需的参数
# 下面的发件人，收件人是用于邮件传输的。
smtpserver = 'smtp.163.com'
username = 'm18807739832@163.com'
password = 'test123456'
sender = '2074899545@qq.com'
# 收件人为多个收件人
receiver = ['3123958139@qq.com']
# 通过Header对象编码的文本，包含utf-8编码信息和Base64编码信息。以下中文名测试ok
subject = '中文标题'
subject = Header(subject, 'utf-8').encode()

# 构造邮件对象MIMEMultipart对象
# 下面的主题，发件人，收件人，日期是显示在邮件页面上的。
msg = MIMEMultipart('mixed')
msg['Subject'] = subject
msg['From'] = '2074899545@qq.com <2074899545@qq.com>'
# 收件人为多个收件人,通过join将列表转换为以;为间隔的字符串
msg['To'] = ";".join(receiver)
msg['Date'] = str(datetime.datetime.now())

# 构造文字内容
text = "Hi!\nHow are you?"
text_plain = MIMEText(text, 'plain', 'utf-8')
msg.attach(text_plain)

# 构造图片链接
sendimagefile = open('BW1_NETVALUE_PIC.jpg', 'rb').read()
image = MIMEImage(sendimagefile)
image.add_header('Content-ID', '<image1>')
image["Content-Disposition"] = 'attachment; filename="BW1_NETVALUE.jpg"'
msg.attach(image)

# 构造html
# 发送正文中的图片:由于包含未被许可的信息，网易邮箱定义为垃圾邮件，报554 DT:SPM ：<p><img src="cid:image1"></p>
html = """
<html>  
  <head></head>  
  <body>  
    <p>Hi!<br>  
       How are you?<br>  
       Here is the <a href="http://www.baidu.com">link</a> you wanted.<br> 
    </p> 
  </body>  
</html>  
"""
text_html = MIMEText(html, 'html', 'utf-8')
text_html["Content-Disposition"] = 'attachment; filename="texthtml.html"'
msg.attach(text_html)


# 构造附件
sendfile = open('BW1_NETVALUE_PIC.jpg', 'rb').read()
text_att = MIMEText(sendfile, 'base64', 'utf-8')
text_att["Content-Type"] = 'application/octet-stream'
# 以下附件可以重命名成aaa.txt
#text_att["Content-Disposition"] = 'attachment; filename="aaa.txt"'
# 另一种实现方式
text_att.add_header('Content-Disposition', 'attachment', filename='aaa.txt')
# 以下中文测试不ok
#text_att["Content-Disposition"] = u'attachment; filename="中文附件.txt"'.decode('utf-8')
msg.attach(text_att)

# 发送邮件
smtp = smtplib.SMTP()
smtp.connect('smtp.qq.com')
# 我们用set_debuglevel(1)就可以打印出和SMTP服务器交互的所有信息。
smtp.set_debuglevel(1)
smtp.login(username, password)
smtp.sendmail(sender, receiver, msg.as_string())
smtp.quit()
