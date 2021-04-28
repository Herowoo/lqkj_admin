import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime,time
from calendar import weekday,monthrange
import re

#########################################################################################
#周月报、工单等
#
#########################################################################################

#配置操作主流程
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

'''
部门周月报表单渲染
'''
# 部门周报添加表单渲染显示
def add_secweekly_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {}) #可能为空
    if not form_data:
        form_data = body.get('form_var',{})
    form_var_dict = {
            "org_id":None,
            "org_list":[],
            "prev_id":None,
            "prev_week_id":None,
            "prev_week_start":None,
            "prev_week_end":None,
            "prev_label_one":None,
            "prev_label_two":None,
            "prev_user_id":None,
            "prev_duties":None,
            "prev_tableData":[],
            "id":None,
            "week_id": None,
            "week_start": None,
            "week_end": None,
            "label_one": None,
            "label_two": None,
            "user_id":user_id,
            "duties":None,
            "tableData": [],
        }
    cur = connection.cursor()
    # 获取用户信息 ： 机构信息 和 用户名,职务列表
    org_sql = "SELECT ORG_ID,ORG_NAME FROM sys_org WHERE ORG_ID IN (SELECT ORG_ID FROM sys_user_org WHERE USER_ID = %s )"
    user_sql = "select STATION from sys_user where user_id = %s "
    cur.execute(user_sql,user_id)
    row = cur.fetchone()
    if row:
        form_var_dict['duties'] = row[0]
    user_list,taget_list = get_userlist_tagetlist()
    form_var_dict['user_list'] = user_list
    form_var_dict['taget_list'] = taget_list

    cur.execute(org_sql, user_id)
    rows = cur.fetchall()
    if rows:
        if form_data.get('org_id',None):
            org_id = int(form_data['org_id'])
        else:
            org_id = rows[0][0]
        org_list = [{'key':item[0],'value':item[1]} for item in rows]
        form_var_dict['org_id'] = org_id
        form_var_dict['org_list'] = org_list
    else:
        public.respcode, public.respmsg = "100501", "无所属机构信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    # 获取上周和本周week_id
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day
    date_str = str(year) + '-' + str(month) + '-' + str(day)
    last_week_day = (datetime.datetime.strptime(date_str, '%Y-%m-%d') - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    last_week_day = [int(item) for item in last_week_day.split('-')]
    # 本周week_id
    week_tuple = get_week_of_month(year, month, day)
    week_id = str(week_tuple)
    # 上周week_id
    prev_week_tuple = get_week_of_month(last_week_day[0], last_week_day[1], last_week_day[2])
    prev_week_id = str(prev_week_tuple)
    form_var_dict['week_id'] = week_id
    form_var_dict['prev_week_id'] = prev_week_id

    # 查询数据库 本周和上周是否有历史记录
    head_sql = "select * from yw_report_section_week_head where org_id=%s and week_id=%s"
    body_sql = "select * from yw_report_section_week_body where org_id=%s and week_id=%s"
    # 本周周报
    cur.execute(head_sql,(org_id,week_id))
    row = cur.fetchone()
    if row:
        form_var_dict['id'] = row[0]
        form_var_dict['duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_week_start_end(year, month, day)
    form_var_dict["week_start"] =  str(start_date)
    form_var_dict["week_end"] = str(end_date)
    # 本周
    form_var_dict['label_one'] = str(week_tuple[0])+'年'+str(week_tuple[1])+'月第'+str(week_tuple[2])+'周工作计划'
    form_var_dict['label_two'] = '区间：'+str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日'+ \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql,(org_id,week_id))
    rows = cur.fetchall()
    field_list = ['body_id','org_id','week_id','plan_matter','for_problem','plan_solve','plan_finish_date','person_liable','completion_progress','true_finish_date','reason','improve_action','user_id','tran_date']
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['tableData'] = tmp_data



    # 上周周报
    cur.execute(head_sql, (org_id, prev_week_id))
    row = cur.fetchone()
    if row:
        form_var_dict['prev_id'] = row[0]
        form_var_dict['prev_user_id'] = row[-2]
        form_var_dict['prev_duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_week_start_end(last_week_day[0], last_week_day[1], last_week_day[2])
    form_var_dict["prev_week_start"] = str(start_date)
    form_var_dict["prev_week_end"] = str(end_date)
    # 标签显示
    form_var_dict['prev_label_one'] = str(prev_week_tuple[0]) + '年' + str(prev_week_tuple[1]) + '月第' + str(prev_week_tuple[2]) + '周工作总结'
    form_var_dict['prev_label_two'] = '区间：' + str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日' + \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql, (org_id, prev_week_id))
    rows = cur.fetchall()
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['prev_tableData'] = tmp_data

    submit_power = {"show": True, "disabled": False}
    form_var_dict['submit_power'] = submit_power

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 部门周报修改表单渲染显示
def upd_secweekly_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {}) #可能为空
    if not form_data:
        form_data = body.get('form_var',{})
    user_id = int(form_data.get('user_id',user_id))
    form_var_dict = {
        "org_id": None,
        "org_list": [],
        "prev_id": None,
        "prev_week_id": None,
        "prev_week_start": None,
        "prev_week_end": None,
        "prev_label_one": None,
        "prev_label_two": None,
        "prev_user_id": None,
        "prev_duties": None,
        "prev_tableData": [],
        "id": None,
        "week_id": None,
        "week_start": None,
        "week_end": None,
        "label_one": None,
        "label_two": None,
        "user_id": user_id,
        "duties": None,
        "tableData": [],
    }
    cur = connection.cursor()
    # 获取用户信息 ： 机构信息 和 用户名
    org_sql = "SELECT ORG_ID,ORG_NAME FROM sys_org WHERE ORG_ID IN (SELECT ORG_ID FROM sys_user_org WHERE USER_ID = %s )"
    user_sql = "select STATION from sys_user where user_id = %s "
    cur.execute(user_sql, user_id)
    row = cur.fetchone()
    if row:
        form_var_dict['duties'] = row[0]
    user_list, taget_list = get_userlist_tagetlist()
    form_var_dict['user_list'] = user_list
    form_var_dict['taget_list'] = taget_list

    cur.execute(org_sql, user_id)
    rows = cur.fetchall()
    if rows:
        if form_data.get('org_id', None):
            org_id = int(form_data['org_id'])
        else:
            org_id = rows[0][0]
        org_list = [{'key':item[0],'value':item[1]} for item in rows]
        form_var_dict['org_id'] = org_id
        form_var_dict['org_list'] = org_list
    else:
        public.respcode, public.respmsg = "100501", "无所属机构信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    # 本周week_id
    week_id = form_data.get('week_id','[0,0,0]')
    week_tuple = json.loads(week_id)
    week_start = json.loads(form_data.get('week_start','[0,0,0]'))
    year,month,day = week_start[0],week_start[1],week_start[2]
    date_str = str(year) + '-' + str(month) + '-' + str(day)
    last_week_day = (datetime.datetime.strptime(date_str, '%Y-%m-%d') - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    last_week_day = [int(item) for item in last_week_day.split('-')]
    # 上周week_id
    prev_week_tuple = get_week_of_month(last_week_day[0], last_week_day[1], last_week_day[2])
    prev_week_id = str(prev_week_tuple)
    form_var_dict['week_id'] = week_id
    form_var_dict['prev_week_id'] = prev_week_id

    # 查询数据库 本周和上周是否有历史记录
    head_sql = "select * from yw_report_section_week_head where org_id=%s and week_id=%s"
    body_sql = "select * from yw_report_section_week_body where org_id=%s and week_id=%s"
    # 本周周报
    cur.execute(head_sql,(org_id,week_id))
    row = cur.fetchone()
    if row:
        form_var_dict['id'] = row[0]
        form_var_dict['user_id'] = row[-2]
        form_var_dict['duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_week_start_end(year, month, day)
    form_var_dict["week_start"] = str(start_date)
    form_var_dict["week_end"] = str(end_date)
    # 本周
    form_var_dict['label_one'] = str(week_tuple[0])+'年'+str(week_tuple[1])+'月第'+str(week_tuple[2])+'周工作计划'
    form_var_dict['label_two'] = '区间：'+str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日'+ \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql,(org_id,week_id))
    rows = cur.fetchall()
    field_list = ['body_id','org_id','week_id','plan_matter','for_problem','plan_solve','plan_finish_date','person_liable','completion_progress','true_finish_date','reason','improve_action','user_id','tran_date']
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['tableData'] = tmp_data



    # 上周周报
    cur.execute(head_sql, (org_id, prev_week_id))
    row = cur.fetchone()
    if row:
        form_var_dict['prev_id'] = row[0]
        form_var_dict['prev_user_id'] = row[-2]
        form_var_dict['prev_duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_week_start_end(last_week_day[0], last_week_day[1], last_week_day[2])
    form_var_dict["prev_week_start"] = str(start_date)
    form_var_dict["prev_week_end"] = str(end_date)
    # 标签
    form_var_dict['prev_label_one'] = str(prev_week_tuple[0]) + '年' + str(prev_week_tuple[1]) + '月第' + str(prev_week_tuple[2]) + '周工作总结'
    form_var_dict['prev_label_two'] = '区间：' + str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日' + \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql, (org_id, prev_week_id))
    rows = cur.fetchall()
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['prev_tableData'] = tmp_data

    # 与当前时间周次做对比，week_id != now_week_id ,提交按钮置灰
    # 当前时间的周次ID
    now_year = datetime.datetime.now().year
    now_month = datetime.datetime.now().month
    now_day = datetime.datetime.now().day
    now_week_tuple = get_week_of_month(now_year, now_month, now_day)
    now_week_id = str(now_week_tuple)
    submit_power = {"show": True, "disabled": False}
    if now_week_id != week_id:
        submit_power['disabled'] = True
    form_var_dict['submit_power'] = submit_power

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,

        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 部门月报添加表单渲染显示
def add_secmonthly_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {}) #可能为空
    if not form_data:
        form_data = body.get('form_var',{})
    form_var_dict = {
            "org_id":None,
            "org_list":[],
            "prev_id":None,
            "prev_month_id":None,
            "prev_month_start":None,
            "prev_month_end":None,
            "prev_label_one":None,
            "prev_label_two":None,
            "prev_user_id":None,
            "prev_duties":None,
            "prev_tableData":[],
            "id":None,
            "month_id": None,
            "month_start": None,
            "month_end": None,
            "label_one": None,
            "label_two": None,
            "user_id":user_id,
            "duties":None,
            "tableData": [],
        }
    cur = connection.cursor()
    # 获取用户信息 ： 机构信息 和 用户名
    org_sql = "SELECT ORG_ID,ORG_NAME FROM sys_org WHERE ORG_ID IN (SELECT ORG_ID FROM sys_user_org WHERE USER_ID = %s )"
    user_sql = "select STATION from sys_user where user_id = %s "
    cur.execute(user_sql, user_id)
    row = cur.fetchone()
    if row:
        form_var_dict['duties'] = row[0]
    user_list, taget_list = get_userlist_tagetlist()
    form_var_dict['user_list'] = user_list
    form_var_dict['taget_list'] = taget_list

    cur.execute(org_sql, user_id)
    rows = cur.fetchall()
    if rows:
        if form_data.get('org_id', None):
            org_id = int(form_data['org_id'])
        else:
            org_id = rows[0][0]
        org_list = [{'key':item[0],'value':item[1]} for item in rows]
        form_var_dict['org_id'] = org_id
        form_var_dict['org_list'] = org_list
    else:
        public.respcode, public.respmsg = "100501", "无所属机构信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    # 获取上月和本月month_id
    day_now = time.localtime()
    year = day_now.tm_year
    month = day_now.tm_mon
    prev_month_tuple = get_prev_month(year,month)
    # 本月month_id
    month_id = str([year,month])
    # 上月month_id
    prev_month_id = str(prev_month_tuple)
    form_var_dict['month_id'] = month_id
    form_var_dict['prev_month_id'] = prev_month_id

    # 查询数据库 本月和上月是否有历史记录
    head_sql = "select * from yw_report_section_month_head where org_id=%s and month_id=%s"
    body_sql = "select * from yw_report_section_month_body where org_id=%s and month_id=%s"
    # 本周周报
    cur.execute(head_sql,(org_id,month_id))
    row = cur.fetchone()
    if row:
        form_var_dict['id'] = row[0]
        form_var_dict['user_id'] = row[-2]
        form_var_dict['duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_month_start_end(year, month)
    form_var_dict["month_start"] =  str(start_date)
    form_var_dict["month_end"] = str(end_date)
    # 本周
    form_var_dict['label_one'] = str(year)+'年'+str(month)+'月工作计划'
    form_var_dict['label_two'] = '区间：'+str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日'+ \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql,(org_id,month_id))
    rows = cur.fetchall()
    field_list = ['body_id','org_id','month_id','plan_matter','for_problem','plan_solve','plan_finish_date','person_liable','completion_progress','true_finish_date','reason','improve_action','user_id','tran_date']
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['tableData'] = tmp_data



    # 上周周报
    cur.execute(head_sql, (org_id, prev_month_id))
    row = cur.fetchone()
    if row:
        form_var_dict['prev_id'] = row[0]
        form_var_dict['prev_user_id'] = row[-2]
        form_var_dict['prev_duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_month_start_end(prev_month_tuple[0], prev_month_tuple[1])
    form_var_dict["prev_month_start"] = str(start_date)
    form_var_dict["prev_month_end"] = str(end_date)
    # 标签显示
    form_var_dict['prev_label_one'] = str(prev_month_tuple[0]) + '年' + str(prev_month_tuple[1]) + '月周工作总结'
    form_var_dict['prev_label_two'] = '区间：' + str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日' + \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql, (org_id, prev_month_id))
    rows = cur.fetchall()
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['prev_tableData'] = tmp_data

    submit_power = {"show": True, "disabled": False}
    form_var_dict['submit_power'] = submit_power

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 部门月报修改表单渲染显示
def upd_secmonthly_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {}) #可能为空
    if not form_data:
        form_data = body.get('form_var',{})
    user_id = int(form_data.get('user_id', user_id))
    form_var_dict = {
        "org_id": None,
        "org_list": [],
        "prev_id": None,
        "prev_month_id": None,
        "prev_month_start": None,
        "prev_month_end": None,
        "prev_label_one": None,
        "prev_label_two": None,
        "prev_user_id": None,
        "prev_duties": None,
        "prev_tableData": [],
        "id": None,
        "month_id": None,
        "month_start": None,
        "month_end": None,
        "label_one": None,
        "label_two": None,
        "user_id": user_id,
        "duties": None,
        "tableData": [],
    }
    cur = connection.cursor()
    # 获取用户信息 ： 机构信息 和 用户名
    org_sql = "SELECT ORG_ID,ORG_NAME FROM sys_org WHERE ORG_ID IN (SELECT ORG_ID FROM sys_user_org WHERE USER_ID = %s )"
    user_sql = "select STATION from sys_user where user_id = %s "
    cur.execute(user_sql, user_id)
    row = cur.fetchone()
    if row:
        form_var_dict['duties'] = row[0]
    user_list, taget_list = get_userlist_tagetlist()
    form_var_dict['user_list'] = user_list
    form_var_dict['taget_list'] = taget_list

    cur.execute(org_sql, user_id)
    rows = cur.fetchall()
    if rows:
        if form_data.get('org_id', None):
            org_id = int(form_data['org_id'])
        else:
            org_id = rows[0][0]
        org_list = [{'key':item[0],'value':item[1]} for item in rows]
        form_var_dict['org_id'] = org_id
        form_var_dict['org_list'] = org_list
    else:
        public.respcode, public.respmsg = "100501", "无所属机构信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    # 本月month_id
    month_id = form_data.get('month_id','[0,0]')
    month_tuple = json.loads(month_id)
    # 上月month_id
    prev_month_tuple = get_prev_month(month_tuple[0],month_tuple[1])
    prev_month_id = str(prev_month_tuple)
    form_var_dict['month_id'] = month_id
    form_var_dict['prev_month_id'] = prev_month_id

    # 查询数据库 本周和上周是否有历史记录
    head_sql = "select * from yw_report_section_month_head where org_id=%s and month_id=%s"
    body_sql = "select * from yw_report_section_month_body where org_id=%s and month_id=%s"
    # 本周周报
    cur.execute(head_sql,(org_id,month_id))
    row = cur.fetchone()
    if row:
        form_var_dict['id'] = row[0]
        form_var_dict['user_id'] = row[-2]
        form_var_dict['duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_month_start_end(month_tuple[0], month_tuple[1])
    form_var_dict["month_start"] = str(start_date)
    form_var_dict["month_end"] = str(end_date)
    # 本周
    form_var_dict['label_one'] = str(month_tuple[0])+'年'+str(month_tuple[1])+'月工作计划'
    form_var_dict['label_two'] = '区间：'+str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日'+ \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql,(org_id,month_id))
    rows = cur.fetchall()
    field_list = ['body_id','org_id','month_id','plan_matter','for_problem','plan_solve','plan_finish_date','person_liable','completion_progress','true_finish_date','reason','improve_action','user_id','tran_date']
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['tableData'] = tmp_data



    # 上周周报
    cur.execute(head_sql, (org_id, prev_month_id))
    row = cur.fetchone()
    if row:
        form_var_dict['prev_id'] = row[0]
        form_var_dict['prev_user_id'] = row[-2]
        form_var_dict['prev_duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_month_start_end(prev_month_tuple[0], prev_month_tuple[1])
    form_var_dict["prev_month_start"] = str(start_date)
    form_var_dict["prev_month_end"] = str(end_date)
    # 标签
    form_var_dict['prev_label_one'] = str(prev_month_tuple[0]) + '年' + str(prev_month_tuple[1]) + '月工作总结'
    form_var_dict['prev_label_two'] = '区间：' + str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日' + \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql, (org_id, prev_month_id))
    rows = cur.fetchall()
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['prev_tableData'] = tmp_data
    # 与当前时间月份做对比，month_id != now_month_id ,提交按钮置灰
    # 当前时间的月份ID
    now_day = time.localtime()
    now_year = now_day.tm_year
    now_month = now_day.tm_mon
    now_month_id = str([now_year, now_month])
    submit_power = {"show": True, "disabled": False}
    if now_month_id != month_id:
        submit_power['disabled'] = True
    form_var_dict['submit_power'] =submit_power



    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

'''
个人周月报表单渲染
'''
# 个人周报添加表单渲染显示
def add_puweekly_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {}) #可能为空
    if not form_data:
        form_data = body.get('form_var',{})
    form_var_dict = {
            "org_id":None,
            "org_list":[],
            "prev_id":None,
            "prev_week_id":None,
            "prev_week_start":None,
            "prev_week_end":None,
            "prev_label_one":None,
            "prev_label_two":None,
            "prev_user_id":None,
            "prev_duties":None,
            "prev_tableData":[],
            "id":None,
            "week_id": None,
            "week_start": None,
            "week_end": None,
            "label_one": None,
            "label_two": None,
            "user_id":user_id,
            "duties":None,
            "tableData": [],
        }
    cur = connection.cursor()
    # 获取用户信息 ： 机构信息 和 用户名
    org_sql = "SELECT ORG_ID,ORG_NAME FROM sys_org WHERE ORG_ID IN (SELECT ORG_ID FROM sys_user_org WHERE USER_ID = %s )"
    user_sql = "select STATION from sys_user where user_id = %s "
    cur.execute(user_sql, user_id)
    row = cur.fetchone()
    if row:
        form_var_dict['duties'] = row[0]
    user_list, taget_list = get_userlist_tagetlist()
    form_var_dict['user_list'] = user_list
    form_var_dict['taget_list'] = taget_list

    cur.execute(org_sql, user_id)
    rows = cur.fetchall()
    if rows:
        if form_data.get('org_id', None):
            org_id = int(form_data['org_id'])
        else:
            org_id = rows[0][0]
        org_list = [{'key':item[0],'value':item[1]} for item in rows]
        form_var_dict['org_id'] = org_id
        form_var_dict['org_list'] = org_list
    else:
        public.respcode, public.respmsg = "100501", "无所属机构信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo


    # 获取上周和本周week_id
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day
    date_str = str(year) + '-' + str(month) + '-' + str(day)
    last_week_day = (datetime.datetime.strptime(date_str, '%Y-%m-%d') - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    last_week_day = [int(item) for item in last_week_day.split('-')]
    # 本周week_id
    week_tuple = get_week_of_month(year, month, day)
    week_id = str(week_tuple)
    # 上周week_id
    prev_week_tuple = get_week_of_month(last_week_day[0], last_week_day[1], last_week_day[2])
    prev_week_id = str(prev_week_tuple)
    form_var_dict['week_id'] = week_id
    form_var_dict['prev_week_id'] = prev_week_id

    # 查询数据库 本周和上周是否有历史记录
    head_sql = "select * from yw_report_personal_week_head where org_id=%s and week_id=%s and user_id=%s"
    body_sql = "select * from yw_report_personal_week_body where org_id=%s and week_id=%s and user_id=%s"
    # 本周周报
    cur.execute(head_sql,(org_id,week_id,user_id))
    row = cur.fetchone()
    if row:
        form_var_dict['id'] = row[0]
        form_var_dict['user_id'] = row[-2]
        form_var_dict['duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_week_start_end(year, month, day)
    form_var_dict["week_start"] =  str(start_date)
    form_var_dict["week_end"] = str(end_date)
    # 本周
    form_var_dict['label_one'] = str(week_tuple[0])+'年'+str(week_tuple[1])+'月第'+str(week_tuple[2])+'周工作计划'
    form_var_dict['label_two'] = '区间：'+str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日'+ \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql,(org_id,week_id,user_id))
    rows = cur.fetchall()
    field_list = ['body_id','org_id','week_id','plan_matter','for_problem','plan_solve','plan_finish_date','person_liable','completion_progress','true_finish_date','reason','improve_action','user_id','tran_date']
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['tableData'] = tmp_data



    # 上周周报
    cur.execute(head_sql, (org_id, prev_week_id,user_id))
    row = cur.fetchone()
    if row:
        form_var_dict['prev_id'] = row[0]
        form_var_dict['prev_user_id'] = row[-2]
        form_var_dict['prev_duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_week_start_end(last_week_day[0], last_week_day[1], last_week_day[2])
    form_var_dict["prev_week_start"] = str(start_date)
    form_var_dict["prev_week_end"] = str(end_date)
    # 标签显示
    form_var_dict['prev_label_one'] = str(prev_week_tuple[0]) + '年' + str(prev_week_tuple[1]) + '月第' + str(prev_week_tuple[2]) + '周工作总结'
    form_var_dict['prev_label_two'] = '区间：' + str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日' + \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql, (org_id, prev_week_id,user_id))
    rows = cur.fetchall()
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['prev_tableData'] = tmp_data

    submit_power = {"show": True, "disabled": False}
    form_var_dict['submit_power'] = submit_power

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 个人周报修改表单渲染显示
def upd_puweekly_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    uid = head.get('uid',None)
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {}) #可能为空
    if not form_data:
        form_data = body.get('form_var',{})
    user_id = int(form_data.get('user_id',uid))
    form_var_dict = {
        "org_id": None,
        "org_list": [],
        "prev_id": None,
        "prev_week_id": None,
        "prev_week_start": None,
        "prev_week_end": None,
        "prev_label_one": None,
        "prev_label_two": None,
        "prev_user_id": None,
        "prev_duties": None,
        "prev_tableData": [],
        "id": None,
        "week_id": None,
        "week_start": None,
        "week_end": None,
        "label_one": None,
        "label_two": None,
        "user_id": user_id,
        "duties": None,
        "tableData": [],
    }
    cur = connection.cursor()
    # 获取用户信息 ： 机构信息 和 用户名
    org_sql = "SELECT ORG_ID,ORG_NAME FROM sys_org WHERE ORG_ID IN (SELECT ORG_ID FROM sys_user_org WHERE USER_ID = %s )"
    user_sql = "select STATION from sys_user where user_id = %s "
    cur.execute(user_sql, user_id)
    row = cur.fetchone()
    if row:
        form_var_dict['duties'] = row[0]
    user_list, taget_list = get_userlist_tagetlist()
    form_var_dict['user_list'] = user_list
    form_var_dict['taget_list'] = taget_list

    cur.execute(org_sql, user_id)
    rows = cur.fetchall()
    if rows:
        if form_data.get('org_id', None):
            org_id = int(form_data['org_id'])
        else:
            org_id = rows[0][0]
        org_list = [{'key':item[0],'value':item[1]} for item in rows]
        form_var_dict['org_id'] = org_id
        form_var_dict['org_list'] = org_list
    else:
        public.respcode, public.respmsg = "100501", "无所属机构信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    # 本周week_id
    week_id = form_data.get('week_id','[0,0,0]')
    week_tuple = json.loads(week_id)
    week_start = json.loads(form_data.get('week_start','[0,0,0]'))
    year,month,day = week_start[0],week_start[1],week_start[2]
    date_str = str(year) + '-' + str(month) + '-' + str(day)
    last_week_day = (datetime.datetime.strptime(date_str, '%Y-%m-%d') - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    last_week_day = [int(item) for item in last_week_day.split('-')]
    # 上周week_id
    prev_week_tuple = get_week_of_month(last_week_day[0], last_week_day[1], last_week_day[2])
    prev_week_id = str(prev_week_tuple)
    form_var_dict['week_id'] = week_id
    form_var_dict['prev_week_id'] = prev_week_id

    # 查询数据库 本周和上周是否有历史记录
    head_sql = "select * from yw_report_section_week_head where org_id=%s and week_id=%s and user_id=%s"
    body_sql = "select * from yw_report_section_week_body where org_id=%s and week_id=%s and user_id=%s"
    # 本周周报
    cur.execute(head_sql,(org_id,week_id,user_id))
    row = cur.fetchone()
    if row:
        form_var_dict['id'] = row[0]
        form_var_dict['user_id'] = row[-2]
        form_var_dict['duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_week_start_end(year, month, day)
    form_var_dict["week_start"] = str(start_date)
    form_var_dict["week_end"] = str(end_date)
    # 本周
    form_var_dict['label_one'] = str(week_tuple[0])+'年'+str(week_tuple[1])+'月第'+str(week_tuple[2])+'周工作计划'
    form_var_dict['label_two'] = '区间：'+str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日'+ \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql,(org_id,week_id,user_id))
    rows = cur.fetchall()
    field_list = ['body_id','org_id','week_id','plan_matter','for_problem','plan_solve','plan_finish_date','person_liable','completion_progress','true_finish_date','reason','improve_action','user_id','tran_date']
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['tableData'] = tmp_data



    # 上周周报
    cur.execute(head_sql, (org_id, prev_week_id,user_id))
    row = cur.fetchone()
    if row:
        form_var_dict['prev_id'] = row[0]
        form_var_dict['prev_user_id'] = row[-2]
        form_var_dict['prev_duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_week_start_end(last_week_day[0], last_week_day[1], last_week_day[2])
    form_var_dict["prev_week_start"] = str(start_date)
    form_var_dict["prev_week_end"] = str(end_date)
    # 标签
    form_var_dict['prev_label_one'] = str(prev_week_tuple[0]) + '年' + str(prev_week_tuple[1]) + '月第' + str(prev_week_tuple[2]) + '周工作总结'
    form_var_dict['prev_label_two'] = '区间：' + str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日' + \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql, (org_id, prev_week_id,user_id))
    rows = cur.fetchall()
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['prev_tableData'] = tmp_data
    # 与当前时间周次做对比，week_id != now_week_id ,提交按钮置灰
    # 当前时间的周次ID
    now_year = datetime.datetime.now().year
    now_month = datetime.datetime.now().month
    now_day = datetime.datetime.now().day
    now_week_tuple = get_week_of_month(now_year, now_month, now_day)
    now_week_id = str(now_week_tuple)
    submit_power = {"show": True, "disabled": False}
    if now_week_id != week_id:
        submit_power['disabled'] = True
    form_var_dict['submit_power'] = submit_power


    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 个人月报添加表单渲染显示
def add_pumonthly_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {}) #可能为空
    if not form_data:
        form_data = body.get('form_var', {})
    form_var_dict = {
            "org_id":None,
            "org_list":[],
            "prev_id":None,
            "prev_month_id":None,
            "prev_month_start":None,
            "prev_month_end":None,
            "prev_label_one":None,
            "prev_label_two":None,
            "prev_user_id":None,
            "prev_duties":None,
            "prev_tableData":[],
            "id":None,
            "month_id": None,
            "month_start": None,
            "month_end": None,
            "label_one": None,
            "label_two": None,
            "user_id":user_id,
            "duties":None,
            "tableData": [],
        }
    cur = connection.cursor()
    # 获取用户信息 ： 机构信息 和 用户名
    org_sql = "SELECT ORG_ID,ORG_NAME FROM sys_org WHERE ORG_ID IN (SELECT ORG_ID FROM sys_user_org WHERE USER_ID = %s )"
    user_sql = "select STATION from sys_user where user_id = %s "
    cur.execute(user_sql, user_id)
    row = cur.fetchone()
    if row:
        form_var_dict['duties'] = row[0]
    user_list, taget_list = get_userlist_tagetlist()
    form_var_dict['user_list'] = user_list
    form_var_dict['taget_list'] = taget_list

    cur.execute(org_sql, user_id)
    rows = cur.fetchall()
    if rows:
        if form_data.get('org_id', None):
            org_id = int(form_data['org_id'])
        else:
            org_id = rows[0][0]
        org_list = [{'key':item[0],'value':item[1]} for item in rows]
        form_var_dict['org_id'] = org_id
        form_var_dict['org_list'] = org_list
    else:
        public.respcode, public.respmsg = "100501", "无所属机构信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo


    # 获取上月和本月month_id
    day_now = time.localtime()
    year = day_now.tm_year
    month = day_now.tm_mon
    prev_month_tuple = get_prev_month(year,month)
    # 本月month_id
    month_id = str([year,month])
    # 上月month_id
    prev_month_id = str(prev_month_tuple)
    form_var_dict['month_id'] = month_id
    form_var_dict['prev_month_id'] = prev_month_id

    # 查询数据库 本月和上月是否有历史记录
    head_sql = "select * from yw_report_section_month_head where org_id=%s and month_id=%s and user_id=%s"
    body_sql = "select * from yw_report_section_month_body where org_id=%s and month_id=%s and user_id=%s"
    # 本周周报
    cur.execute(head_sql,(org_id,month_id,user_id))
    row = cur.fetchone()
    if row:
        form_var_dict['id'] = row[0]
        form_var_dict['user_id'] = row[-2]
        form_var_dict['duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_month_start_end(year, month)
    form_var_dict["month_start"] =  str(start_date)
    form_var_dict["month_end"] = str(end_date)
    # 本周
    form_var_dict['label_one'] = str(year)+'年'+str(month)+'月工作计划'
    form_var_dict['label_two'] = '区间：'+str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日'+ \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql,(org_id,month_id,user_id))
    rows = cur.fetchall()
    field_list = ['body_id','org_id','month_id','plan_matter','for_problem','plan_solve','plan_finish_date','person_liable','completion_progress','true_finish_date','reason','improve_action','user_id','tran_date']
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['tableData'] = tmp_data



    # 上周周报
    cur.execute(head_sql, (org_id, prev_month_id,user_id))
    row = cur.fetchone()
    if row:
        form_var_dict['prev_id'] = row[0]
        form_var_dict['prev_user_id'] = row[-2]
        form_var_dict['prev_duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_month_start_end(prev_month_tuple[0], prev_month_tuple[1])
    form_var_dict["prev_month_start"] = str(start_date)
    form_var_dict["prev_month_end"] = str(end_date)
    # 标签显示
    form_var_dict['prev_label_one'] = str(prev_month_tuple[0]) + '年' + str(prev_month_tuple[1]) + '月周工作总结'
    form_var_dict['prev_label_two'] = '区间：' + str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日' + \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql, (org_id, prev_month_id,user_id))
    rows = cur.fetchall()
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['prev_tableData'] = tmp_data

    submit_power = {"show": True, "disabled": False}
    form_var_dict['submit_power'] = submit_power

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 个人月报修改表单渲染显示
def upd_pumonthly_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    uid = head.get('uid', None)
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {})  # 可能为空
    if not form_data:
        form_data = body.get('form_var',{})
    user_id = int(form_data.get('user_id', uid))
    form_var_dict = {
        "org_id": None,
        "org_list": [],
        "prev_id": None,
        "prev_month_id": None,
        "prev_month_start": None,
        "prev_month_end": None,
        "prev_label_one": None,
        "prev_label_two": None,
        "prev_user_id": None,
        "prev_duties": None,
        "prev_tableData": [],
        "id": None,
        "month_id": None,
        "month_start": None,
        "month_end": None,
        "label_one": None,
        "label_two": None,
        "user_id": user_id,
        "duties": None,
        "tableData": [],
    }
    cur = connection.cursor()
    # 获取用户信息 ： 机构信息 和 用户名
    org_sql = "SELECT ORG_ID,ORG_NAME FROM sys_org WHERE ORG_ID IN (SELECT ORG_ID FROM sys_user_org WHERE USER_ID = %s )"
    user_sql = "select STATION from sys_user where user_id = %s "
    cur.execute(user_sql, user_id)
    row = cur.fetchone()
    if row:
        form_var_dict['duties'] = row[0]
    user_list, taget_list = get_userlist_tagetlist()
    form_var_dict['user_list'] = user_list
    form_var_dict['taget_list'] = taget_list

    cur.execute(org_sql, user_id)
    rows = cur.fetchall()
    if rows:
        if form_data.get('org_id', None):
            org_id = int(form_data['org_id'])
        else:
            org_id = rows[0][0]
        org_list = [{'key':item[0],'value':item[1]} for item in rows]
        form_var_dict['org_id'] = org_id
        form_var_dict['org_list'] = org_list
    else:
        public.respcode, public.respmsg = "100501", "无所属机构信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    # 本月month_id
    month_id = form_data.get('month_id','[0,0]')
    month_tuple = json.loads(month_id)
    # 上月month_id
    prev_month_tuple = get_prev_month(month_tuple[0],month_tuple[1])
    prev_month_id = str(prev_month_tuple)
    form_var_dict['month_id'] = month_id
    form_var_dict['prev_month_id'] = prev_month_id

    # 查询数据库 本周和上周是否有历史记录
    head_sql = "select * from yw_report_section_month_head where org_id=%s and month_id=%s and user_id=%s"
    body_sql = "select * from yw_report_section_month_body where org_id=%s and month_id=%s and user_id=%s"
    # 本周周报
    cur.execute(head_sql,(org_id,month_id,user_id))
    row = cur.fetchone()
    if row:
        form_var_dict['id'] = row[0]
        form_var_dict['user_id'] = row[-2]
        form_var_dict['duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_month_start_end(month_tuple[0], month_tuple[1])
    form_var_dict["month_start"] = str(start_date)
    form_var_dict["month_end"] = str(end_date)
    # 本周
    form_var_dict['label_one'] = str(month_tuple[0])+'年'+str(month_tuple[1])+'月工作计划'
    form_var_dict['label_two'] = '区间：'+str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日'+ \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql,(org_id,month_id,user_id))
    rows = cur.fetchall()
    field_list = ['body_id','org_id','month_id','plan_matter','for_problem','plan_solve','plan_finish_date','person_liable','completion_progress','true_finish_date','reason','improve_action','user_id','tran_date']
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['tableData'] = tmp_data



    # 上周周报
    cur.execute(head_sql, (org_id, prev_month_id,user_id))
    row = cur.fetchone()
    if row:
        form_var_dict['prev_id'] = row[0]
        form_var_dict['prev_user_id'] = row[-2]
        form_var_dict['prev_duties'] = row[-1]
        start_date = json.loads(row[3])
        end_date = json.loads(row[4])
    else:
        start_date, end_date = get_month_start_end(prev_month_tuple[0], prev_month_tuple[1])
    form_var_dict["prev_month_start"] = str(start_date)
    form_var_dict["prev_month_end"] = str(end_date)
    # 标签
    form_var_dict['prev_label_one'] = str(prev_month_tuple[0]) + '年' + str(prev_month_tuple[1]) + '月工作总结'
    form_var_dict['prev_label_two'] = '区间：' + str(start_date[0]) + '年' + str(start_date[1]) + '月' + str(start_date[2]) + '日' + \
                                 '-' + str(end_date[0]) + '年' + str(end_date[1]) + '月' + str(end_date[2]) + '日'
    # body 数据
    cur.execute(body_sql, (org_id, prev_month_id,user_id))
    rows = cur.fetchall()
    if rows:
        tmp_data = []
        for row in rows:
            tmp_dict = {}
            for index,item in enumerate(field_list):
                tmp_dict[item] = row[index]
            tmp_data.append(tmp_dict)
        form_var_dict['prev_tableData'] = tmp_data

    # 与当前时间月份做对比，month_id != now_month_id ,提交按钮置灰
    # 当前时间的月份ID
    now_day = time.localtime()
    now_year = now_day.tm_year
    now_month = now_day.tm_mon
    now_month_id = str([now_year, now_month])
    submit_power = {"show": True, "disabled": False}
    if now_month_id != month_id:
        submit_power['disabled'] = True
    form_var_dict['submit_power'] = submit_power

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo



#  获取当日是本月的第几周 (2020,1,1)
def get_week_of_month(year, month, day):
    """
    获取指定的某天是某个月的第几周
    周一为一周的开始
    实现思路：就是计算当天在本年的第y周，本月一1号在本年的第x周，然后求差即可。
    因为查阅python的系统库可以得知：
    """
    begin = int(datetime.date(year, month, 1).strftime("%W"))
    end = int(datetime.date(year, month, day).strftime("%W"))

    return str(year)+'年'+str(month)+'月第'+str(end-begin+1)+'周'

# 根据日期获取周的开始和结束日期
def get_week_start_end(y,m,d):
    if y and m and d and 1 <= int(m) <= 12 and 1 <= int(d) <= 31:
        w = datetime.date(int(y), int(m), int(d))
        w = weekday(int(y), int(m), int(d))  # 二选其一
        date_str = str(y) + '-' + str(m) + '-' + str(d)
        start_date = (datetime.datetime.strptime(date_str,'%Y-%m-%d') - datetime.timedelta(days=w)).strftime('%Y-%m-%d')
        # start_date = [int(item) for item in start_date.split('-')]
        end_date = (datetime.datetime.strptime(date_str,'%Y-%m-%d') + datetime.timedelta(days=(6-w))).strftime('%Y-%m-%d')
        # end_date = [int(item) for item in end_date.split('-')]
        return start_date,end_date

# 获取上月月份
def get_prev_month(year,month):
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1
    return [year,month]

# 根据月份获取开始日期和结束日期
def get_month_start_end(year,month):
    day_begin = [year, month, 1]  # 月初肯定是1号
    wday, monthRange = monthrange(year, month)
    day_end = [year, month, monthRange]
    return day_begin,day_end

# 获取用户名和职务
def get_username_target(user_id):
    user_sql = "SELECT USER_NAME,STATION FROM sys_user WHERE USER_ID = %s "
    cur = connection.cursor()
    cur.execute(user_sql,user_id)
    row = cur.fetchone()
    user_name = row[0]
    target_code = row[1]
    cur.close()
    return user_name,target_code

 # 获取用户列表 和 职务列表
def get_userlist_tagetlist():
    target_sql = "select dict_code,dict_target from sys_ywty_dict where DICT_NAME='POSITION'"
    user_sql = "select USER_ID,USER_NAME from sys_user"
    cur = connection.cursor()
    cur.execute(target_sql)
    rows = cur.fetchall()
    taget_list = []
    for item in rows:
        tmp_dict = {
            'key': item[0],
            'value': item[1]
        }
        taget_list.append(tmp_dict)
    cur.execute(user_sql)
    rows = cur.fetchall()
    user_list = []
    for item in rows:
        tmp_dict = {
            'key': item[0],
            'value': item[1]
        }
        user_list.append(tmp_dict)
    return user_list,taget_list


#个人周报信息展示
def person_week_show(request):
    log = public.logger
    body = public.req_body
    form_data = body.get('form_data') #可能为空
    form_var={}

    try:
        #获取当前年份和月份
        now_time = time.localtime()
        now_year = now_time.tm_year
        now_month = now_time.tm_mon
        now_day = now_time.tm_mday

        #获取上周的年月日
        my_time = datetime.datetime.now() + datetime.timedelta(days=-7)
        last_week_time = time.localtime(my_time.timestamp())
        last_week_year = last_week_time.tm_year
        last_week_month = last_week_time.tm_mon
        last_week_day = last_week_time.tm_mday

        cur = connection.cursor()  # 创建游标

        #根据用户ID获取用户信息
        sql = "select user_id,user_name from sys_user where user_id=%s"
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        form_var['user_id_options'] = []
        for item in rows:
            form_var['user_id_options'].append({"key": item[0], "value": item[1]})
            form_var['user_id'] = item[0]
        #用户机构信息
        sql="select a.org_id, b.org_name from sys_user_org a, sys_org b where a.org_id=b.org_id and a.user_id=%s"
        cur.execute( sql,public.user_id )
        rows=cur.fetchall()
        form_var['org_id_options']=[]
        for item in rows:
            form_var['org_id_options'].append({"key":item[0], "value":item[1]})
            form_var['org_id'] = item[0]
        #用户岗位信息
        sql = "select a.station, b.dict_target from sys_user a, sys_ywty_dict b " \
              "where a.station=b.dict_code and b.dict_name='POSITION' and a.user_id=%s"
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        form_var['duties_options'] = []
        for item in rows:
            form_var['duties_options'].append({"key": item[0], "value": item[1]})
            form_var['duties'] = item[0]

        #获取上周周报内容：
        form_var['week_id_l'] = get_week_of_month(last_week_year, last_week_month, last_week_day)
        sql = "select id, tran_date, week_id, week_start, week_end from yw_report_personal_week_head where user_id=%s and week_id=%s "
        cur.execute(sql, (public.user_id, form_var.get('week_id_l') ) )
        row = cur.fetchone()
        if not row:
            #无数据
            form_var['id_l'] = None
            form_var['tran_date_l'] = None
            # form_var['week_id_l'] = None
            form_var['week_start_l'], form_var['week_end_l'] = get_week_start_end(last_week_year, last_week_month, last_week_day)
            form_var['bodyinfo_l'] = []
        else:
            form_var['id_l'] = row[0]
            form_var['tran_date_l'] = row[1]
            form_var['week_id_l'] = row[2]
            form_var['week_start_l'] = row[3]
            form_var['week_end_l'] = row[4]
            sql = "select id, plan_matter, for_problem, plan_finish_date, completion_progress, true_finish_date, improve_action " \
                  "from yw_report_personal_week_body where head_id=%s"
            cur.execute(sql, ( form_var.get('week_id_l')))
            rows = cur.fetchall()
            form_var['bodyinfo_l'] = []
            for item in rows:
                item_data = {}
                item_data['body_id'] = item[0]
                item_data['plan_matter'] = item[1]
                item_data['for_problem'] = item[2]
                item_data['plan_finish_date'] = item[3]
                item_data['completion_progress'] = item[4]
                item_data['true_finish_date'] = item[5]
                item_data['improve_action'] = item[6]
                form_var['bodyinfo_l'].append(item_data)

        if not form_data or len(form_data)==0: #无上送数据，新增周报信息
            form_var['id_n'] = None
            form_var['tran_date_n']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            form_var['week_id_n'] = get_week_of_month(now_year, now_month, now_day)
            form_var['week_start_n'],form_var['week_end_n'] = get_week_start_end(now_year, now_month, now_day)
            bodyinfo_n_data={
                "plan_matter":"",
                "for_problem": "",
                "plan_finish_date": "",
            }
            form_var['bodyinfo_n'] = []
            form_var['bodyinfo_n'].append(bodyinfo_n_data)
        else:#查询本周周报详情
            form_var['week_id_n'] = get_week_of_month(now_year, now_month, now_day)
            sql = "select id, tran_date, week_id, week_start, week_end from yw_report_personal_week_head where user_id=%s and week_id=%s "
            cur.execute(sql, (public.user_id, form_var.get('week_id_n')))
            row = cur.fetchone()
            if not row:
                # 无数据
                form_var['id_n'] = None
                form_var['tran_date_n'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # form_var['week_id_n'] = get_week_of_month(now_year, now_month, now_day)
                form_var['week_start_n'], form_var['week_end_n'] = get_week_start_end(now_year, now_month, now_day)
                bodyinfo_n_data = {
                    "plan_matter": "",
                    "for_problem": "",
                    "plan_finish_date": "",
                }
                form_var['bodyinfo_n'] = []
                form_var['bodyinfo_n'].append(bodyinfo_n_data)
            else:
                form_var['id_n'] = row[0]
                form_var['tran_date_n'] = row[1]
                form_var['week_id_n'] = row[2]
                form_var['week_start_n'] = row[3]
                form_var['week_end_n'] = row[4]
                form_var['bodyinfo_n'] = []
                sql = "select id, plan_matter, for_problem, plan_finish_date, completion_progress, true_finish_date, improve_action " \
                      "from yw_report_personal_week_body where head_id=%s"
                cur.execute(sql, (form_var.get('id_n')))
                rows = cur.fetchall()
                for item in rows:
                    item_data = {}
                    item_data['body_id'] = item[0]
                    item_data['plan_matter'] = item[1]
                    item_data['for_problem'] = item[2]
                    item_data['plan_finish_date'] = item[3]
                    # item_data['completion_progress'] = item[4]
                    # item_data['true_finish_date'] = item[5]
                    # item_data['improve_action'] = item[6]
                    form_var['bodyinfo_n'].append(item_data)


        cur.close()  # 关闭游标

        body['form_var']=form_var

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#个人周报信息保存
def person_week_save(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var') #可能为空
    try:
        cur = connection.cursor()  # 创建游标

        #本周周报-登记head表
        form_var['tran_date_n'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if form_var.get('id_n'):
            sql = "update yw_report_personal_week_head set tran_date=%s,org_id=%s,user_id=%s,duties=%s where id=%s"
            cur.execute(sql, (
            form_var.get('tran_date_n'), form_var.get('org_id'), form_var.get('user_id'), form_var.get('duties'),
            form_var.get('id_n')))
        else:
            sql = "insert into yw_report_personal_week_head(tran_date, week_id, week_start, week_end, org_id, user_id, duties) " \
                  "values(%s, %s, %s, %s, %s, %s,%s )"
            cur.execute(sql,   (form_var.get('tran_date_n'), form_var.get('week_id_n'),form_var.get('week_start_n'),
                                form_var.get('week_end_n'), form_var.get('org_id'), form_var.get('user_id'), form_var.get('duties') ))
            form_var['id_n']=cur.lastrowid
        #上周周报-登记head表
        if form_var.get('id_l'):
            form_var['tran_date_l'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "update yw_report_personal_week_head set tran_date=%s,org_id=%s,user_id=%s,duties=%s where id=%s"
            cur.execute(sql, (
            form_var.get('tran_date_l'), form_var.get('org_id'), form_var.get('user_id'), form_var.get('duties'),
            form_var.get('id_l')))

        # 本周周报-登记body表
        if form_var.get('bodyinfo_n'):
            sql = "delete from yw_report_personal_week_body where head_id=%s"
            log.info(sql % form_var.get('id_n',''))
            cur.execute(sql,  form_var.get('id_n') )
            for item in form_var.get('bodyinfo_n'):
                if item.get('plan_matter'):
                    sql = "insert into yw_report_personal_week_body(head_id, plan_matter, for_problem, plan_finish_date) " \
                          "values(%s, %s, %s, %s)"
                    cur.execute(sql, ( form_var.get('id_n'), item.get('plan_matter'), item.get('for_problem'),
                                       item.get('plan_finish_date') ) )

        # 上周周报-更新body表
        for item in form_var.get('bodyinfo_n'):
            if item.get('body_id'):
                sql = "update yw_report_personal_week_body " \
                      "set completion_progress=%s, true_finish_date=%s, improve_action=%s where id=%s"
                cur.execute(sql,
                            (form_var.get('completion_progress'), item.get('true_finish_date'),
                             item.get('improve_action'), item.get('body_id')))

        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#部门月报信息展示
def section_month_show(request):
    log = public.logger
    body = public.req_body
    form_data = body.get('form_data') #可能为空
    form_var={}
    form_var['bodyinfo_n'] = [] #本月待办工作

    if form_data and form_data.get('user_id'): #有原数据
        newflag = False
        userid = form_data.get('user_id')
    else: #新增数据
        newflag = True
        userid = public.user_id

    try:
        # 获取本月月份ID,第一天和最后一天
        today = datetime.datetime.now()
        this_month_id = today.strftime('%Y%m')  # 本月月份ID
        this_month_start_day = datetime.date(today.year, today.month, 1)  # 当月第一最后一天
        month_last_day = monthrange(today.year, today.month)[1]  ## 最后一天的天数
        this_month_end_day = datetime.date(today.year, today.month, month_last_day)  # 当月最后一天

        # 获取上月月份ID, 上月的第一天和最后一天
        last_day = this_month_start_day + datetime.timedelta(days=-1)
        last_month_id = last_day.strftime('%Y%m')  # 上月月份ID
        last_month_start_day = datetime.date(last_day.year, last_day.month, 1)  # 当月第一最后一天
        month_last_day = monthrange(last_day.year, last_day.month)[1]  ## 最后一天的天数
        last_month_end_day = datetime.date(last_day.year, last_day.month, month_last_day)  # 当月最后一天
        # print(this_month_id, this_month_start_day, this_month_end_day)
        # print(last_month_id, last_month_start_day, last_month_end_day)

        cur = connection.cursor()  # 创建游标

        #根据用户ID获取用户信息
        sql = "select user_id, user_name from sys_user where user_id=%s"
        cur.execute(sql, userid)
        rows = cur.fetchall()
        form_var['user_id_options'] = []
        for item in rows:
            form_var['user_id_options'].append({"key": item[0], "value": item[1]})
            form_var['user_id'] = item[0]
        #用户机构信息
        sql="select a.org_id, b.org_name from sys_user_org a, sys_org b where a.org_id=b.org_id and a.user_id=%s"
        cur.execute( sql,userid )
        rows=cur.fetchall()
        form_var['org_id_options']=[]
        for item in rows:
            form_var['org_id_options'].append({"key":item[0], "value":item[1]})
            form_var['org_id'] = item[0]
        #用户岗位信息
        sql = "select a.station, b.dict_target from sys_user a, sys_ywty_dict b " \
              "where a.station=b.dict_code and b.dict_name='POSITION' and a.user_id=%s"
        cur.execute(sql, userid)
        rows = cur.fetchall()
        form_var['duties_options'] = []
        for item in rows:
            form_var['duties_options'].append({"key": item[0], "value": item[1]})
            form_var['duties'] = item[0]

        #获取上月月报内容：
        sql = "select id, tran_date, month_id, month_start, month_end from yw_report_section_month_head " \
              "where user_id='%s' and month_id='%s' " % (userid, last_month_id )
        cur.execute( sql )
        row = cur.fetchone()
        if not row:
            #无数据
            form_var['id_l'] = None
            form_var['tran_date_l'] = today.strftime('%Y-%m-%d %H:%M:%S')
            form_var['month_id_l'] = last_month_id
            form_var['month_start_l'] = last_month_start_day.strftime('%Y-%m-%d')
            form_var['month_end_l'] = last_month_end_day.strftime('%Y-%m-%d')
            form_var['bodyinfo_l'] = []
        else:
            form_var['id_l'] = row[0]
            form_var['tran_date_l'] = row[1].strftime('%Y-%m-%d %H:%M:%S')
            form_var['month_id_l'] = row[2]
            form_var['month_start_l'] = row[3]
            form_var['month_end_l'] = row[4]
            sql = "select id, plan_matter, for_problem, plan_finish_date, completion_progress, true_finish_date, improve_action " \
                  "from yw_report_section_month_body where head_id='%s'" % form_var.get('id_l')
            log.info(sql)
            cur.execute( sql )
            rows = cur.fetchall()
            form_var['bodyinfo_l'] = []
            for item in rows:
                item_data = {}
                item_data['body_id'] = item[0]
                item_data['plan_matter'] = item[1]
                item_data['for_problem'] = item[2]
                item_data['plan_finish_date'] = item[3]
                item_data['completion_progress'] = item[4]
                item_data['true_finish_date'] = item[5]
                item_data['improve_action'] = item[6]

                if not item_data['completion_progress']:
                    item_data['completion_progress'] ='0'
                form_var['bodyinfo_l'].append(item_data)

                # log.info('completion_progress=[%s]' % item_data['completion_progress'])
                # if item_data['completion_progress'] !='100' and item_data['completion_progress'] !='100%' \
                #         and item_data['completion_progress'] !='已完成' \
                #         and item_data['completion_progress'] !='完成':
                #     #上月未完成的任务，自动添加到本月
                #     form_var['bodyinfo_n'].append(item_data)

        if not form_data or len(form_data)==0: #无上送数据，新增周报信息
            form_var['id_n'] = None
            form_var['tran_date_n']=today.strftime('%Y-%m-%d %H:%M:%S')
            form_var['month_id_n'] = this_month_id
            form_var['month_start_n'] = this_month_start_day.strftime('%Y-%m-%d')
            form_var['month_end_n'] = this_month_end_day.strftime('%Y-%m-%d')
            bodyinfo_n_data={
                "plan_matter":"",
                "for_problem": "",
                "plan_finish_date": "",
            }
            form_var['bodyinfo_n'].append(bodyinfo_n_data)
        else:#查询本周周报详情
            sql = "select id, tran_date, month_id, month_start, month_end from yw_report_section_month_head " \
                  "where user_id=%s and month_id=%s " % (userid, this_month_id)
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                # 无数据
                form_var['id_n'] = None
                form_var['tran_date_n'] = today.strftime('%Y-%m-%d %H:%M:%S')
                form_var['month_id_n'] = this_month_id
                form_var['month_start_n'] = this_month_start_day.strftime('%Y-%m-%d')
                form_var['month_end_n'] = this_month_end_day.strftime('%Y-%m-%d')
                bodyinfo_n_data = {
                    "plan_matter": "",
                    "for_problem": "",
                    "plan_finish_date": "",
                }
                form_var['bodyinfo_n'].append(bodyinfo_n_data)
            else:
                form_var['id_n'] = row[0]
                form_var['tran_date_n'] = row[1]
                form_var['month_id_n'] = row[2]
                form_var['month_start_n'] = row[3]
                form_var['month_end_n'] = row[4]
                sql = "select id, plan_matter, for_problem, plan_finish_date, completion_progress, true_finish_date, improve_action " \
                      "from yw_report_section_month_body where head_id='%s'" % (form_var.get('id_n'))
                cur.execute(sql)
                rows = cur.fetchall()
                for item in rows:
                    item_data = {}
                    item_data['body_id'] = item[0]
                    item_data['plan_matter'] = item[1]
                    item_data['for_problem'] = item[2]
                    item_data['plan_finish_date'] = item[3]
                    # item_data['completion_progress'] = item[4]
                    # item_data['true_finish_date'] = item[5]
                    # item_data['improve_action'] = item[6]
                    form_var['bodyinfo_n'].append(item_data)

        cur.close()  # 关闭游标

        body['form_var']=form_var

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#部门月报信息保存
def section_month_save(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var') #可能为空
    try:
        cur = connection.cursor()  # 创建游标
        today = datetime.datetime.now()
        #本周周报-登记head表
        form_var['tran_date_n'] = today.strftime('%Y-%m-%d %H:%M:%S')
        if form_var.get('id_n'):
            sql = "update yw_report_section_month_head set tran_date=%s,org_id=%s,user_id=%s,duties=%s where id=%s"
            cur.execute(sql, (
            form_var.get('tran_date_n'), form_var.get('org_id'), form_var.get('user_id'), form_var.get('duties'),
            form_var.get('id_n')))
        else:
            sql = "insert into yw_report_section_month_head(tran_date, month_id, month_start, month_end, org_id, user_id, duties) " \
                  "values(%s, %s, %s, %s, %s, %s,%s )"
            cur.execute(sql,   (form_var.get('tran_date_n'), form_var.get('month_id_n'),form_var.get('month_start_n'),
                                form_var.get('month_end_n'), form_var.get('org_id'), form_var.get('user_id'), form_var.get('duties') ))
            form_var['id_n']=cur.lastrowid

        # 本周周报-登记body表
        if form_var.get('bodyinfo_n'):
            sql = "delete from yw_report_section_month_body where head_id=%s"
            log.info(sql % form_var.get('id_n',''))
            cur.execute(sql,  form_var.get('id_n') )
            for item in form_var.get('bodyinfo_n'):
                if item.get('plan_matter'):
                    if not item.get('plan_finish_date'):
                        cur.close()  # 关闭游标
                        public.respcode, public.respmsg = "872001", "计划完成时间不可为空!"
                        public.respinfo = HttpResponse(public.setrespinfo())
                        return public.respinfo
                    sql = "insert into yw_report_section_month_body(head_id, plan_matter, for_problem, plan_finish_date) " \
                          "values(%s, %s, %s, %s)"
                    cur.execute(sql, ( form_var.get('id_n'), item.get('plan_matter'), item.get('for_problem'),
                                       item.get('plan_finish_date') ) )

        # 上周周报-更新body表
        for item in form_var.get('bodyinfo_l'):
            if item.get('body_id'):
                sql = "update yw_report_section_month_body " \
                      "set completion_progress=%s, true_finish_date=%s, improve_action=%s where id=%s"
                cur.execute(sql,
                            (form_var.get('completion_progress'), item.get('true_finish_date'),
                             item.get('improve_action'), item.get('body_id')))

        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo
