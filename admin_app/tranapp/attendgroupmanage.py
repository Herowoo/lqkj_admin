import sys
from django.shortcuts import render, redirect, HttpResponse
from django.db import connection, transaction
import json

from admin_app import models
from admin_app.sys import public
import datetime
from admin_app.tranapp import pubfunc
import requests
import itertools

###########################################################################################################
# 考勤组管理
# add by Wuxm, 2021.03.16
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


# 更新考勤組人員
def attend_manage_group_cfg(request):
    log = public.logger
    form_var = public.req_body['form_var']
    try:
        cur = connection.cursor()  # 创建游标
        group_list = form_var.get('group_list')
        if not group_list:
            public.respcode, public.respmsg = "310310", "请先选择考勤組!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sql = "select 1 from yw_workflow_attend_group_user where group_id=%s"
        cur.execute(sql, group_list)
        row = cur.fetchone()
        if row:  # 有数据， 更新
            sql = "update yw_workflow_attend_group_user set user_id=%s where group_id=%s"
        else:  # 无数据，插入
            sql = "insert into yw_workflow_attend_group_user (user_id, group_id) values (%s, %s)"
        log.info(sql, (str(form_var.get('userinfo')), group_list))
        cur.execute(sql, (str(form_var.get('userinfo')), group_list))
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
def get_user_info(request):
    log = public.logger
    form_data = public.req_body['form_data']

    try:
        # group_list = form_data.get('group_list')
        # if not group_list:
        #     public.respcode, public.respmsg = "310310", "请先选择考勤组!"
        #     public.respinfo = HttpResponse(public.setrespinfo())
        #     return public.respinfo

        cur = connection.cursor()  # 创建游标
        # sql = "SELECT group_id, group_name from yw_workflow_attend_group"
        # cur.execute(sql)
        # row = cur.fetchone()
        # if row: #有数据
        #     form_data['group_list'] = row[0]
        #     if row[1]:
        #         form_data['read_cfginfo'] = eval(row[1])
        #     else:
        #         form_data['read_cfginfo'] = eval([])
        #
        #     form_data['write_cfgtype'] = row[2]
        #     if row[3]:
        #         form_data['write_cfginfo'] = eval(row[3])
        #     else:
        #         form_data['write_cfginfo'] = eval([])

        # 获取下拉配置属性
        sql = "SELECT group_id, group_name from yw_workflow_attend_group"
        cur.execute(sql)
        rows = cur.fetchall()
        options = []
        group_list = rows[0][0]
        form_data['group_list'] = rows[0][1]  # 考勤组初始值
        for item in rows:
            options.append({"key": item[0], "value": item[1]})
        form_data['group_list_option'] = options

        # 全部用户
        sql = "SELECT user_id,user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows = cur.fetchall()
        all_user = []
        dic_user = {}
        for item in rows:
            all_user.append(item[0])
            dic_user[item[0]] = item[1]
        # 已分配当前组组用户
        sql = "SELECT user_id from yw_workflow_attend_group_user where group_id = %s"
        cur.execute(sql, group_list)
        rows = cur.fetchone()
        group_user = eval(rows[0])
        form_data['userinfo'] = group_user

        # 配置穿梭框数据
        transfer = []
        for item in dic_user:
            transfer.append({"key": item, "label": dic_user.get(item), "disabled": False})
        form_data['userinfo_option'] = transfer

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

        sql = "select dict_code,CONCAT(dict_code,'-',dict_target) from sys_ywty_dict where " \
              "dict_name='DOCMENT_MANAGE_READ_CFGTYPE' "
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


