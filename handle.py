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


# 采集新URL的来源
valid_pattern = re.compile(u'[\u0030-\u0039\u0041-\u005a\u0061-\u007a\u4e00-\u9fa5()\',.]+')
valid_pattern = re.compile(u'[\u4e00-\u9fa5]+')

def purify_search_word(word):
    if not word:
        return ''
    return ' '.join(re.findall(valid_pattern, word))

def is_valid(typename):
    if not purify_search_word(typename).strip():
        return False
    else:
        return True

db_urls_set = set()
dup_id_list = []
bad_id_list = []
start_timestamp = int(time.time()) - 60*60*5
for d in lrun('select id, url, title, keyword, tokens from crm_website order by id desc'):
    uniq_url = d['url'].lower()
    if not uniq_url in db_urls_set:
        db_urls_set.add(uniq_url)
    else:
        dup_id_list.append(str(d['id']))

    if is_valid(d['title']) or is_valid(d['keyword']) or is_valid(d['tokens']):
        pass
    else:
        bad_id_list.append(str(d['id']))

    if len(uniq_url) > 200:
        bad_id_list.append(str(d['id']))


else:
    print (','.join(dup_id_list))
    print (', '.join(bad_id_list))

if dup_id_list or bad_id_list:
    pass
    # lrun('delete from crm_website where id in ({0})'.format(','.join(dup_id_list+bad_id_list)))
else:
    print('clean')
