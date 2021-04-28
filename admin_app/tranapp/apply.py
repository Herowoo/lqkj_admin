import sys
from django.shortcuts import render, redirect, HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
from admin_app.sys import public_db
import os
from admin_app.tranapp import pubfunc
from admin_app.sys import formcfg


###########################################################################################################
# 各种申请的特殊流程
# add by litz, 2020.06.03
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


# 用车申请，根据车辆类型获取车牌基本信息

def get_car_info(request):
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    form_var = body.get("form_var")
    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if not form_var:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select car_number,car_image,user_id,car_address from yw_workflow_apply_car_info where car_type=%s"
        cur.execute(sql, (body.get('select_key')))
        row = cur.fetchone()
        if row:
            body['form_var']['car_number'] = row[0]
            if row[1]:
                body['form_var']['car_image'] = eval(row[1])
            else:
                body['form_var']['car_image'] = []
            body['form_var']['car_curator'] = public_db.get_username(row[2])
            body['form_var']['start_address'] = row[3]
        else:
            body['form_var']['car_number'] = ''
            body['form_var']['car_image'] = []
            body['form_var']['car_curator'] = ''
            body['form_var']['start_address'] = ''
        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
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


# 用车申请-提交请求
def use_car_apply_commit(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        id = form_var.get('id')

        if not form_var.get('department'):
            public.respcode, public.respmsg = "333102", "申请部门不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('start_address'):
            public.respcode, public.respmsg = "333102", "取车地点不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('end_address'):
            public.respcode, public.respmsg = "333102", "还车地点不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('start_date'):
            public.respcode, public.respmsg = "333102", "预计取车时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('end_date'):
            public.respcode, public.respmsg = "333102", "预计还车时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('car_type'):
            public.respcode, public.respmsg = "333102", "车辆类型不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('car_number'):
            public.respcode, public.respmsg = "333102", "车牌号码不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('use_person'):
            public.respcode, public.respmsg = "333102", "使用人不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('car_mileage'):
            public.respcode, public.respmsg = "333102", "预计公里数不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('reason'):
            public.respcode, public.respmsg = "333102", "申请原因不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标

        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_car where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if row[0] not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if row[1] != public.user_id:
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

            sql = "update yw_workflow_apply_car set department=%s,start_address=%s,end_address=%s, start_date=%s, end_date=%s, " \
                  "car_type=%s, use_person=%s, car_person=%s,car_number=%s,car_mileage=%s,reason=%s,remark=%s, status='0' where id=%s "
            cur.execute(sql, (form_var.get('department'), form_var.get('start_address'), form_var.get('end_address'),
                              form_var.get('start_date'), form_var.get('end_date'), form_var.get('car_type'),
                              form_var.get('use_person'), form_var.get('car_person'), form_var.get('car_number'),
                              form_var.get('car_mileage'), form_var.get('reason'), form_var.get('remark'), id))

        else:  # 插入数据
            # order_number = public_db.Get_SeqNo('USE_CAR')
            order_number = form_var.get('use_car_apply_number')
            if order_number == '' or not order_number:
                order_number = public_db.Get_SeqNo('USE_CAR')
            body['form_var']['order_number'] = order_number

            sql = "insert into yw_workflow_apply_car(order_number,user_id,department,start_address,end_address," \
                  "start_date, end_date,car_type,use_person,car_person,car_number,car_mileage,reason,remark, status) " \
                  "values(%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,'0')"
            cur.execute(sql, (order_number, public.user_id, form_var.get('department'),
                              form_var.get('start_address'), form_var.get('end_address'), form_var.get('start_date'),
                              form_var.get('end_date'), form_var.get('car_type'), form_var.get('use_person'),
                              form_var.get('car_person'), form_var.get('car_number'), form_var.get('car_mileage'),
                              form_var.get('reason'), form_var.get('remark')))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]

        cur.close()

        submit_power = {"show": True, "disabled": True}  # 提交按钮置灰

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 用车申请-归还
def use_car_apply_return(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        id = form_var.get('id')

        if not id:
            public.respcode, public.respmsg = "333102", "用车申请数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        sql = "select status, apply_state from yw_workflow_apply_car where id=%s"
        cur.execute(sql, id)
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "333001", "原数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # if row[0] == '3' :
        #     public.respcode, public.respmsg = "333003", "车辆已归还!"
        #     public.respinfo = HttpResponse(public.setrespinfo())
        #     return public.respinfo
        if row[1] != '1':
            public.respcode, public.respmsg = "333004", "审批未通过!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sql = "update yw_workflow_apply_car set status=%s,act_returntime=%s,act_returnaddr=%s, act_mileage=%s, act_others=%s  where id=%s "
        cur.execute(sql, ('3', form_var.get('act_returntime'), form_var.get('act_returnaddr'),
                          form_var.get('act_mileage'), form_var.get('act_others'), id))

        cur.close()

        body['form_var']['status'] = '3'

        submit_power = {"show": True, "disabled": True}  # 提交按钮置灰

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 用车报表打印
def use_car_report(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:

        cur = connection.cursor()  # 创建游标
        sql = "select status, apply_state from yw_workflow_apply_car where id=%s"
        cur.execute(sql, id)
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "333001", "原数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # if row[0] == '3' :
        #     public.respcode, public.respmsg = "333003", "车辆已归还!"
        #     public.respinfo = HttpResponse(public.setrespinfo())
        #     return public.respinfo
        if row[1] != '1':
            public.respcode, public.respmsg = "333004", "审批未通过!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sql = "update yw_workflow_apply_car set status=%s,act_returntime=%s,act_returnaddr=%s, act_mileage=%s, act_others=%s  where id=%s "
        cur.execute(sql, ('3', form_var.get('act_returntime'), form_var.get('act_returnaddr'),
                          form_var.get('act_mileage'), form_var.get('act_others'), id))

        cur.close()

        body['form_var']['status'] = '3'

        submit_power = {"show": True, "disabled": True}  # 提交按钮置灰

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 用章申请-提交请求
def use_seal_apply_commit(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        id = form_var.get('id')

        if not form_var.get('department'):
            public.respcode, public.respmsg = "335102", "申请部门不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('use_addr'):
            public.respcode, public.respmsg = "335102", "使用地点不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('start_date'):
            public.respcode, public.respmsg = "335102", "预计开始时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('end_date'):
            public.respcode, public.respmsg = "335102", "预计归还时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('seal_type'):
            public.respcode, public.respmsg = "335102", "印章类型不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('use_person'):
            public.respcode, public.respmsg = "335102", "使用人不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('use_reason'):
            public.respcode, public.respmsg = "335102", "使用事由不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标

        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_seal where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "335001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if row[0] not in ['0', '2']:
                public.respcode, public.respmsg = "335002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if row[1] != public.user_id:
                public.respcode, public.respmsg = "335004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

            sql = "update yw_workflow_apply_seal set department=%s,file_name=%s,file_num=%s, start_date=%s, " \
                  "end_date=%s, " \
                  "seal_type=%s, " \
                  "use_person=%s, " \
                  "use_addr=%s," \
                  "use_reason=%s," \
                  "remark=%s," \
                  "status='0' " \
                  "where id=%s "
            cur.execute(sql, (form_var.get('department'), form_var.get('file_name'), form_var.get('file_num'),
                              form_var.get('start_date'), form_var.get('end_date'), form_var.get('seal_type'),
                              form_var.get('use_person'), form_var.get('use_addr'),
                              form_var.get('use_reason'), form_var.get('remark'), id))

        else:  # 插入数据

            order_number = public_db.Get_SeqNo('USE_SEAL')
            body['form_var']['order_number'] = order_number

            sql = "insert into yw_workflow_apply_seal(order_number,user_id,department,use_reason,file_name," \
                  "file_num,start_date, end_date,seal_type,use_person,use_addr,remark,status) " \
                  "values(%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,'0' )"
            cur.execute(sql, (form_var.get('order_number'), public.user_id, form_var.get('department'),
                              form_var.get('use_reason'), form_var.get('file_name'), form_var.get('file_num'),
                              form_var.get('start_date'), form_var.get('end_date'), form_var.get('seal_type'),
                              form_var.get('use_person'), form_var.get('use_addr'), form_var.get('remark')))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]

        cur.close()

        submit_power = {"show": True, "disabled": True}  # 提交按钮置灰

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 用章申请-归还
def use_seal_apply_return(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        id = form_var.get('id')

        if not id:
            public.respcode, public.respmsg = "335102", "用章申请数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        sql = "select status, apply_state from yw_workflow_apply_seal where id=%s"
        cur.execute(sql, id)
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "335001", "原数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if row[0] == '3':
            public.respcode, public.respmsg = "335003", "印章已归还!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if row[1] != '3':
            public.respcode, public.respmsg = "335004", "审批未通过!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sql = "update yw_workflow_apply_seal set status=%s,act_returntime=%s,act_returnaddr=%s, act_others=%s  where id=%s "
        cur.execute(sql, ('3', form_var.get('act_returntime'), form_var.get('act_returnaddr'),
                          form_var.get('act_others'), id))

        cur.close()

        body['form_var']['status'] = '3'

        submit_power = {"show": True, "disabled": True}  # 提交按钮置灰

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# # TODO: def travel_apply_commit():
# # handle travel apply task, 
# # need build database table first.

# 出差申请 - 提出申请
def travel_apply_commit(request):
    # input: request with travel_apply_commit json.
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        id = form_var.get('id')

        if not form_var.get('department'):
            public.respcode, public.respmsg = "333102", "申请部门不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('start_date'):
            public.respcode, public.respmsg = "333102", "计划出差时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('end_date'):
            public.respcode, public.respmsg = "333102", "出差结束时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('reason'):
            public.respcode, public.respmsg = "333102", "出差事由不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标

        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_travel where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

            sql = ("update yw_workflow_apply_travel set "
                   "department=%s,"
                   "start_address=%s, "
                   "end_address=%s, "
                   "start_date=%s, "
                   "end_date=%s, "
                   "days=%s, "
                   "actual_start_date=%s, "
                   "actual_end_date=%s, "
                   "reason=%s, "
                   "remark=%s, "
                   "status='0' where id=%s ")
            cur.execute(sql, (form_var.get('department'),
                              form_var.get('start_address'),
                              form_var.get('end_address'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              int(form_var.get('days')),
                              form_var.get('actual_start_date'),
                              form_var.get('actual_end_date'),
                              form_var.get('reason'),
                              form_var.get('remark'),
                              id))

        else:  # 插入数据
            order_number = public_db.Get_SeqNo('TRAVEL_APPLY')
            body['form_var']['order_number'] = order_number

            sql = ("insert into yw_workflow_apply_travel("
                   "order_number,"
                   "user_id,"
                   "user_name,"
                   "department,"
                   "start_address,"
                   "end_address,"
                   "tool, "
                   "start_date, "
                   "end_date,"
                   "days, "
                   "reason, "
                   "remark, "
                   "status ) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'0')")
            cur.execute(sql, (form_var.get('order_number'),
                              public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              form_var.get('start_address'),
                              form_var.get('end_address'),
                              form_var.get('tool'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              int(form_var.get('days')),
                              form_var.get('reason'),
                              form_var.get('remark')))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
    #     cur.close()
    #     submit_power = {"show": True, "disabled": True} #提交按钮置灰
    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300025", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 出差完成
def travel_finish_commit(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        id = form_var.get('id')

        if not id:
            public.respcode, public.respmsg = "333102", "出差申请数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        sql = "select status, apply_state from yw_workflow_apply_travel where id=%s"
        cur.execute(sql, id)
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "333001", "原数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # if row[0] == '3' :
        #     public.respcode, public.respmsg = "333003", "已完成"
        #     public.respinfo = HttpResponse(public.setrespinfo())
        #     return public.respinfo
        if row[1] != '1':
            public.respcode, public.respmsg = "333004", "审批未通过!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sql = ("update yw_workflow_apply_travel set "
               "status=%s, "
               "actual_start_date=%s, "
               "actual_end_date=%s, "
               "remark=%s  where id=%s ")
        cur.execute(sql, ('3',
                          form_var.get('actual_start_date'),
                          form_var.get('act_end_date'),
                          form_var.get('remark'), id))
        cur.close()
        body['form_var']['status'] = '3'
        submit_power = {"show": True, "disabled": True}  # 提交按钮置灰

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 出差申请 - 明细报表
def travel_report(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        cur = connection.cursor()  # 创建游标
        sql = "select status, apply_state from yw_workflow_apply_travel where id=%s"
        cur.execute(sql, id)
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "333001", "原数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if row[1] != '1':
            public.respcode, public.respmsg = "333004", "审批未通过!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        sql = "update yw_workflow_apply_car set status=%s,act_returntime=%s,act_returnaddr=%s, act_mileage=%s, act_others=%s  where id=%s "
        cur.execute(sql, ('3', form_var.get('act_returntime'), form_var.get('act_returnaddr'),
                          form_var.get('act_mileage'), form_var.get('act_others'), id))
        cur.close()
        body['form_var']['status'] = '3'
        submit_power = {"show": True, "disabled": True}  # 提交按钮置灰
    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 请假申请 - 提交申请单
def absence_apply_commit(request):
    # input: request with absence_apply_commit json.
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        id = form_var.get('id')
        start_date = form_var.get('start_date')
        end_date = form_var.get('end_date')
        if not form_var.get('department'):
            public.respcode, public.respmsg = "333102", "申请部门不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not start_date:
            public.respcode, public.respmsg = "333104", "请假开始时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not end_date:
            public.respcode, public.respmsg = "333105", "请假结束时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not start_date < end_date:
            public.respcode, public.respmsg = "333109", "请假结束时间要晚于开始时间!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('category'):
            public.respcode, public.respmsg = "333106", "请假类型不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if str(form_var.get('category')) == '1' and not form_var.get('reason'):
            public.respcode, public.respmsg = "333112", "事假必填请假事由!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('agent_name'):
            public.respcode, public.respmsg = "333107", "工作代理人不可为空"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # if not form_var.get('reason'):
        #     public.respcode, public.respmsg = "333108", "请假事由不可为空!"
        #     public.respinfo = HttpResponse(public.setrespinfo())
        #     return public.respinfo
        days_input = form_var.get("days")
        days_input_int = 0
        # default_value
        try:
            if days_input:
                s_days = simple_days(start_date, end_date)
                days_input_int = int(days_input)
                if s_days is not None and days_input_int > s_days + 1:
                    public.respcode, public.respmsg = "333109", "请输入正确的天数或留空"
                    public.respinfo = HttpResponse(public.setrespinfo())
                    return public.respinfo
        except ValueError:
            public.respcode, public.respmsg = "333110", "请输入正确格式的天数，或留空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 周六是否算上班，以及节假日，精确应该通过同步数据库放假安排数据确定，现程序计算不计算周六，开放用户输入校正
        # days, seconds = onwork_days_seconds(start_date, end_date)
        # hours = upint(seconds / (60 * 60))
        # if days_input_int:
        #     days = days_input_int
        seconds = absence_all(start_date, end_date)
        hours = format((seconds / (60 * 60)), '.1f')
        hours = float(hours)
        days = int(hours / 8)
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_absence where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

            sql = ("update yw_workflow_apply_absence set "
                   "department=%s,"
                   "start_date=%s, "
                   "end_date=%s, "
                   "agent_name=%s, "
                   "days=%s, "
                   "hours=%s, "
                   "category=%s, "
                   "reason=%s, "
                   "remark=%s, "
                   "status='0' "
                   "where id=%s ")
            cur.execute(sql, (form_var.get('department'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              form_var.get('agent_name'),
                              days,
                              hours,
                              form_var.get('category'),
                              form_var.get('reason'),
                              form_var.get('remark'),
                              id))
            body['form_var']['days'] = str(days)
            body['form_var']['hours'] = str(hours)
        else:  # 插入数据
            order_number = public_db.Get_SeqNo('ABSENCE_APPLY')
            body['form_var']['order_number'] = order_number

            sql = ("insert into yw_workflow_apply_absence("
                   "order_number,"
                   "user_id,"
                   "department,"
                   "user_name,"
                   "agent_name, "
                   "category, "
                   "reason, "
                   "start_date, "
                   "end_date,"
                   "days, "
                   "hours, "
                   "remark "
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (form_var.get('order_number'),
                              public.user_id,
                              form_var.get('department'),
                              form_var.get('user_name'),
                              form_var.get('agent_name'),
                              form_var.get('category'),
                              form_var.get('reason'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              days,
                              hours,
                              form_var.get('remark')))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
                body['form_var']['days'] = str(days)
                body['form_var']['hours'] = str(hours)
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % (sql))
            #     cur.close()
            form_var['submit_power'] = {"show": True, "disabled": True}  # 提交按钮置灰
    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        try:
            cur.close()
        except:
            pass
        public.respcode, public.respmsg = "300025", "生成数据失败!" + str(repr(ex))
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    #
    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def simple_days(start_s, end_s):
    t1 = datetime.datetime.strptime(start_s, "%Y-%m-%d %H:%M:%S")
    t2 = datetime.datetime.strptime(end_s, "%Y-%m-%d %H:%M:%S")
    if t1 < t2:
        dt = t2 - t1
        return dt.days
    else:
        return None


def onwork_days_seconds(start_s, end_s, overtime=False):
    """
    input start time, end time, as standard time str.
    
    """
    fmt_str = "%Y-%m-%d %H:%M:%S"
    t1 = datetime.datetime.strptime(start_s, fmt_str)
    t2 = datetime.datetime.strptime(end_s, fmt_str)
    if t1 < t2:
        dt = t2 - t1
    else:
        dt = t1 - t2
    am_start = datetime.datetime.strptime("%s %s" % (end_s[:10], "08:30:00"), fmt_str)
    am_end = datetime.datetime.strptime("%s %s" % (end_s[:10], "11:30:00"), fmt_str)
    pm_start = datetime.datetime.strptime("%s %s" % (end_s[:10], "13:00:00"), fmt_str)
    pm_end = datetime.datetime.strptime("%s %s" % (end_s[:10], "18:00:00"), fmt_str)
    cnt_day = 0
    t_acc = t1
    flag = (t_acc.day < t2.day)
    while (flag):
        if not overtime and not (
                # t_acc.weekday() == 5 or
                t_acc.weekday() == 6
        ):
            # should read database about saturday.
            # saturday and sunday not counted.
            cnt_day += 1
        t_acc = t_acc + datetime.timedelta(days=1)
        flag = bool(t_acc.day < t2.day)
    # end while loop
    if overtime:
        seconds = dt.seconds
    if t2 < am_start:
        cnt_day -= 1
        t2 = pm_end
    if t_acc < am_start:
        t_acc = am_start
    if am_end < t_acc < pm_start:
        t_acc = am_end
    if pm_end < t2:
        t2 = pm_end
    if am_end < t2 < pm_start:
        t2 = pm_start
    # noon rest
    if not (t_acc <= t2):
        seconds = 0
    else:
        dt = t2 - t1
        if (t_acc <= am_start and pm_end <= t2):
            cnt_day += 1
            seconds = 0
        else:
            if (t_acc <= am_end and pm_start <= t2):
                seconds = dt.seconds - 5400
            else:
                seconds = dt.seconds
    return cnt_day, seconds


def upint(hour_float):
    hour_int = int(hour_float)
    hours = hour_int + 1 if (hour_int < hour_float) else hour_int
    return hours


# 精确时间到0.5小时
def aj_halfhour(flt):
    Balfour = int(flt)
    dec = flt - Balfour
    if 0.25 > dec >= 0:
        Balfour += 0.0
    elif 0.75 > dec >= 0.25:
        Balfour += 0.5
    else:
        Balfour += 1.0
    return Balfour


def absence_apply_finish(request):
    pass


def absence_apply_report(request):
    pass


def out_apply_commit(request):
    # input: request with out_apply_commit json.
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        id = form_var.get('id')
        start_date = form_var.get('start_date')
        end_date = form_var.get('end_date')
        if not form_var.get('department'):
            public.respcode, public.respmsg = "333102", "申请部门不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not start_date:
            public.respcode, public.respmsg = "333104", "外出开始时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not end_date:
            public.respcode, public.respmsg = "333105", "外出结束时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not (start_date < end_date):
            public.respcode, public.respmsg = "333109", "外出结束时间要晚于开始时间!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('address'):
            public.respcode, public.respmsg = "333107", "外出地点不可为空"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('reason'):
            public.respcode, public.respmsg = "333107", "外出事由不可为空"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        days, seconds = onwork_days_seconds(start_date, end_date)
        hours = upint(seconds / (60 * 60))
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_out where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_out set "
                   "department=%s,"
                   "start_date=%s, "
                   "end_date=%s, "
                   "hours=%s, "
                   "reason=%s, "
                   "remark=%s, "
                   "status='0' "
                   "where id=%s ")
            cur.execute(sql, (form_var.get('department'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              hours,
                              form_var.get('reason'),
                              form_var.get('remark'),
                              id))
            body['form_var']['hours'] = str(hours)
        else:  # 插入数据
            order_number = public_db.Get_SeqNo('OUT_APPLY')
            body['form_var']['order_number'] = order_number
            sql = ("insert into yw_workflow_apply_out("
                   "order_number,"
                   "user_id,"
                   "department,"
                   "user_name,"
                   "start_date, "
                   "end_date, "
                   "address, "
                   "reason, "
                   "remark, "
                   "hours "
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (form_var.get('order_number'),
                              public.user_id,
                              form_var.get('department'),
                              form_var.get('user_name'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              form_var.get('address'),
                              form_var.get('reason'),
                              form_var.get('remark'),
                              hours))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
                body['form_var']['hours'] = str(hours)
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % (sql))
    #     cur.close()
    #     submit_power = {"show": True, "disabled": True} #提交按钮置灰
    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        try:
            cur.close()
        except:
            pass
        public.respcode, public.respmsg = "300025", "生成数据失败!" + str(repr(ex))
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    #
    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def overtime_apply_commit(request):
    # input: request with overtime_apply_commit json.
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        id = form_var.get('id')
        start_date = form_var.get('start_date')
        end_date = form_var.get('end_date')
        if not form_var.get('department'):
            public.respcode, public.respmsg = "333102", "申请部门不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not start_date:
            public.respcode, public.respmsg = "333104", "加班开始时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not end_date:
            public.respcode, public.respmsg = "333105", "加班结束时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not (start_date < end_date):
            public.respcode, public.respmsg = "333109", "加班结束时间要晚于开始时间!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('reason'):
            public.respcode, public.respmsg = "333107", "加班事由不可为空"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        days = pubfunc.get_days(start_date, end_date)
        seconds = overtime_all(start_date, end_date)
        hours = aj_halfhour(seconds / (60 * 60))
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_overtime where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != public.user_id:
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_overtime set "
                   "department=%s,"
                   "start_date=%s, "
                   "end_date=%s, "
                   "days=%s, "
                   "hours=%s, "
                   "reason=%s, "
                   "status='0' "
                   "where id=%s ")
            cur.execute(sql, (form_var.get('department'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              days,
                              hours,
                              form_var.get('reason'),
                              form_var.get('remark'),
                              id))
            body['form_var']['hours'] = str(hours)
        else:  # 插入数据
            order_number = public_db.Get_SeqNo('OVERTIME_APPLY')
            body['form_var']['order_number'] = order_number
            sql = ("insert into yw_workflow_apply_overtime("
                   "order_number,"
                   "user_id,"
                   "department,"
                   "user_name,"
                   "start_date, "
                   "end_date, "
                   "reason, "
                   "days,"
                   "hours "
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (form_var.get('order_number'),
                              public.user_id,
                              form_var.get('department'),
                              form_var.get('user_name'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              form_var.get('reason'),
                              days,
                              hours))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
                body['form_var']['hours'] = str(hours)
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % (sql))
    #     cur.close()
    #     submit_power = {"show": True, "disabled": True} #提交按钮置灰
    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        try:
            cur.close()
        except:
            pass
        public.respcode, public.respmsg = "300025", "生成数据失败!" + str(repr(ex))
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    #
    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def hire_apply_commit(request):
    # input: request with overtime_apply_commit json.
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        id = form_var.get('id')
        start_date = form_var.get('start_date')
        end_date = form_var.get('end_date')
        if not form_var.get('department'):
            public.respcode, public.respmsg = "333102", "申请部门不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not start_date:
            public.respcode, public.respmsg = "333104", "加班开始时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not end_date:
            public.respcode, public.respmsg = "333105", "加班结束时间不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not (start_date < end_date):
            public.respcode, public.respmsg = "333109", "加班结束时间要晚于开始时间!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not form_var.get('reason'):
            public.respcode, public.respmsg = "333107", "加班事由不可为空"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        days, seconds = onwork_days_seconds(start_date, end_date)
        hours = upint(seconds / (60 * 60))
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_overtime where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != public.user_id:
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_overtime set "
                   "department=%s,"
                   "start_date=%s, "
                   "end_date=%s, "
                   "days=%s, "
                   "hours=%s, "
                   "reason=%s, "
                   "status='0' "
                   "where id=%s ")
            cur.execute(sql, (form_var.get('department'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              days,
                              hours,
                              form_var.get('reason'),
                              form_var.get('remark'),
                              id))
            body['form_var']['hours'] = str(hours)
        else:  # 插入数据
            order_number = public_db.Get_SeqNo('OVERTIME_APPLY')
            body['form_var']['order_number'] = order_number
            sql = ("insert into yw_workflow_apply_overtime("
                   "order_number,"
                   "user_id,"
                   "department,"
                   "user_name,"
                   "start_date, "
                   "end_date, "
                   "reason, "
                   "days,"
                   "hours "
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (form_var.get('order_number'),
                              public.user_id,
                              form_var.get('department'),
                              form_var.get('user_name'),
                              form_var.get('start_date'),
                              form_var.get('end_date'),
                              form_var.get('reason'),
                              days,
                              hours))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
                body['form_var']['hours'] = str(hours)
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % (sql))
    #     cur.close()
    #     submit_power = {"show": True, "disabled": True} #提交按钮置灰
    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        try:
            cur.close()
        except:
            pass
        public.respcode, public.respmsg = "300025", "生成数据失败!" + str(repr(ex))
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    #
    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def is_holiday(st):
    """是否节假日"""
    # cur = connection.cursor()
    # sql_getholiday = "SELECT fest_day from yw_stcs_holiday where fest_year in (%s, %s)"
    # sql_getnormalday = "SELECT normal_day from yw_stcs_holiday where fest_year in (%s, %s)"
    # cur.execute(sql_getholiday, datetime.datetime.now().year, datetime.datetime.now().year+1)
    # holiday = cur.fetchall()
    # cur.execute(sql_getnormalday, datetime.datetime.now().year, datetime.datetime.now().year + 1)
    # normalday = cur.fetchall()
    # cur.close()
    # if normalday.count(st) > 0:
    #     return 1
    # elif holiday.count(st) > 0:
    #     return 0
    # elif datetime.datetime.strptime(st, '%Y-%m-%d').isoweekday() == 7:
    #     return 0
    # elif datetime.datetime.strptime(st, '%Y-%m-%d').isocalendar()[1] % 2 == 0 and datetime.datetime.strptime(st, '%Y-%m-%d').isoweekday() == 6:
    #     return 0
    # else:
    if datetime.datetime.strptime(st, '%Y-%m-%d %H:%M:%S').isoweekday() == 7:
        return 0
    elif datetime.datetime.strptime(st, '%Y-%m-%d %H:%M:%S').isocalendar()[1] % 2 == 0 and datetime.datetime.strptime(
            st, '%Y-%m-%d %H:%M:%S').isoweekday() == 6:
        return 0
    else:
        return 1


# 返回所有加班时间（单位：秒）
def overtime_all(st, ed):
    seconds = 0
    if pubfunc.get_days(st, ed) > 0:
        list_date = pubfunc.get_datelist(st[:10], ed[:10])
        i = 0
        while i < len(list_date) - 1:
            seconds += overtime_oneday(list_date[i], list_date[i][:10] + ' 23:59:59')
            i += 1
        lastday = list_date[len(list_date) - 1]
        # 追加第一天加班时间
        seconds += overtime_oneday(st, st[:10] + ' 23:59:59')
        # 追加最后一天加班时间
        seconds += overtime_oneday(lastday, ed)
    else:
        seconds = overtime_oneday(st, ed)
    return seconds


# 返回当天加班时间（单位：秒）
def overtime_oneday(st, ed):
    fmt_str = "%Y-%m-%d %H:%M:%S"
    dt_st = datetime.datetime.strptime(st, fmt_str)
    dt_ed = datetime.datetime.strptime(ed, fmt_str)
    if is_holiday(st) == 1:
        work = set([datetime.datetime.strptime("%s %s" % (st[:10], "08:30:00"), fmt_str),
                    datetime.datetime.strptime("%s %s" % (st[:10], "18:00:00"), fmt_str)])
    else:
        work = set([datetime.datetime.strptime("%s %s" % (st[:10], "11:30:00"), fmt_str),
                    datetime.datetime.strptime("%s %s" % (st[:10], "13:00:00"), fmt_str)])
    if dt_ed < dt_st:
        return 0
    else:
        return pubfunc.set_dif([dt_st, dt_ed], work).seconds


# 返回所有加班时间（单位：秒）
def absence_all(st, ed):
    seconds = 0
    if pubfunc.get_days(st, ed) > 0:
        list_date = pubfunc.get_datelist(st[:10], ed[:10])
        i = 0
        while i < len(list_date) - 1:
            seconds += absence_oneday(list_date[i], list_date[i][:10] + ' 23:59:59')
            i += 1
        lastday = list_date[len(list_date) - 1]
        # 追加第一天加班时间
        seconds += absence_oneday(st, st[:10] + ' 23:59:59')
        # 追加最后一天加班时间
        seconds += absence_oneday(lastday, ed)
    else:
        seconds = absence_oneday(st, ed)
    return seconds


# 返回当天加班时间（单位：秒）
def absence_oneday(st, ed):
    fmt_str = "%Y-%m-%d %H:%M:%S"
    dt_st = datetime.datetime.strptime(st, fmt_str)
    dt_ed = datetime.datetime.strptime(ed, fmt_str)
    if is_holiday(st):
        work_am = {datetime.datetime.strptime("%s %s" % (st[:10], "08:30:00"), fmt_str),
                   datetime.datetime.strptime("%s %s" % (st[:10], "11:30:00"), fmt_str)}
        work_pm = {datetime.datetime.strptime("%s %s" % (st[:10], "13:00:00"), fmt_str),
                   datetime.datetime.strptime("%s %s" % (st[:10], "18:00:00"), fmt_str)}
    else:
        work_am = {datetime.datetime.strptime("%s %s" % (st[:10], "00:00:00"), fmt_str),
                   datetime.datetime.strptime("%s %s" % (st[:10], "00:00:00"), fmt_str)}
        work_pm = {datetime.datetime.strptime("%s %s" % (st[:10], "00:00:00"), fmt_str),
                   datetime.datetime.strptime("%s %s" % (st[:10], "00:00:00"), fmt_str)}
    if dt_ed < dt_st:
        return 0
    else:
        return pubfunc.set_inter([dt_st, dt_ed], work_am).seconds + pubfunc.set_inter([dt_st, dt_ed], work_pm).seconds


def recru_finish_commit(request):
    """招聘申请提交"""
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    form_var = body.get("form_var")
    id = form_var.get("id")
    tran_date = form_var.get("tran_date")
    expect_date = form_var.get("expect_date")
    if tran_date > expect_date:
        public.respcode, public.respmsg = "333103", "期望到岗时间不能早于申请时间!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if not form_var:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('department'):
        public.respcode, public.respmsg = "333102", "申请部门不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('recru_position'):
        public.respcode, public.respmsg = "333102", "招聘职位不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('recru_number'):
        public.respcode, public.respmsg = "333102", "招聘人数不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    try:
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_recruiment where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_recruiment set "
                   "user_name=%s,"
                   "department=%s, "
                   "recru_position=%s, "
                   "recru_number=%s, "
                   "req_degree=%s, "
                   "req_age=%s, "
                   "req_gender=%s,"
                   "req_exp=%s,"
                   "recru_requre=%s,"
                   "reason=%s,"
                   "tran_date=%s,"
                   "expect_date=%s,"
                   "status='0' "
                   "where id=%s ")
            cur.execute(sql, (form_var.get('user_name'),
                              form_var.get('department'),
                              form_var.get('recru_position'),
                              form_var.get('recru_number'),
                              form_var.get('req_degree'),
                              form_var.get('req_age'),
                              form_var.get('req_gender'),
                              form_var.get('req_exp'),
                              form_var.get('recru_requre'),
                              form_var.get('reason'),
                              form_var.get('tran_date'),
                              form_var.get('expect_date'),
                              id))
        else:  # 插入数据
            order_number = form_var.get('recru_apply_number')
            if order_number == '' or not order_number:
                order_number = public_db.Get_SeqNo('RECRU_APPLY')
            sql = ("insert into yw_workflow_recruiment("
                   "user_id,"
                   "user_name,"
                   "department,"
                   "recru_position,"
                   "recru_number,"
                   "req_degree, "
                   "req_age, "
                   "req_gender, "
                   "req_exp, "
                   "recru_requre, "
                   "reason,"
                   "tran_date,"
                   "expect_date "
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              form_var.get('recru_position'),
                              form_var.get('recru_number'),
                              form_var.get('req_degree'),
                              form_var.get('req_age'),
                              form_var.get('req_gender'),
                              form_var.get('req_exp'),
                              form_var.get('recru_requre'),
                              form_var.get('reason'),
                              tran_date,
                              expect_date))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % (sql))

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
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


def stay_apply_commit(request):
    """协议酒店入住申请"""
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    form_var = body.get("form_var")
    id = form_var.get("id")
    tran_date = form_var.get("tran_date")
    check_in_time = form_var.get('start_time')
    check_out_time = form_var.get('end_time')
    real_in_time = form_var.get('real_in_time')
    real_out_time = form_var.get('real_out_time')
    if real_in_time == '':
        real_in_time = None
    if real_out_time == '':
        real_out_time = None
    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if not form_var:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not check_in_time:
        public.respcode, public.respmsg = "110222", "计划入住时间不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not check_out_time:
        public.respcode, public.respmsg = "110222", "计划退房时间不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if check_out_time < check_in_time:
        public.respcode, public.respmsg = "333103", "退房时间不能早于入住时间!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('department'):
        public.respcode, public.respmsg = "333102", "申请部门不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('hotel_id'):
        public.respcode, public.respmsg = "333102", "协议酒店不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('vistor_number'):
        public.respcode, public.respmsg = "333102", "入住人数不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('aff_unit'):
        public.respcode, public.respmsg = "333102", "所属单位不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('reason'):
        public.respcode, public.respmsg = "333102", "入住事由不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_hotel where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_hotel set "
                   "user_id=%s,"
                   "user_name=%s,"
                   "department=%s, "
                   "hotel_id=%s, "
                   "vistor_number=%s, "
                   "aff_unit=%s, "
                   "entra_type=%s, "
                   "reason=%s,"
                   "check_in_time=%s,"
                   "check_out_time=%s,"
                   "real_in_time=%s,"
                   "real_out_time=%s,"
                   "remark=%s,"
                   "tran_date=%s "
                   "where id=%s ")
            cur.execute(sql, (public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              form_var.get('hotel_id'),
                              form_var.get('vistor_number'),
                              form_var.get('visitor_unit'),
                              form_var.get('entra_type'),
                              form_var.get('reason'),
                              check_in_time,
                              check_out_time,
                              real_in_time,
                              real_out_time,
                              form_var.get('remark'),
                              form_var.get('tran_date'),
                              id))
        else:  # 插入数据
            order_number = form_var.get('hotel_apply_number')
            if order_number == '' or not order_number:
                order_number = public_db.Get_SeqNo('HOTEL_APPLY')
            sql = ("insert into yw_workflow_apply_hotel("
                   "order_number,"
                   "user_name,"
                   "department, "
                   "hotel_id, "
                   "vistor_number, "
                   "aff_unit, "
                   "entra_type, "
                   "reason,"
                   "check_in_time,"
                   "check_out_time,"
                   "real_in_time,"
                   "real_out_time,"
                   "remark,"
                   "tran_date"
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (order_number,
                              public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              form_var.get('hotel_id'),
                              form_var.get('vistor_number'),
                              form_var.get('visitor_unit'),
                              form_var.get('entra_type'),
                              form_var.get('reason'),
                              check_in_time,
                              check_out_time,
                              real_in_time,
                              real_out_time,
                              form_var.get('remark'),
                              form_var.get('tran_date')))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % sql)

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
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


def purchase_apply_commit(request):
    """采购申请"""
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    form_var = body.get("form_var")
    id = form_var.get("id")
    tran_date = form_var.get("tran_date")
    expact_time = form_var.get('expact_time')
    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if not form_var:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('department'):
        public.respcode, public.respmsg = "333102", "申请部门不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('item_number'):
        public.respcode, public.respmsg = "333102", "物品数量不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('use_for'):
        public.respcode, public.respmsg = "333102", "用途不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('item_id'):
        public.respcode, public.respmsg = "333102", "申请物品不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not expact_time:
        public.respcode, public.respmsg = "333102", "期望采购时间不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_purchase where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_purchase set "
                   "user_id=%s,"
                   "user_name=%s,"
                   "department=%s, "
                   "item_type=%s, "
                   "item_name=%s, "
                   "item_number=%s, "
                   "use_for=%s, "
                   "add_on=%s,"
                   "expact_time=%s,"
                   "remark=%s,"
                   "tran_date=%s "
                   "where id=%s ")
            cur.execute(sql, (public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              form_var.get('item_type'),
                              form_var.get('item_name'),
                              form_var.get('item_number'),
                              form_var.get('use_for'),
                              str(form_var.get('add_on')),
                              form_var.get('expact_time'),
                              form_var.get('remark'),
                              form_var.get('tran_date'),
                              id))
        else:  # 插入数据
            order_number = form_var.get('purchase_apply_number')
            if order_number == '' or not order_number:
                order_number = public_db.Get_SeqNo('PURCHASE_APPLY')
            sql = ("insert into yw_workflow_apply_purchase("
                   "order_number,"
                   "user_id,"
                   "user_name,"
                   "department, "
                   "item_type, "
                   "item_id, "
                   "item_number, "
                   "use_for, "
                   "add_on,"
                   "expact_time,"
                   "entry_time,"
                   "remark,"
                   "tran_date"
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (order_number, public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              form_var.get('item_type'),
                              form_var.get('item_id'),
                              form_var.get('item_number'),
                              form_var.get('use_for'),
                              str(form_var.get('add_on')),
                              form_var.get('expact_time'),
                              form_var.get('remark'),
                              form_var.get('tran_date')))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % (sql,))

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
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


