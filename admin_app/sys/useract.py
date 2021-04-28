import hashlib
import sys
from django.shortcuts import HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime


###########################################################################################################
# 用户登陆、用户信息修改、用户密码信息、用户信息查询、用户待办事项、登陆历史、操作历史。
# add by litz, 20200413
#
###########################################################################################################

# 增删改查配置数据操作主流程
@transaction.atomic()
def Main_Proc(request):
    public.respcode, public.respmsg = "999998", "交易开始处理!"
    log = public.logger
    sid = transaction.savepoint()
    func_name = public.tran_type + '(request)'
    if globals().get(public.tran_type):
        log.info('---[%s]-begin---' % (public.tran_type), extra={'ptlsh': public.req_seq})
        public.respinfo = eval(func_name)
        log.info('---[%s]-end----' % (public.tran_type), extra={'ptlsh': public.req_seq})
    else:
        public.respcode, public.respmsg = "100002", "trantype error!"
        public.respinfo = HttpResponse(public.setrespinfo())
    if public.respcode == "000000":
        # 提交事务
        transaction.savepoint_commit(sid)
    # else:
    #     # 回滚事务
    #     transaction.savepoint_rollback(sid)
    return public.respinfo


# 用户使用密码登陆
def user_login_bypasswd(request):
    log = public.logger
    body = public.req_body
    login_name = body.get('login_name')
    login_pswd = body.get('login_pswd')
    try:
        cur = connection.cursor()  # 创建游标
        sql = "select user_id,passwd,state, head_imgurl from sys_user where login_name=%s "
        cur.execute(sql, login_name)
        row = cur.fetchone()
        if not row:
            cur.close()
            public.respcode, public.respmsg = "101000", "用户不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        public.user_id = row[0]
        passwd = row[1]
        state = row[2]
        db_head_imgurl = row[2]
        if row[3]:
            db_head_imgurl = eval(row[3])
        else:
            db_head_imgurl = []

        if state != '1':
            cur.close()
            public.respcode, public.respmsg = "101001", "用户状态异常!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if passwd != login_pswd:
            cur.close()
            public.respcode, public.respmsg = "101002", "用户密码不正确!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur.close()

        checkstr = str(public.user_id) + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        m = hashlib.md5()
        m.update(checkstr.encode('utf-8'))
        public.check_sum = m.hexdigest()
        # log.info('checksum=' + public.check_sum)

        # session赋值
        request.session['uid'] = public.user_id
        request.session['user_id'] = public.user_id
        request.session['checksum'] = public.check_sum
        request.session['logintype'] = 'password'  # password-密码, qrcode-二维码,msgcode-短信

    except Exception as ex:
        log.error("登陆失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "101009", "登陆失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "用户登陆成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "uid": public.user_id,
            "checksum": public.check_sum,
            "head_imgurl": db_head_imgurl,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 跳转登陆后获取用户名称、头像、登陆方式等信息
def get_user_info(request):
    log = public.logger
    body = public.req_body

    try:
        # 查找管理台用户信息表权限
        cur = connection.cursor()
        sql = "select user_name, login_name, passwd, station, certi_type, certi, sex, address, tel, email, state, head_imgurl, snote " \
              "from sys_user where user_id='%s'" % (public.user_id)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            db_user_name = row[0]
            db_login_name = row[1]
            db_passwd = row[2]
            db_station = row[3]
            db_certi_type = row[4]
            db_certi = row[5]
            db_sex = row[6]
            db_address = row[7]
            db_tel = row[8]
            db_email = row[9]
            db_state = row[10]
            if row[11]:
                db_head_imgurl = eval(row[11])
            else:
                db_head_imgurl = []
            db_snote = row[12]
        else:
            cur.close()
            public.respcode, public.respmsg = "101004", "用户不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

    except Exception as ex:
        log.error("用户信息查询失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "101010", "用户信息查询失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "用户信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "user_name": db_user_name,
            # "passwd": db_passwd,
            "station": db_station,
            "certi_type": db_certi_type,
            "certi": db_certi,
            "sex": db_sex,
            "address": db_address,
            "tel": db_tel,
            "email": db_email,
            "state": db_state,
            "head_imgurl": db_head_imgurl,
            "snote": db_snote,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 新增用户 --暂时不用。
def add_user_info(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    user_name = form_var.get('user_name', '')
    login_name = form_var.get('login_name', '')
    passwd = form_var.get('passwd', '')
    station = form_var.get('station', '')
    certi_type = form_var.get('certi_type', '')
    certi = form_var.get('certi', '')
    sex = form_var.get('sex', '')
    address = form_var.get('address', '')
    tel = form_var.get('tel', '')
    email = form_var.get('email', '')
    state = form_var.get('state', '')
    head_imgurl = str(form_var.get('head_imgurl', ''))
    snote = form_var.get('snote', '')

    if not user_name:
        public.respcode, public.respmsg = "101101", "用户名不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not login_name:
        public.respcode, public.respmsg = "101102", "登陆名不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not passwd:
        public.respcode, public.respmsg = "101103", "登陆密码不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        # 查找管理台用户信息表权限
        cur = connection.cursor()
        sql = "select user_name from sys_user where login_name='%s'" % (login_name)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            cur.close()
            public.respcode, public.respmsg = "101011", "用户已存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sql = "insert into sys_user(user_name,login_name,passwd,station,certi_type, certi,sex,address,tel, email, state, head_imgurl,operate_userid, snote) " \
              "values(%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s)"
        insert_paras = (
        user_name, login_name, passwd, station, certi_type, certi, sex, address, tel, email, state, head_imgurl,
        public.user_id, snote)
        cur.execute(sql, insert_paras)

        cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
        row = cur.fetchone()
        if row:
            uid = row[0]
            userid = uid
            log.info('USER_ID生成，自增字段ID:%s' % str(uid), extra={'ptlsh': public.req_seq})
        else:
            public.respcode, public.respmsg = "100119", "用户信息添加异常!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 用户角色处理
        userrole = form_var.get('user_role')
        sql = "delete from sys_user_role where user_id=%s "
        cur.execute(sql, userid)
        for item in userrole:
            sql = "insert into sys_user_role(user_id, role_id, user_above_id, operate_userid) values(%s, %s, %s, %s)"
            cur.execute(sql, (userid, item, public.user_id, public.user_id))

        # 用户机构处理
        org_selectd = form_var.get('org_selectd')
        sql = "delete from sys_user_org where user_id=%s "
        cur.execute(sql, userid)
        for item in org_selectd:
            sql = "insert into sys_user_org(user_id, org_id, user_above_id, operate_userid) values(%s, %s, %s, %s)"
            log.info(sql % (userid, item, public.user_id, public.user_id), extra={'ptlsh': public.req_seq})
            cur.execute(sql, (userid, item, public.user_id, public.user_id))

        cur.close()

    except Exception as ex:
        log.error("用户信息添加失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "101010", "用户信息添加失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "用户信息添加成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "user_name": user_name,
            "uid": uid,
            "head_imgurl": head_imgurl,
            "certi_type": certi_type,
            "certi": certi,
            "sex": sex,
            "address": address,
            "tel": tel,
            "state": state,
            "snote": snote,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 修改用户信息,用户密码等
def update_user_info(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        # 查找管理台用户信息表权限
        cur = connection.cursor()
        sql = "select user_name, login_name, passwd, station, certi_type, certi, sex, address, tel, email, state, head_imgurl, snote " \
              "from sys_user where user_id='%s'" % (public.user_id)
        log.info("用户信息查询:" + str(sql), exc_info=True, extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            db_user_name = row[0]
            db_login_name = row[1]
            db_passwd = row[2]
            db_station = row[3]
            db_certi_type = row[4]
            db_certi = row[5]
            db_sex = row[6]
            db_address = row[7]
            db_tel = row[8]
            db_email = row[9]
            db_state = row[10]
            db_head_imgurl = row[11]
            db_snote = row[12]
        else:
            cur.close()
            public.respcode, public.respmsg = "101004", "用户不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        login_name = form_var.get('login_name', db_login_name)
        user_name = form_var.get('user_name', db_user_name)
        userid = form_var.get('user_id')
        station = form_var.get('station', db_station)
        certi_type = form_var.get('certi_type', db_certi_type)
        certi = form_var.get('certi', db_certi)
        sex = form_var.get('sex', db_sex)
        address = form_var.get('address', db_address)
        tel = form_var.get('tel', db_tel)
        email = form_var.get('email', db_email)
        state = form_var.get('state', db_state)
        head_imgurl = str(form_var.get('head_imgurl', db_head_imgurl))
        snote = form_var.get('snote', db_snote)
        passwd_new = form_var.get('passwd', db_passwd)

        sql = "update sys_user set login_name=%s, user_name=%s, passwd=%s, station=%s,certi_type=%s, certi=%s, sex=%s, address=%s, " \
              "tel=%s,email=%s, state=%s, head_imgurl=%s, operate_userid=%s, operate_datetime=%s, snote=%s where user_id=%s"
        log.info(
            "用户信息更新:" + sql % (login_name, user_name, passwd_new, station, certi_type, certi, sex, address, tel, email,
                               state, head_imgurl, public.user_id, datetime.datetime.now(), snote, userid),
            extra={'ptlsh': public.req_seq})
        cur.execute(sql, (
        login_name, user_name, passwd_new, station, certi_type, certi, sex, address, tel, email, state, head_imgurl,
        public.user_id, datetime.datetime.now(), snote, userid))

        # 用户角色处理
        userrole = form_var.get('user_role')
        sql = "delete from sys_user_role where user_id=%s "
        log.info(sql)
        cur.execute(sql, userid)
        for item in userrole:
            sql = "insert into sys_user_role(user_id, role_id, user_above_id, operate_userid) values(%s, %s, %s, %s)"
            log.info(sql % (userid, item, public.user_id, public.user_id))
            cur.execute(sql, (userid, item, public.user_id, public.user_id))

        # 用户机构处理
        org_selectd = form_var.get('org_selectd')
        sql = "delete from sys_user_org where user_id=%s "
        cur.execute(sql, userid)
        for item in org_selectd:
            sql = "insert into sys_user_org(user_id, org_id, user_above_id, operate_userid) values(%s, %s, %s, %s)"
            log.info( sql % (userid, item, public.user_id, public.user_id) , extra={'ptlsh': public.req_seq})
            cur.execute(sql, (userid, item, public.user_id, public.user_id))

        cur.close()
    except Exception as ex:
        log.error("用户信息更新失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "101010", "用户信息更新失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "用户信息修改成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "user_name": user_name,
            "uid": public.user_id,
            "head_imgurl": head_imgurl,
            "certi_type": certi_type,
            "certi": certi,
            "sex": sex,
            "address": address,
            "tel": tel,
            "state": state,
            "snote": snote,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 用户自己修改用户密码
def update_user_passwd(request):
    log = public.logger
    body = public.req_body
    passwd_old = body.get('passwd_old')
    passwd_new = body.get('passwd_new')

    try:
        # 查找管理台用户信息表权限
        cur = connection.cursor()
        sql = "select passwd from sys_user where user_id='%s'" % (public.user_id)
        log.info("用户信息查询:" + str(sql), exc_info=True, extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            db_passwd = row[0]
        else:
            cur.close()
            public.respcode, public.respmsg = "101004", "用户不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        if passwd_new:  # 有新密码，需要修改密码
            if passwd_old != db_passwd:
                cur.close()
                public.respcode, public.respmsg = "101002", "用户旧密码不正确!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        else:
            cur.close()
            public.respcode, public.respmsg = "101009", "用户新密码是必输项!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sql = "update sys_user set  passwd=%s where user_id=%s"
        log.info("用户信息更新:" + sql % (passwd_new, public.user_id), extra={'ptlsh': public.req_seq})
        cur.execute(sql, (passwd_new, public.user_id))

        cur.close()

    except Exception as ex:
        log.error("用户信息更新失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "101010", "用户信息更新失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "用户信息修改成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {},
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 用户消息列表获取,最近的新消息
def user_message_list(request):
    log = public.logger
    body = public.req_body
    try:

        cur = connection.cursor()  # 创建游标
        sql = "select id, tran_date, type, content, msg_status from sys_user_message where user_id=%s and state='0'"
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        msglist = []
        if rows:
            for item in rows:
                msglist.append({"id": item[0], "datetime": item[1], "content": item[3], "msg_status": item[4]})

        cur.close()

    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "msg_list": msglist,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 用户消息详情获取,消息内容，并更新阅读时间
def user_message_info(request):
    log = public.logger
    body = public.req_body
    id = body.get('id')
    try:
        cur = connection.cursor()  # 创建游标
        sql = "select id,tran_date,type,content,message,msg_status from sys_user_message where id=%s "
        cur.execute(sql, id)
        row = cur.fetchone()
        if not row:
            cur.close()
            public.respcode, public.respmsg = "101012", "消息不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        msginfo = {"id": row[0], "datetime": row[1], "content": row[3],
                   "message": row[4], "msg_status": row[5]}

        sql = "update sys_user_message set read_time=%s,state='1' where id=%s"
        cur.execute(sql, (datetime.datetime.now(), id))

        cur.close()

    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "msg_info": msginfo,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 键值转换
def formKvsTran(cur, form_id, kvs):
    log = public.logger
    # log.info('开始转换,form_id=%s,kvs=%s'%(form_id,kvs))
    # #用车申请
    # if str(form_id)in ('10102', '10199','10196','10200'):
    sql = ''
    for key, value in kvs.items():
        try:
            if key == 'user_id':  # 用户
                sql = "select user_name from sys_user where user_id=%s" % value
                cur.execute(sql)
                kvs[key] = cur.fetchone()[0]
            elif key == 'department':  # 部门
                sql = "select org_name from sys_org where org_spell='%s'" % value
                cur.execute(sql)
                kvs[key] = cur.fetchone()[0]
            # elif key=='car_type': #车辆类型
            #     sql="select CONCAT(car_type,'-',car_number) from yw_workflow_apply_car_info where status='1' and car_type='%s'"% value
            #     cur.execute(sql)
            #     kvs[key] = cur.fetchone()[0]
            #     # kvs[key] = value
            elif key == 'status':  # 当前状态
                if str(form_id) == '10102':
                    sql = "select dict_target from sys_ywty_dict where dict_name='YW_WORKFLOW_APPLY_CAR.STATUS' and dict_code=%s" % value
                else:
                    sql = "select dict_target from sys_ywty_dict where dict_name='WORKFLOW_APPLY_TABLE_STATUS' and dict_code=%s" % value
                cur.execute(sql)
                kvs[key] = cur.fetchone()[0]
            elif key == 'apply_state':  # 审批状态
                sql = "select dict_target from sys_ywty_dict where dict_name='FLOW_WORK_APPLY_STATE' and dict_code=%s" % value
                cur.execute(sql)
                kvs[key] = cur.fetchone()[0]
            elif key == 'category':  # 请假类型
                sql = "select DICT_TARGET from sys_ywty_dict where  dict_name='LEAVE_TYPE' and  DICT_CODE ='%s'" % value
                cur.execute(sql)
                kvs[key] = cur.fetchone()[0]
            elif key == 'seal_type':  # 用章类型
                sql = "select DICT_TARGET from sys_ywty_dict where  dict_name='SEAL_TYPE' and  DICT_CODE ='%s'" % value
                cur.execute(sql)
                kvs[key] = cur.fetchone()[0]
        except Exception as ex:
            log.info('sql:' + sql)
            log.info('form_id:[%s], data:[%s]' % (form_id, str(kvs)))
            log.error('数据字典映射失败:' + str(ex))
    return kvs


# 获取form值字典
def getFormTable(cur, form_id, gl_id):
    # 根据form_id查询表名
    sql = "select table_name, selsql, table_head from sys_workflow_tran where form_id='%s'" % form_id
    cur.execute(sql)
    row = cur.fetchone()
    table_name = row[0]
    selsql = row[1]
    if selsql:  # 直接配置查询的SQL语句-支持联表查询
        sql = selsql % (gl_id)
        filed_name_list = []
        for field_id in sql.split('select')[1].split('from')[0].split(','):
            filed_name_list.append(field_id.strip())
        tableHead = eval(row[2])
    else:
        # 获取记录字段名列表
        sql = "select field_id,field_name from sys_form_cfg_fieldlist where form_id='%s' and show_able='Y' " \
              "and comp_type in ('textarea', 'input', 'datetime', 'select', 'radio', 'date') order by id asc" \
              % (form_id)
        cur.execute(sql)
        rows = cur.fetchall()
        tableHead = []
        filed_name_list = []
        for field_id, field_name in rows:
            if field_name == '拟用印类型':
                show_style = "background-color:#DCDCDC; color:	#FF6A6A"
            else:
                show_style = None
            tableHead.append({
                'name': field_id,
                'label': field_name,
                'style': show_style
            })
            filed_name_list.append(field_id)
        sql = "select %s from %s where id=%s" % (','.join(filed_name_list), table_name, gl_id)
    # print('xx sql=', sql)
    tableData = {}
    cur.execute(sql)
    row = cur.fetchone()
    if row:
        for i in range(len(row)):
            tableData[filed_name_list[i]] = row[i]
            # if value_type_dict[filed_name_list[i]]=='int':
            #     filed_dict[filed_name_list[i]] = int(row[i])

    return tableHead, tableData


# 获取待审批详情
def get_wait_apply_detail(request):
    log = public.logger
    body = public.req_body
    try:
        cur = connection.cursor()  # 创建游标
        node_id = body.get('node_id')
        # gl_id=body.get('gl_id')
        # 根据node_id查form_id,gl_id
        sql = "select form_id,gl_id from sys_workflow_node_list where node_id=%s" % node_id
        # cur.execute(sql)
        # wf_id=cur.fetchone()[0]
        # #根据wf_id查form_id
        # sql="select form_id from sys_workflow_node_cfg where wf_id=%s"%wf_id
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            # 查历史表
            sql = "select form_id,gl_id from sys_workflow_node_list_his where node_id=%s" % node_id
            # cur.execute(sql)
            # wf_id=cur.fetchone()[0]
            # #根据wf_id查form_id
            # sql="select form_id from sys_workflow_node_cfg where wf_id=%s"%wf_id
            cur.execute(sql)
            row = cur.fetchone()

        form_id = row[0]
        gl_id = row[1]
        # 根据form_id获取tableHead和tableData
        tableHead, tableData = getFormTable(cur, form_id, gl_id)

        # 键值转换
        tableData = formKvsTran(cur, form_id, tableData)


    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "tableHead": tableHead,
            "tableData": [tableData]
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 获取流程进度
def get_flow_speed(request):
    log = public.logger
    body = public.req_body
    try:
        cur = connection.cursor()  # 创建游标
        order_number = body.get('order_number')
        # 查询全部流程节点
        sql = "select A.wf_id,A.insert_date,A.update_date,A.node_state,A.notes,B.user_name,A.title,A.wf_type from sys_workflow_node_list A " \
              "left join sys_user B on A.user_id=B.user_id where A.order_number='%s' order by A.node_id" % (
                  order_number)
        cur.execute(sql)
        rows = cur.fetchall()
        if len(rows) == 0:
            # 查询历史流程节点
            sql = "select A.wf_id,A.insert_date,A.update_date,A.node_state,A.notes,B.user_name,A.title,A.wf_type from sys_workflow_node_list_his A " \
                  "left join sys_user B on A.user_id=B.user_id where A.order_number='%s' order by A.node_id" % (
                      order_number)
            cur.execute(sql)
            rows = cur.fetchall()
        step_data = []
        temp = {}
        for wf_id, insert_date, update_date, node_state, notes, user_name, title, wf_type in rows:
            if temp.get(str(wf_id)):
                temp[str(wf_id)].append([wf_id, insert_date, update_date, node_state, notes, user_name, title, wf_type])
            else:
                temp[str(wf_id)] = [[wf_id, insert_date, update_date, node_state, notes, user_name, title, wf_type]]

        commit_flag = True
        active = 0
        for wf_id, values in temp.items():
            desc_data = []
            status_dict = {
                '0': '等待审核',
                '1': '审核通过',
                '2': '审核失败'
            }
            description = '审核通过'
            title = ''
            flag = True  # 是否继续下一节点
            for wf_id, insert_date, update_date, node_state, notes, user_name, title, wf_type in values:
                if node_state == '0':
                    update_date = ''
                if wf_type == 'apply_user':
                    content = '发起申请'
                    node_state = '1'
                else:
                    content = status_dict[node_state]
                desc_data.append({
                    'user': user_name,
                    'content': content,
                    'datetime': update_date,
                    'result_opinion': notes
                })
                if node_state == '2' or node_state == '0':
                    flag = False

                if node_state == '2':
                    description = '不同意'
                if node_state == '0' and description == '审核通过':
                    description = '进行中'
                title = title
            status = ''
            if description == '审核通过' or description == '发起申请':
                status = 'success'
            elif description == '进行中':
                status = 'wait'
                commit_flag = False
            elif description == '不同意':
                status = 'error'
            if flag:
                active += 1
            step_data.append({
                'title': title,
                'description': description,
                'status': status,
                'descdata': desc_data,
            })

        # 如果审批已经结束，增加一个节点“审批结束”
        if commit_flag:
            step_data.append({
                'title': '流程结束',
                'description': '审批完成',
                'status': 'success',
                'descdata': [],
            })

        examform = {
            "commit_flag": commit_flag,
            "active": active,
            "stepdata": step_data
        }




    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "examform": examform
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 审批处理
def workflow_apply_handle(request):
    log = public.logger
    body = public.req_body
    try:
        cur = connection.cursor()  # 创建游标
        node_id = body.get('node_id')
        result = body.get('result')
        remark = body.get('remark')
        order_number = body.get('order_number')
        if result:
            node_state = '1'
        else:
            node_state = '2'
        # 将流程节点状态更新
        sql = "update sys_workflow_node_list set update_date=CURRENT_TIMESTAMP, node_state='%s',notes='%s' " \
              "where node_id='%s'" % (node_state, remark, node_id)
        cur.execute(sql)

        # 判断审核状态
        flag = 0  # 0等待 1通过 2失败
        # 如果有状态为2的审核记录 就认为最终审核失败
        sql = "select node_id from sys_workflow_node_list where order_number='%s' and node_state='2'" % order_number
        cur.execute(sql)
        rows = cur.fetchall()
        if rows:
            flag = 2
        # 如果没有等待审核的记录 并且没有失败记录 认为审核通过
        sql = "select node_id from sys_workflow_node_list where order_number='%s' and node_state='0' and wf_type!='apply_user'" % order_number
        cur.execute(sql)
        rows = cur.fetchall()
        if not rows and flag == 0:
            flag = 1
        if flag != 0:
            # 根据node_id查询 form_id
            sql = "select form_id from sys_workflow_node_list where node_id='%s'" % node_id
            cur.execute(sql)
            form_id = cur.fetchone()[0]

            # 根据form_id查询table_name
            sql = "select table_name from sys_workflow_tran where form_id='%s'" % form_id
            cur.execute(sql)
            table_name = cur.fetchone()[0]
            if flag == 1:  # 审核通过执行操作
                # 将原数据表数据审批状态更改为2
                sql = "update %s set apply_state='1' where order_number='%s'" % (table_name, order_number)
                cur.execute(sql)
                # 将list表里的发起状态改为1
                sql = "update sys_workflow_node_list set  update_date=CURRENT_TIMESTAMP, node_state='1',update_date=%s " \
                      "where order_number=%s and wf_type='apply_user'"
                cur.execute(sql, (datetime.datetime.now(), order_number))
            elif flag == 2:  # 审核失败执行操作
                # 将原数据表数据审批状态更改为2
                sql = "update %s set apply_state='2' where order_number='%s'" % (table_name, order_number)
                cur.execute(sql)
                # 将list表里的发起状态改为2
                sql = "update sys_workflow_node_list set update_date=CURRENT_TIMESTAMP, node_state='2',update_date=%s " \
                      "where order_number=%s and wf_type='apply_user'"
                cur.execute(sql, (datetime.datetime.now(), order_number))

            if flag == 2:
                # 审核失败将node_list记录插入历史表并删除
                sql = "insert into sys_workflow_node_list_his select * from sys_workflow_node_list where order_number='%s'" % order_number
                cur.execute(sql)
                sql = "delete from sys_workflow_node_list where order_number='%s'" % order_number
                cur.execute(sql)
                # # 查询原表记录的所有字段名
                # sql="select column_name from information_schema.columns where TABLE_SCHEMA='lqkj_db' and table_name='yw_workflow_apply_car' and column_name!='id'"
                # cur.execute(sql)
                # rows=cur.fetchall()
                # filed_list=[]
                # for row in rows:
                #     filed_list.append(row[0])
                # sql="insert into %s (%s) select %s from %s where order_number='%s'"%(table_name,','.join(filed_list),','.join(filed_list),table_name,order_number)
                # log.info('复制单条记录sql=%s'%sql)
                # cur.execute(sql)
                # lastid=cur.lastrowid
                # sql="update %s set apply_state='0' where id=%s"%(table_name,lastid)
                # log.info('修改复制记录sql=%s' % sql)
                # cur.execute(sql)



    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "msg": '处理成功'
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 用户首页信息获取
def user_index_msg_list(request):
    log = public.logger
    body = public.req_body
    try:
        cur = connection.cursor()  # 创建游标
        msg_tableData = []
        # 获取消息列表，最近10条
        sql = "select id, tran_date, type, content, message, msg_status from sys_user_message where user_id=%s order by id desc limit 10"
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        if rows:
            for item in rows:
                itemdict = {
                    "id": item[0],
                    "datetime": item[1],
                    "content": '[' + str(item[1]) + '] ' + str(item[3]),
                    "msg_status": item[5],
                    "color": 'rgba(70,130,180,0.8)'
                }
                msg_tableData.append(itemdict)

        his_tableData = []
        # 获取操作历史列表，最近10条
        sql = "select id,req_time,tran_type, case resp_code when '000000' then '处理成功' else '处理失败' end 'msg_status' " \
              "from sys_user_operate_list where user_id=%s order by id desc limit 10"
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        if rows:
            for item in rows:
                itemdict = {
                    "id": item[0],
                    # "datetime": item[1],
                    "content": '[' + str(item[1]) + '] ' + str(item[2]),
                    "msg_status": item[3],
                    "color": 'rgba(70,130,180,0.8)'
                }
                his_tableData.append(itemdict)
        # sql="insert into sys_role(role_id,role_name,role_above_id,role_state,operate_userid, snote) " \
        #     "values(%s, %s, %s, %s, %s, %s)"
        # cur.execute(sql, ( body.get('ROLE_ID'), body.get('ROLE_NAME'), body.get('ROLE_ABOVE_ID'), '1',
        #                    public.user_id,  body.get('SNOTE') ) )

        # 待审批列表 当前到达该用户节点的才返回（考虑前边审核失败的情况）
        # 查询待审批列表
        sql = "select  A.node_id,A.gl_id,A.node_state,A.update_date,A.order_number from sys_workflow_node_list A where  A.user_id='%s' and A.node_prev=0 and A.node_state='0'   UNION select A.node_id,A.gl_id,A.node_state,A.update_date,A.order_number from sys_workflow_node_list A inner join sys_workflow_node_list B on A.node_prev=B.node_id where A.user_id='%s' and B.node_state='1' and A.node_state='0'" % (
        public.user_id, public.user_id)
        log.info('sql=%s' % sql)
        cur.execute(sql)
        rows = cur.fetchall()
        print(rows)
        color_dict = {
            '0': '#E6A23C',
            '1': '#67C23A',
            '2': '#F56C6C'
        }
        auditTableData = []
        for node_id, gl_id, node_state, update_date, order_number in rows:
            msg_status_dict = {
                '0': '待审批',
                '1': '已通过',
                '2': '未通过'
            }
            auditTableData.append({
                "node_id": node_id,
                "gl_id": gl_id,
                "datetime": update_date,
                "content": '【任务】单号:%s,日期:%s' % (order_number, update_date.strftime('%Y-%m-%d')),
                "msg_status": msg_status_dict[node_state],
                "color": color_dict[node_state]
            })
        cur.close()
        # 测试报文
        pagelist = [
            {
                "name": '通知公告',
                "icon": 'el-icon-message-solid',
                "tableData": [
                    {
                        "id": '1',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": '#B4072C'
                    },
                    {
                        "id": '2',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.8)'
                    },
                    {
                        "id": '3',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.3)'
                    },
                    {
                        "id": '4',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.3)'
                    },
                    {
                        "id": '5',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.3)'
                    },
                    {
                        "id": '6',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.3)'
                    },
                ]
            },
            {
                "name": '我的申请',
                "icon": 'el-icon-s-order',
                "tableData": [
                    {
                        "id": '1',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": '#B4072C'
                    },
                    {
                        "id": '2',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.8)'
                    },
                    {
                        "id": '3',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.3)'
                    },
                    {
                        "id": '4',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.3)'
                    },
                    {
                        "id": '5',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.3)'
                    },
                    {
                        "id": '6',
                        "datetime": '2020-04-21 13:23:46',
                        "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                        "msg_status": '已通过',
                        "color": 'rgba(70,130,180,0.3)'
                    },
                ]
            },
            {
                "name": '待审批列表',
                "form_id": "10101",
                "icon": 'el-icon-question',
                "tableData": auditTableData
                # "tableData": [
                #     {
                #         "id":'1',
                #         "datetime":'2020-04-21 13:23:46',
                #         "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                #         "msg_status": '已通过',
                #         "color": '#B4072C'
                #     },
                #     {
                #         "id":'2',
                #         "datetime":'2020-04-21 13:23:46',
                #         "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                #         "msg_status": '已通过',
                #         "color": 'rgba(70,130,180,0.8)'
                #     },
                #     {
                #         "id":'3',
                #         "datetime":'2020-04-21 13:23:46',
                #         "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                #         "msg_status": '已通过',
                #         "color": 'rgba(70,130,180,0.3)'
                #     },
                #     {
                #         "id":'4',
                #         "datetime":'2020-04-21 13:23:46',
                #         "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                #         "msg_status": '已通过',
                #         "color": 'rgba(70,130,180,0.3)'
                #     },
                #     {
                #         "id":'5',
                #         "datetime":'2020-04-21 13:23:46',
                #         "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                #         "msg_status": '已通过',
                #         "color": 'rgba(70,130,180,0.3)'
                #     },
                #     {
                #         "id":'6',
                #         "datetime":'2020-04-21 13:23:46',
                #         "content": '【任务】单号:XW-20200326-001,日期:2020-04-01，cs1已审批',
                #         "msg_status": '已通过',
                #         "color": 'rgba(70,130,180,0.3)'
                #     },
                # ]
            },
            {
                "name": '消息列表',
                "icon": 'el-icon-s-comment',
                "tableData": msg_tableData
            },
            {
                "name": '操作历史',
                "icon": 'el-icon-video-camera-solid',
                "tableData": his_tableData
            },
        ]

    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "pagelist": pagelist,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 获取待审批列表
