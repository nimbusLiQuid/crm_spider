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
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

try:
    TAG_ID = int(sys.argv[1])
except IndexError:
    TAG_ID = 3

try:
    UNIQLE_FILE = sys.argv[2]
except IndexError:
    UNIQLE_FILE = None


bad_url_redis = redis.Redis(port= os.environ.get('REDIS_PORT') or 6019, db=2)
bad_url_set = set([i.decode('utf-8', 'ignore') for i in bad_url_redis.keys()])

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
                                   password='cout<<A7Sm6eqitslue5M8',
                                   db='crm_website',
                                   port=3306,
                                   charset='utf8',
                                   cursorclass=pymysql.cursors.DictCursor)

local_cursor = local_connection.cursor()


# only right for python3
emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)

def remove_emoji(text):
    return emoji_pattern.sub(r'', text)


def run(sql):
    logging.info(sql)
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
    logging.info(sql)
    affected_rows = local_cursor.execute(sql)
    data = local_cursor.fetchall()
    sys.stderr.write('==> %d rows affected.\n' % affected_rows)
    #print(data)
    return data


def spider_url_to_dpi_url(url):
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    return url


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

    sql = 'replace into '
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


# 采集新URL的来源
yun_db_urls_set = set()
start_timestamp = int(time.time()) - 60*60*48
for d in run('select urls from crm_order_result where telecom_update_time > {0} and tags is null'.format(start_timestamp)):
    assert 'urls' in d
    for url in d['urls'].split('|'):
        if 'host.' in url[:8] and '-' in url[:8]:
            try:
                prefix_id, correnct_url = url.split('-', 1)
                url = correnct_url
            except ValueError:
                pass
        yun_db_urls_set.add(url)

if len(yun_db_urls_set) == 0:
    logging.info('no new url')

# 无需再爬取的URL认定为6个月内出现在数据库中的URL
# 如果是6个月之前的，就需要再爬取了
NOW = int(time.time())
all_url_set = set()
for d in lrun('select distinct url from crm_website where timestamp > {0}'.format(NOW - 6 * 30 * 24 * 60 * 60)):
    all_url_set.add(d['url'].lower())


"""
TIMESTAMP=`date -d "-0 day" "+%Y%m%d%M%H%S"`
python3 yun_db.py > urls_to_spider_${TIMESTAMP}.txt
python spider.py urls_to_spider_${TIMESTAMP}.txt > urls_content_${TIMESTAMP}.txt
"""


def clean_str_for_mysql_db(raw_str):
    raw_str = remove_emoji(raw_str)
    raw_str = raw_str.replace('🎵', '')
    raw_str = raw_str.replace('🤔', '')
    return raw_str.replace('\'', '')


pattern_d = []

if UNIQLE_FILE:
    job_files = [UNIQLE_FILE]
else:
    job_files = glob.glob('urls_content/urls_content_*.txt')


for filename in job_files:
    with open(filename, errors='ignore') as f:
        for line in f:
            line = line.strip()
            try:
                url, body = line.split('\t', 1)
            except ValueError as e:
                continue

            url = spider_url_to_dpi_url(url).lower()
            # 20180104 update
            url = url[:200]

            if not is_html_content_valid(body):
                bad_url_redis[url] = 1
                continue

            if url in all_url_set:
                continue

            body = clean_str_for_mysql_db(body)
            parts = body.split('\01')
            for i in range(5):
                parts.append('')

            title, keywords, description, plist, alist = parts[0], parts[1], parts[2], parts[3], parts[4]
            tokens_str = ' '.join([title, keywords, description, plist, alist])
            m_dict = {
                'url': url,
                'timestamp': NOW,
                'title': title,
                'keyword': keywords,
                'tokens': ','.join(analyse.extract_tags(tokens_str, allowPOS=['ns', 'n', 'vn', 'v','nr', 'j', 'nz', 'l', 'ad', 'eng'])),
                'tag_id': TAG_ID,
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

for part in slice_list(pattern_d, 100):
    sql_line = add_records(part)
    #print(sql_line)
    lrun(sql_line)

connection.commit()
connection.close()
local_connection.commit()
local_connection.close()

allow_suffix = """
cn
less
jpeg
ini
txt
xml
ico
zip
ts
gif
json
html
net
aspx
css
do
m3u8
js
dat
hk
dz
jpg
php
woff2
png
ashx
cab
com
dwr
jsc
otf
ttf
"""
allow_suffix = allow_suffix.strip()
allow_suffix_list = []
for line in allow_suffix.split('\n'):
    line = line.strip()
    if line:
        allow_suffix_list.append('.' + line)

allow_suffix_list += ['.jpeg', '.jpg', '.mp4', '.pdf', '.woff',
                    '.ttf', '.mp3', '.less', '.png', '.js', '.doc',
                    '.json', '.zip', '.apk', '.exe', '.avi', '.doc',
                    '.docx', '.webp', '.wav', '.gif', '.ogg']

allow_suffix_list = [i for i in set(allow_suffix_list)]

# 判断URL是否值得爬
def url_qualified_for_spider(url):
    url = url.lower()
    # 1. 并非百度特殊url
    condition1 = '.baidu.com/it/' not in url
    # 2. 并非文件URL模式
    condition2 = True
    for pattern in allow_suffix_list:
        if url.endswith(pattern):
            condition2 = False
            break
    # 3. 并非超短URL或者明显无意义的字符串
    condition3 = len(url) > 5 and "." in url
    return condition1 and condition2 and condition3

# 请勿改变输出的URL的大小写，因为有的网站是大小写敏感的
for i in yun_db_urls_set:
    if i not in all_url_set and i not in bad_url_set:
        if url_qualified_for_spider(i):
            print(i)

