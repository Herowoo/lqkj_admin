import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
from admin_app.sys import public_db
import os

###########################################################################################################
#维修信息录入、维修记录录入
#add by zhangji, 2020.06.10
#
###########################################################################################################

# 各种维修信息操作
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

# 维修信息查询录入
def repair_info_insert( request ):
    log = public.logger
    body = public.req_body
    form_id = body.get('form_id', '')
    form_var = body.get('form_var')
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        id = None
        new_snid = form_var.get('new_snid',None)
        form_var['new_snid'] = None
        if not new_snid:
            id = form_var.get("id",None)

        if (not new_snid) and (not id):
            public.respcode, public.respmsg = "340101", "录入SN码不能为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        repair_list = ['id','tran_date','snid','fail_process','prod_date','prod_line',
                       'Platform_Num','Batch_Num','Plan_Num','pro_test_result','pro_test_value',
                       'meter_test_result','meter_test_value','Hw_Version','Fw_Version',
                       'model_id','gw_id','Vendor_id','fault_description','repair_description',
                       'gconfirm_people','gconfirm_date','repair_people','repaired_date','status']
        # 将form_var 所有数据初始化
        for item in repair_list:
            form_var[item] = None

        cur = connection.cursor()  # 创建游标
        # 维修信息表查询SQL
        repair_idsql = "select * from yw_project_repair_info where id = %s"
        repair_snsql = "select * from yw_project_repair_info where snid = %s"
        # 抄表信息表查询SQL
        meter_sql = "select insert_date,prod_line,Platform_Num,Batch_Num,Test_Result,Test_Value," \
                    "Hw_Version,Fw_Version,Module_ID,Chip_mmid,Vendor_id from " \
                    "yw_project_meterread_test_info where Board_SN = %s AND Test_Result!='Pass' "
        # 产测信息表查询SQL
        protest_sql = "select insert_date,prod_line,Platform_Num,Batch_Num,Test_Result,Test_Value," \
                      "Hw_Version,Fw_Version,Chip_mmid,Vendor_id from yw_project_product_test_info " \
                      "where Board_SN = %s AND Test_Result!='Pass' "
        # 生产项目信息表
        proinfo_sql = "select distinct plan_id  from yw_project_plan_info where order_id= %s"

        if id: # 有id历史数据查询并回显
            cur.execute(repair_idsql,id)
            row = cur.fetchone()
            if row:
                for index,item in enumerate(repair_list):
                    form_var[item] = row[index]
        else: # 无id时操作
            # 首先查询维修数据表中有无记录
            cur.execute(repair_snsql,new_snid)
            row = cur.fetchone()
            if row:
                for index, item in enumerate(repair_list):
                    form_var[item] = row[index]
            else:
                #  查询抄表信息表中是否存在对应 SN 码 不通过信息
                cur.execute(meter_sql,new_snid)
                meter_row = cur.fetchone()
                log.info('meter_row=',meter_row)
                if meter_row:
                    plan_num = None
                    cur.execute(proinfo_sql,(meter_row[3]))
                    plan_row = cur.fetchone()
                    if plan_row:
                        plan_num = plan_row[0]
                    else:
                        public.respcode, public.respmsg = "340103", "未找到对应计划单号!"
                        public.respinfo = HttpResponse(public.setrespinfo())

                    repair_tuple = (None,nowTime,new_snid,'抄表',meter_row[0],meter_row[1],
                                    meter_row[2],meter_row[3],plan_num,'','',meter_row[4],
                                    meter_row[5],meter_row[6],meter_row[7],meter_row[8],
                                    meter_row[9],meter_row[10],None,None,None,'0')
                else:
                    cur.execute(protest_sql, new_snid)
                    protest_row = cur.fetchone()
                    log.info('protest_row=', protest_row)
                    if protest_row:
                        plan_num = None
                        cur.execute(proinfo_sql, (protest_row[3]))
                        plan_row = cur.fetchone()
                        if plan_row:
                            plan_num = plan_row[0]
                        else:
                            public.respcode, public.respmsg = "340103", "未找到对应计划单号!"
                            public.respinfo = HttpResponse(public.setrespinfo())

                        repair_tuple = (None, nowTime, new_snid, '产测', protest_row[0], protest_row[1],
                                        protest_row[2], protest_row[3], plan_num,  protest_row[4],
                                        protest_row[5],'', '', protest_row[6], protest_row[7],None,
                                        protest_row[8],protest_row[9], None, None, None, '0')
                    else:
                        public.respcode, public.respmsg = "340102", "生产数据不存在故障记录信息!"
                        public.respinfo = HttpResponse(public.setrespinfo())
                        return public.respinfo

                sql_str1,sql_str2 = '',''
                for item in repair_list:
                    sql_str1 = sql_str1 + item + ','
                    sql_str2 = sql_str2 + '%s'+ ','
                insert_sql = "INSERT INTO yw_project_repair_info(" + sql_str1[0:-1] + ") VALUES(" + sql_str2[0:-1] + ") "
                cur.execute(insert_sql,repair_tuple)
                id = cur.lastrowid

                for index, item in enumerate(repair_list):
                    form_var[item] = repair_tuple[index]
                form_var['id'] = id

        cur.close()

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_var":form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 维修信息查询
def repair_info_select( request ):
    log = public.logger
    body = public.req_body
    form_id = body.get('form_id', '')
    form_var = body.get('form_var')
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        id = None
        new_snid = form_var.get('new_snid',None)
        form_var['new_snid'] = None
        if not new_snid:
            id = form_var.get("id",None)

        if (not new_snid) and (not id):
            public.respcode, public.respmsg = "340101", "录入SN码不能为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        repair_list = ['id','tran_date','snid','fail_process','prod_date','prod_line',
                       'Platform_Num','Batch_Num','Plan_Num','pro_test_result','pro_test_value',
                       'meter_test_result','meter_test_value','Hw_Version','Fw_Version',
                       'model_id','gw_id','Vendor_id','fault_description','repair_description',
                       'gconfirm_people','gconfirm_date','repair_people','repaired_date','status']

        cur = connection.cursor()  # 创建游标
        # 维修信息表查询SQL
        repair_idsql = "select * from yw_project_repair_info where id = %s"
        repair_snsql = "select * from yw_project_repair_info where snid = %s AND " + form_var['where']
         # and " + form_var['where']
        log.info('repair_snsql=',repair_snsql)
        # 将form_var 所有数据初始化
        for item in repair_list:
            form_var[item] = None

        if id: # 有id历史数据查询并回显
            cur.execute(repair_idsql,id)
            row = cur.fetchone()
            if row:
                for index,item in enumerate(repair_list):
                    form_var[item] = row[index]
        else: # 无id时操作
            # 首先查询维修数据表中有无记录
            cur.execute(repair_snsql,new_snid)
            row = cur.fetchone()
            if row:
                for index, item in enumerate(repair_list):
                    form_var[item] = row[index]
            else:
                public.respcode, public.respmsg = "340105", "未找到相关待维修记录!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        cur.close()

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_var":form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 维修完成信息录入-工程确认
def repair_info_confirm( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = head.get('uid', None)
    form_id = body.get('form_id', '')
    form_var = body.get('form_var')
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        id = form_var.get("id",None)

        if not id:
            public.respcode, public.respmsg = "340105", "ID不能为空,请先进行维修记录查询!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        repair_list = ['id', 'tran_date', 'snid', 'fail_process', 'prod_date', 'prod_line',
                       'Platform_Num', 'Batch_Num', 'Plan_Num', 'pro_test_result', 'pro_test_value',
                       'meter_test_result', 'meter_test_value', 'Hw_Version', 'Fw_Version',
                       'model_id', 'gw_id', 'Vendor_id', 'fault_description', 'repair_description',
                       'gconfirm_people', 'gconfirm_date', 'repair_people', 'repaired_date', 'status']

        cur = connection.cursor()  # 创建游标
        # 维修信息表查询SQL
        repair_idsql = "select * from yw_project_repair_info where id = %s"
        upd_sql = "UPDATE yw_project_repair_info set fault_description=%s, repair_description=%s,gconfirm_people=%s, gconfirm_date=%s, status=%s WHERE id=%s"

        if id: # 有id历史数据查询并回显
            # 更新维修信息
            tuple = (form_var['fault_description'], form_var['repair_description'], user_id,nowTime, form_var['status'], form_var['id'])
            cur.execute(upd_sql, tuple)
            # 更新SN码最终状态信息表
            if form_var['status'] in ('1','3'):
                upd_snid_final_status(form_var['snid'])

            # 查询数据库记录并回显
            cur.execute(repair_idsql,id)
            row = cur.fetchone()
            if row:
                for index,item in enumerate(repair_list):
                    form_var[item] = row[index]
        else: # 无id时操作
            public.respcode, public.respmsg = "340105", "ID不能为空,请先录入维修记录!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur.close()

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_var":form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 维修完成信息录入-维修录入
def repair_info_update( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = head.get('uid', None)
    form_id = body.get('form_id', '')
    form_var = body.get('form_var')
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        id = form_var.get("id",None)

        if not id:
            public.respcode, public.respmsg = "340105", "ID不能为空,请先进行维修记录查询!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        repair_list = ['id', 'tran_date', 'snid', 'fail_process', 'prod_date', 'prod_line',
                       'Platform_Num', 'Batch_Num', 'Plan_Num', 'pro_test_result', 'pro_test_value',
                       'meter_test_result', 'meter_test_value', 'Hw_Version', 'Fw_Version',
                       'model_id', 'gw_id', 'Vendor_id', 'fault_description', 'repair_description',
                       'gconfirm_people', 'gconfirm_date', 'repair_people', 'repaired_date', 'status']

        cur = connection.cursor()  # 创建游标
        # 维修信息表查询SQL
        repair_idsql = "select * from yw_project_repair_info where id = %s"
        upd_sql = "UPDATE yw_project_repair_info set fault_description=%s, repair_description=%s, repair_people=%s, repaired_date=%s, status=%s WHERE id=%s"

        if id: # 有id历史数据查询并回显
            # 更新维修信息
            tuple = (form_var['fault_description'], form_var['repair_description'], user_id, nowTime, form_var['status'], form_var['id'])
            cur.execute(upd_sql, tuple)
            # 更新SN码最终状态信息表
            if form_var['status'] in ('1', '3'):
                upd_snid_final_status(form_var['snid'])

            # 查询数据库记录并回显
            cur.execute(repair_idsql,id)
            row = cur.fetchone()
            if row:
                for index,item in enumerate(repair_list):
                    form_var[item] = row[index]
        else: # 无id时操作
            public.respcode, public.respmsg = "340105", "ID不能为空,请先录入维修记录!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur.close()

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_var":form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 更新SN 码最终状态信息表
def upd_snid_final_status(Board_SN):
    insert_snfial_sql = "INSERT INTO yw_project_snid_final_status(id, Board_SN, insert_date, prod_prcesses, " \
                        "fail_count, final_status) VALUES (%s, %s, %s, %s, %s, %s);"
    cur = connection.cursor()
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(insert_snfial_sql,(None,Board_SN,nowTime,'维修完成',0,'0'))
    cur.close()