#! /bin/sh
#* ** * * ** * * ** * * ** * * ** * * ** * * ** * * ** * * ** * * * * *
# run.sh
# 爬虫系统总入口
# 作者: 林泉
# 版本: 0.3
# last update: 2018-01-05
# crontab -l
# 2,12,22,32,42,52 5-19 * * * source /home/linquan/.bash_profile; cd /home/linquan/workspace/crm_spider; sh run.sh  > update.log 2>&1
#*/5 * * * * source /home/linquan/.bash_profile; cd /home/linquan/workspace/chudian/log_system; sh get.sh; cd /home/linquan/workspace/crm_spider; sh run.sh  > run.log 2>&1

source /home/linquan/.bash_profile
export PATH=/usr/local/bin/:${PATH}
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"

function log()
{
    date_=`date "+%Y%m%d %H:%M:%S "`
    echo ${date_}" "$*
}

# 轮询数据库字段是否>=1，如果>=1，则开始；如果=0就直接简单退出
# # # # 你有更好的办法吗?

str=`curl -u bcdata:bcdata@2701 https://op.vm1.cn/pv.php 2>/dev/null`
# 如果是0个任务则退出
if [ ${str:0:1} = "0"  ]; then
    log "nothing new from https://op.vm1.cn"
    exit 0
else
    log "something new."
fi
# 如果是负数个任务，也退出，并记录异常信息
if [ ${str:0:1} = "-"  ]; then
    log "amazing news from https://op.vm1.cn"
    exit 0
else
    log "something new and amazing."
fi

#ls -l `which python`
#ls -l `which python3`
#ls -l `which python2.6`

# 如果已经存在此进程就直接退出
P_COUNT=`ps aux | grep run.sh | wc -l`
log "$P_COUNT process line with run.sh is running, contains crontab pid and grep itself. "
if [ $P_COUNT -le 8 ]; then
    log "Process run.sh is runnning good."
else
    log "Process is running abnormal. Process numbers is: ${P_COUNT}"
    log "Maybe another run.sh is running, exit now by running: killall run.sh"
    exit 0
fi

TIMESTAMP=`date -d "-0 day" "+%Y%m%d%H%M"`
DELETE=`date -d "-2 month" "+%Y%m"`

URL_DIR=urls_to_spider
mkdir -p ${URL_DIR}
URL_FILE=${URL_DIR}/urls_to_spider_${TIMESTAMP}.txt

log "-------------------------------------------------------------------------------------"
log "generating new urls to be crawled..."
# 获取新的待爬取的URL
python3 yun_db.py > ${URL_FILE} 2>/dev/null

CONTENT_DIR=urls_content
mkdir -p ${CONTENT_DIR}
CONTENT_FILE=${CONTENT_DIR}/urls_content_${TIMESTAMP}.txt
log "-------------------------------------------------------------------------------------"
log "running spiders..."
python spider.py ${URL_FILE} > ${CONTENT_FILE} 2>/dev/null
log "spiders done."

TIMESTAMP=`date -d "-0 day" "+%Y%m%d%H%M"`
URL_FILE=${URL_DIR}/urls_to_spider_${TIMESTAMP}.txt

log "-------------------------------------------------------------------------------------"
# 同步数据结果到数据库中
log "updating results..."
python3 yun_db.py > ${URL_FILE} 2>> ./yun_result.log

LOG_DIR=update_log
mkdir -p ${LOG_DIR}

# 使用获取到的页面结果，将新的URL更新进去
python3 update_url_content.py > ${LOG_DIR}/update_${TIMESTAMP}.log 2>&1

# 预设内容系统
# 使用预先设置的页面内容，将获取失败的内容重新填写
python3 update_missing_url_contents.py >  ${LOG_DIR}/missing_${TIMESTAMP}.log 2>&1

# 剪刀系统: ✂️   使用自定义细分规则，从tag_id = 3 来细分标签
python3 data_divide.py >> ${LOG_DIR}/update_${TIMESTAMP}.log 2>&1

#find . -name "*.txt" -type f -size 0c|xargs -n 1 rm

# 清理过多的日志
rm -f ${URL_DIR}/urls_to_spider_${DELETE}*.txt
rm -f ${CONTENT_DIR}/urls_content_${DELETE}*.txt
rm -f ${LOG_DIR}/update_${DELETE}*.log
rm -f ${LOG_DIR}/missing_${DELETE}*.log
log "-------------------------------------------------------------------------------------"
# 标记爬虫任务数 -1
curl -u bcdata:bcdata@2701 "https://op.vm1.cn/pv.php?action=p" 2>/dev/null
log "Finish All Task."
