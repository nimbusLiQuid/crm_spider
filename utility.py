#!/usr/bin/python
# -*- coding: utf-8 -*--
"""
the utility used in BCDATA CRM+ system
"""
import time
import hashlib

RTB_PREFIX = 'BC_RTB'


def is_found_in_quick(query, targets):
    for target in targets:
        if target in query:
            return True
    else:
        return False


def spider_url_to_dpi_url(url):
    """
    :param url:
    :return:
    >>> spider_url_to_dpi_url('http://www.baidu.com/blah')
    'www.baidu.com/blah'
    """
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    return url


def dpi_url_to_spider_url(dpi_url):
    """
    >>> dpi_url_to_spider_url('mp3.baidu.com')
    'http://mp3.baidu.com/'
    >>> dpi_url_to_spider_url('mp3.baidu.com/foo/')
    'http://mp3.baidu.com/foo/'
    """
    spider_url = dpi_url
    if not dpi_url.startswith('http://'):
        spider_url = 'http://' + dpi_url
    if dpi_url.split('/')[0] == dpi_url:
        spider_url += '/'
    return spider_url


def url_remove_params(url_with_param):
    """
    >>> url_remove_params('m.so.m/search?key=hadoop')
    'm.so.m/search'
    >>> url_remove_params('www.happysmile.co.jp/item.html')
    'www.happysmile.co.jp/item.html'
    >>> url_remove_params('w')
    'w'
    >>> url_remove_params('')
    ''
    """
    pos1 = url_with_param.find('?')
    if pos1 > 0:
        return url_with_param[:pos1]
    else:
        return url_with_param


def url_to_host(url):
    """
    >>> url_to_host('http://www.acfun.com/site/news/12312321.html')
    'www.acfun.com'
    >>> url_to_host('https://www.google.com/')
    'www.google.com'
    >>> url_to_host('m.123123.com/fildsf/foo/bar.aspx')
    'm.123123.com'
    """
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    pos1 = url.find('/')
    if pos1 > 0:
        url_host = url[:pos1]
        return url_host
    else:
        return url


__suffix__ = ['com', 'cn', 'net', 'org', 'edu', 'vc', 'biz',
              'in', 'co', 'top', 'tech', 'club', 'tv', 'to']
__suffix__ = set(__suffix__)


def host_to_domain(host):
    """
    convert a host to domain: like: m.jd.com ==> jd.com
    this function is very slow
    :param host: the input host
    :return: the domain
    """
    try:
        host, port = host.split(':')
    except ValueError:
        host, port = host, None
    segs = host.split('.')
    if len(segs) == 4 and ''.join(segs).isdigit():
        return host
    else:
        domain_tokens = []
        for token in segs[::-1]:
            domain_tokens.append(token)
            if token not in __suffix__:
                break
        return '.'.join(domain_tokens[::-1])


def unix_time_to_str(value, format_str='%Y%m%d %H:%M:%S'):
    if isinstance(value, int):
        value = float(value)
    value = time.localtime(value)
    return time.strftime(format_str, value)


def str_to_unix_time(dt, format_str='%Y%m%d %H:%M:%S'):
    s = time.mktime(time.strptime(dt, format_str))
    return int(s)


def md5_value(key):
    md5value = hashlib.md5()
    md5value.update(key)
    return md5value.hexdigest()


def count_one(counter_dict, value):
    if not value:
        return
    try:
        counter_dict[value] += 1
    except KeyError:
        counter_dict[value] = 1


def collector_volume(collector):
    """
    计算计数容器的计数值之和
    :param collector: 计数容器
    :return: int, 总数

    >>> a = {'alpha': 12, 'beta': 1, 'gamma': 23}
    >>> print collector_volume(a)
    36
    """
    total = 0
    for _, count in collector.iteritems():
        total += count
    return total


def slice_list(input_list, size):
    """
    :param input_list: 输入的大列表
    :param size: 分割的小列表的个数
    :return: 分割后的二维列表
    """
    input_size = len(input_list)
    slice_size = input_size / size
    remain = input_size % size
    result = []
    iterator = iter(input_list)
    for i in range(size):
        result.append([])
        for j in range(slice_size):
            result[i].append(iterator.next())
        if remain:
            result[i].append(iterator.next())
            remain -= 1
    return result


def chunks(l, n):
    """
    将列表按照等大小进行分割
    :param l: 传入的列表
    :param n: 分割的大小
    :return: 分隔好的列表，返回迭代器对象
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


# Purify Targets_groups, make sure it's well designed.
# b中含有完全包括a的结果是很危险的
def remove_duplicated_tokens_from_target_groups(group_a, group_b):
    tokens_in_a_and_contains_in_b = set()
    tokens_in_b_and_contains_in_a = set()
    for token in group_a:
        if is_found_in_quick(token, group_b):
            tokens_in_a_and_contains_in_b.add(token)

    for token in group_b:
        if is_found_in_quick(token, group_a):
            tokens_in_b_and_contains_in_a.add(token)

    for token in tokens_in_a_and_contains_in_b:
        del group_a[token]

    for token in tokens_in_b_and_contains_in_a:
        del group_b[token]


def simplify_single_tokens(group, ref_group_a, ref_group_b):
    duplicated_tokens_collector = set()
    for token in group:
        if is_found_in_quick(token, ref_group_a) and is_found_in_quick(token, ref_group_b):
            duplicated_tokens_collector.add(token)
    for token in duplicated_tokens_collector:
        del group[token]


def simplify_group_tokens(group):
    longer_tokens_collector = set()
    for i in group:
        for j in group:
            if i in j and i != j:
                longer_tokens_collector.add(j)
    for token in longer_tokens_collector:
        del group[token]


def conf(key, database):
    try:
        return database[key]
    except KeyError, e:
        return {}

