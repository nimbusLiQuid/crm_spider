#!/usr/bin/python
# -*- coding: utf-8 -*--
import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('.')
import requests
from bs4 import BeautifulSoup
import random
import re
import threading
from multiprocessing import Pool, Queue
import Queue as queue
from contextlib import contextmanager
import os.path
import signal
import load_search_db
import warnings  
from fake_useragent import UserAgent

# 忽略警告
warnings.filterwarnings("ignore") 

# ------------------------------
#  ______   ______  ______   ______  _____  _____    ______  ______
# | |  | \ | |     / |      | |  | \  | |  | | \ \  | |     | |  | \
# | |--| < | |     '------. | |__|_/  | |  | |  | | | |---- | |__| |
# |_|__|_/ |_|____  ____|_/ |_|      _|_|_ |_|_/_/  |_|____ |_|  \_\
#  _       _____  ______     ______    _    _   ______   ______
# | |       | |  | |  \ \   / | _| \  | |  | | | |  | | | |  \ \
# | |   _   | |  | |  | |   | | \  |  | |  | | | |__| | | |  | |
# |_|__|_| _|_|_ |_|  |_|   \_|__|__\ \_|__|_| |_|  |_| |_|  |_|

# 多进程、多线程Python爬虫
# 注意！本爬虫仅对中文和英文(utf-8)世界的编码能保证100%的正确解码! 
# 对于 日文(JIS)等语言支持度非常差
# 林泉 @ 百川通联
# Verson 0.0.1
# 2016.12.21
# Python 2.7.11
# Python3 不兼容
# 依赖关系如下:
"""
pip install bs4
pip install requests
sudo yum install libxml2 libxml2-devel libxml2-python libxslt libxslt-devel
sudo pip install lxml
sudo pip install cryptography
sudo pip install urllib3[secure]
pip install fake-useragent
"""


# 可高效利用网络IO爬取页面信息
# 输入参数1： 装载URL列表的文件，一行一个， 可带http://也可不带
# 输出行：URL + '\t' + '\01'.join([title, keywords, description, ' '.join(p_list), ' '.join(a_list)])
# 注释： p_list, 页面上<p>的集合，用空格分开
# 注释： a_list, 页面上<a>的集合，用空格分开
#
# 多线程爬虫提取页面信息
# 配置如下

# 进程数: 推荐与CPU数相同
PROCESS_NUM = 4
# 线程数: 推荐20左右
thread_count = 20
# timeout 设置，5秒
time_out = 5
# -------------------------------

# fake_useragent从某网站获取最新的ua数据，并将其缓存到/tmp/目录下
fake_ua = UserAgent()
# ------------------- functions ---------------------------

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


def get_encoding_from_headers(headers):
    """Returns encodings from given HTTP Header Dict.

    :param headers: dictionary to extract encoding from.
    """
    content_type = headers.get('content-type')

    if not content_type:
        return None

    content_type, params = cgi.parse_header(content_type)

    if 'charset' in params:
        return params['charset'].strip("'\"")

    if 'text' in content_type:
        return 'ISO-8859-1'


def get_encodings_from_content(content):
    """Returns encodings from given content string.

    :param content: bytestring to extract encodings from.
    """
    charset_re = re.compile(r'<meta.*?charset=["\']*(.+?)["\'>]', flags=re.I)
    pragma_re = re.compile(r'<meta.*?content=["\']*;?charset=(.+?)["\'>]', flags=re.I)
    xml_re = re.compile(r'^<\?xml.*?encoding=["\']*(.+?)["\'>]')

    return (charset_re.findall(content) +
            pragma_re.findall(content) +
            xml_re.findall(content))


@property
def apparent_encoding(self):
    """The apparent encoding, provided by the lovely Charade library
    (Thanks, Ian!)."""
    return chardet.detect(self.content)['encoding']

def monkey_patch():
    prop = requests.models.Response.content
    def content(self):
        _content = prop.fget(self)
        if self.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(_content)
            if encodings:
                self.encoding = encodings[0]
            else:
                self.encoding = self.apparent_encoding
            _content = _content.decode(self.encoding, 'replace').encode('utf8', 'replace')
            self._content = _content
        return _content
    requests.models.Response.content = property(content)

# 若执行monkey_patch则会丧失更改response.encoding之后，自动更新response.text这一重要特性
# 所以不再使用这个monkey_patch，（其实这个本身也不好）
# monkey_patch()


def toggle_chinese_page_encoding(original_encoding):
    """
    >>> print toggle_chinese_page_encoding('gbk')
    utf-8
    >>> print toggle_chinese_page_encoding('utf-8')
    gbk
    """
    original_encoding = original_encoding.lower()
    if original_encoding == 'gbk' or original_encoding == 'gb2312':
        return 'utf-8'
    elif original_encoding == 'utf-8':
        return 'gbk'


# update: 2018-03-19: 现在限制了爬取的页面（文件等其他东西）的大小在50K以内，
# 避免过大的网页卡住爬虫。使用stream=True
def parse_url(url):
    normal_https_flag = False
    headers = {'User-Agent': fake_ua.random}
    try:
        r2 = requests.get(url=url, headers=headers, timeout=time_out, stream=True)
        r2.raise_for_status()
        content_length = r2.header.get('Content-Length')
        if not content_length:
            content_length = 0
        print(content_length)
        content_length = int(content_length)
    except:
        normal_https_flag = True

    if normal_https_flag:
        url = spider_url_to_dpi_url(url)
        url = 'https://' + url 
        try:
            r2 = requests.get(url=url, headers=headers, timeout=time_out)
        except:
            print('%s\t%s' % (url, 'Error-001-程序未能成功地获取页面信息'))
            return 0

    try:
        # requests 对于中文编码的判断不是很准:通常中文网页不是utf-8就是gbk，在这里做简单的判断
        # 1. 先假定认为是utf-8
        if r2.encoding.lower() not in ['utf-8', 'gb2312', 'gbk']:
            r2.encoding = 'utf-8'
        # 2. 如果页面上直接就有gb2312, 那么就是gbk了
        for line in r2.text.split('\n')[:30]:
            line = line.lower()
            if 'meta' in line:
                if 'gb2312' in line:
                    r2.encoding = 'gbk'
                    break
        # print r2.encoding
        soup = BeautifulSoup(r2.text, 'lxml')
    except:
        print('%s\t%s' % (url, 'Error-002-程序未能成功地分析页面信息'))
        return 0

    try:
        title = soup.title.string
        good_cnt = 0
        bad_cnt = 0
        # 如果标题中有这个字符，那么认为是这种情况: 本来是gb2312的网页，被错误的轨道了utf-8编码下，因此需要重新编码
        for charactor in title:
            # 忽略英文和符号字符, 最后两个是日文破折号和全角空格
            if charactor.lower() in u"\r \nabcdefghijklmnopqrstuvwxyz0123456789,.<>!@#$%^&*()[]{}-=+_|/\\~。，【】——（）"u'\u2015'u'\u3000':
                continue
            # 如果是3500常用字系列的，则认为是正确编码
            if charactor in load_search_db.cn_lib_str:
                good_cnt += 1
            # 否则认为是错误编码
            else:
                bad_cnt += 1
        # 如果错误多，认为是未明确声明的gbk编码
        if good_cnt < bad_cnt:
            # 此时就交换中文世界里最常用的两种编码: toggle: utf-8, gbk
            r2.encoding = toggle_chinese_page_encoding(r2.encoding)
            soup = BeautifulSoup(r2.text, 'lxml')
            title = soup.title.string
    except AttributeError:
        print('%s\t%s' % (url, 'Error-003-该页面没有标题'))
        return 0

    if not title:
        print('%s\t%s' % (url, 'Error-003-标题为空'))
        return 0

    try:
        description = soup.find(attrs={"name":"description"})['content']
    except TypeError:
        description = ''
    except KeyError:
        description = ''
    try:
        keywords = soup.find(attrs={"name":"keywords"})['content']
    except TypeError:
        keywords = ''
    except KeyError:
        keywords = ''

    # 采集页面信息
    p_list = []
    collectable_tag = ['h1', 'h2', 'h3', 'h4', 'h5', 'p']
    for tag_name in collectable_tag:
        for i in soup.find_all(tag_name):
            if i.string:
                p_list.append(i.string.strip())

    # 采集页面链接
    a_list = []
    for i in soup.find_all('a'):
        if i.string:
            a_list.append(i.string.strip())

    title = title.strip()
    keywords = keywords.strip()
    description = description.strip()
    data_tuple = title, keywords, description, ' '.join(p_list), ' '.join(a_list)
    msg_body = '\01'.join(data_tuple)
    msg_body = msg_body.replace('\r', '')
    msg_body = msg_body.replace('\n', '')
    msg_body = msg_body.replace('\t', '')
    if r2.url:
        print '%s\t%s' % (url, msg_body)
    else:
        print('%s\t%s' % (url, 'Error-004-程序异常'))


class SpiderThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.queue = q

    def run(self):
        while True:
            if not self.queue.empty():
                try:
                    parse_url(self.queue.get())
                except Exception, e:
                    sys.stderr.write(str(e) + '\n')
            else:
                break


def main_process_handler():
    # 进程内队列，用于多线程处理
    process_queue = queue.Queue()
    # 将分配得到的url灌入本地的队列中
    while True:
        if url_queue.empty():
            break
        url = url_queue.get(True)
        process_queue.put(url)
        # 如果公共队列为空，则停止获取

    # 转入本地多线程执行
    threads = []
    for thread_index in range(0, thread_count):
        spider_thread = SpiderThread(process_queue)
        threads.append(spider_thread)
    # start all threads
    for t in threads:
        t.start()
    # wait untill all threads finish
    for t in threads:
        t.join()


def slice_list(input, size):
    input_size = len(input)
    slice_size = input_size / size
    remain = input_size % size
    result = []
    iterator = iter(input)
    for i in range(size):
        result.append([])
        for j in range(slice_size):
            result[i].append(iterator.next())
        if remain:
            result[i].append(iterator.next())
            remain -= 1
    return result

@contextmanager
def terminating(thing):
    try:
        yield thing
    finally:
        thing.terminate()


def is_https_site(the_input_url):
    if '.kmway.' in the_input_url:
        return True
    else:
        return False

# ------------------- main ------------------------
if __name__ == '__main__':
    # 构建多进程队列
    url_queue = Queue()
    # 向队列中插入文件内的url，补全https或者http
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            line = line.split(None, 1)[0]
            if not line.startswith('http://') and not line.startswith('https://'):
                if is_https_site(line):
                    line = 'https://' + line
                else:
                    line = 'http://' + line
            url_queue.put(line)

    # print url_queue.qsize()
    # 打开进程池，开始处理队列中的url
    if url_queue.qsize() > 0:
        with terminating(Pool(processes=PROCESS_NUM)) as p:
            p.apply(main_process_handler)
    else:
        pass