# 考勤组排班保存
def attend_schedule_save(request):
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    try:
        cur = connection.cursor()  # 创建游标

        month_id = form_var.get('month_id')
        group_list = form_var.get('group_list')
        # 插入休息日字段
        day_list_option = form_var.get('day_list_option')
        day_list = form_var.get('day_list')
        month_day_list = []
        for item in day_list_option:
            month_day_list.append(item.get('key'))
        res_day_list = set(month_day_list).difference(set(day_list))
        res_day_list = list(res_day_list)
        sql_value = (str(day_list), str(res_day_list), form_var.get('work_time'), form_var.get('closing_time'),
                     form_var.get('am_closing'), form_var.get('pm_start'),
                     form_var.get('group_list'), form_var.get('month_id'))
        log.info("============STR_LIST===========")
        log.info(str(form_var.get('day_list')))
        if month_id and group_list:
            sql = 'select 1 from yw_workflow_attend_group_cfg where group_id = %s and month_id = %s'
            cur.execute(sql, (form_var.get('group_list'), form_var.get('month_id')))

            row = cur.fetchone()
            if row:  # 有数据， 更新
                sql = "update yw_workflow_attend_group_cfg set work_day=%s, rest_day=%s,work_time=%s," \
                      "closing_time=%s,am_closing_time=%s,pm_start_time=%s where group_id = %s and month_id = %s"
            else:  # 无数据，插入
                sql = "insert into yw_workflow_attend_group_cfg (work_day,rest_day,work_time,closing_time," \
                      "am_closing_time,pm_start_time, group_id, month_id) values (%s, %s, %s, %s, %s, %s, %s, %s)"
        else:
            pass
        log.info(sql, sql_value)

        cur.execute(sql, sql_value)
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


def attend_report_detail(st_date, ed_date):
    log = public.logger
    frm = '%Y-%m-%d'
    day_list = pubfunc.get_datelist(st_date, ed_date)
    # 时间段内正常考勤员工
    try:
        start_date = datetime.datetime.strptime(st_date, frm)
        end_date = datetime.datetime.strptime(ed_date, frm)
        cur = connection.cursor()
        sql = "SELECT emp_name,attend_number,attend_group,entry_date,leave_date from sys_staff_info "
        cur.execute(sql)
        staff_rows = cur.fetchall()
        for day in day_list:
            sql = "SELECT emp_name,attend_number,attend_group from sys_staff_info where last_work_day >= %s "
    except Exception as ex:
        log.info("Error: "+str(ex))


def general_attend_report_mx(request):
    """生成考勤明细报表"""
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    # 用户所在组列表
    group_id = []
    month_id = form_var.get('month_id')
    if not month_id:
        public.respcode, public.respmsg = "310310", "请先选择考勤月份!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    try:
        cur = connection.cursor()  # 创建游标
        # 返回 [考勤组-用户] 表
        sql = "select group_id,user_id from yw_workflow_attend_group_user"
        cur.execute(sql)
        group_user = cur.fetchall()
        # 请假类型
        # sql = "SELECT dict_code,dict_target from sys_ywty_dict where dict_name = 'LEAVE_TYPE'"
        sql = "SELECT category,attend_name FROM yw_workflow_attend_dict"
        cur.execute(sql)
        attend_set = {}
        rows = cur.fetchall()
        for row in rows:
            attend_set[row[0]] = row[1]
        # 查询请假信息
        absence_list = []
        sql = "SELECT s.uid,start_date,end_date,category,apply_state from yw_workflow_apply_absence a JOIN sys_user s" \
              " on a.user_id = s.USER_ID where s.uid is not null"
        cur.execute(sql)
        tb_absence = cur.fetchall()
        for row in tb_absence:
            temp_set = {row[0]: (row[1], row[2], row[3], row[4])}
            absence_list.append(temp_set)
        # 查询出差信息
        travel_list = []
        sql = "SELECT s.uid,start_date,end_date,apply_state from yw_workflow_apply_travel a JOIN sys_user s " \
              " on a.user_id = s.USER_ID where s.uid is not null"
        cur.execute(sql)
        tb_travel = cur.fetchall()
        for row in tb_travel:
            temp_set = {row[0]: (row[1], row[2], row[3])}
            travel_list.append(temp_set)

        # 展开考勤排班
        schedule_set = {}
        sql = "SELECT group_id,month_id,work_day,rest_day,work_time,closing_time,am_closing_time,pm_start_time" \
              " from yw_workflow_attend_group_cfg where month_id = %s"
        cur.execute(sql, month_id)
        group_cfg = cur.fetchall()
        # 批量更新sql
        sql_del_value = []
        sql_ins_value = []
        for row in group_cfg:
            group_id = row[0]
            month_id = row[1]
            work_time = row[4]
            closing_time = row[5]
            am_closing_time = row[6]
            pm_start_time = row[7]
            work_day_list = eval(row[2])
            res_day_list = eval(row[3])
            worktime_set = {}
            for workday in work_day_list:
                day_string = month_id + '-' + workday
                am_start_date = pubfunc.str_datetime(day_string + ' ' + work_time)
                am_close_date = pubfunc.str_datetime(day_string + ' ' + am_closing_time)
                pm_start_date = pubfunc.str_datetime(day_string + ' ' + pm_start_time)
                pm_close_date = pubfunc.str_datetime(day_string + ' ' + closing_time)
                worktime_set[day_string] = (am_start_date, am_close_date, pm_start_date, pm_close_date)
            for restday in res_day_list:
                day_string = month_id + '-' + restday
                worktime_set[day_string] = None
            schedule_set[group_id] = worktime_set
        # 根据月份与工号分组查询原始考勤记录表
        sql = "SELECT name,job_num,DATE_FORMAT(attend_time,'%%Y-%%m-%%d'), MIN(DATE_FORMAT(attend_time,'%%H:%%i:%%s'))" \
              ",MAX(DATE_FORMAT(attend_time,'%%H:%%i:%%s')) 'out_time',department " \
              "from yw_workflow_attend_mx where month_id = %s group by job_num,DATE_FORMAT(attend_time,'%%Y-%%m-%%d')"
        cur.execute(sql, month_id)
        ds = cur.fetchall()
        for item in ds:  # 每人每天出勤
            user_name = item[0]
            job_num = item[1]
            day = item[2]
            in_time = datetime.datetime.strptime(day + item[3], '%Y-%m-%d%H:%M:%S')
            out_time = datetime.datetime.strptime(day + item[4], '%Y-%m-%d%H:%M:%S')
            department = item[5]
            # 出勤状态
            state = []
            gid = []
            # 查询user_id所在考勤组
            for t in group_user:
                if job_num in t[1]:
                    gid.append(t[0])
            day_schedule_list = []
            for g in gid:
                # 查询考勤组排班安排
                if schedule_set.get(g):
                    day_schedule_list.append(schedule_set.get(g).get(day))
            # 当天有多个排班时间，上班时间取最早，下班时间取最晚
            if len(day_schedule_list) > 1:
                a0 = day_schedule_list[0][0]
                a1 = day_schedule_list[0][1]
                a2 = day_schedule_list[0][2]
                a3 = day_schedule_list[0][3]
                for dsl in day_schedule_list:
                    if dsl[0] < a0:
                        a0 = dsl[0]
                    if dsl[1] > a1:
                        a1 = dsl[1]
                    if dsl[2] < a2:
                        a2 = dsl[2]
                    if dsl[3] > a3:
                        a3 = dsl[3]
                day_schedule = (a0, a1, a2, a3)
            elif len(day_schedule_list) == 1:
                day_schedule = day_schedule_list[0]
            else:
                # 当天没有排班
                day_schedule = None
                state.append('公休')
            # 工作日
            if day_schedule:
                am_start = day_schedule[0]
                am_close = day_schedule[1]
                pm_start = day_schedule[2]
                pm_close = day_schedule[3]
                # 是否请假
                for line in absence_list:
                    absence = line.get(job_num)
                    if absence:
                        ab_start_date = absence[0]
                        ab_end_date = absence[1]
                        category = attend_set.get(absence[2])
                        ab_state = absence[3]
                        if ab_start_date >= pm_close or ab_end_date <= am_start:
                            # state += get_attend_state(in_time, out_time, am_start, pm_close)
                            pass
                        # 请上午半天
                        elif ab_start_date <= am_start and pm_start >= ab_end_date >= am_close:
                            # 判断下午上班状态
                            state.append(category)
                            state += get_attend_state(in_time, out_time, pm_start, pm_close)
                        # 请全天
                        elif ab_start_date <= am_start and ab_end_date >= pm_close:
                            state.append(category)
                        # 请下午半天
                        elif pm_start >= ab_start_date >= am_close and ab_end_date >= pm_close:
                            # 判断上午午上班状态
                            state.append(category)
                            state += get_attend_state(in_time, out_time, am_start, am_close)
                        else:
                            # 请几个小时，特殊情况手动处理
                            state.append('待处理')
                    else:
                        pass
                # 是否出差
                tv_type = '出差'
                for line in travel_list:
                    tv = line.get(job_num)
                    if tv:
                        tv_start_date = tv[0]
                        tv_end_date = tv[1]
                        tv_state = tv[2]
                        if tv_start_date >= pm_close or tv_end_date <= am_start:
                            # state += get_attend_state(in_time, out_time, am_start, pm_close)
                            pass
                        # 上午出差
                        elif tv_start_date <= am_start and pm_start >= tv_end_date >= am_close:
                            # 判断下午上班状态
                            state.append(tv_type)
                            state += get_attend_state(in_time, out_time, pm_start, pm_close)
                        # 全天出差
                        elif tv_start_date <= am_start and tv_end_date >= pm_close:
                            state.append(tv_type)
                        # 下午出差
                        elif pm_start >= tv_start_date >= am_close and tv_end_date >= pm_close:
                            # 判断上午午上班状态
                            state.append(tv_type)
                            state += get_attend_state(in_time, out_time, am_start, am_close)
                        else:
                            # 出差几个小时，特殊情况手动处理
                            state.append('待处理')
                    else:
                        pass
                # 计算出勤状态
                state += get_attend_state(in_time, out_time, am_start, pm_close)
            # 公休日
            else:
                # 加班
                state.append('加班')

            sql_del_value.append((job_num, day))
            sql_ins_value.append((department, job_num, user_name, day, in_time.strftime('%T'),
                                  out_time.strftime('%T'), str(state)))
        # 更新考勤报表
        sql = "delete from yw_workflow_attend_report_mx where job_num = %s and natural_day = %s"
        cur.executemany(sql, sql_del_value)
        sql = "INSERT INTO yw_workflow_attend_report_mx (department,job_num,user_name,natural_day,in_time," \
              "out_time,state) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        # cur.execute(sql, (department, job_num, user_name, day, in_time.strftime('%T'),
        #                   out_time.strftime('%T'), str(state)))
        cur.executemany(sql, sql_ins_value)

        # # 总报表

        general_attend_report(month_id)
        # 显示报表
        sql = "select id,month_id,department,user_name,job_num,chid,zaot,gonx,tx,shij,bingj,chuc,sangj,cj,pcj," \
              "attend_days,work_days from yw_workflow_attend_report where month_id = %s limit 0,10"
        cur.execute(sql, month_id)
        rows = cur.fetchall()
        list_table_show = []
        rowcount = 1
        for row in rows:
            dic_row = {'data_seq_no': rowcount, 'month_id': row[1], 'department': row[2], 'user_name': row[3],
                       'job_num': row[4], 'chid': row[5], 'zaot': row[6], 'gonx': row[7], 'tx': row[8], 'shij': row[9],
                       'bingj': row[10], 'chuc': row[11], 'sangj': row[12], 'cj': row[13], 'pcj': row[14],
                       'attend_days': row[15], 'work_days': row[16]}
            list_table_show.append(dic_row)
            rowcount += 1
        form_var['table_report_mx'] = list_table_show
        #
        # export_power = {"show": True, "disabled": False}  # 放开导出按钮
        # form_var['export_power'] = export_power
        # form_var['export_file_power'] = {"show": True, "disabled": False}
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


def get_attend_state(in_time, out_time, work_time, closing_time, offset=1, delay=30):
    """入参：入场时间，出场时间，上班时间，下班时间，闸机时间偏移量默认+1分组，迟到早退延迟时间，默认30分钟"""
    state = []
    work_time += datetime.timedelta(minutes=offset)
    # closing_time += datetime.timedelta(minutes=offset)
    if in_time <= work_time and out_time >= closing_time:
        state.append('正常')
    # 上班后半小时内进场（迟到）
    elif work_time < in_time <= work_time + datetime.timedelta(minutes=delay):
        state.append('迟到')
    # 提前半小时离场（早退）
    elif closing_time > out_time >= closing_time - datetime.timedelta(minutes=delay):
        state.append('早退')
    # 否则视为事假
    else:
        state.append('事假')
    return state


def general_attend_report(month_id):
    """根据考勤明细报表生成总报表"""
    log = public.logger
    try:
        cur = connection.cursor()
        # 获取考勤组-用户列表
        sql = "select group_id,user_id from yw_workflow_attend_group_user"
        cur.execute(sql)
        group_user = cur.fetchall()
        # 获取请假类型字典表
        attend_type_set = {}
        sql = "SELECT category,attend_name from yw_workflow_attend_dict"
        cur.execute(sql)
        all_row = cur.fetchall()
        for item in all_row:
            attend_type_set[item[0]] = item[1]
        # 工号列表
        job_num_list = []
        sql = "SELECT job_num from yw_workflow_attend_report_mx where SUBSTR(natural_day,1,7) = %s GROUP BY job_num"
        cur.execute(sql, month_id)
        # 批量执行sql
        sql_del_value = []
        sql_ins_value = []
        for job_num in cur.fetchall():
            # 查询明细报表
            sql = "SELECT department,job_num,user_name,natural_day,state from yw_workflow_attend_report_mx " \
                  " where SUBSTR(natural_day,1,7) = %s AND job_num = %s"
            cur.execute(sql, (month_id, job_num[0]))
            zhc, chid, zaot, gonx, tx, shij, bingj, chuc, sangj, cj, pcj, jiab = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            row = cur.fetchall()
            department = row[0][0]
            job_num = row[0][1]
            user_name = row[0][2]
            for item in row:
                attend_state = eval(item[4])
                if '正常' in attend_state:
                    zhc += 1
                if '迟到' in attend_state:
                    chid += 1
                if '早退' in attend_state:
                    zaot += 1
                if '公休' in attend_state:
                    gonx += 1
                if '调休' in attend_state:
                    tx += 1
                if '事假' in attend_state:
                    shij += 1
                if '病假' in attend_state:
                    bingj += 1
                if '出差' in attend_state:
                    chuc += 1
                if '丧假' in attend_state:
                    sangj += 1
                if '产假' in attend_state:
                    cj += 1
                if '陪产假' in attend_state:
                    pcj += 1
                if '加班' in attend_state:
                    jiab += 1
            # 出勤天数
            attend_days = zhc + chid + zaot + tx
            if shij > 0:
                # 每月有一天事假可作为正常出勤
                attend_days += 1
            # 工作天数，如果员工在多个考勤组，按考勤天数最多的来计算
            work_days = 0
            gid = []
            # 查询job_num所在考勤组
            for t in group_user:
                if job_num in eval(t[1]):
                    gid.append(t[0])
            for g in gid:
                # 查询考勤组排班安排
                sql = "SELECT work_day from yw_workflow_attend_group_cfg where month_id = %s and group_id = %s"
                cur.execute(sql, (month_id, g))
                row = cur.fetchone()
                temp = len(eval(row[0]))
                if temp > work_days:
                    work_days = temp
            sql_del_value.append((month_id, job_num))
            sql_ins_value.append(
                (department, user_name, job_num, month_id, chid, zaot, gonx, tx, shij, bingj, chuc, sangj,
                 cj, pcj, attend_days, work_days))
        # 更新报表
        sql = "delete from yw_workflow_attend_report WHERE month_id = %s and job_num = %s"
        # cur.execute(sql, (month_id, job_num))
        cur.executemany(sql, sql_del_value)
        sql = "INSERT INTO yw_workflow_attend_report (department,user_name,job_num,month_id,chid,zaot,gonx,tx," \
              "shij,bingj,chuc,sangj,cj,pcj,attend_days,work_days) " \
              "values (%s,%s,%s,%s,%s,  %s,%s,%s,%s,%s,   %s,%s,%s,%s,%s,%s)"
        # sql_value = (department, user_name, job_num, month_id, chid, zaot, gonx, tx, shij, bingj, chuc, sangj,
        #              cj, pcj, attend_days, work_days)
        cur.executemany(sql, sql_ins_value)
    except Exception as ex:
        log.error(ex)
    finally:
        cur.close()


