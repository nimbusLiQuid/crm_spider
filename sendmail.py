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
import json
import datetime

SMTP_SERVER = "smtp.ym.163.com"
SMTP_PORT = 25
SMTP_USERNAME = "crm_robot@baicdata.com"
# SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') or "65b-aWk-Dpn-MaB"
SMTP_PASSWORD = "U2k-MxA-hLZ-d8k"
#U2k-MxA-hLZ-d8k

# 请注意: 在这里的代码中修改 MAILTO_LIST 不再有效了
# 因为在函数generate_mail_to_list_from_wiki_page的调用结果中，
# MAILTO_LIST被修改了
MAILTO_LIST = [
    "林泉<linquan@baicdata.com>",
    "何帅<heshuai@baicdata.com>",
    "董灵瑜<donglingyu@baicdata.com>",
    "郭丽杰<guolijie@baicdata.com>",
    "周露<zhoulu@baicdata.com>",
    "梁宵琦<liangxiaoqi@baicdata.com>"
]
MAIL_FROM = "CRM自动报表<crm_robot@baicdata.com>"
MAIL_CONFIG_URL = 'http://118.178.237.93/bcwiki/doku.php?id=crm:crm_email'


def generate_mail_to_list_from_wiki_page():
    """
    # >>> print json.dumps(generate_mail_to_list_from_wiki_page(), ensure_ascii=False)
    # >>> assert generate_mail_to_list_from_wiki_page() == MAILTO_LIST
    """
    page_lines = []
    start_index, end_index = 0, -1
    with open('/var/www/html/bcwiki/data/pages/crm/crm_email.txt', errors='ignore') as f:
        page_lines = f.read().split('\n')
    for i, line in enumerate(page_lines):
        if '<code>' in line:
            start_index = i + 1
        elif '</code>' in line:
            end_index = i
            break
    # print start_index, end_index
    mail_to_list_lines = page_lines[start_index:end_index]
    # 对邮件列表整形
    checked_mail_list = []
    for email in mail_to_list_lines:
        # fixme: could do more
        if '@' in email:
            checked_mail_list.append(email)
    return mail_to_list_lines

MAILTO_LIST = generate_mail_to_list_from_wiki_page()


def to_html_content(content):
    content = content.replace(' ', '&nbsp;')
    content = content.replace('\n', '<br />')
    content = '<font face="Courier New, Courier, monospace">' + content + '</font>'
    tip = "<hr><p style='color:gray'>如果您不想收到此类邮件，请去<a href='{0}'>邮件设置</a>页面进行退订操作</p>".format(MAIL_CONFIG_URL)
    tip += "<p style='color:gray'>2013-{0} BCData Co,ltd.</p>".format(datetime.date.today().year)
    content += tip
    return content

def sendmail(from_, to_list, subject, content):
    content = to_html_content(content)
    msg = MIMEText(content, _subtype="html", _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = from_
    # using a ", \t" to join will make mail in macOS look fine  -- lin quan
    msg["To"] = ", \t".join(to_list)
    try:
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.sendmail(from_, to_list, msg.as_string())
        smtp.close()
        return True
    except smtplib.SMTPException:
        return False


def send_excel_result(msg, mail_title=None):
    if not mail_title:
        mail_title = '数据导入结果 %s' % time.strftime('%Y-%m-%d %H:%M:%S')
    sendmail(MAIL_FROM, MAILTO_LIST, mail_title, msg)

if __name__ == '__main__':
    # 用main函数启动时，仅为测试发信之用
    MAILTO_LIST = ["linquan@baicdata.com", "donglingyu@baicdata.com"]
    MAILTO_LIST = ["linquan@baicdata.com"]
    send_excel_result(sys.argv[1], sys.argv[2])