def wine_apply_commit(request):
    """招待用酒申请"""
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    form_var = body.get("form_var")
    id = form_var.get("id")
    tran_date = form_var.get("tran_date")
    item_name = form_var.get('item_name')
    item_number = form_var.get('item_number')

    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if not form_var:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not tran_date:
        public.respcode, public.respmsg = "333102", "申请部门不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('department'):
        public.respcode, public.respmsg = "333102", "申请部门不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not item_number:
        public.respcode, public.respmsg = "333102", "物品数量不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('visitor_name'):
        public.respcode, public.respmsg = "333102", "宴请人员不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not item_name:
        public.respcode, public.respmsg = "333102", "申请物品不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('hotel_name'):
        public.respcode, public.respmsg = "333102", "宴会地点不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select apply_status, user_id from yw_workflow_apply_article where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_wine set "
                   "user_id=%s,"
                   "user_name=%s,"
                   "department=%s, "
                   "item_name=%s, "
                   "item_number=%s,"
                   "visitor_name=%s,"
                   "hotel_name=%s,"
                   "remark=%s "
                   "where id=%s ")
            cur.execute(sql, (public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              item_name,
                              item_number,
                              form_var.get('visitor_name'),
                              form_var.get('hotel_name'),
                              form_var.get('remark'),
                              id))
        else:  # 插入数据
            order_number = form_var.get('banquet_apply_number')
            if order_number == '' or not order_number:
                order_number = public_db.Get_SeqNo('WINE_APPLY')
            sql = ("insert into yw_workflow_apply_wine("
                   "user_id,"
                   "user_name,"
                   "department,"
                   "order_number,"
                   "item_name,"
                   "item_number, "
                   "visitor_name,"
                   "hotel_name,"
                   "remark,"
                   "tran_date,"
                   "apply_statue,"
                   "approve_status"
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              order_number,
                              item_name,
                              item_number,
                              form_var.get('visitor_name'),
                              form_var.get('hotel_name'),
                              form_var.get('remark'),
                              form_var.get('tran_date'),
                              form_var.get('apply_statue'),
                              form_var.get('approve_status')
                              )
                        )
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % (sql,))

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
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



