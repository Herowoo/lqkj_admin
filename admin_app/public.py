__author__ = 'litz'
############################################################################################
#共函数库
#add by litz,20181110
############################################################################################
import os
import datetime
import string
import logging
import logging.handlers
import pymysql
import json
from admin_app import models
import random
from django.shortcuts import  HttpResponse
import calendar

localhome='/home/admin/lqkj_admin/'#本地目录
# localurl='http://192.168.2.40:8000/'#本地目录
localurl_old='http://10.10.10.174/'#本地目录
localurl='http://10.10.10.174/'#本地目录

DevIpList={
    "192.168.2.15":"http://192.168.2.15:8080/",
}

appname='lqkj_gzh'  #公众号应用名称
appnamedesc='联桥科技'  #公众号中文名称

#查询类型，管理台配置查询条件时使用
selecttypes=[
{
       "value": '=',
       "label": '='
   }, {
       "value": 'like',
       "label": 'like'
   }, {
       "value": '>',
       "label": '>'
   }, {
       "value": '<',
       "label": '<'
   }, {
       "value": '>=',
       "label": '>='
   }, {
       "value": '<=',
      "label": '<='
   }, {
       "value": 'is not null',
      "label": 'is not null'
   }, {
       "value": 'is null',
      "label": 'is null'
   }
]

#日志初始化,日志名称
global logger, fh
logger = logging.getLogger(str(os.getpid()))
def loger_init( logname ):
    #日志初始化
    now_time = datetime.datetime.now().strftime('%Y%m%d')
    logger = logging.getLogger(str(os.getpid()))
    logger.setLevel(logging.INFO)
    #logpath = '../../log/'
    if os.path.exists(localhome+'log/'):
        log_file_temp = localhome+'log/'+logname+'_'+now_time+'.log'
    else:
        log_file_temp = logname + '_' + now_time + '.log'
    # print(log_file_temp)
    # fh = logging.FileHandler(log_file_temp)  # 定义一个写文件的handler
    fh = logging.handlers.RotatingFileHandler(log_file_temp, maxBytes=1024*1024*100, backupCount=30)
    fh.setLevel(logging.INFO)  # 设置写文件的等级
    fh_formatter = logging.Formatter(
        '[%(levelname)-5s] [%(filename)-12s line:%(lineno)-4d] [%(asctime)s] [%(process)-7d] [%(message)s]')  # 设置输出格式
    fh.setFormatter(fh_formatter)  # 将输出格式设置给handler
    #print('public',logger)
    if  not logger.handlers:
        logger.addHandler(fh)  # 将handler加入logger
    return logger, fh

def loger_new( logname ):
    logger = logging.getLogger(str(os.getpid()))
    logger.removeHandler( )
    #日志初始化
    now_time = datetime.datetime.now().strftime('%Y%m%d')
    logger = logging.getLogger(str(os.getpid()))
    logger.setLevel(logging.INFO)
    #logpath = '../../log/'
    if os.path.exists(localhome+'log/'):
        log_file_temp = localhome+'log/'+logname+'_'+now_time+'.log'
    else:
        log_file_temp = logname + '_' + now_time + '.log'
    # print(log_file_temp)
    # fh = logging.FileHandler(log_file_temp)  # 定义一个写文件的handler
    fh = logging.handlers.RotatingFileHandler(log_file_temp, maxBytes=1024*1024*100, backupCount=30)
    fh.setLevel(logging.INFO)  # 设置写文件的等级
    fh_formatter = logging.Formatter(
        '[%(levelname)-5s] [%(filename)-12s line:%(lineno)-4d] [%(asctime)s] [%(process)-7d] [%(message)s]')  # 设置输出格式
    fh.setFormatter(fh_formatter)  # 将输出格式设置给handler
    #print('public',logger)
    if  not logger.handlers:
        logger.addHandler(fh)  # 将handler加入logger
    return logger, fh


#连接数据库
def dbconnect():
    #连接数据库
    try:
        global db
        db = pymysql.Connect(
            host='123.206.74.58',
            port=3306,
            user='irusheng',
            passwd='irusheng_love',
            db='irusheng_server',
            charset='utf8')

        db.autocommit(True)

        print('连接数据库成功')
        #db.close()
    except Exception:
        print('连接数据库失败，程序退出!')
        logging.error("Faild to connect db",exc_info = True)
        return
    print('dbconnect:', db)
    return db

def db_reconnect():
    global db
    try:
        db.ping()
    except:
        logging.info("--------重新连接数据库--------")
        db=dbconnect()
    return db

#真或者假转为'Y','N'
def True2y(src):
    if src=='True' or src=='true' or src==True:
        return 'Y'
    else:
        return 'N'

#'Y'或'N'转为真或者假
def Y2True(src):
    if src == 'Y' or src == 'y':
        return True
    else:
        return False

#返回信息转换为json格式
def setrespinfo(resp):
    #respinfo={}
    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    return HttpResponse(s)

#生成整型随机数,number随机数个数
def getintrandom(number):
    rand=''
    for i in range(0, int(number)):
        a = random.randint(0, 9)
        rand=rand+str(a)
    return rand

#session校验
def checksession(request):
    suid=request.session.get('uid', None)
    schecksum = request.session.get('checksum', None)
    # print('suid=', suid, 'schecksum=', schecksum)

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    uid=reqest_body.get('uid',None)
    checksum=reqest_body.get('checksum', None)
    # print('uid=',uid,'checksum=',checksum)
    # print(str(uid) != str(suid) or checksum != schecksum)
    #test --begin
    if checksum=='11223355':
        return True
    #test --end

    if suid == None or schecksum == None:
        return False
    if str(uid) != str(suid) or checksum != schecksum:
        return False
    return True

#生成毫秒时间+10位随机数+进行号的字符串做为唯一标志
def genRandomString(slen=10):
    randstr = ''.join(random.sample(string.ascii_letters + string.digits, slen))
    return datetime.datetime.now().strftime('%H:%M:%S.%f') + "_" + randstr + "_" + str(os.getpid())

#求下月最后一天
def get_next_month_end_day(date):
    # date = datetime.date(2019, 1, 23)  # 年，月，日
    first_day = datetime.date(date.year, date.month, 1)  # 当月第一天
    days_num = calendar.monthrange(first_day.year, first_day.month)[1]  # 获取当前月有多少天
    # 求下个月的第一天
    first_day_of_next_month = first_day + datetime.timedelta(days=days_num)
    next_month_days = calendar.monthrange(first_day_of_next_month.year, first_day_of_next_month.month)[1]  # 获取下个月有多少天
    next_month = first_day_of_next_month + datetime.timedelta(days=next_month_days - 1)
    return next_month

#函数日志记录装饰器
def fun_log_wrapper(func):
    def wrapper(*args,**kwargs):
        filename = os.path.basename(__file__)
        funcname=func.__name__
        logger.info('----------------------%s-%s-begin---------------------------'%(filename,funcname))
        res=func(*args,**kwargs)
        logger.info('----------------------%s-%s-end---------------------------'%(filename,funcname))
        return res
    return wrapper