def get_wait_apply_list(request):
    log = public.logger
    body = public.req_body
    search = body.get('search', [])
    otherWhere = ''
    pageSize = body.get('pageSize', 10)
    currentPage = body.get('currentPage', 1)
    position_start = (currentPage - 1) * pageSize
    position_end = currentPage * pageSize
    sqllimit = " limit %s, %s" % (position_start, position_end)

    for where in search:
        if type(where['b']) == int:
            otherWhere += " and %s %s %s" % (where['a'], where['to'], where['b'])
        else:
            otherWhere += " and %s %s '%s'" % (where['a'], where['to'], where['b'])

    try:
        cur = connection.cursor()  # 创建游标
        # 待审批列表 当前到达该用户节点的才返回（考虑前边审核失败的情况）
        # 查询待审批列表
        sql = "select node_id,gl_id,node_state,update_date,order_number from " \
              "(select  A.node_id,A.gl_id,A.node_state,A.update_date,A.order_number from sys_workflow_node_list A " \
              "where  A.user_id='%s' and A.node_prev=0 and A.node_state='0' and A.wf_type!='apply_user' " \
              "UNION select A.node_id,A.gl_id,A.node_state,A.update_date,A.order_number from sys_workflow_node_list A " \
              "inner join sys_workflow_node_list B on A.node_prev=B.node_id where A.user_id='%s' and B.node_state='1' " \
              "and A.node_state='0' and A.wf_type!='apply_user') as T where 1=1 %s order by order_number desc %s" \
              % (public.user_id, public.user_id, otherWhere, sqllimit)
        log.info('sql=%s' % sql)
        cur.execute(sql)
        rows = cur.fetchall()
        print(rows)
        color_dict = {
            '0': '#E6A23C',
            '1': '#67C23A',
            '2': '#F56C6C'
        }
        auditTableData = []
        for node_id, gl_id, node_state, update_date, order_number in rows:
            msg_status_dict = {
                '0': '待审批',
                '1': '已通过',
                '2': '未通过'
            }

            # 获取申请用户名称
            subsql = "select b.user_name, a.update_date from sys_workflow_node_list a, sys_user b " \
                     "where a.user_id=b.user_id and a.wf_type='apply_user' and a.order_number='%s'" % order_number
            cur.execute(subsql)
            row = cur.fetchone()
            if row:
                user_name = row[0]
                upd_time = row[1]
            else:
                user_name = ''
                upd_time = ''

            # 获取流程名称
            subsql = "select b.wf_name from sys_workflow_node_list a, sys_workflow_tran b " \
                     "where a.form_id=b.form_id and a.wf_type='apply_user' and a.order_number='%s'" % order_number
            cur.execute(subsql)
            row = cur.fetchone()
            if row:
                wf_name = row[0]
            else:
                wf_name = '任务'

            auditTableData.append({
                "node_id": node_id,
                "gl_id": gl_id,
                "datetime": update_date,
                "content": '【%s】单号:%s,申请日期:%s' % (wf_name, order_number, upd_time.strftime('%Y-%m-%d')),
                "msg_status": msg_status_dict[node_state],
                "color": color_dict[node_state],
                "order_number": order_number,
                "apply_time": upd_time,
                "wf_name": wf_name,
                "user_name": user_name,
            })
        cur.close()


    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "name": '待审批列表',
            "form_id": "10101",
            "icon": 'el-icon-question',
            "table_data": auditTableData

        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 获取我的申请列表
