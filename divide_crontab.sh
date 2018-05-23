# 数据分配子系统总入口
# 作者： 林泉

# 版本: 0.1

source /home/linquan/.bash_profile
export PATH=/usr/local/bin/:${PATH}
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export PYTHONIOENCODING="UTF-8"

ls -l `which python`
ls -l `which python3`
ls -l `which python2.6`

# 使用自定义细分规则，从tag_id = 3 来细分标签
TIMESTAMP=`date -d "-0 day" "+%Y%m%d%H%M%S"`
python3 data_divide_dev.py /var/www/html/bcwiki/data/pages/crm/crm_tag_divide_glj.txt  >> ./divide/update_${TIMESTAMP}.log 2>&1

echo "结果如下:"

cat ./divide/update_${TIMESTAMP}.log

echo "已完成数据划分任务 ✂️"
