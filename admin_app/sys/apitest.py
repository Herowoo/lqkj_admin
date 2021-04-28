import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
import requests
import random
import string

###########################################################################################################
#接口测试交易
#后台透传转发,方便大量的测试案例
#
###########################################################################################################
@transaction.atomic()
def Main_Proc( request ):
    public.respcode, public.respmsg = "999998", "交易开始处理!"
    log = public.logger
    sid = transaction.savepoint()
    func_name=public.tran_type+'(request)'
    if globals().get(public.tran_type):
        log.info('---[%s]-begin---' % (public.tran_type), extra={'ptlsh': public.req_seq})
        public.respinfo = eval(func_name)
        log.info('---[%s]-end----' % (public.tran_type), extra={'ptlsh': public.req_seq})
    else:
        public.respcode, public.respmsg = "100002", "trantype error!"
        public.respinfo = HttpResponse( public.setrespinfo() )
    if public.respcode=="000000":
        # 提交事务
        transaction.savepoint_commit(sid)
    # else:
    #     # 回滚事务
    #     transaction.savepoint_rollback(sid)
    return public.respinfo

#接口测试交易--保存报文配置
def save_pkg_info( request ):
    log = public.logger
    form_var = public.req_body.get('form_var')

    id=form_var.get('id')
    if form_var.get('req_pkg'):
        req_pkg= form_var.get('req_pkg')
    else:
        req_pkg=''
    if form_var.get('resp_pkg'):
        resp_pkg = form_var.get('resp_pkg')
    else:
        resp_pkg = ''
    try:
        cur = connection.cursor()  # 创建游标
        if id:#更新数据
            sql="update sys_api_test set api_name=%s, req_url=%s, req_pkg=%s, resp_pkg=%s, create_userid=%s, " \
                "create_datetime=%s, snote=%s where id=%s"
            cur.execute(sql, (form_var.get('api_name'), form_var.get('req_url'), req_pkg, resp_pkg, public.user_id,
                              datetime.datetime.now(), form_var.get('snote'), id) )
        else: #插入数据
            # sqllog = "insert into sys_api_test(api_name, req_pkg, resp_pkg, create_userid, snote) " \
            #          "values( '%s', '%s', '%s', '%s', '%s')" \
            #          %(form_var.get('api_name'), req_pkg, resp_pkg, int(public.user_id), id)
            # log.info(sqllog, extra={'ptlsh':public.req_seq})

            sql = "insert into sys_api_test(api_name, req_url, req_pkg, resp_pkg, create_userid, snote) values( %s, %s, %s, %s, %s, %s)"
            cur.execute(sql,(form_var.get('api_name'), form_var.get('req_url'), req_pkg, resp_pkg, int(public.user_id), id) )

            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                id = row[0]
                log.info('测试报文保存，自增字段ID:%s' % str(id), extra={'ptlsh': public.req_seq})
            else:
                public.respcode, public.respmsg = "300104", "登记报文配置信息表异常!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        cur.close() #关闭游标
        
    except Exception as ex:
        log.error("登记报文配置信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "登记报文配置信息失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "新增报文配置成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id": public.req_body.get("form_id"),
            "form_var": {
                "id": id,
                "api_name": form_var.get("api_name"),
                "req_url": form_var.get("req_url"),
                "req_pkg": form_var.get("req_pkg"),
                "resp_pkg": form_var.get("resp_pkg"),
                "snote": form_var.get("snote"),
            }
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 接口测试交易--发起交易
def tran_pkg_info(request):
    log = public.logger
    form_var = public.req_body.get('form_var')

    id = form_var.get('id')

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select req_pkg from sys_api_test where id=%s"
        cur.execute(sql, (id))
        row=cur.fetchone()
        if row:
            req_pkg = row[0]
        else:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "300114", "报文配置信息不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        log.info("type1=%s, req_pkg=%s" % (type(req_pkg), req_pkg), extra={'ptlsh': public.req_seq})
        req_pkg_json=json.loads(req_pkg)

        if req_pkg_json["HEAD"].get("req_seq"):
            req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join( random.sample(string.digits, 2))
            req_pkg_json["HEAD"]["req_seq"]=req_seq
        if req_pkg_json["HEAD"].get("checksum"):
            req_pkg_json["HEAD"]["checksum"] = "11223355"

        url = form_var.get('req_url')
        req_pkg = json.dumps(req_pkg_json)

        log.info("url=%s" % url, extra={'ptlsh': public.req_seq})
        log.info("type2=%s, req_pkg=%s" % (type(req_pkg), req_pkg), extra={'ptlsh': public.req_seq})
        resp_pkg = requests.post(url, req_pkg)
        resp_pkg = json.dumps(resp_pkg.text, cls=public.JsonCustomEncoder, ensure_ascii=False)
        resp_pkg = eval(resp_pkg) #格式化返回的报文
        # print('2', type(resp_pkg), resp_pkg)
        resp_pkg_json=json.loads(resp_pkg)
        head = resp_pkg_json.get('HEAD')
        resp_code = head.get('respcode')

        sql = "update sys_api_test set resp_pkg=%s, resp_code=%s where id=%s"
        log.info("sql=" +sql % ( str(resp_pkg), str(resp_code), id ), extra={'ptlsh': public.req_seq})
        cur.execute(sql, ( str(resp_pkg), str(resp_code), id ) )
        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("接口测试失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "接口测试失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "接口测试成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id": public.req_body.get("form_id"),
            "form_var": {
                "id": id,
                "api_name": form_var.get("api_name"),
                "req_url": form_var.get("req_url"),
                "req_pkg": req_pkg,
                "resp_pkg": resp_pkg,
                "snote": form_var.get("snote"),
            }
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

