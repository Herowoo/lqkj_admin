import sys
from django.db import connection
from admin_app.sys import public
from admin_app.sys import public_db
from django.shortcuts import HttpResponse
import json
from admin_app.tranapp import pubfunc

###########################################################################################################
#穿梭框数据处理函数
#add by litz, 2020.05.11
#
###########################################################################################################

#穿梭框-测试函数
def transferFun( request ):
    print('transferFun:')
    transferData = ["5"] #已选中数据，绑定变量
    transfer = [  #全部数据, 数据变量
        {
            "key": "1",
            "label": "label1",
            "disabled": False
        },
        {
            "key": "2",
            "label": "label2",
            "disabled": False
        },
        {
            "key": "3",
            "label": "label3",
            "disabled": False
        },
        {
            "key": "4",
            "label": "label4",
            "disabled": False
        },
        {
            "key": "5",
            "label": "label5",
            "disabled": False
        },
        {
            "key": "6",
            "label": "label6",
            "disabled": False
        },
        {
            "key": "7",
            "label": "label7",
            "disabled": False
        },
        {
            "key": "11222",
            "label": "11111111",
            "disabled": False
        }
    ]
    return transferData, transfer

#穿梭框-用户角色
def transfer_userrole( request ):
    log = public.logger
    body = public.req_body
    form_data = body.get('form_data')
    try:
        transfer = [] # 全部数据, 数据变量
        transferData = []  # 已选中数据，绑定变量

        cur = connection.cursor()  # 创建游标
        sql = "select role_id,role_name from sys_role where role_state='1' "
        cur.execute(sql)
        rows=cur.fetchall()
        for item in rows:
            transfer.append( { "key": item[0],  "label": item[0]+'-'+item[1], "disabled": False} )

        #用户已拥有的角色
        if form_data.get('user_id'):
            sql = "select role_id from sys_user_role where user_id=%s"
            cur.execute(sql, form_data.get('user_id') )
            rows=cur.fetchall()
            for item in rows:
                transferData.append( item[0] )

    except Exception as ex:
        log.error("生成穿梭框数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "303010", "生成穿梭框数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return '' ''

    return transferData, transfer


#穿梭框-文件档案管理用户列表, 下拉选择后直接调用的交易
def transfer_docment_readmanage1_usercfg( request ):
    log = public.logger
    body = public.req_body
    select_key = body.get('select_key')
    form_var = body.get('form_var')
    file_type=form_var.get('file_type')
    try:
        transfer = [] # 全部数据, 数据变量
        transferData = []  # 已选中数据，绑定变量

        # print(effect_row)
        if not file_type:
            public.respcode, public.respmsg = "310310", "请先选择文件类型!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        if select_key == 'byorg':
            sql = "select org_id, org_name from sys_org where org_state='1' "
        else:
            sql = "SELECT user_id, user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows=cur.fetchall()
        for item in rows:
            transfer.append( { "key": item[0],  "label": str(item[0])+'-'+item[1], "disabled": False} )

        #此文件类型已拥有的权限
        sql = "select read_cfginfo from yw_workflow_document_manage_cfg where file_type=%s"
        cur.execute(sql, file_type )
        row=cur.fetchone()
        if row:
            for subitem in eval(row[0]):
                transferData.append( subitem )
        cur.close()

        form_var['read_cfginfo_options'] = transfer
        form_var['read_cfginfo'] = transferData
    except Exception as ex:
        log.error("生成穿梭框数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "303010", "生成穿梭框数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return '' ''

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#穿梭框-文件档案管理用户列表, 下拉选择后直接调用的交易
def transfer_docment_writemanage1_usercfg( request ):
    log = public.logger
    body = public.req_body
    select_key = body.get('select_key')
    form_var = body.get('form_var')
    file_type=form_var.get('file_type')
    try:
        transfer = [] # 全部数据, 数据变量
        transferData = []  # 已选中数据，绑定变量

        # print(effect_row)
        if not file_type:
            public.respcode, public.respmsg = "310310", "请先选择文件类型!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        if select_key == 'byorg':
            sql = "select org_id, org_name from sys_org where org_state='1' "
        else:
            sql = "SELECT user_id, user_name FROM sys_user  WHERE state='1'"
        cur.execute(sql)
        rows=cur.fetchall()
        for item in rows:
            transfer.append( { "key": item[0],  "label": str(item[0])+'-'+item[1], "disabled": False} )

        #此文件类型已拥有的权限
        sql = "select write_cfginfo from yw_workflow_document_manage_cfg where file_type=%s"
        cur.execute(sql, file_type )
        row = cur.fetchone()
        if row:
            for subitem in eval(row[0]):
                transferData.append(subitem)
        cur.close()

        form_var['write_cfginfo_options'] = transfer
        form_var['write_cfginfo'] = transferData
    except Exception as ex:
        log.error("生成穿梭框数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "303010", "生成穿梭框数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return '' ''

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 穿梭框-考勤组管理，考勤组列表, 下拉选择后直接调用的交易
def transfer_attend_manage_groupcfg( request ):
    log = public.logger
    body = public.req_body
    select_key = body.get('select_key')
    form_var = body.get('form_var')
    group_list = form_var.get('group_list')
    try:
        transfer = []       # 全部数据, 数据变量
        transfer_data = []   # 已选中数据，绑定变量

        if not group_list:
            public.respcode, public.respmsg = "310310", "请先选择考勤組!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        # sql = "SELECT user_id,user_name FROM sys_user  WHERE state='1'"
        sql = "SELECT job_num,name from yw_workflow_attend_mx GROUP BY job_num"
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            transfer.append({"key": item[0], "label": str(item[1]), "disabled": False})
        sql = "SELECT user_id from yw_workflow_attend_group_user where group_id = %s"
        log.info("group_list: [%s]" % group_list)
        cur.execute(sql, group_list)
        row = cur.fetchone()
        if row:
            for subitem in eval(row[0]):
                transfer_data.append( subitem )
        cur.close()

        form_var['userinfo_option'] = transfer
        form_var['userinfo'] = transfer_data
    except Exception as ex:
        log.error("生成穿梭框数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "303010", "生成穿梭框数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return '' ''

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 穿梭框-考勤排班管理，考勤组列表, 下拉选择后直接调用的交易
def transfer_attend_schedule_groupcfg( request ):
    log = public.logger
    body = public.req_body
    select_key = body.get('select_key')
    form_var = body.get('form_var')
    month_id = form_var.get('month_id')
    group_list = form_var.get('group_list')
    try:
        transfer = []       # 全部数据, 数据变量
        transfer_data = []   # 已选中数据，绑定变量
        work_time, closing_time = '', ''
        if not month_id:
            public.respcode, public.respmsg = "310310", "请先选择考勤月份!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 返回$month_id当月所有天数
        date_list = pubfunc.get_month_day_list(month_id)
        for item in date_list:
            transfer.append({"key": item[0], "label": str(item[1])+' 【'+item[2]+'】', "disabled": False})
        form_var['day_list_option'] = transfer
        # 查询对应月份与考勤组的工作日
        cur = connection.cursor()  # 创建游标
        sql = "SELECT work_day,work_time,closing_time,am_closing_time,pm_start_time from yw_workflow_attend_group_cfg"\
              " where group_id = %s and month_id = %s"
        cur.execute(sql, (group_list, month_id))
        row = cur.fetchone()
        log.info(str(row))
        if row:
            for subitem in eval(row[0]):
                    transfer_data.append(subitem)
            work_time = row[1]
            closing_time = row[2]
            am_closing = row[3]
            pm_start = row[4]
            form_var['day_list'] = transfer_data
            form_var['work_time'] = work_time
            form_var['closing_time'] = closing_time
            form_var['am_closing'] = am_closing
            form_var['pm_start'] = pm_start
            # log.info(str(transfer_data))
        else:
            form_var['day_list'] = transfer_data
    except Exception as ex:
        log.error("生成穿梭框数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "303010", "生成穿梭框数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return '' ''

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo