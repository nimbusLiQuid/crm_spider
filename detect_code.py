#!/usr/bin/python
#! coding: utf-8
import sys
import os
import re
import urllib
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('.')
from load_search_db import *


fuzzy_contain_words = []

def is_valid_search_word(word):
    """
    判断一个词是不是有效的中文词: 含有中文即可
    :param word:
    :return: True or False

    >>> if is_valid_search_word('an是好的s不不a'): print 'yes'
    yes
    """
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')
    return zhPattern.search(word.decode('utf-8', 'ignore'))


def parse_url_params(params):
    """
    从url参数列表生成参数字典
    :param params: params参数列表字符串
    :return: 参数字典

    >>> parse_url_params('foo=bar&tom=jerry&k=1&bo=fa')
    {'k': '1', 'foo': 'bar', 'bo': 'fa', 'tom': 'jerry'}
    """
    param_kv_dict = {}
    for pair in params.split('&'):
        if len(pair.split('=')) == 2:
            key, value = pair.split('=')
            if value != '':
                param_kv_dict[key] = value
    return param_kv_dict


def find_query_from_params_accuracy(host, param_kv_dict):
    query, se_cate = '', OTHER
    search_host_info = {}
    if host in search_host_dict:
        search_host_info = search_host_dict[host]
    else:
        host = host.split('.', 1)[0]
        if host in search_host_dict:
            search_host_info = search_host_dict[host]

    if search_host_info:
        se_cate = search_host_info['type']
        keytag_list = search_host_info['keytag']
        for key in param_kv_dict:
            if key in keytag_list:
                query = param_kv_dict[key]
                break
    return query, se_cate


def find_query_from_params_fuse(param_kv_dict):
    """
    模糊匹配参数列表中的搜索结果:
    有两种模糊匹配的方式:
    1. 看参数列表字典中的key是否位于某集合中: search_word
    2. 看参数列表字典中的key是否包含了包含某关键字集合中的关键字: fuzzy_contain_words
    :param param_kv_dict: 参数列表字典
    :return: 未解码的原始字符串(包含%E3%D2%F7的那种)
    """
    query, match_type = '', OTHER
    for key, value in param_kv_dict.iteritems():
        if key in search_tag_dict:
            query, match_type = value, key
            # 只有在query可能为一个中文搜索结果的时候，才将其返回，否则忽略掉，下同
            if query.count('%') >= 2:
                break
        else:
            for word in fuzzy_contain_words:
                if word in key.lower():
                    query, match_type = value, word
                    if query.count('%') >= 2:
                        break
    return query, match_type


def find_query_from_path(host, url_path):
    query, se_cate = '', OTHER
    search_host_info = {}
    if host in search_host_dict:
        search_host_info=search_host_dict[host]
    else:
        host = host.split('.', 1)[0]
        if host in search_host_dict:
            search_host_info = search_host_dict[host]

    if search_host_info:
        se_cate = search_host_info['type']
        if search_host_info.has_key('badpath') and url_path.find(search_host_info['badpath']) >= 0:
            return query, se_cate

        if search_host_info.has_key('begintag'):
            begin_tag_list = search_host_info['begintag']
            for begintag in begin_tag_list:
                query_begin =  url_path.find(begintag)
                if query_begin >= 0:
                    query_begin += len(begintag)
                    query_end = -1
                    if search_host_info.has_key('endtag'):
                        end_tag_list = search_host_info['endtag']
                        for endtag in end_tag_list:
                            query_end = url_path.find(endtag, query_begin)
                            if query_end >= 0:
                                break
                    query = url_path[query_begin:query_end]
                    if len(query) > 0:
                        break
    return query, se_cate


def find_query_from_url(url):
    try:
        body, params = url.split('?', 1)
    except ValueError:
        body, params = url, None
    host = body.split('/')[0]
    # URL斜线中的中文
    query, se_cate = find_query_from_path(host, body)
    if query:
        return query, se_cate

    # 参数列表中的中文
    if not params:
        return '', OTHER

    # 精确查找 or 模糊查找
    param_kv_dict = parse_url_params(params)
    query, se_cate = find_query_from_params_accuracy(host, param_kv_dict)
    return query, se_cate
    # 不再使用模糊查找以节约内存
    # if query:
    #     return query, se_cate
    # else:
    #     return find_query_from_params_fuse(param_kv_dict)


def decode_query(query_unquote):
    """
    对已经转码后的结果稍作处理
    :param query_unquote: 已经转码后的utf-8结果
    :return: 稍作处理后的结果

    >>> print decode_query('我爱+北京')
    我爱 北京
    >>> print decode_query('  我爱\\n北京\\r  ')
    我爱北京
    >>> import urllib2
    >>> # UTF-8 test
    >>> print decode_query(urllib2.unquote('%E7%99%BE%E5%B7%9D%E9%80%9A%E8%81%94'))
    百川通联
    >>> # GBK test，这个字符串是用textmate中的GB18030制造的。
    >>> print decode_query(urllib2.unquote('%B0%D9%B4%A8GBK%B1%E0%C2%EB'))
    百川GBK编码
    """
    if query_unquote == '':
        return ''

    # the 'gbk_cnt >= (utf8_cnt * 1.5)' algorithm used in decode_query_unknow_coding is slightly faster
    # than chardet.detect, especially in Chinese web world, since utf-8 and gbk are the 2 mostly used
    # encoding. An experiment show that when sentence get longer, chardet.detect is faster, however, here
    # we recommend using the 'gbk_cnt >= (utf8_cnt * 1.5)' algorithm.             -- Quan Lin, 2017.02.22

    # the Python way:

    query_str = decode_query_unknow_coding(query_unquote)

    query_str = query_str.translate(None, '\n\r')
    # m.baidu.com 会将用户输入的空格转换成+, 这里将他们还原
    query_str = query_str.replace('+', ' ')
    query_str = query_str.strip()
    return query_str


def decode_query_unknow_coding(query_unquote):
    """
    使用比对gbk和utf8字节长度的方法，
    从bin字节序列中解码得到文字内容
    :param query_unquote:二进制字节内容
    :return:明文文字内容

    >>> import urllib2
    >>> # UTF-8 test
    >>> print decode_query_unknow_coding(urllib2.unquote('%E7%99%BE%E5%B7%9D%E9%80%9A%E8%81%94'))
    百川通联
    >>> # GBK test，这个字符串是用textmate中的GB18030制造的。
    >>> print decode_query_unknow_coding(urllib2.unquote('%B0%D9%B4%A8GBK%B1%E0%C2%EB'))
    百川GBK编码
    """
    # 对未知编码的字符串按照中文世界最常用的两种编码进行猜测解码
    query_str = ''
    decode_str1 = query_unquote.decode('gbk', 'ignore').encode('utf8')
    decode_str2 = query_unquote.decode('utf8', 'ignore').encode('utf8')
    # print type(decode_str1), decode_str1
    # print type(decode_str2), decode_str2
    utf8_cnt = 0
    decode_str_utf8 = unicode(decode_str2, 'utf8')
    for word in decode_str_utf8:
        if word in cn_lib_str:
            utf8_cnt += 1
    gbk_cnt = 0
    decode_str_gbk = unicode(decode_str1, 'utf8')
    for word in decode_str_gbk:
        if word in cn_lib_str:
            gbk_cnt += 1

    if utf8_cnt >= gbk_cnt :
        query_str = decode_str2
        return 'utf-8'
    else:
        query_str = decode_str1
        return 'gbk'
    #return query_str


def find_query(url):
    """
    从url中寻找搜索词和中文内容
    :param url: 待分析的URL
    :return: 获取到的中文搜索结果

    >>> query, se_cate = find_query('m.baidu.com/search?word=%E7%99%BE%E5%B7%9D%E9%80%9A%E8%81%94')
    >>> assert query == '百川通联' and se_cate == 'gene'
    >>> query, se_cate = find_query('')
    >>> assert query == '' and se_cate == OTHER
    """
    if not url:
        return '', OTHER
    # extract raw_query
    query_raw, se_cate = find_query_from_url(url)
    query_unquote = urllib.unquote(urllib.unquote(query_raw))

    # special case: 1. like a url
    if query_unquote[0:7] == 'http://':
        url = query_unquote
        query_raw, se_cate = find_query_from_url(url)
        query_unquote = urllib.unquote(urllib.unquote(query_raw))
    # special case: 2.  like a param_list
    elif query_unquote.find('&') >= 0 and query_unquote.find('=') >= 0:
        host = url.split('?')[0].split('/')[0]
        url = host + '/?'+query_unquote
        query_raw, se_cate = find_query_from_url(url)
        query_unquote = urllib.unquote(urllib.unquote(query_raw))

    # decode raw
    query_decode = decode_query(query_unquote)

    # check contains Chinese
    if not is_valid_search_word(query_decode):
        query_decode = ''
    return query_decode, se_cate



def calc_weight_rtb(url, userAgent):
    """
    calculate a tag: weight
    :param url: the url that need to be tagged
    :param userAgent: used to determine whether the device is a phone
    :return: None, but modified the global info_collector
    """
    global info_collector
    # output a dictionary like:
    # {
    #  '2816': {'weight': 10.0},
    #  '1281': {'weight': 9.8087311366299996},
    #  '3588': {'weight': 9.6544369254099998},
    # }
    vw_weight = url_weight_manager_rtb.get_weight(url, userAgent)
    if vw_weight and len(vw_weight) > 0:
        if '1800' in vw_weight:
            info_collector[RIPE_MARK] = 1
        for cate_id in vw_weight:
            if cate_id not in info_collector:
                info_collector[cate_id] = vw_weight[cate_id]


def build_url_db(urls_filename):
    """
    从文件创建URL规则库，改用ac自动机进行匹配
    :param urls_filename: 规则文件名，目前是urls.txt
    :return: 创建好的ac自动机
    """
    automation = ahocorasick.Automaton()
    # 1. 将符合搜索站的结果打上搜索痕迹
    for search_host in search_host_dict:
        automation.add_word(search_host, 'Q')

    # 2. 读入订单任务的url规则
    with open(urls_filename) as f:
        for line in f:
            line = line.strip()
            try:
                code, url = line.split('\t')
                url = utility.spider_url_to_dpi_url(url)
            except ValueError:
                continue
            automation.add_word(url, code)

    # 3. 增加手动的黑名单
    for black_pattern in xml_reader.get_blacklist_from_xml('blacklist.xml'):
        automation.add_word(black_pattern, 0)

    # 4. 将高pv的域名添加进入黑名单
    top_cdpi_file = 'top_cdpi_urls.txt'
    if os.path.exists(top_cdpi_file):
        with open(top_cdpi_file) as f:
            for line in f:
                line = line.rstrip('\n')
                try:
                    _, url_pattern = line.split()
                except ValueError:
                    continue
                automation.add_word(url_pattern, 0)

    automation.make_automaton()
    return automation


if __name__ == '__main__':
    pass
