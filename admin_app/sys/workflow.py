import sys
from django.shortcuts import HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
from admin_app.sys import public_db
from admin_app.tranapp import pubfunc
import datetime


###########################################################################################################
# 审核流程配置，审核流程处理，工单系统
# add by litz, 20200429
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


# 获取流程配置，并插入用户待处理流程明细表
def WorkDue_ByType(wf_id, wf_type):
    log = public.logger

    if wf_id:
        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.app_id, menu_path " \
              "from sys_workflow_node_cfg  where wf_id='%s' " % (wf_id)
    else:
        # 新发起的流程。
        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.app_id, menu_path " \
              "from sys_workflow_node_cfg  where wf_type='%s' and wf_prev is null " % (wf_type)

    log.info("获取流程配置:" + sql, extra={'ptlsh': public.req_seq})
    cur = connection.cursor()  # 创建游标
    cur.execute(sql)
    rows = cur.fetchall()

    for item in rows:
        menuinfo = {}

    cur.close()
    # 返回结果
    return True


# 流程审批管理-查询审批明细
def get_workflow_info(request):
    log = public.logger
    body = public.req_body
    nodeid = body.get("node_id")

    if not nodeid:
        public.respcode, public.respmsg = "100221", "节点ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        flow_info = {
            "node_id": "1111",
            "node_name": "审批流程",
            "tabledata": [
                {"label": "申请类型", "value": "用章申请"},
                {"label": "申请人", "value": "张三"},
                {"label": "申请时间", "value": "2020-04-29 13:39:22"},
                {"label": "申请用途", "value": "网站备案"},
                {"label": "使用时间", "value": "2020-04-30 至 2020-05-01 "},
                {"label": "附件", "value": [234, 233]},
                {"label": "当前状态", "value": "申请中"},
            ],
            "node_flow": [
                {"name": " 提交(张三)"},
                {"name": " 审批(李四)"},
                {"name": " 审批(王五)"},
                {"name": " 归档(赵六)"},
            ],
            "node_status": False,  # False-未处理,True-已处理
            "node_active": 2,
            "node_act": "",  # 处理动作 1-同意 2-不同意
            "snote": "",  # 说明
            "file": [222, 333],
        }
        # 模拟返回
        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "flow_info": flow_info,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 审批流程配置时，获取表单的字段信息
def workflow_get_formfield_info(request):
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")

    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select field_id, field_name from sys_form_cfg_fieldlist where form_id=%s " \
              "and comp_type in ('textarea', 'input', 'datetime', 'select', 'radio', 'date')"
        cur.execute(sql, formid)
        rows = cur.fetchall()
        field_list = []
        for item in rows:
            field_list.append({"key": item[0], "value": item[1]})

        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "field_list": field_list,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 审批流程配置时，获取用户列表信息
def workflow_get_user_list(request):
    log = public.logger
    body = public.req_body
    # formid=body.get("form_id")
    #
    # if not formid:
    #     public.respcode, public.respmsg = "110221", "表单ID不可为空!"
    #     public.respinfo = HttpResponse(public.setrespinfo())
    #     return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select user_id, user_name from sys_user where state='1' "
        cur.execute(sql)
        rows = cur.fetchall()
        user_list = []

        # 先初始化几个特殊的用户
        user_list.append({"key": "org_leader", "value": 'org_leader' + '-' + '部门负责人'})

        for item in rows:
            user_list.append({"key": item[0], "value": str(item[0]) + '-' + item[1]})

        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "user_list": user_list,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 审批流程配置时，获取部门列表信息
def workflow_get_org_list(request):
    log = public.logger
    body = public.req_body
    org_list = []
    try:
        cur = connection.cursor()

        sql = " select org_id, org_name from sys_org where org_state='1' "
        log.info(sql)
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            org_list.append({"key": item[0], "value": str(item[0]) + '-' + item[1]})
        cur.close()

    except Exception as ex:
        cur.close()
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "org_list": org_list,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 审批流程配置时，获取一个流程ID
def workflow_cfg_create(request):
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")

    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    wf_id = int(public.getintrandom(6))
    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "wf_id": wf_id,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 审批流程配置时，根据表单ID，获取审批流程配置信息
def get_workflow_cfg_info(request):
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")

    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        workflow_info = []
        cur = connection.cursor()  # 创建游标
        sql = "select wf_id, wf_notes, wf_prev,wf_type,wf_cfg from sys_workflow_node_cfg where form_id=%s "
        cur.execute(sql, formid)
        rows = cur.fetchall()
        for item in rows:
            wfinfo = {}
            wfinfo['wf_id'] = item[0]
            wfinfo['wf_notes'] = item[1]
            wfinfo['wf_prev'] = item[2]
            wfinfo['wf_type'] = item[3]
            if item[4]:
                wfinfo['wf_cfg'] = eval(item[4])
            else:
                wfinfo['wf_cfg'] = {}
            workflow_info.append(wfinfo)
        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "workflow_info": workflow_info,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 审批流程配置时，保存配置信息
