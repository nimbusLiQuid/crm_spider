# 爬虫系统总入口
# 作者： 林泉

# 版本: 0.1

# crontab -l
# 2,12,22,32,42,52 5-19 * * * source /home/linquan/.bash_profile; cd /home/linquan/workspace/crm_spider; sh run.sh  > update.log 2>&1

source /home/linquan/.bash_profile
export PATH=/usr/local/bin/:${PATH}

# 如果已经存在此进程就直接退出
P_COUNT=`ps aux | grep run.sh | wc -l`
echo $P_COUNT
if [ $P_COUNT -eq 1 ]; then
    echo "Process run.sh is runnning."
else
    echo "Process is not running."
fi

TIMESTAMP=`date -d "-0 day" "+%Y%m%d%H%M"`
DELETE=`date -d "-0 day -1 hour" "+%Y%m%d%H%M"`

URL_DIR=urls_to_spider
mkdir -p ${URL_DIR}
URL_FILE=${URL_DIR}/urls_to_spider_${TIMESTAMP}.txt

# 获取新的待爬取的URL
python3 yun_db.py > ${URL_FILE}

CONTENT_DIR=urls_content
mkdir -p ${CONTENT_DIR}
CONTENT_FILE=${CONTENT_DIR}/urls_content_${TIMESTAMP}.txt
python2.6  spider.py ${URL_FILE} > ${CONTENT_FILE} 2>/dev/null

TIMESTAMP=`date -d "-0 day" "+%Y%m%d%H%M"`
URL_FILE=${URL_DIR}/urls_to_spider_${TIMESTAMP}.txt

# 同步数据结果到数据库中
python3 yun_db.py > ${URL_FILE}

LOG_DIR=update_log
mkdir -p ${LOG_DIR}

# 使用获取到的页面结果，将新的URL更新进去
python3 update_url_content.py > ${LOG_DIR}/update_${TIMESTAMP}.log 2>&1

#find . -name "*.txt" -type f -size 0c|xargs -n 1 rm

# 清理过多的日志
rm -f ${URL_DIR}/urls_to_spider_${DELETE}.txt
rm -f ${CONTENT_DIR}/urls_content_${DELETE}.txt
rm -f ${LOG_DIR}/update_${DELETE}.log
