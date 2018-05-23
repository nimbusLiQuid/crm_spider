#!/usr/bin/python3
#! coding: utf-8
"""
应用reftable，将爬虫爬取失败的结果重新登记
"""

import pymysql.cursors
import sys
import time
sys.path.append('.')
from jieba import analyse
# Connect to the database
import re
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
                                   password='cout<<A7Sm6eqitslue5M8',
                                   db='crm_website',
                                   port=3306,
                                   charset='utf8',
                                   cursorclass=pymysql.cursors.DictCursor)

local_cursor = local_connection.cursor()

def run(sql):
    print('----', sql, '-----')
    if not sql:
        return
    affected_rows = cursor.execute(sql)
    data = cursor.fetchall()
    sys.stderr.write('==> %d rows affected.\n' % affected_rows)
    #print(data)
    return data


def lrun(sql):
    if not sql:
        return
    #print('----', sql, '-----')
    affected_rows = local_cursor.execute(sql)
    data = local_cursor.fetchall()
    sys.stderr.write('==> %d rows affected.\n' % affected_rows)
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

"""



def spider_url_to_dpi_url(url):
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    return url

ref_d = {}

with open('ref.txt') as f:
    for line in f:
        line = line.strip()
        line = spider_url_to_dpi_url(line)
        try:
            url, code_id, rest = line.split(None, 2)
        except ValueError:
            continue

        try:
            ref_d[code_id].add(frozenset([url, rest]))
        except KeyError:
            ref_d[code_id] = set()
            ref_d[code_id].add(frozenset([url, rest]))
        
#print(ref_d)


def is_html_content_valid(page_content):
    bad_patterns = ['Error', 'error', '404', '对不起', u'对不起', 'Bad', 'Forbidden']
    for pattern in bad_patterns:
        if pattern in page_content:
            return False
    else:
        return True


NOW = int(time.time())
total_update_count = 0
for d in run('select id, tag_id, keywords, urls, urls_content, data_description, feedback from crm_order_result where telecom_update_time > 1492618703 and order_id = 802 and data_description is not null and data_description != ""  '):
    # print(d['data_description'])
    if d['urls_content'] and is_html_content_valid(d['urls_content']):
        run('update crm_order_result set tags = %d,  order_id = 0, tag_id = 3 where id = %d' % (NOW, d['id']))
        continue

    url_code_id_str = d['data_description']
    real_title = ''
    for url_code_id in url_code_id_str.split('|'):
        try:
            _, code_id = url_code_id.split('.')
        except ValueError:
            continue

        try:
            url_title_set = ref_d[code_id]
            for url, title in url_title_set:
                if url in d['urls']:
                    real_title += title
                    break
        except KeyError:
            continue

    if real_title:
        run('update crm_order_result set tags = %d, urls_content = "%s", order_id = 0, tag_id = 3 where id = %d' % (NOW, real_title, d['id']))
        total_update_count += 1

connection.commit()
connection.close()

print('total_update_count:')
print(total_update_count)
