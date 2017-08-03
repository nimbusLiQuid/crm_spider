#!/usr/bin/python3
#! coding: utf-8
"""
此脚本实现了根据json形式的文本列表，将order_id = 0 仓库中的数据实现了数据细分
必须用英文双引号、英文逗号、英文冒号。
用双斜线注释掉的部分不会执行。执行周期是每隔十分钟，在爬虫系统处理完之后执行。

字段说明:
    tag_id： 变更后的tag_id
    from_tag_id: 变更前的tag_id，不写默认为3
    keywords: 页面和正文中包括的单词，多个用英文逗号隔开
    exclude: 页面和正文中排除的单词，多个用英文逗号隔开
    origin: 选择的省份，不写默认为全国。
    date: 数据的日期，例如“20170611”，加不加引号均可。如果不写，默认是今天。
    order_id: 分配去的订单号，可以是一个数字(0则代表不分配去具体的订单)；也可以是一个列表，如[123, 234, 345], 代表平均分配到这些订单中。
    limit: 每次操作的数据的最大条数的限制，如不写则没有限制。

"""

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
from random import choice
import os.path

DIY_IP = '8.8.8.8'

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



def data_selecter(token, date, tag_id):
    CONDITION_LIST = [
        "SELECT",
        "id, tag_id, order_id, origin",
        "FROM crm_order_result WHERE", 
        "tag_id = {0}".format(tag_id or 3),  # 好315加盟标签
        # "and order_id = 0", # 在导入之前分配
        #"and contact_try_times = 0 and feedback_uid = 0 ",  # 未使用
        "and from_unixtime(telecom_update_time, '%Y%m%d') = '{0}'".format(date),  #当日数据
    ]
    if token:
        key_list = token.split(',')
        CONDITION_LIST.append("and {0}".format(build_keywords_filter_condition(key_list)))
    SQL = ' '.join(CONDITION_LIST)
    #print(SQL)
    data = run(SQL)
    print('Total: {0}'.format(len(data) ))
    print('-'*30)
    print(json.dumps(data, ensure_ascii=True, indent=2))



def tag_divider(new_order_id, new_tag_id, key_list, exclude_list, province_names, given_date, from_tag_id=3, limit=None):
    total_update_count = 0
    NOW = int(time.time())

    try:
        DATE = sys.argv[1]
    except IndexError:
        # DATE = time.strftime('%Y%m%d')
        DATE = given_date

    # print(type(from_tag_id))
    if isinstance(from_tag_id, int):
        TAG_CONDITION = "tag_id = {0}".format(from_tag_id or 3)
    elif isinstance(from_tag_id, list):
        TAG_CONDITION = "tag_id in ({0})".format(','.join([str(i) for i in from_tag_id]))

    CONDITION_LIST = [
        "SELECT",
        "id, tag_id, keywords, urls, urls_content, origin",
        "FROM crm_order_result WHERE", 
        TAG_CONDITION,
        "and order_id = 0", # 在导入之前分配
        "and contact_try_times = 0 and feedback_uid = 0 ",  # 未使用
        "and from_unixtime(telecom_update_time, '%Y%m%d') = '{0}'".format(DATE),  #当日数据
    ]

    if key_list:
        CONDITION_LIST.append("and {0}".format(build_keywords_filter_condition(key_list)))

    if exclude_list:
        CONDITION_LIST.append("and not {0}".format(build_keywords_filter_condition(exclude_list)))

    if province_names:
        CONDITION_LIST.append("and origin in {0}".format(province_names))

    if limit:
        CONDITION_LIST.append("limit {0}".format(limit))

    SQL = ' '.join(CONDITION_LIST)
    print(SQL)

    specify_new_order_id = 0
    for m_dict in run(SQL):
        if isinstance(new_order_id, list):
            # random distribute:
            # specify_new_order_id = choice(new_order_id)

            # mod equal distribute:
            specify_new_order_id = new_order_id[total_update_count % len(new_order_id)]
        elif isinstance(new_order_id, int):
            specify_new_order_id = new_order_id

        if specify_new_order_id == 0:
            run('update crm_order_result set order_id = {0},  tag_id = {1}  where id = {2}'.format(specify_new_order_id, new_tag_id,  m_dict['id']), simulate=False)
        else:
            run('update crm_order_result set order_id = {0},  tag_id = {1}, update_order_data_time = {2} where id = {3}'.format(specify_new_order_id, new_tag_id, NOW,  m_dict['id']), simulate=False)

        total_update_count += 1

    # add action log
    # insert into crm_action_log
    # code: {200: "导入", 201: "退还" }
    # data_a: order_id, data_b: tag_id, data_c: 操作数据个数
    # uid: 2103
    # time: 时间
    if specify_new_order_id != 0:
        run("insert into crm_action_log (uid, code, data_a, data_b, data_c, time, client_ip) values ({0}, {1}, {2}, {3}, {4}, {5}, '{6}' )".format(2103, 200, specify_new_order_id, new_tag_id, total_update_count, NOW, DIY_IP))
    connection.commit()

    print('total_update_count:')
    print(total_update_count)

    if total_update_count >= 1:
        mail_msg = []
        x = prettytable.PrettyTable([",".join(key_list)])
        x.add_row(['+%d' % total_update_count])
        mail_msg.append(str(x))
        mail_msg.append('-'*16)
        mail_msg.append(current_job_line)
        mail_msg.append('-'*16)
        mail_msg.append(SQL)
        send_excel_result('\n'.join(mail_msg), u'[结果通知] 加盟行业标签细分 ✂️')



if __name__ == '__main__':
    # 读入董在wiki上的文件；
    # {"tag_id": 106, "order_id": 870, "keywords": "猪排,火鸡,大象"}
    # {"tag_id": 104, "order_id": 861, "keywords": "鸡排,冰淇淋"}
    # 
    # {"from_tag_id": 3, "tag_id": 104, "order_id": 861, "keywords": "鸡排,冰淇淋"}
    # {"origin": "shandong,shanghai", "from_tag_id": 3, "tag_id": 104, "order_id": 861, "keywords": "鸡排,冰淇淋"}
    realpath = os.path.split(os.path.realpath(__file__))[0]
    print(realpath)
    current_job_line = ''
    with open(realpath + '/crm_tag_divide.txt', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            try:
                m_dict = json.loads(line)
            except ValueError:
                continue
            if 'origin' in m_dict:
                province_names = m_dict['origin']
                province_names = [ "'" + i + "'" for i in province_names.split(',')]
                province_names = '({0})'.format(','.join(province_names))
            else:
                province_names = ''


            if 'order_id' not in m_dict:
                m_dict['order_id'] = 0

            if 'from_tag_id' not in m_dict:
                m_dict['from_tag_id'] = 3
            # 关键词
            if 'keywords' not in m_dict:
                m_dict['keywords'] = ''
            if m_dict['keywords']:
                key_list = m_dict['keywords'].split(',')
            else:
                key_list = []
            # 排除的关键词
            if 'exclude' not in m_dict:
                m_dict['exclude'] = ''
            if m_dict['exclude']:
                exclude_list = m_dict['exclude'].split(',')
            else:
                exclude_list = []

            if 'date' not in m_dict:
                given_date_str = time.strftime('%Y%m%d')
            else:
                given_date_str = str(m_dict['date'])

            if 'limit' not in m_dict:
                limit = None
            else:
                limit = m_dict['limit']

            current_job_line = line
            tag_divider(new_order_id = m_dict['order_id'],
                        new_tag_id = m_dict['tag_id'],
                        key_list = key_list,
                        exclude_list = exclude_list,
                        province_names = province_names,
                        given_date = given_date_str,
                        from_tag_id = m_dict['from_tag_id'],
                        limit = limit)

