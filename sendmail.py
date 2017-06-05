# coding: utf-8
#!/usr/bin/python
import os
import sys
import re
import smtplib
import subprocess
import threading
import time
import logging
from email.mime.text import MIMEText

SMTP_SERVER     = "smtp.ym.163.com"
SMTP_PORT       = 25

SMTP_USERNAME   = "linquan@baicdata.com"
SMTP_PASSWORD   = "65b-aWk-Dpn-MaB"

MAILTO_LIST     = [
                  "linquan@baicdata.com",
                  "heshuai@baicdata.com",
                  "donglingyu@baicdata.com"
                  ]
# MAILTO_LIST = ['linquan@baicdata.com']
MAIL_FROM       = "林泉的自动报表<linquan@baicdata.com>"


def to_html_content(content):
    content = content.replace(' ', '&nbsp;')
    content = content.replace('\n', '<br />')
    content = '<font face="Courier New, Courier, monospace">' + content + '</font>'
    return content

def sendmail(from_, to_list, subject, content):
    content = to_html_content(content)
    msg = MIMEText(content, _subtype="html", _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = from_
    msg["To"] = ";".join(to_list)
    try:
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.sendmail(from_, to_list, msg.as_string())
        smtp.close()
        return True
    except smtplib.SMTPException:
        return False


def send_excel_result(msg):
    sendmail(MAIL_FROM, MAILTO_LIST, '数据导入结果 %s' % time.strftime('%Y-%m-%d %H:%M:%S'), msg)

if __name__ == '__main__':
    MAILTO_LIST = ["linquan@baicdata.com"]
    sendmail(MAIL_FROM, MAILTO_LIST, '测试101', '+-------+---------------+\n| \xe6\xa0\x87\xe9\xa2\x981 |     erere     |\n+-------+---------------+\n|   1   |      232      |\n|  1213 |     223232    |\n|  dfdf | 2dfdsfds23232 |\n+-------+---------------+')
