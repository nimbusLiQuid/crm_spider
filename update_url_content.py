#!/usr/bin/python3
#! coding: utf-8

import pymysql.cursors
import sys
import time
sys.path.append('.')
from jieba import analyse
# Connect to the database
from sendmail import send_excel_result
import re
import prettytable
from url_utility import *


valid_pattern = re.compile(u'[\u0030-\u0039\u0041-\u005a\u0061-\u007a\u4e00-\u9fa5()\',]+')

connection = pymysql.connect(host='115.29.175.16',
                             user='crm_online',
                             password='cout<<7zvzOFMCnx14MfjQ',
                             db='thinkphp_crm_yun',
                             port=3306,
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)

cursor = connection.cursor()

local_connection = pymysql.connect(host='localhost',
                                   user='root',
                                   password='meeChoo7',
                                   db='crm_website',
                                   port=3306,
                                   charset='utf8',
                                   cursorclass=pymysql.cursors.DictCursor)

local_cursor = local_connection.cursor()

def run(sql):
    #print('----', sql, '-----')
    if not sql:
        return
    affected_rows = cursor.execute(sql)
    data = cursor.fetchall()
    sys.stderr.write('crm: ==> %d rows.\n' % affected_rows)
    #print(data)
    return data


def lrun(sql):
    if not sql:
        return
    #print('----', sql, '-----')
    affected_rows = local_cursor.execute(sql)
    data = local_cursor.fetchall()
    sys.stderr.write('spider: ==> %d rows.\n' % affected_rows)
    #print(data)
    return data

"""
+-----------+------------------+------+-----+---------+----------------+
| Field     | Type             | Null | Key | Default | Extra          |
+-----------+------------------+------+-----+---------+----------------+
| id        | int(11) unsigned | NO   | PRI | NULL    | auto_increment |
| url       | text             | NO   |     | NULL    |                |
| timestamp | int(11)          | YES  |     | NULL    |                |
| title     | varchar(11)      | YES  |     | NULL    |                |
| keyword   | text             | YES  |     | NULL    |                |
| tokens    | text             | YES  |     | NULL    |                |
| tag_id    | int(11)          | YES  |     | NULL    |                |
| crawled   | int(11)          | YES  |     | NULL    |                |
+-----------+------------------+------+-----+---------+----------------+
with open('../py_spider/all.txt', errors='ignore') as f:
    for line in f.readlines():
        line = line.strip()
        try:
            url, body = line.split('\t', 1)
            title, keywords, description, plist, alist = body.split('\01')
        except ValueError:
            continue

        url = url.lstrip('http://')
        url = url.lstrip('https://')
"""

pattern_d = {}
for m_dict in lrun('select url, title, keyword from crm_website where tag_id = 3'):
    url = m_dict['url']
    if 'Error' in m_dict['title']:
        continue
    # pattern_d[url] = m_dict['title'] + m_dict['keyword'] + m_dict['tokens']
    pattern_d[url] = m_dict['title'] + m_dict['keyword']

def is_html_content_valid(page_content):
    bad_patterns = ['Error', 'error', '404', '对不起', u'对不起', 'Bad', 'Forbidden']
    for pattern in bad_patterns:
        if pattern in page_content:
            return False
    else:
        return True


NOW = int(time.time())
total_update_count = 0
rubbish_count = 0
# 只处理12个小时以内的记录
start_timestamp = int(time.time()) - 60*60*12
for d in run('select id, tag_id, keywords, urls, urls_content, data_description from crm_order_result where telecom_update_time > {0} and tags is null and feedback = 0'.format(start_timestamp)):
    #url_id_parts = d['data_description'].split('|')
    content_list = []
    for url in d['urls'].split('|'):
        if 'host.' in url[:8] and '-' in url[:8]:
            try:
                prefix_id, correnct_url = url.split('-', 1)
                url = correnct_url
            except ValueError:
                pass
        host_part = url.split('/', 1)[0]
        the_html_content = ''
        if '(' in url or ')' in url:
            continue

        # the main routine
        # 如果url直接命中了以往的数据库记录:
        if url in pattern_d:
            the_html_content = pattern_d[url]
            if is_html_content_valid(the_html_content):
                content_list.append(the_html_content)
            else:
                if host_part in pattern_d:
                    the_html_content = pattern_d[host_part]
                    if is_html_content_valid(the_html_content):
                        content_list.append(the_html_content)
        # 否则就看看URL的host是否命中了数据库记录:
        elif host_part in pattern_d:
            the_html_content = pattern_d[host_part]
            if is_html_content_valid(the_html_content):
                content_list.append(the_html_content)
    
    keywords = d['keywords']
    # 看看content_list是否为空，如果为空，证明没有什么可供显示的，那么就把它废弃
    if not keywords and not content_list and d['tag_id'] in [3, 70]:
        run('update crm_order_result set tag_id = %d, order_id = %d where id = %d' % (72, 802, d['id'])) 
        total_update_count += 1
        rubbish_count += 1
        continue

    content_list = '|'.join(content_list)
    content_list = ' '.join(re.findall(valid_pattern, content_list)).strip()
    if content_list:
        run('update crm_order_result set tags = %d , urls_content = "%s" where id = %d' % (NOW, content_list, d['id']))
        total_update_count += 1


connection.commit()

print('total_update_count:')
print(total_update_count)
print('rubbish_count:')
print(rubbish_count)

if total_update_count >= 10 or rubbish_count >= 10:
    x = prettytable.PrettyTable(["填写网页信息总量", "废弃数据总量"])
    x.add_row([total_update_count - rubbish_count, rubbish_count])
    send_excel_result(str(x))

connection.close()