def workflow_cfg_save(request):
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    workflow_info = body.get("workflow_info")
    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if not workflow_info:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    # wf_id列表：
    wf_id_list = pubfunc.get_list_from_dict(workflow_info, 'wf_id')

    try:
        cur = connection.cursor()  # 创建游标
        # 原form_id对应wf_id
        form_wf_list = []
        sql = "select wf_id from sys_workflow_node_cfg where form_id = %s"
        cur.execute(sql, formid)
        rows = cur.fetchall()
        for row in rows:
            form_wf_list.append(row[0])
        log.info("原id：%s" % str(form_wf_list))
        log.info("请求id：%s" % str(wf_id_list))
        # 新增wf_id
        append_wf_id = pubfunc.get_def_list(wf_id_list, form_wf_list)
        log.info("新增id：%s" % str(append_wf_id))
        # 更新wf_id
        update_wf_id = pubfunc.get_insec_list(form_wf_list, wf_id_list)
        log.info("更新id：%s" % str(update_wf_id))

        prev_id_dict = {}
        for item in workflow_info:
            wf_id = item.get('wf_id')
            if wf_id in append_wf_id:
                sql = "insert into sys_workflow_node_cfg (" \
                      "form_id," \
                      "wf_type," \
                      "wf_prev," \
                      "wf_cfg," \
                      "wf_notes," \
                      "wf_state) values (%s,%s,%s,%s,%s,%s) "
                cur.execute(sql, (formid, item.get('wf_type'), item.get('wf_prev'),
                                  str(item.get('wf_cfg')), item.get('wf_notes'), 1))
                # 更新wf_id新旧数据字典
                cur.execute("SELECT LAST_INSERT_ID()")
                row = cur.fetchone()
                new_wf_id = row[0]
                prev_id_dict[wf_id] = new_wf_id

            if wf_id in update_wf_id:
                sql = "update sys_workflow_node_cfg set form_id=%s,wf_type=%s,wf_prev=%s,wf_cfg=%s,wf_notes=%s," \
                      "wf_state=%s where wf_id=%s"
                cur.execute(sql, (formid, item.get('wf_type'), item.get('wf_prev'),
                                  str(item.get('wf_cfg')), item.get('wf_notes'), 1, wf_id))
                prev_id_dict[wf_id] = wf_id
        # 删除wf_id
        delete_wf_id = pubfunc.get_def_list(form_wf_list, wf_id_list)
        log.info("删除id：%s" % str(delete_wf_id))

        for item in delete_wf_id:
            # 删除form_id关联节点
            sql_del = "delete from sys_workflow_node_cfg where wf_id = %s"
            cur.execute(sql_del, item)

        # 更新prev_id
        for item in workflow_info:
            old_prev_id = item.get('wf_prev')
            new_prev_id = prev_id_dict.get(old_prev_id)
            if new_prev_id:
                sql = "update sys_workflow_node_cfg set wf_prev=%s where wf_prev=%s and wf_prev != 0"
                cur.execute(sql, (new_prev_id, old_prev_id))
    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    finally:
        cur.close()  # 关闭游标
    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 获取工单明细
def get_order_detail(request):
    log = public.logger
    body = public.req_body
    form_data = body.get('form_data')
    if not form_data:
        public.respcode, public.respmsg = "000000", "无查询条件!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    id = form_data.get('id')
    if not id:
        public.respcode, public.respmsg = "000000", "无查询条件!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select id,sponsor, start_time,order_type,order_urgent_type,receiver,receiving_department, " \
              "require_completion_time, except_completion_time,actual_time,state, requirements_ziliao, task_completion_ziliao, " \
              "requirments, task_completion_info, remarks from yw_workflow_work_order where id=%s"

        orderinfo = public_db.GetSelData(cur, sql, id)
        body['form_var'] = orderinfo[0]

        sponsor = body['form_var'].get('sponsor')
        order_type = body['form_var'].get('order_type')
        receiving_department = body['form_var'].get('receiving_department')
        receiver = body['form_var'].get('receiver')
        # 发起人数据字典
        sql = "select user_id as 'key', user_name as 'value' from sys_user where user_id=%s" % (sponsor)
        body['form_var']['sponsor_options'] = public_db.GetSelData(cur, sql)
        # 接收人数据字典
        sql = "select user_id as 'key', user_name as 'value' from sys_user where user_id=%s" % (receiver)
        body['form_var']['receiver_options'] = public_db.GetSelData(cur, sql)
        # 接收部门数据字典
        sql = "select distinct ORG_SPELL as 'key', ORG_NAME as 'value' from sys_org where ORG_SPELL='%s'" \
              % (receiving_department)
        body['form_var']['receiving_department_options'] = public_db.GetSelData(cur, sql)
        # 工单类型数据字典
        sql = "select dict_code as 'key', dict_target as 'value' from sys_ywty_dict " \
              "where dict_name='WORKORDER_TYPE' and dict_code='%s' " % (order_type)
        body['form_var']['order_type_options'] = public_db.GetSelData(cur, sql)

        body['form_var']['order_urgent_type_info'] = [{"key": "0", "value": "紧急"}, {"key": "1", "value": "一般"},
                                                      {"key": "2", "value": "普通"}]
        body['form_var']['state_info'] = [{"key": "0", "value": "未完成"}, {"key": "1", "value": "待确认"},
                                          {"key": "2", "value": "已完成"}]

        # 关闭游标
        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 工单信息-新增
