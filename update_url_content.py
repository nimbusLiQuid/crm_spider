#!/usr/bin/python3
#! coding: utf-8

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

        url = url.lstrip('http://')
        url = url.lstrip('https://')
"""

pattern_d = {}
for m_dict in lrun('select url, title, keyword, tokens from crm_website where tag_id = 3'):
    url = m_dict['url']
    # pattern_d[url] = m_dict['title'] + m_dict['keyword'] + m_dict['tokens']
    pattern_d[url] = m_dict['title'] + m_dict['keyword']

def is_html_content_valid(page_content):
    bad_patterns = ['Error', 'error', '404', '对不起', u'对不起']
    for pattern in bad_patterns:
        if pattern in page_content:
            return False
    else:
        return True


dly_pattern_d = {
    u"肉蟹煲": 83,
    u"米线": 83,
    u"冰激凌": 90,
    u"冰淇淋": 90,
    u"冒菜": 90,
    u"串串": 90,
    u"麻辣烫": 90
}

dly_province_d = {
    90: 'jiangsu,zhejiang,shandong,henan,anhui,shanghai'
}

NOW = int(time.time())
total_update_count = 0
for d in run('select id, tag_id, keywords, urls, urls_content, data_description, feedback, origin from crm_order_result where telecom_update_time > 1495036851  and tags is null and feedback = 0'):
    #url_id_parts = d['data_description'].split('|')
    content_list = []
    for url in d['urls'].split('|'):
        # handle mistake
        # 1
        # 2
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
        if url in pattern_d:
            the_html_content = pattern_d[url]
            if is_html_content_valid(the_html_content):
                content_list.append(the_html_content)
            else:
                if host_part in pattern_d:
                    the_html_content = pattern_d[host_part]
                    if is_html_content_valid(the_html_content):
                        content_list.append(the_html_content)
        elif host_part in pattern_d:
            the_html_content = pattern_d[host_part]
            if is_html_content_valid(the_html_content):
                content_list.append(the_html_content)
    
    keywords = d['keywords']
    if not keywords and not content_list and d['tag_id'] in [3, 70]:
        run('update crm_order_result set tag_id = %d, order_id = %d where id = %d' % (72, 802, d['id'])) 
        total_update_count += 1
        continue

    content_list = '|'.join(content_list)
    content_list = ' '.join(re.findall(valid_pattern, content_list)).strip()
    if content_list:
        run('update crm_order_result set tags = %d , urls_content = "%s" where id = %d' % (NOW, content_list, d['id']))
        total_update_count += 1

    # 董灵瑜需求
    continue
    if content_list or keywords:
        for key_token, new_tag_id in dly_pattern_d.items():
            if new_tag_id in dly_province_d:
                province_list = dly_province_d[new_tag_id]
                if d['origin'] in province_list:
                    if keywords and key_token in d['keywords']:
                        if content_list and key_token in d['urls_content']:
                            run('update crm_order_result set tag_id = %d  where id = %d' % (new_tag_id, d['id']))
                            total_update_count += 1
                            break
            else:
                if keywords and key_token in d['keywords']:
                    if content_list and key_token in d['urls_content']:
                        run('update crm_order_result set tag_id = %d  where id = %d' % (new_tag_id, d['id']))
                        total_update_count += 1
                        break

connection.commit()

print('total_update_count:')
print(total_update_count)