def get_my_apply_list(request):
    log = public.logger
    body = public.req_body
    search = body.get('search', [])
    pageSize = body.get('pageSize', 10)
    currentPage = body.get('currentPage', 1)
    otherWhere = ''
    for where in search:
        if type(where['b']) == int:
            otherWhere += " and %s %s %s" % (where['a'], where['to'], where['b'])
        else:
            otherWhere += " and %s %s '%s'" % (where['a'], where['to'], where['b'])

    # log.info('otherWhere=%s'%otherWhere)
    try:
        cur = connection.cursor()  # 创建游标
        # sql="select table_name,wf_name from sys_workflow_tran"
        # cur.execute(sql)
        # rows=cur.fetchall()
        apply_list = []
        color_dict = {
            '0': '#E6A23C',
            '1': '#67C23A',
            '2': '#F56C6C'
        }
        msg_status_dict = {
            '0': '待审批',
            '1': '已通过',
            '2': '未通过'
        }

        position_start = (currentPage - 1) * pageSize
        position_end = currentPage * pageSize
        sqllimit = " limit %s, %s" % (position_start, position_end)

        sql = ("select a.node_id,a.order_number,a.user_id,a.node_state,a.insert_date,b.wf_name from "
               "(select node_id,order_number,user_id,node_state,insert_date,form_id "
               "from sys_workflow_node_list where wf_type='apply_user'"
               "union all "
               "select node_id,order_number,user_id,node_state,insert_date,form_id "
               "from sys_workflow_node_list_his where wf_type='apply_user') "
               "as a left join sys_workflow_tran b on a.form_id=b.form_id "
               "where user_id=%s %s  order by a.insert_date desc %s ") % (
                  public.user_id, otherWhere, sqllimit)
        # log.info('获取我的申请列表:'+sql)
        cur.execute(sql)
        rows = cur.fetchall()

        for node_id, order_number, user_id, node_state, insert_date, wf_name in rows:
            # 根据任务单号获取是否已经申请通过
            subsql = "select distinct node_state from sys_workflow_node_list where order_number='%s' " \
                     "UNION " \
                     "select distinct node_state from sys_workflow_node_list_his where order_number='%s'" \
                     % (order_number, order_number)
            cur.execute(subsql)
            subrows = cur.fetchall()
            substatelist = []
            for subitem in subrows:
                substatelist.append(str(subitem[0]))
            # log.info("审批状态:"+str(substatelist)+'--'+subsql)
            if '2' in substatelist:  # 判断顺序很重要，审批不通过->审批中->审批通过
                node_state = '2'
            elif '0' in substatelist:
                node_state = '0'
            else:
                node_state = '1'

            # 获取流程名称
            subsql = "select b.wf_name, a.update_date from sys_workflow_node_list a, sys_workflow_tran b " \
                     "where a.form_id=b.form_id and a.wf_type='apply_user' and a.order_number='%s'" % order_number
            cur.execute(subsql)
            row = cur.fetchone()
            if row:
                wf_name = row[0]
                upd_time = row[1]
            else:
                wf_name = '任务'
                upd_time = datetime.datetime.now()

            apply_list.append({
                "node_id": node_id,
                'order_number': order_number,
                "wf_name": wf_name,
                'apply_state': node_state,
                "msg_status": msg_status_dict[node_state],
                "color": color_dict[node_state],
                "content": '【%s】单号:%s,申请日期:%s' % (wf_name, order_number, upd_time.strftime('%Y-%m-%d')),
                'user_id': user_id,
                "apply_date": insert_date
            })
        # for table_name,wf_name in rows:
        #     sql="select order_number,apply_state,user_id from %s where user_id='%s'"%(table_name,public.user_id)
        #     cur.execute(sql)
        #     rows2=cur.fetchall()
        #     for order_number,apply_state,user_id in rows2:
        #         apply_list.append({
        #             'order_number':order_number,
        #             "wf_name":wf_name,
        #             'apply_state':apply_state,
        #             "msg_status": msg_status_dict[apply_state],
        #             "color": color_dict[apply_state],
        #             "content": '【任务】单号:%s' % (order_number),
        #             'user_id':user_id
        #         })
        cur.close()


    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "name": '我的申请',
            "form_id": "10135",
            "icon": 'el-icon-s-order',
            "pageSize": pageSize,
            "currentPage": currentPage,
            "table_data": apply_list,
            "table_total": len(apply_list)
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 获取操作历史
def get_opera_his(request):
    log = public.logger
    body = public.req_body
    search = body.get('search', [])
    pageSize = body.get('pageSize', 10)
    currentPage = body.get('currentPage', 1)
    otherWhere = ''
    for where in search:
        if type(where['b']) == int:
            otherWhere += " and %s %s %s" % (where['a'], where['to'], where['b'])
        else:
            otherWhere += " and %s %s '%s'" % (where['a'], where['to'], where['b'])

    # log.info('otherWhere=%s'%otherWhere)
    try:
        table_data = []
        cur = connection.cursor()  # 创建游标
        sql = "select id,req_time,tran_type, case resp_code when '000000' then '处理成功' else '处理失败' end 'msg_status' from sys_user_operate_list where user_id=%s order by id desc limit 10"
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        if rows:
            for item in rows:
                itemdict = {
                    "id": item[0],
                    # "datetime": item[1],
                    "content": '[' + str(item[1]) + '] ' + str(item[2]),
                    "msg_status": item[3],
                    "color": 'rgba(70,130,180,0.8)'
                }
                table_data.append(itemdict)
        cur.close()


    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "name": '操作历史',
            "form_id": "",
            "icon": 'el-icon-video-camera-solid',
            "table_data": table_data,
            "table_total": len(table_data)
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 获取未读消息列表
def get_msg_list(request):
    log = public.logger
    body = public.req_body
    search = body.get('search', [])
    pageSize = body.get('pageSize', 10)
    currentPage = body.get('currentPage', 1)
    otherWhere = ''
    for where in search:
        if type(where['b']) == int:
            otherWhere += " and %s %s %s" % (where['a'], where['to'], where['b'])
        else:
            otherWhere += " and %s %s '%s'" % (where['a'], where['to'], where['b'])

    # log.info('otherWhere=%s'%otherWhere)
    try:
        table_data = []
        cur = connection.cursor()  # 创建游标

        msg_tableData = []
        # 获取消息列表，最近10条
        sql = "select id, tran_date, type, content, message, msg_status from sys_user_message where user_id=%s order by id desc limit 10"
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        if rows:
            for item in rows:
                itemdict = {
                    "id": item[0],
                    "datetime": item[1],
                    "content": '[' + str(item[1]) + '] ' + str(item[3]),
                    "msg_status": item[5],
                    "color": 'rgba(70,130,180,0.8)'
                }
                msg_tableData.append(itemdict)

        cur.close()


    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "name": '未读消息列表',
            "form_id": "10233",
            "icon": 'el-icon-s-comment',
            "table_data": msg_tableData,
            "table_total": len(msg_tableData)
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 获取待办事项
def get_todo_list(request):
    log = public.logger
    body = public.req_body
    search = body.get('search', [])
    pageSize = body.get('pageSize', 10)
    currentPage = body.get('currentPage', 1)
    otherWhere = ''
    for where in search:
        if type(where['b']) == int:
            otherWhere += " and %s %s %s" % (where['a'], where['to'], where['b'])
        else:
            otherWhere += " and %s %s '%s'" % (where['a'], where['to'], where['b'])

    # log.info('otherWhere=%s'%otherWhere)
    try:
        table_data = []
        cur = connection.cursor()  # 创建游标

        sql = "select a.id,a.require_completion_time,b.DICT_TARGET,a.requirments,'待处理', a.require_completion_time " \
              "from yw_workflow_work_order a, sys_ywty_dict b where a.order_type=b.DICT_CODE and b.DICT_NAME='WORKORDER_TYPE' " \
              "and a.receiver='%s' and a.state='0' " % (public.user_id)

        sql = sql + "union all " \
                    "select a.id,a.require_completion_time,b.DICT_TARGET,a.requirments,'待确认', a.require_completion_time " \
                    "from yw_workflow_work_order a, sys_ywty_dict b where a.order_type=b.DICT_CODE and b.DICT_NAME='WORKORDER_TYPE' " \
                    "and a.sponsor='%s' and a.state='1' " % (public.user_id)
        log.info(sql)
        cur.execute(sql)
        rows = cur.fetchall()

        nowdate = datetime.datetime.now()
        for item in rows:
            itemdict = {}
            itemdict['id'] = item[0]
            itemdict['content'] = '[' + str(item[1]) + '] ' + '[' + str(item[2]) + '] ' + str(item[3])
            itemdict['msg_status'] = item[4]

            if item[1]:
                order_complete_date = datetime.datetime.strptime(str(item[1]), '%Y-%m-%d')
            else:
                order_complete_date = datetime.datetime.strptime(str(item[5]), '%Y-%m-%d')
            cal_day = (nowdate - order_complete_date).days
            if cal_day > 2:
                itemdict['color'] = 'rgba(255,99,71,0.8)'
            elif cal_day > 5 and cal_day < 10:
                itemdict['color'] = 'rgba(255,193,37,0.8)'
            else:
                itemdict['color'] = 'rgba(70,130,180,0.8)'
            table_data.append(itemdict)
        cur.close()


    except Exception as ex:
        log.error("查询数据表信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "name": '待办事项',
            "form_id": "10170",
            "icon": 'el-icon-video-camera-solid',
            "table_data": table_data,
            "table_total": len(table_data)
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo
