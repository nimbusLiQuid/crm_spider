#!/usr/bin/python3
#! coding: utf-8

import pymysql.cursors
import glob
import sys
import time
import types
import re
from jieba import analyse
from url_utility import *
import redis
import os

bad_url_redis = redis.Redis(port= os.environ.get('REDIS_PORT') or 6019, db=2)

# Connect to the database

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
    #sys.stderr.write('==> %d rows affected.\n' % affected_rows)
    #print(data)
    return data


def lrun(sql):
    if not sql:
        return
    #print('----', sql, '-----')
    affected_rows = local_cursor.execute(sql)
    data = local_cursor.fetchall()
    #sys.stderr.write('==> %d rows affected.\n' % affected_rows)
    #print(data)
    return data


TABLE = 'crm_website'

def build_column_index():
    col_set = set()
    a = lrun('show columns from ' + TABLE)
    for d in a:
        col_set.add(d['Field'])
    #print(col_set)
    return col_set

column_index_dict = build_column_index()

def add_records(attr_dict_list):
    if not attr_dict_list:
        return ''

    sql = 'insert into '
    key_list = []
    for key, value in attr_dict_list[0].items():
        if key in column_index_dict:
            key_list.append(key)
    columns = ', '.join(key_list)
    columns = TABLE + '(' + columns + ')'
    values_part = ' values '
    values_tokens = []
    for attr_dict in attr_dict_list:
        value_list = []
        for key, value in attr_dict.items():
            if key in column_index_dict:
                value_list.append(value)
        new_str_list = []
        for item in value_list:
            if isinstance(item, int):
                new_str_list.append(str(item))
            elif isinstance(item, str):
                new_str_list.append('\'' + item + '\'')
            else:
                raise ValueError
        assert(len(new_str_list) == len(value_list))
        del value_list
        values = ', '.join(new_str_list)
        values = '(' + values + ')'
        values_tokens.append(values)
    else:
        sql = sql + columns + values_part + ','.join(values_tokens) + ';'
    return sql


yun_db_urls_set = set()
for d in run('select urls from crm_order_result where telecom_update_time > 1496727303 and tags is null'):
    assert 'urls' in d
    for url in d['urls'].split('|'):
        if '(' in url or ')' in url:
            continue
        if 'host.' in url[:8] and '-' in url[:8]:
            try:
                prefix_id, correnct_url = url.split('-', 1)
                url = correnct_url
            except ValueError:
                pass
        yun_db_urls_set.add(url)

all_url_set = set()
for d in lrun('select distinct url from crm_website'):
    all_url_set.add(d['url'].lower())

NOW = int(time.time())
pattern_d = []

"""
TIMESTAMP=`date -d "-0 day" "+%Y%m%d%M%H%S"`
python3 yun_db.py > urls_to_spider_${TIMESTAMP}.txt
python spider.py urls_to_spider_${TIMESTAMP}.txt > urls_content_${TIMESTAMP}.txt
"""

for filename in glob.glob('urls_content/urls_content_*.txt'):
    with open(filename, errors='ignore') as f:
        for line in f:
            line = line.strip()
            try:
                url, body = line.split('\t', 1)
            except ValueError as e:
                continue

            url = url.lstrip('http://')
            url = url.lstrip('https://')
            url = url.lower()

            if not is_html_content_valid(body):
                bad_url_redis[url] = 1
                continue

            if url in all_url_set:
                continue

            parts = body.split('\01')

            for i in range(5):
                parts.append('')

            title, keywords, description, plist, alist = parts[0], parts[1], parts[2], parts[3], parts[4]
            m_dict = {
                'url': url,
                'timestamp': NOW,
                'title': title.replace('\'', ''),
                'keyword': keywords.replace('\'', ''),
                'tokens': ','.join(analyse.extract_tags(description + plist+ alist)).replace('\'', ''),
                'tag_id': 3,
                'crawled': 1
            }
            pattern_d.append(m_dict)


def slice_list(input_list, size):
    input_size = len(input_list)
    slice_size = int(input_size / size)
    remain = input_size % size
    result = []
    iterator = iter(input_list)
    for i in range(size):
        result.append([])
        for j in range(slice_size):
            result[i].append(next(iterator))
        if remain:
            result[i].append(next(iterator))
            remain -= 1
    return result

for part in slice_list(pattern_d, 500):
    sql_line = add_records(part)
    #print(sql_line)
    lrun(sql_line)

connection.commit()
local_connection.commit()

for i in yun_db_urls_set - all_url_set:
    print(i)