def meetingroom_apply_commit(request):
    """会议室使用申请"""
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    form_var = body.get("form_var")
    id = form_var.get("id")
    tran_date = form_var.get("tran_date")
    start_time = form_var.get('start_time')
    end_time = form_var.get('end_time')
    start_time = pubfunc.str_datetime(start_time, '%Y-%m-%d %H:%M:%S')
    end_time = pubfunc.str_datetime(end_time, '%Y-%m-%d %H:%M:%S')
    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('meeting_room'):
        public.respcode, public.respmsg = "333102", "会议室不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('use_for'):
        public.respcode, public.respmsg = "333102", "用途不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('attend_member'):
        public.respcode, public.respmsg = "333102", "参会人员不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not (start_time or end_time):
        public.respcode, public.respmsg = "333102", "开始/结束时间不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if start_time < datetime.datetime.now():
        public.respcode, public.respmsg = "333102", "请重新选择开始时间"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if start_time > end_time:
        public.respcode, public.respmsg = "333102", "开始时间不能晚于结束时间!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    cur = connection.cursor()  # 创建游标

    try:
        # 判断该会议室在时间段内是否可用
        sql = "select start_time,end_time from yw_workflow_apply_meetingroom " \
              "where meeting_room = %s " \
              "and (status != '2' or apply_status != '4')" \
              "and not(end_time<=%s or start_time>=%s)"
        cur.execute(sql, (form_var.get('meeting_room'), start_time, end_time))
        row = cur.fetchone()
        if row:
            public.respcode, public.respmsg = "333103", "该会议室被占用，时间为%s至%s，请选择其他时间段" % (row[0], row[1])
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_meetingroom where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_meetingroom set "
                   "user_id=%s,"
                   "user_name=%s,"
                   "meeting_room=%s, "
                   "use_for=%s, "
                   "start_time=%s, "
                   "end_time=%s, "
                   "attend_member=%s, "
                   "service_status=%s,"
                   "id=%s ")
            cur.execute(sql, (public.user_id,
                              form_var.get('user_name'),
                              form_var.get('meeting_room'),
                              form_var.get('use_for'),
                              form_var.get('start_time'),
                              form_var.get('end_time'),
                              form_var.get('attend_member'),
                              form_var.get('service_status'),
                              id))
        else:  # 插入数据
            order_number = form_var.get('meetingroom_apply_number')
            if order_number == '' or not order_number:
                order_number = public_db.Get_SeqNo('USE_MEETING_ROOM')
            sql = ("insert into yw_workflow_apply_meetingroom("
                   "user_id,"
                   "user_name,"
                   "order_number,"
                   "meeting_room,"
                   "use_for, "
                   "start_time, "
                   "end_time, "
                   "attend_member, "
                   "service_status,"
                   "tran_date,"
                   "apply_status,"
                   "status"
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (public.user_id,
                              form_var.get('user_name'),
                              order_number,
                              form_var.get('meeting_room'),
                              form_var.get('use_for'),
                              form_var.get('start_time'),
                              form_var.get('end_time'),
                              form_var.get('attend_member'),
                              form_var.get('service_status'),
                              form_var.get('tran_date'),
                              form_var.get('apply_status'),
                              form_var.get('status')))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
            log.info("insert or update sql:%s" % (sql))

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
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


def reception_apply_commit(request):
    """来访接待申请"""
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    form_var = body.get("form_var")
    id = form_var.get("id")
    tran_date = form_var.get("tran_date")
    start_time = form_var.get('start_time')
    end_time = form_var.get('end_time')
    start_time = pubfunc.str_datetime(start_time, '%Y-%m-%d %H:%M:%S')
    end_time = pubfunc.str_datetime(end_time, '%Y-%m-%d %H:%M:%S')
    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('visitor_unit'):
        public.respcode, public.respmsg = "333102", "访客单位不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('visitor_name'):
        public.respcode, public.respmsg = "333102", "访客姓名不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('visitor_number'):
        public.respcode, public.respmsg = "333102", "来访人数不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('visit_purpose'):
        public.respcode, public.respmsg = "333102", "来访目的不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not start_time:
        public.respcode, public.respmsg = "333102", "来访时间不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if start_time < datetime.datetime.now():
        public.respcode, public.respmsg = "333102", "请重新选择开始时间"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if start_time > end_time:
        public.respcode, public.respmsg = "333102", "来访时间不能晚于返程时间!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    cur = connection.cursor()  # 创建游标

    try:
        if id:  # 更新数据
            sql = "select approve_status, user_id from yw_workflow_apply_reception where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_reception set "
                   "user_id=%s,"
                   "user_name=%s,"
                   "visitor_unit=%s,"
                   "visitor_name=%s, "
                   "visitor_position=%s,"
                   "visitor_number=%s,"
                   "visit_purpose=%s, "
                   "visit_itinerary=%s, "
                   "start_time=%s,"
                   "end_time=%s,"
                   "use_car_apply=%s,"
                   "hotel_apply=%s,"
                   "meetingroom_apply=%s,"
                   "banquet_apply=%s,"
                   "use_car_apply_number=%s,"
                   "meetingroom_apply_number=%s,"
                   "hotel_apply_number=%s,"
                   "banquet_apply_number=%s,"
                   "visit_arange=%s "
                   "where id=%s")
            cur.execute(sql, (
                public.user_id, form_var.get('user_name'), form_var.get('visitor_unit'), form_var.get('visitor_name'),
                form_var.get('visitor_position'), form_var.get('visitor_number'), form_var.get('visit_purpose'),
                form_var.get('visit_itinerary'), form_var.get('start_time'), form_var.get('end_time'),
                form_var.get('use_car_apply'), form_var.get('hotel_apply'), form_var.get('meetingroom_apply'),
                form_var.get('banquet_apply'), form_var.get('use_car_apply_number'),
                form_var.get('meetingroom_apply_number'), form_var.get('hotel_apply_number'),
                form_var.get('banquet_apply_number'), form_var.get('visit_arange'), id
            ))
        else:  # 插入数据
            order_number = public_db.Get_SeqNo('RECEP_APPLY')
            body['form_var']['order_number'] = order_number
            sql = ("insert into yw_workflow_apply_reception("
                   "order_number,"
                   "user_id,"
                   "user_name,"
                   "department,"
                   "visitor_unit,"
                   "visitor_name,"
                   "visitor_position,"
                   "visitor_number,"
                   "visit_purpose, "
                   "visit_itinerary, "
                   "start_time,"
                   "end_time,"
                   "use_car_apply,"
                   "hotel_apply,"
                   "meetingroom_apply,"
                   "banquet_apply,"
                   "use_car_apply_number,"
                   "meetingroom_apply_number,"
                   "hotel_apply_number,"
                   "banquet_apply_number,"
                   "visit_arange,"
                   "remark,"
                   "tran_date,"
                   "apply_status,"
                   "approve_status"
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (order_number,
                              public.user_id, form_var.get('user_name'),
                              form_var.get('department'), form_var.get('visitor_unit'),
                              form_var.get('visitor_name'),
                              form_var.get('visitor_position'), form_var.get('visitor_number'),
                              form_var.get('visit_purpose'),
                              form_var.get('visit_itinerary'), form_var.get('start_time'), form_var.get('end_time'),
                              form_var.get('use_car_apply'), form_var.get('hotel_apply'),
                              form_var.get('meetingroom_apply'),
                              form_var.get('banquet_apply'), form_var.get('use_car_apply_number'),
                              form_var.get('meetingroom_apply_number'), form_var.get('hotel_apply_number'),
                              form_var.get('banquet_apply_number'), str(form_var.get('visit_arange')),
                              form_var.get('remark'), form_var.get('tran_date'),
                              form_var.get('apply_status'), form_var.get('approve_status')
                              ))

            # 触发消息通知
            visit_floor = form_var.get('visit_arange')
            if visit_floor:
                content = '参观通知：'
                message = '''来自%s的客户将于%s来厂参观，请大家做好准备''' % (form_var.get('visitor_unit'), form_var.get('start_time'))
                for item in visit_floor:
                    if item == '一楼车间':
                        # select user from sys_user where user_position = '一楼车间'
                        # send_message(uid, content, message)
                        pass
                    if item == '二楼车间':
                        pass
                    if item == '实验室':
                        pass

            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
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


def create_car_apply_number(request):
    """生成用车申请单号"""
    body = public.req_body
    log = public.logger

    try:
        body['form_var']['use_car_apply_number'] = public_db.Get_SeqNo("USE_CAR")
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


def create_meeting_apply_number(request):
    """生成会议室申请单号"""
    body = public.req_body
    log = public.logger

    try:
        body['form_var']['meetingroom_apply_number'] = public_db.Get_SeqNo("USE_MEETING_ROOM")
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


def create_hotel_apply_number(request):
    """生成酒店入住申请单号"""
    body = public.req_body
    log = public.logger

    try:
        body['form_var']['hotel_apply_number'] = public_db.Get_SeqNo("HOTEL_APPLY")
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


def create_banquet_apply_number(request):
    """生成招待用酒申请单号"""
    body = public.req_body
    log = public.logger

    try:
        body['form_var']['banquet_apply_number'] = public_db.Get_SeqNo("WINE_APPLY")
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


def send_message(list_uid, content, message):
    "消息推送"
    log = public.logger
    if list_uid:
        try:
            cur = connection.cursor()
            insert_value_list = []
            for uid in list_uid:
                insert_value_list.append(uid, datetime.datetime.now(), 'flow', content, message, '处理中', '0')

            sql = '''insert into sys_user_message (user_id, tran_date, type, content, message, msg_status, state)
             values (%s, %s, %s, %s, %s, %s, %s)'''
            cur.executemany(sql, insert_value_list)
        except Exception as ex:
            log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo


