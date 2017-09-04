#!/usr/bin/python
# -*- coding: utf-8 -*--
import sys
from xml.etree import ElementTree as ET
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('.')


def load_cn_lib(cn_lib_file):
    f = open(cn_lib_file, 'r')
    cn_lib_str = set([])
    for line in f:
        line = line.strip()
        cn_lib_str.add(unicode(line, 'utf8'))
    f.close()
    return cn_lib_str

def load_search_word_tag(filename):
    tag_dict = {}
    with open(filename) as f:
        for line in f:
            line = line.strip()
            try:
                search_tag, pv = line.split(None, 1)
            except ValueError:
                continue
            tag_dict[search_tag] = 1
    return tag_dict


def load_ref_word_tag(filename):
    tag_dict = {}
    with open(filename) as f:
        for line in f:
            line = line.strip()
            tag_dict[line] = 1
    return tag_dict


def load_search_xml(filename):
    """
    从XML文件中加载搜索引擎(下文中的se)和中文文本数据规则, 包括参数列表规则和斜线规则
    :param filename: 输入的xml文件
    :return: 多重嵌套的字典结构

    >>> test_db = load_search_xml('search_conf.xml')
    >>> assert test_db
    >>> baidu_se = test_db['m.baidu.com']
    >>> print baidu_se
    {'keytag': ['word'], 'endtag': ['/'], 'type': 'gene', 'begintag': ['w=0_10_', 'w=10_10_', 'w=1_20_']}
    >>> for i in test_db:
    ...     se_db = test_db[i]
    ...     assert 'type' in se_db and 'keytag' in se_db

    """
    per=ET.parse(filename)
    all_se_types=per.findall('./search_type')
    key_dict={}
    for se_cate in all_se_types:
        for child in se_cate.getchildren():
            domain=child.attrib['domain']
            keytags=child.attrib['keytag'].split('.')
            # keytag: a list contains all se param keys
            # type: se cate
            key_dict[domain] = {'keytag': keytags, 'type': se_cate.attrib['name']}
            if child.attrib.has_key('begintag'):
                begintag=child.attrib['begintag']
                key_dict[domain]['begintag'] = begintag.split('.')

            if child.attrib.has_key('endtag'):
                endtag=child.attrib['endtag']
                key_dict[domain]['endtag'] = endtag.split('.')

            if child.attrib.has_key('badpath'):
                badpath=child.attrib['badpath']
                key_dict[domain]['badpath'] = badpath
    return key_dict

CN_LIB = 'cn_lib.txt'
SEARCH_CONF = 'search_conf.xml'
SEARCH_WORD = 'search_word'

cn_lib_str = load_cn_lib(CN_LIB)