def export_report_excel(request):
    """导出考勤报表"""
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    month_id = form_var.get('month_id')
    if not month_id:
        public.respcode, public.respmsg = "310310", "请先选择考勤月份!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        sql = "select month_id,department,user_name,job_num,chid,zaot,gonx,tx,shij,bingj,chuc,sangj,cj,pcj,attend_days," \
              "work_days from yw_workflow_attend_report where month_id = '%s'" % month_id
        cur = connection.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "310314", "该月尚未生成报表!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        file_name = month_id + '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '考勤报表.xlsx'
        full_file_name = public.localhome + '/static/filedown/' + file_name
        # 导出Excel
        pubfunc.export_excel(full_file_name, sql)
        form_var['file_download_path'] = '/static/filedown/' + file_name

    except Exception as ex:
        log.error(ex)
        # tr.close()
        log.error('导出数据到excel文件错误', exc_info=True)
        data = {
            "respcode": "000000",
            "respmsg": "导出数据到excel文件错误",
            "trantype": public.req_head.get('trantype', None)
        }
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


def export_abnormal_detail_excel(request):
    """导出考勤异常详单"""
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    month_id = form_var.get('month_id')
    if not month_id:
        public.respcode, public.respmsg = "310310", "请先选择考勤月份!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        sql = "select id,state from yw_workflow_attend_report_mx where substr(natural_day,1,7) = '%s'" % month_id
        cur = connection.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        if not rows:
            public.respcode, public.respmsg = "310314", "该月尚未生成报表!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        else:
            id_list = []
            abnormal_list = ['迟到', '早退', '事假', '病假', '丧假', '产假', '陪产假', '待处理']
            for row in rows:
                attend_state = eval(row[1])
                if set(attend_state).intersection(set(abnormal_list)):
                    id_list.append(row[0])
            abnormal_sql = "select department,job_num,user_name,natural_day,in_time,out_time,state " \
                           "from yw_workflow_attend_report_mx " \
                           "where id in %s" % str(tuple(id_list))

            file_name = month_id + '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '考勤异常记录.xlsx'
            full_file_name = public.localhome + '/static/filedown/' + file_name
            # 导出Excel
            pubfunc.export_excel(full_file_name, abnormal_sql)
            form_var['file_download_path'] = '/static/filedown/' + file_name

    except Exception as ex:
        log.error(ex)
        # tr.close()
        log.error('导出数据到excel文件错误', exc_info=True)
        data = {
            "respcode": "000000",
            "respmsg": "导出数据到excel文件错误",
            "trantype": public.req_head.get('trantype', None)
        }
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