def office_item_apply_commit(request):
    """办公用品采购申请"""
    log = public.logger
    body = public.req_body
    formid = body.get("form_id")
    form_var = body.get("form_var")
    id = form_var.get("id")
    tran_date = form_var.get("tran_date")
    if not formid:
        public.respcode, public.respmsg = "110221", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if not form_var:
        public.respcode, public.respmsg = "110222", "配置信息不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('department'):
        public.respcode, public.respmsg = "333102", "申请部门不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('item_number'):
        public.respcode, public.respmsg = "333102", "物品数量不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('use_for'):
        public.respcode, public.respmsg = "333102", "用途不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_var.get('item_name'):
        public.respcode, public.respmsg = "333102", "申请物品不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        if id:  # 更新数据
            sql = "select status, user_id from yw_workflow_apply_article where id=%s"
            cur.execute(sql, id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "333001", "原数据不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[0]) not in ['0', '2']:
                public.respcode, public.respmsg = "333002", "审批状态非初始,不可修改!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if str(row[1]) != str(public.user_id):
                public.respcode, public.respmsg = "333004", "只可修改自己的单据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = ("update yw_workflow_apply_article set "
                   "user_id=%s,"
                   "user_name=%s,"
                   "department=%s, "
                   "item_name=%s, "
                   "item_number=%s, "
                   "item_unit=%s,"
                   "use_for=%s, "
                   "add_on=%s,"
                   "remark=%s "
                   "where id=%s ")
            cur.execute(sql, (public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              form_var.get('item_name'),
                              form_var.get('item_number'),
                              form_var.get('item_unit'),
                              form_var.get('use_for'),
                              str(form_var.get('add_on')),
                              form_var.get('remark'),
                              id))
        else:  # 插入数据
            order_number = form_var.get('office_item_apply_number')
            if order_number == '' or not order_number:
                order_number = public_db.Get_SeqNo('ITEM_APPLY')
            sql = ("insert into yw_workflow_apply_article("
                   "order_number,"
                   "user_id,"
                   "user_name,"
                   "department, "
                   "item_type, "
                   "item_name,"
                   "item_number, "
                   "item_unit,"
                   "use_for, "
                   "add_on,"
                   "remark,"
                   "tran_date,"
                   "apply_status,"
                   "approve_status"
                   ") values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
            cur.execute(sql, (order_number,
                              public.user_id,
                              form_var.get('user_name'),
                              form_var.get('department'),
                              '办公用品',
                              form_var.get('item_name'),
                              form_var.get('item_number'),
                              form_var.get('item_unit'),
                              form_var.get('use_for'),
                              str(form_var.get('add_on')),
                              form_var.get('remark'),
                              form_var.get('tran_date'),
                              form_var.get('apply_status'),
                              form_var.get('approve_status')))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                body['form_var']['id'] = row[0]
            # log.info('---[tran_type:%s]-end----' % (public.tran_type), extra={'form_var': form_var})
            log.info("insert or update sql:%s" % (sql,))

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
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