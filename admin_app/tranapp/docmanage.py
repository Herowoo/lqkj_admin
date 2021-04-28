import sys
from django.shortcuts import render, redirect, HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
from admin_app.sys import public_db


###########################################################################################################
# 文件档案管理
# add by litz, 2020.05.15
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


# 文档管理权限配置
def docment_manage_fileauth_cfg(request):
    log = public.logger
    form_var = public.req_body['form_var']

    try:
        cur = connection.cursor()  # 创建游标

        file_type = form_var.get('file_type')
        if not file_type:
            public.respcode, public.respmsg = "310310", "请先选择文件类型!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        form_var['read_cfginfo'] = str(form_var.get('read_cfginfo'))
        form_var['write_cfginfo'] = str(form_var.get('write_cfginfo'))

        flag, msg = public_db.insert_or_update_table(cur, 'yw_workflow_document_manage_cfg', **form_var)
        if not flag:
            public.respcode, public.respmsg = "310310", msg
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # sql = "select 1 from yw_workflow_document_manage_cfg where file_type=%s"
        # cur.execute(sql, file_type)
        # row = cur.fetchone()
        # if row:  # 有数据， 更新
        #     sql = "update yw_workflow_document_manage_cfg set read_cfgtype=%s,read_cfginfo=%s, write_cfgtype=%s,write_cfginfo=%s  " \
        #           "where file_type=%s"
        # else:  # 无数据，插入
        #     sql = "insert into yw_workflow_document_manage_cfg(read_cfgtype,read_cfginfo,write_cfgtype,write_cfginfo, file_type) " \
        #           "values(%s, %s, %s, %s, %s)"
        # cur.execute(sql,
        #             (form_var.get('read_cfgtype'), str(form_var.get('read_cfginfo')), form_var.get('write_cfgtype'),
        #              str(form_var.get('write_cfginfo')), file_type))
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


# 获取文档管理权限配置信息
def get_doccfg_info(request):
    log = public.logger
    form_data = public.req_body['form_data']

    try:
        file_type = form_data.get('file_type')
        if not file_type:
            public.respcode, public.respmsg = "310310", "请先选择文件类型!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        sql = "select read_cfgtype,read_cfginfo,write_cfgtype,write_cfginfo from yw_workflow_document_manage_cfg where file_type=%s"
        cur.execute(sql, file_type)
        row = cur.fetchone()
        if row:  # 有数据
            form_data['read_cfgtype'] = row[0]
            if row[1]:
                form_data['read_cfginfo'] = eval(row[1])
            else:
                form_data['read_cfginfo'] = eval([])

            form_data['write_cfgtype'] = row[2]
            if row[3]:
                form_data['write_cfginfo'] = eval(row[3])
            else:
                form_data['write_cfginfo'] = eval([])

        # 获取下拉配置属性
        sql = "select dict_code, dict_target from sys_ywty_dict where DICT_NAME='DOCMENT_MANAGE_DOCTYPE'"
        cur.execute(sql)
        rows = cur.fetchall()
        options = []
        for item in rows:
            options.append({"key": item[0], "value": item[1]})
        form_data['filetype_options'] = options

        sql = "select dict_code,CONCAT(dict_code,'-',dict_target) from sys_ywty_dict where dict_name='DOCMENT_MANAGE_READ_CFGTYPE'"
        cur.execute(sql)
        rows = cur.fetchall()
        options = []
        for item in rows:
            options.append({"key": item[0], "value": item[1]})
        form_data['read_cfgtype_options'] = options
        form_data['write_cfgtype_options'] = options

        if form_data.get('read_cfgtype') == 'byorg':
            sql = "select org_id, org_name from sys_org where org_state='1' "
        else:
            sql = "SELECT user_id, user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows = cur.fetchall()
        transfer = []
        for item in rows:
            transfer.append({"key": item[0], "label": str(item[0]) + '-' + item[1], "disabled": False})
        form_data['read_cfginfo_options'] = transfer

        if form_data.get('write_cfgtype') == 'byorg':
            sql = "select org_id, org_name from sys_org where org_state='1' "
        else:
            sql = "SELECT user_id, user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows = cur.fetchall()
        transfer = []
        for item in rows:
            transfer.append({"key": item[0], "label": str(item[0]) + '-' + item[1], "disabled": False})
        form_data['write_cfginfo_options'] = transfer

    except Exception as ex:
        log.error("查询数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "查询数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_data
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


# 获取文档管理权限配置信息
def get_doccfg_info_new(request):
    log = public.logger
    form_data = public.req_body['form_data']

    try:
        file_type = form_data.get('file_type')
        if not file_type:
            public.respcode, public.respmsg = "310310", "请先选择文件类型!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 根据文件类型获取公司、二级、三级文件类型代码
        # file_type += '_' * 2
        # company, seclass, trdclass, *_ = file_type.split('_')
        cur = connection.cursor()  # 创建游标
        sql = "select read_cfgtype,read_cfginfo,write_cfgtype,write_cfginfo from yw_workflow_document_manage_cfg where file_type=%s"
        cur.execute(sql, file_type)
        row = cur.fetchone()
        if row:  # 有数据
            form_data['read_cfgtype'] = row[0]
            if row[1]:
                form_data['read_cfginfo'] = eval(row[1])
            else:
                form_data['read_cfginfo'] = eval([])

            form_data['write_cfgtype'] = row[2]
            if row[3]:
                form_data['write_cfginfo'] = eval(row[3])
            else:
                form_data['write_cfginfo'] = eval([])

        # 获取下拉配置属性
        company = form_data['company']
        seclass = form_data['seclasstype']
        trdclass = form_data['trdclasstype']

        sql = "select class_spell, class_name from yw_workflow_document_classtype where class_rank=1 "
        cur.execute(sql)
        rows = cur.fetchall()
        options = [{'key': k, 'value': v} for k, v in rows]
        form_data['company_options'] = options

        if company:
            sql = "select class_spell, class_name from yw_workflow_document_classtype where class_rank=2 and class_top=%s "
            cur.execute(sql, company)
            rows = cur.fetchall()
            options = [{'key': k, 'value': v} for k, v in rows]
            form_data['seclasstype_options'] = options

        if seclass:
            sql = "select class_spell, class_name from yw_workflow_document_classtype where class_rank=3 and class_top=%s "
            cur.execute(sql, seclass)
            rows = cur.fetchall()
            options = [{'key': k, 'value': v} for k, v in rows]
            form_data['trdclasstype_options'] = options


        sql = "select dict_code,CONCAT(dict_code,'-',dict_target) from sys_ywty_dict where dict_name='DOCMENT_MANAGE_READ_CFGTYPE'"
        cur.execute(sql)
        rows = cur.fetchall()
        options = []
        for item in rows:
            options.append({"key": item[0], "value": item[1]})
        form_data['read_cfgtype_options'] = options
        form_data['write_cfgtype_options'] = options

        if form_data.get('read_cfgtype') == 'byorg':
            sql = "select org_id, org_name from sys_org where org_state='1' "
        else:
            sql = "SELECT user_id, user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows = cur.fetchall()
        transfer = []
        for item in rows:
            transfer.append({"key": item[0], "label": str(item[0]) + '-' + item[1], "disabled": False})
        form_data['read_cfginfo_options'] = transfer

        if form_data.get('write_cfgtype') == 'byorg':
            sql = "select org_id, org_name from sys_org where org_state='1' "
        else:
            sql = "SELECT user_id, user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows = cur.fetchall()
        transfer = []
        for item in rows:
            transfer.append({"key": item[0], "label": str(item[0]) + '-' + item[1], "disabled": False})
        form_data['write_cfginfo_options'] = transfer

    except Exception as ex:
        log.error("查询数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "查询数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_data
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


# 文档保存
def docment_file_save(request):
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    try:
        cur = connection.cursor()  # 创建游标

        id = form_var.get('id')

        if id:  # 有数据， 更新
            sql = "update yw_workflow_document_manage set file_type=%s,file_id=%s, file_name=%s,file_content=%s," \
                  "img_file=%s, create_userid=%s, create_time=%s, org_id=%s, file_state=%s ,expiring_date=%s where " \
                  "id=%s "
            sqlvalue = (form_var.get('file_type'), form_var.get('file_id'), form_var.get('file_name'),
                        str(form_var.get('file_content')), form_var.get('img_file'), public.user_id,
                        datetime.datetime.now(), form_var.get('org_id'), form_var.get('file_state'),
                        form_var.get('expiring_date'), id)
            cur.execute(sql, sqlvalue)
        else:  # 无数据，插入
            file_id = public_db.Get_SeqNo('DOCMENT_NO')
            file_id = file_id.replace('[ORG]', form_var.get('org_id'))
            file_id = file_id.replace('[ORG]', form_var.get('org_id'))
            body['form_var']['file_id'] = file_id

            sql = "insert into yw_workflow_document_manage(file_type, file_id, file_name, file_content, img_file, " \
                  "create_userid, create_time, org_id, file_state,expiring_date ) " \
                  "values(%s, %s, %s, %s, %s,  %s, %s, %s, %s, %s)"
            sqlvalue = (form_var.get('file_type'), file_id, form_var.get('file_name'),
                        str(form_var.get('file_content')), form_var.get('img_file'), public.user_id,
                        datetime.datetime.now(), form_var.get('org_id'), form_var.get('file_state'),
                        form_var.get('expiring_date'))
            cur.execute(sql, sqlvalue)

    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


def docment_company_save(request):
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    try:
        company = form_var.get('class_name')
        com_spell = form_var.get('class_spell')
        if not company:
            public.respcode, public.respmsg = "310314", "公司名称不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not com_spell:
            public.respcode, public.respmsg = "310314", "公司代码不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        cur = connection.cursor()  # 创建游标
        # 公司代码不可重复
        sql = "select 1 from yw_workflow_document_classtype where class_spell = %s and class_rank=1"
        cur.execute(sql, com_spell)
        row = cur.fetchone()
        if row:
            public.respcode, public.respmsg = "310317", "公司代码已存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        id = form_var.get('id')

        if id:  # 有数据， 更新
            sql = "update yw_workflow_document_classtype set class_name=%s,class_spell=%s, class_rank=%s," \
                  "update_date=%s where id=%s"
            sqlvalue = (company, com_spell, '1',
                        datetime.datetime.now(), id)
            cur.execute(sql, sqlvalue)
        else:  # 无数据，插入

            sql = "insert into yw_workflow_document_classtype(class_name, class_spell, class_rank, update_date) " \
                  "values(%s, %s, %s, %s)"
            sqlvalue = (company, com_spell, 1,
                        datetime.datetime.now())
            cur.execute(sql, sqlvalue)

    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


def docment_copy_by_company(request):
    """文档二级目录复制"""
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    try:
        company = form_var.get('company')
        if not company:
            public.respcode, public.respmsg = "310314", "公司不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        cur = connection.cursor()  # 创建游标
        # 查询该公司下属二级目录
        sql = "select class_name,class_spell from yw_workflow_document_classtype where class_top = %s and class_rank=2 "
        cur.execute(sql, company)
        rows = cur.fetchall()
        if not rows:
            public.respcode, public.respmsg = "310318", "该公司下没有可供复制的二级目录!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        dict_list = [{'class_name': k, 'class_spell': v} for k, v in rows]
        form_var['seclasstypelist'] = dict_list
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "查询数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


def docment_seclasstype_save(request):
    """文档二级目录保存"""
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    try:
        company = form_var.get('company')
        seclasstypelist = form_var.get('seclasstypelist')
        if not company:
            public.respcode, public.respmsg = "310314", "公司不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not seclasstypelist:
            public.respcode, public.respmsg = "310314", "二级文档类别不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        cur = connection.cursor()  # 创建游标
        i = 1
        sql_value_list = []
        # 检查list内元素
        for item in seclasstypelist:
            cn = item.get('class_name')
            cs = item.get('class_spell')
            flag = True
            if not cn:
                flag = False
                errmsg = '第%d行二级文档类别不可为空!' % i
            if not cs:
                flag = False
                errmsg = '第%d行二级文档代码不可为空!' % i
            sql = "select 1 from yw_workflow_document_classtype where class_rank = 2 and class_top = %s " \
                  "and class_spell=%s"
            cur.execute(sql, (company, cs))
            row = cur.fetchone()
            if row:
                flag = False
                errmsg = '第%d行二级文档代码已存在!' % i
            if not flag:
                public.respcode, public.respmsg = "310314", errmsg
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql_value_list.append((cn, cs, 2, company, datetime.datetime.now()))
            i += 1
        id = form_var.get('id')

        if id:  # 有数据， 更新
            pass
        else:  # 无数据，插入
            sql = "insert into yw_workflow_document_classtype (class_name, class_spell, class_rank, class_top," \
                  " update_date) values (%s, %s, %s, %s, %s)"
            cur.executemany(sql, sql_value_list)

    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


def docment_copy_by_seclass(request):
    """文档三级目录复制"""
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    try:
        company = form_var.get('company')
        seclasstype = form_var.get('seclasstype')
        if not company:
            public.respcode, public.respmsg = "310314", "公司不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not seclasstype:
            public.respcode, public.respmsg = "310314", "二级文档类别不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        cur = connection.cursor()  # 创建游标
        # 查询该公司下属二级目录
        sql = "select class_name,class_spell from yw_workflow_document_classtype where class_top = %s and class_rank=3 "
        cur.execute(sql, seclasstype)
        rows = cur.fetchall()
        if not rows:
            public.respcode, public.respmsg = "310318", "该文档类别下没有可供复制的三级目录!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        dict_list = [{'class_name': k, 'class_spell': v} for k, v in rows]
        form_var['trdclasslist'] = dict_list
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "查询数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


def docment_trdclasstype_save(request):
    """文档三级目录保存"""
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    try:
        seclasstype = form_var.get('seclasstype')
        trdclasslist = form_var.get('trdclasslist')
        if not trdclasslist:
            public.respcode, public.respmsg = "310314", "三级文档类别不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not seclasstype:
            public.respcode, public.respmsg = "310314", "二级文档类别不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        cur = connection.cursor()  # 创建游标
        i = 1
        sql_value_list = []
        # 检查list内元素
        for item in trdclasslist:
            cn = item.get('class_name')
            cs = item.get('class_spell')
            flag = True
            if not cn:
                flag = False
                errmsg = '第%d行三级文档类别不可为空!' % i
            if not cs:
                flag = False
                errmsg = '第%d行三级文档代码不可为空!' % i
            sql = "select 1 from yw_workflow_document_classtype where class_rank = 3 and class_top = %s " \
                  "and class_spell=%s"
            cur.execute(sql, (seclasstype, cs))
            row = cur.fetchone()
            if row:
                flag = False
                errmsg = '第%d行三级文档代码已存在!' % i
            if not flag:
                public.respcode, public.respmsg = "310314", errmsg
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql_value_list.append((cn, cs, 3, seclasstype, datetime.datetime.now()))
            i += 1
        id = form_var.get('id')

        if id:  # 有数据， 更新
            pass
        else:  # 无数据，插入
            sql = "insert into yw_workflow_document_classtype (class_name, class_spell, class_rank, class_top," \
                  " update_date) values (%s, %s, %s, %s, %s)"
            cur.executemany(sql, sql_value_list)
        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)

    return public.respinfo


def get_doc_seclass_info(request):
    """获取二级文件类型信息"""
    log = public.logger
    form_data = public.req_body['form_data']

    try:
        file_type = form_data.get('file_type')
        if not file_type:
            public.respcode, public.respmsg = "310310", "请先选择文件类型!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 根据文件类型获取公司、二级、三级文件类型代码
        # file_type += '_' * 2
        # company, seclass, trdclass, *_ = file_type.split('_')
        cur = connection.cursor()  # 创建游标
        sql = "select read_cfgtype,read_cfginfo,write_cfgtype,write_cfginfo from yw_workflow_document_manage_cfg where file_type=%s"
        cur.execute(sql, file_type)
        row = cur.fetchone()
        if row:  # 有数据
            form_data['read_cfgtype'] = row[0]
            if row[1]:
                form_data['read_cfginfo'] = eval(row[1])
            else:
                form_data['read_cfginfo'] = eval([])

            form_data['write_cfgtype'] = row[2]
            if row[3]:
                form_data['write_cfginfo'] = eval(row[3])
            else:
                form_data['write_cfginfo'] = eval([])

        # 获取下拉配置属性
        sql = "select class_spell, class_name from yw_workflow_document_classtype where class_rank=1 "
        cur.execute(sql)
        rows = cur.fetchall()
        options = [{'key': k, 'value': v} for k, v in rows]
        form_data['company_options'] = options
        # form_data['company'] = company
        # form_data['seclasstype'] = seclass
        # form_data['trdclasstype'] = trdclass

        sql = "select dict_code,CONCAT(dict_code,'-',dict_target) from sys_ywty_dict where dict_name='DOCMENT_MANAGE_READ_CFGTYPE'"
        cur.execute(sql)
        rows = cur.fetchall()
        options = []
        for item in rows:
            options.append({"key": item[0], "value": item[1]})
        form_data['read_cfgtype_options'] = options
        form_data['write_cfgtype_options'] = options

        if form_data.get('read_cfgtype') == 'byorg':
            sql = "select org_id, org_name from sys_org where org_state='1' "
        else:
            sql = "SELECT user_id, user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows = cur.fetchall()
        transfer = []
        for item in rows:
            transfer.append({"key": item[0], "label": str(item[0]) + '-' + item[1], "disabled": False})
        form_data['read_cfginfo_options'] = transfer

        if form_data.get('write_cfgtype') == 'byorg':
            sql = "select org_id, org_name from sys_org where org_state='1' "
        else:
            sql = "SELECT user_id, user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows = cur.fetchall()
        transfer = []
        for item in rows:
            transfer.append({"key": item[0], "label": str(item[0]) + '-' + item[1], "disabled": False})
        form_data['write_cfginfo_options'] = transfer

    except Exception as ex:
        log.error("查询数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "查询数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_data
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    finally:
        cur.close()  # 关闭游标

    return public.respinfo


def generate_doc_no(classtype, filename, rulestr, version_tile='A', version=0):
    if isinstance(rulestr, str):
        ret = rulestr
        sql_value = (None, None)
        if '[YYYY]' in ret:
            ret = ret.replace('[YYYY]', datetime.datetime.now().strftime('%Y'))
            sql_value = (4, datetime.datetime.now().strftime('%Y'))
        if '[YYYY_MM]' in ret:
            ret = ret.replace('[YYYY_MM]', datetime.datetime.now().strftime('%Y_%m'))
            sql_value = (7, datetime.datetime.now().strftime('%Y-%m'))
        if '[YYYY_MM_DD]' in ret:
            ret = ret.replace('[YYYY_MM_DD]', datetime.datetime.now().strftime('%Y_%m_%d'))
            sql_value = (10, datetime.datetime.now().strftime('%Y-%m-%d'))
        if '[SEQNO]' in rulestr:
            cur = connection.cursor()
            try:
                sql = "SELECT count(1) from yw_workflow_document_manage_his where substr(create_time,1,%s) = %s"
                cur.execute(sql, sql_value)
                row = cur.fetchone()
                count = int(row[0])
                seqstr = str(count+1)
                seqstr = seqstr.rjust(4, '0')
                ret = ret.replace('[SEQNO]', seqstr)
                # 查询版本号
                sql = "SELECT count(1) from yw_workflow_document_manage_his where file_type = %s and file_name=%s"
                cur.execute(sql, (classtype, filename))
                row = cur.fetchone()
                version = int(row[0])
            except Exception as ex:
                return False, ex.__str__()
            finally:
                cur.close()
        return True, classtype+ret+version_tile+str(version)
    else:
        return False, '文件编号规则格式不正确！'


def document_file_commit(request):
    '''文档内容保存'''
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    try:
        param_not_null = {
            "company": "公司名称",
            "seclasstype": "二级文件类型",
            "trdclasstype": "三级文件类型",
            "file_type": "文件类型代码",
            "org_id": "所属机构",
            "file_content": "文件"
        }
        for k in param_not_null:
            if not form_var.get(k):
                public.respcode, public.respmsg = "320439", param_not_null.get(k) + '不可为空'
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        cur = connection.cursor()
        # 生成文件编号
        flag, file_id = generate_doc_no(form_var.get('file_type')+'_'+form_var.get('org_id'),
                                        form_var.get('file_name'), '_[YYYY_MM]_[SEQNO]_')
        if not flag:
            public.respcode, public.respmsg = "320438", file_id
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        form_var['file_id'] = file_id
        form_var['file_content'] = str(form_var.get('file_content'))
        # 更新内容
        flag, msg = public_db.insert_or_update_table(cur, 'yw_workflow_document_manage_his', **form_var)
        if not flag:
            public.respcode, public.respmsg = "320438", msg
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        cur.close()
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)

    return public.respinfo