def order_detail_add(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    if not form_var:
        public.respcode, public.respmsg = "387711", "上送数据异常!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标

        sql = "insert into yw_workflow_work_order(start_time,sponsor,  order_type, receiver, order_urgent_type, " \
              "receiving_department, require_completion_time, requirments, requirements_ziliao, remarks, state) " \
              "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '0')"
        cur.execute(sql,
                    (form_var.get('start_time'), public.user_id, form_var.get('order_type'), form_var.get('receiver'),
                     form_var.get('order_urgent_type'), form_var.get('receiving_department'),
                     form_var.get('require_completion_time'), form_var.get('requirments'),
                     str(form_var.get('requirements_ziliao')), form_var.get('remarks')))
        form_var['state_info'] = '0'

        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.respcode, public.respmsg = "999999", str(ex)
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 工单明细,更新
def order_detail_update(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    if not form_var:
        public.respcode, public.respmsg = "387711", "上送数据异常!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    id = form_var.get('id')
    if not id:
        public.respcode, public.respmsg = "387712", "无查询条件!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select sponsor, receiver, state from yw_workflow_work_order where id=%s"
        cur.execute(sql, id)
        row = cur.fetchone()
        if not row:
            cur.close()
            public.respcode, public.respmsg = "387713", "数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        db_sponsor = row[0]
        db_receiver = row[1]
        db_state = row[2]

        if db_state != '0':
            cur.close()
            public.respcode, public.respmsg = "387715", "非初始发布状态,无法修改信息!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # log.info(str(public.user_id)+'=='+str(db_sponsor)+'=='+str(db_receiver), extra={'ptlsh': public.req_seq})
        # log.info(str(type(public.user_id)) + '==' + str(type(db_sponsor)) + '==' + str(type(db_receiver)), extra={'ptlsh': public.req_seq})
        # print(type(public.user_id), public.user_id, type(db_sponsor), db_sponsor, type(db_receiver), db_receiver)

        if int(public.user_id) == db_sponsor:
            sql = "UPDATE yw_workflow_work_order SET start_time=%s, order_type=%s, receiver=%s, order_urgent_type=%s, " \
                  "receiving_department=%s, require_completion_time=%s, requirments=%s,requirements_ziliao=%s," \
                  "remarks=%s, state='0' where id=%s"
            cur.execute(sql, (form_var.get('start_time'), form_var.get('order_type'), form_var.get('receiver'),
                              form_var.get('order_urgent_type'), form_var.get('receiving_department'),
                              form_var.get('require_completion_time'), form_var.get('requirments'),
                              str(form_var.get('requirements_ziliao')), form_var.get('remarks'), form_var.get('id')))
            form_var['state_info'] = '0'
        elif int(public.user_id) == db_receiver:
            if form_var.get('except_completion_time') and form_var.get('actual_time'):
                sql = "UPDATE yw_workflow_work_order SET except_completion_time=%s, actual_time=%s, task_completion_info=%s, " \
                      "task_completion_ziliao=%s, remarks=%s, state= '1' where id=%s"
                cur.execute(sql, (form_var.get('except_completion_time'), form_var.get('actual_time'),
                                  form_var.get('task_completion_info'),
                                  str(form_var.get('task_completion_ziliao')), form_var.get('remarks'),
                                  form_var.get('id')))
            elif not form_var.get('except_completion_time') and form_var.get('actual_time'):
                sql = "UPDATE yw_workflow_work_order SET actual_time=%s, task_completion_info=%s, " \
                      "task_completion_ziliao=%s, remarks=%s, state= '1' where id=%s"
                cur.execute(sql, (form_var.get('actual_time'), form_var.get('task_completion_info'),
                                  str(form_var.get('task_completion_ziliao')), form_var.get('remarks'),
                                  form_var.get('id')))
            elif form_var.get('except_completion_time') and not form_var.get('actual_time'):
                sql = "UPDATE yw_workflow_work_order SET except_completion_time=%s, task_completion_info=%s, " \
                      "task_completion_ziliao=%s, remarks=%s, state= '1' where id=%s"
                cur.execute(sql, (form_var.get('except_completion_time'), form_var.get('task_completion_info'),
                                  str(form_var.get('task_completion_ziliao')), form_var.get('remarks'),
                                  form_var.get('id')))
            else:
                sql = "UPDATE yw_workflow_work_order SET  task_completion_info=%s, task_completion_ziliao=%s, remarks=%s where id=%s"
                cur.execute(sql, (form_var.get('task_completion_info'), str(form_var.get('task_completion_ziliao')),
                                  form_var.get('remarks'), form_var.get('id')))
                form_var['state_info'] = '1'
        else:
            cur.close()
            public.respcode, public.respmsg = "387714", "无操作权限!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.respcode, public.respmsg = "387888", str(ex)
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo
