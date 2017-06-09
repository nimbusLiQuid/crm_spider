#!/usr/bin/python3
#! coding: utf-8

import pymysql.cursors
import sys
import time
import json
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

def run(sql, simulate=False):
    if simulate:
        print('----', sql, '-----')
        return
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

def is_html_content_valid(page_content):
    bad_patterns = ['Error', 'error', '404', '对不起', u'对不起', 'Bad', 'Forbidden']
    for pattern in bad_patterns:
        if pattern in page_content:
            return False
    else:
        return True


def build_keywords_filter_condition(keywords):
    """
    >>> keywords = ['火鸡', '咖啡']
    >>> print(build_keywords_filter_condition(keywords))
    (concat(keywords, urls_content) like '%火鸡%' or concat(keywords, urls_content) like '%咖啡%')
    """
    condition_list = []
    for keyword in keywords:
        keyword = keyword.strip()
        if keyword:
            condition_list.append("concat(keywords, urls_content) like '%{0}%'".format(keyword))
    return "({0})".format(' or '.join(condition_list))



def tag_divider(new_order_id, new_tag_id, key_list):
    total_update_count = 0
    rubbish_count = 0

    try:
        DATE = sys.argv[1]
    except IndexError:
        DATE = time.strftime('%Y%m%d')

    CONDITION_LIST = [
        "SELECT",
        "id, tag_id, keywords, urls, urls_content, origin",
        "FROM crm_order_result WHERE", 
        "tag_id = 3",  # 好315加盟标签
        "and order_id = 0", # 在导入之前分配
        "and contact_try_times = 0 and feedback_uid = 0 ",  # 未使用
        "and from_unixtime(telecom_update_time, '%Y%m%d') = '{0}'".format(DATE),  #当日数据
        "and {0}".format(build_keywords_filter_condition(key_list))
    ]
    SQL = ' '.join(CONDITION_LIST)
    print(SQL)

    for m_dict in run(SQL):
        run('update crm_order_result set order_id = {0},  tag_id = {1} where id = {2}'.format(new_order_id, new_tag_id, m_dict['id']), simulate=False)
        total_update_count += 1

    connection.commit()

    print('total_update_count:')
    print(total_update_count)
    print('rubbish_count:')
    print(rubbish_count)

    if total_update_count >= 10 or rubbish_count >= 10:
        x = prettytable.PrettyTable(["鸡排冰淇淋筛选条数", "废弃数据总量"])
        x.add_row([total_update_count - rubbish_count, rubbish_count])
        send_excel_result(str(x))



if __name__ == '__main__':
    # 读入董在wiki上的文件；
    # {"tag_id": 106, "order_id": 870, "keywords": "猪排,火鸡,大象"}
    # {"tag_id": 104, "order_id": 861, "keywords": "鸡排,冰淇淋"}
    with open('crm_tag_divide.txt') as f:
        for line in f:
            line = line.strip()
            try:
                m_dict = json.loads(line)
            except ValueError:
                continue
            tag_divider(new_order_id = m_dict['order_id'], new_tag_id = m_dict['tag_id'], key_list = m_dict['keywords'].split(','))