def export_overtime_detail_excel(request):
    """导出随线人员加班详单"""
    log = public.logger
    body = public.req_body
    form_var = body['form_var']
    month_id = form_var.get('month_id')
    if not month_id:
        public.respcode, public.respmsg = "310310", "请先选择考勤月份!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()
        sql = "select id,state from yw_workflow_attend_report_mx where substr(natural_day,1,7) = '%s'" % month_id
        cur.execute(sql)
        rows = cur.fetchall()
        if not rows:
            public.respcode, public.respmsg = "310314", "该月尚未生成报表!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        else:
            # 查询随线人员列表
            sql = "select user_id from yw_workflow_attend_group_user where group_id = '3'"
            cur.execute(sql)
            row = cur.fetchone()
            sx_user = eval(row[0])
            # 查询该组人员下班时间
            sql = "SELECT name,department,job_num,DATE_FORMAT(attend_time,'%%Y-%%m-%%d'), " \
                  "MIN(DATE_FORMAT(attend_time,'%%H:%%i:%%s'))" \
                  ",MAX(DATE_FORMAT(attend_time,'%%H:%%i:%%s')) 'out_time' " \
                  "from yw_workflow_attend_mx where month_id = '%s' and job_num in %s " \
                  "group by job_num,DATE_FORMAT(attend_time,'%%Y-%%m-%%d') ORDER BY job_num" % (month_id, str(tuple(sx_user)))
            cur.execute(sql)
            rows = cur.fetchall()
            overtime_detail_list = []
            overtime_detail_title = ('姓名', '部门', '工号', '日期', '上班时间', '下班时间', '加班时间')
            overtime_detail_list.append(overtime_detail_title)
            if rows:
                log.info('OK')
                fmt = '%H:%M:%S'
                for row in rows:
                    temp_list = list(row)
                    leave_time = datetime.datetime.strptime(row[5], fmt)
                    end_time = datetime.datetime.strptime('18:00:00', fmt)
                    if leave_time > end_time:
                        over_time = leave_time - end_time
                        over_hours = pubfunc.aj_halfhour(over_time.seconds/3600)
                    else:
                        over_hours = 0
                    temp_list.append(over_hours)
                    overtime_detail_list.append(tuple(temp_list))
            else:
                public.respcode, public.respmsg = "310314", "未查询到加班信息!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            # 加班汇总表
            # 待优化
            overtime_list = [('月份', '姓名', '部门', '工号', '加班时长')]
            # 优化后代码
            temp_list = overtime_detail_list[1:]
            temp_list.sort(key=lambda x: x[2])
            l = itertools.groupby(temp_list, lambda x: x[2])
            for k, v in l:
                total_time = 0
                for x in v:
                    month = x[3][:7]
                    name = x[0]
                    depart = x[1]
                    total_time += x[6]
                overtime_list.append((month, name, depart, k, total_time))
            # 结束
            # temp_job_num = overtime_detail_list[1][2]
            # total_hour = 0
            # temp_row = []
            # for l in overtime_detail_list[1:]:
            #     if temp_job_num == l[2]:
            #         total_hour += float(l[6])
            #         temp_row = [l[3][:7], l[0], l[1], l[2], total_hour]
            #     else:
            #         overtime_list.append(temp_row)
            #         temp_row = []
            #         temp_job_num = l[2]
            #         total_hour = float(l[6])
            list_all = [overtime_detail_list, overtime_list]
            file_name = month_id + '_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '随线人员加班记录.xlsx'
            full_file_name = public.localhome + '/static/filedown/' + file_name
            # 导出Excel
            # pubfunc.list2excel(full_file_name, overtime_detail_list)
            pubfunc.list2excel_test(full_file_name, *list_all)
            form_var['file_download_path'] = '/static/filedown/' + file_name

    except Exception as ex:
        log.error(ex)
        # tr.close()
        log.error('导出数据到excel文件错误', exc_info=True)
        data = {
            "respcode": "000000",
            "respmsg": "导出数据到excel文件错误",
            "trantype": public.req_head.get('trantype', None)
        }
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


