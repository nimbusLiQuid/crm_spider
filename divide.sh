# 数据分配子系统总入口
# 作者： 林泉

# 版本: 0.1

# crontab -l

source /home/linquan/.bash_profile
export PATH=/usr/local/bin/:${PATH}
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export PYTHONIOENCODING="UTF-8"

echo "开始执行..."

ls -l `which python`
ls -l `which python3`
ls -l `which python2.6`

# 如果已经存在此进程就直接退出

TIMESTAMP=`date -d "-0 day" "+%Y%m%d%H%M"`
DELETE=`date -d "-0 day -1 hour" "+%Y%m%d%H"`


# 使用自定义细分规则，从tag_id = 3 来细分标签
python3 data_divide.py >> ./divide/update_${TIMESTAMP}.log 2>&1

#find . -name "*.txt" -type f -size 0c|xargs -n 1 rm

# 清理过多的日志

echo "已完成数据划分任务 ✂️"
echo "结果如下:"

cat ./divide/update_${TIMESTAMP}.log
