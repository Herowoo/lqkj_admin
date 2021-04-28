from django.shortcuts import HttpResponse
from django.db import connection
import sys
import traceback
import json
import random
import string
import datetime
from admin_app.sys import public

maxlength = 1024 ** 2  # 最大日志记载


# 入口主流程.V6版本管理台接口通讯都先经过此函数
# @transaction.atomic  # 当前视图函数中支持事务 #外加事务支持的业务代码内部就不要做泛型的try catch异常捕捉，这样会导致，真正的事务支持接不到异常，导致可能所需的事务回滚不会执行。
def Enter(request):
    global log, fh
    operate_list_upd_flag = False  # 更新用户操作流水表标志
    # 请求流水号赋初值
    public.req_seq = 'PT_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(
        random.sample(string.digits, 6))  # 请求流水号，变量初始化一下 用户号8位+日期6位+序列号6位

    # print('根目录:', public.localhome)

    def check_user_auth():
        sql = "select  state from sys_user where user_id=%s "
        cur.execute(sql, public.user_id)
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "110002", "用户不存在!"
            return False
        db_state = row[0]
        if str(db_state) != '1':
            public.respcode, public.respmsg = "110003", "用户状态异常!"
            return False
        # 校验成功。
        return True

    try:
        cur = connection.cursor()  # 创建游标

        starttime = datetime.datetime.now()
        # 获取访问路径
        if request.path[-1] == '/':
            param1 = request.path.rsplit('/')[-2]
        else:
            param1 = request.path.rsplit('/')[-1]

        # 初始化日志，根据请求的接口类别自动创建子日志
        if param1:
            log, fh = public.loger_init(param1)
        else:
            log, fh = public.loger_init('Admin_Main')

        log.info('----------------------Admin_Main-begin---------------------------', extra={'ptlsh': public.req_seq})
        log.info("请求path:[%s]" % request.path, extra={'ptlsh': public.req_seq})
        log.info("请求method:[%s]" % request.method, extra={'ptlsh': public.req_seq})
        log.info("请求GET:[%s]" % request.GET, extra={'ptlsh': public.req_seq})

        reqest_body = json.loads(request.body.decode(encoding='utf-8'))  # 请求报文转换为JSON报文
        if request.method != "POST":  # 仅支持POST调用
            public.respcode, public.respmsg = "100000", "api error! Support only POST!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        if len(str(request.body)) < maxlength:  # 日志太大不打印了,如文件上传等日志。
            req_pkg = reqest_body
            log.info("请求body:[%d][%s]" % (len(str(request.body)), str(req_pkg)), extra={'ptlsh': public.req_seq})
        else:
            req_pkg = '请求报文太大，不再登记到表中'  # 大的请求报文不再登记到表中

        # 获取请求变量
        public.req_ip = request.META.get('REMOTE_ADDR')  # 请求IP地址
        public.req_head = reqest_body.get('HEAD', None)  # 请求报文头
        public.req_body = reqest_body.get('BODY', None)  # 请求报文体
        if public.req_head:
            public.menu_id = public.req_head.get('mid', '')  # 菜单ID
            public.user_id = public.req_head.get('uid', None)  # 请求用户ID
            public.check_sum = public.req_head.get('checksum')  # session校验码
            public.tran_type = public.req_head['tran_type']  # 交易代码
            public.req_seq = public.req_head['req_seq']  # 请求流水号
        else:
            log.info("请求报文头错误!", extra={'ptlsh': public.req_seq})
            public.respcode, public.respmsg = "100000", "请求报文头错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 判断是否记录日志
        sql = "select 1 from sys_nolog_trantype where tran_type=%s"
        # log.info("判断是否记录日志:"+sql % public.tran_type, extra={'ptlsh': public.req_seq})
        cur.execute(sql, public.tran_type)
        row = cur.fetchone()
        # log.info("判断是否记录日志row:" + str(row), extra={'ptlsh': public.req_seq})
        if not row:
            try:
                sql = "INSERT INTO sys_user_operate_list(user_id,tran_type,req_ip,req_seq,req_pkg) VALUES (%s,%s,%s,%s,%s)"
                cur.execute(sql, (public.user_id, public.tran_type, public.req_ip, public.req_seq, str(req_pkg)))
                # connection.commit()  # 直接提交事务
                operate_list_upd_flag = True  # 有插入有更新，无插入不更新
            except Exception as e:
                log.error('插入用户操作日志表失败:' + str(e), exc_info=True, extra={'ptlsh': public.req_seq})
                public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
                if 'for key' in str(e):
                    log.info("请求流水号重复![%s]" % public.req_seq, extra={'ptlsh': public.req_seq})
                    public.respcode, public.respmsg = "100000", "请求流水号重复!"
                    public.respinfo = HttpResponse(public.setrespinfo())
                    return public.respinfo
                else:
                    public.respcode, public.respmsg = "100000", "插入用户操作日志表失败!"
                    public.respinfo = HttpResponse(public.setrespinfo())
                    return public.respinfo

        # 校验session
        if public.tran_type not in ['user_login_bypasswd']:
            # sesession校验
            if public.checksession(request) == False:
                public.respcode, public.respmsg = "100000", "请重新登陆!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            else:
                log.info("Session校验通过", extra={'ptlsh': public.req_seq})

            # 判断用户状态,用户权限
            if not check_user_auth():
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        # 根据请求path处理接口数据
        path = request.path.split('/')
        # 调用指定函数
        try:
            # 动态地import需要创建的类，减少报错，内存的使用，加快速度等
            cmd_import = 'from admin_app.%s import %s' % (path[2], path[3])
            # print('cmd_import=', cmd_import)
            exec(cmd_import)  # 动态地import需要创建的类
            func_main_name = '%s.Main_Proc(request)' % (path[3])
            # print('func_main_name=', func_main_name)
            log.info("----Main-[%s.Main_Proc]-start---" % (path[3]), extra={'ptlsh': public.req_seq})
            public.respinfo = eval(func_main_name)
            log.info("----Main-[%s.Main_Proc]-end----" % (path[3]), extra={'ptlsh': public.req_seq})
        except Exception as ex:
            log.error('程序运行错误:' + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
            public.respcode, public.respmsg = "110001", "url error!"
            public.respinfo = HttpResponse(public.setrespinfo())

        cur.close()  # 关闭游标
        return public.respinfo
    except Exception as e:
        # print("获取错误信息:", traceback.print_exc())
        log.error('程序运行错误:' + str(e), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    finally:
        try:
            if not public.respinfo:  # 如果返回信息为空
                public.respcode, public.respmsg = "1000009", "系统错误[返回数据异常]"
                public.respinfo = HttpResponse(public.setrespinfo())

            resp_pkg = public.respinfo.getvalue().decode(encoding='utf-8')
            if len(str(resp_pkg)) < maxlength:  # 日志太大不打印了,如文件上传等日志。
                # print('finally3, respinfo=', public.respinfo)
                log.info("返回报文:[%d][%s]" % (len(str(public.respinfo)), resp_pkg), extra={'ptlsh': public.req_seq})
            else:
                resp_pkg = '返回报文太大，不记录到表中'  # 返回报文太大，不记录到表中

            if operate_list_upd_flag:
                # 获取错误堆栈中的错误信息，并格式化
                if public.exc_type and public.exc_value and public.exc_traceback:
                    errmsg = str(public.exc_type) + ' ' + str(public.exc_value)
                    for item in traceback.extract_tb(public.exc_traceback, 10):
                        # print('item=', item[0], item[1],item[2],item[3], type(item[0])) #“预处理”堆栈跟踪条目是一个4元组（文件名，行号，函数名称*，文本）
                        errmsg = errmsg + '\n' + repr(item)
                else:
                    errmsg = ''  # 未获取到错误信息
                # 更新用户操作流水表返回结果
                cur = connection.cursor()  # 创建游标
                sql = "update sys_user_operate_list set user_id=%s, resp_time=%s,resp_code=%s,resp_msg=%s,resp_pkg=%s,error_msg=%s where req_seq=%s"
                cur.execute(sql, (
                public.user_id, datetime.datetime.now(), public.respcode, public.respmsg, str(resp_pkg), str(errmsg),
                public.req_seq))
                connection.commit()  # 直接提交事务
                cur.close()  # 关闭游标
            # connection.close() #关闭数据库

            log.info('交易处理时间: %s' % str(datetime.datetime.now() - starttime), extra={'ptlsh': public.req_seq})
            log.info('----------------------Admin_Main-end---------------------------', extra={'ptlsh': public.req_seq})

            if fh:
                fh.close()
                log.removeHandler(fh)
        except Exception as e:
            log.error('系统finally处理失败:' + str(e), exc_info=True, extra={'ptlsh': public.req_seq})
        return public.respinfo