def entryregs(request):
    """入职登记"""
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        id = form_var.get('id')
        if id:
            # 不允许修改
            public.respcode, public.respmsg = "100000", '暂不支持修改'
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        param_not_null = {
            "customer": "客户",
            "tran_date": "日期",
            "prod_name": "名称",
            "prod_type": "型号",
            "prod_unit": "单位",
            "prod_count": "数量",
            "remark_bom": "BOM号",
            "amount_bom": "BOM价格",
            "amount_scfl": "生产辅料成本",
            "amount_rgcb": "人工成本",
            "amount_trans": "运输成本",
            "remark_profit": "利润百分比",
            "remark_tax": "税费百分比",
            "market_price": "市场价",
            "remark_suggest_price": "增值税"
        }
        for k in param_not_null:
            if not form_var.get(k):
                public.respcode, public.respmsg = "320430", param_not_null.get(k) + '不可为空'
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        # 插入次要信息表
        cur = connection.cursor()
        sql = "insert into sys_staff_info_less (jy_sj1, jy_xx1, jy_zy1, jy_zs1, jy_sj2, jy_xx2, jy_zy2, jy_zs2, " \
              "jy_sj3, jy_xx3, jy_zy3, jy_zs3, gz_sj1, gz_dw1, gz_gw1, gz_lz1, gz_zmr1, gz_sj2, gz_dw2, gz_gw2, " \
              "gz_lz2, gz_zmr2, gz_sj3, gz_dw3, gz_gw3, gz_lz3, gz_zmr3, cy_xm1, cy_gx1, cy_dw1, cy_dh1, cy_xm2, " \
              "cy_gx2, cy_dw2, cy_dh2, media_source, source_desc, zwpj, hr_evaluate) " \
              "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s," \
              "%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        sql_value = (form_var.get('jy_sj1'), form_var.get('jy_xx1'), form_var.get('jy_zy1'), form_var.get('jy_zs1'), form_var.get('jy_sj2'), form_var.get('jy_xx2'), form_var.get('jy_zy2'), form_var.get('jy_zs2'), form_var.get('jy_sj3'), form_var.get('jy_xx3'), form_var.get('jy_zy3'), form_var.get('jy_zs3'), form_var.get('gz_sj1'), form_var.get('gz_dw1'), form_var.get('gz_gw1'), form_var.get('gz_lz1'), form_var.get('gz_zmr1'), form_var.get('gz_sj2'), form_var.get('gz_dw2'), form_var.get('gz_gw2'), form_var.get('gz_lz2'), form_var.get('gz_zmr2'), form_var.get('gz_sj3'), form_var.get('gz_dw3'), form_var.get('gz_gw3'), form_var.get('gz_lz3'), form_var.get('gz_zmr3'), form_var.get('cy_xm1'), form_var.get('cy_gx1'), form_var.get('cy_dw1'), form_var.get('cy_dh1'), form_var.get('cy_xm2'), form_var.get('cy_gx2'), form_var.get('cy_dw2'), form_var.get('cy_dh2'), form_var.get('media_source'), form_var.get('source_desc'), form_var.get('zwpj'), form_var.get('hr_evaluate'))
        cur.execute(sql, sql_value)

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