import sys
from django.shortcuts import render, redirect, HttpResponse
from django.db import connection, transaction
import json

from admin_app import models
from admin_app.sys import public
import datetime
from admin_app.tranapp import pubfunc
from admin_app.sys import public_db
import requests
import itertools


###########################################################################################################
# 人员管理
# add by Wuxm, 2021.04.22
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
            "staff_name": "姓名",
            "gender": "性别",
            "hometown": "籍贯",
            "id_number": "身份证号码",
            "personal_phone": "联系电话",
            "address": "现居地"
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
        sql_value = (form_var.get('jy_sj1'), form_var.get('jy_xx1'), form_var.get('jy_zy1'), form_var.get('jy_zs1'),
                     form_var.get('jy_sj2'), form_var.get('jy_xx2'), form_var.get('jy_zy2'), form_var.get('jy_zs2'),
                     form_var.get('jy_sj3'), form_var.get('jy_xx3'), form_var.get('jy_zy3'), form_var.get('jy_zs3'),
                     form_var.get('gz_sj1'), form_var.get('gz_dw1'), form_var.get('gz_gw1'), form_var.get('gz_lz1'),
                     form_var.get('gz_zmr1'), form_var.get('gz_sj2'), form_var.get('gz_dw2'), form_var.get('gz_gw2'),
                     form_var.get('gz_lz2'), form_var.get('gz_zmr2'), form_var.get('gz_sj3'), form_var.get('gz_dw3'),
                     form_var.get('gz_gw3'), form_var.get('gz_lz3'), form_var.get('gz_zmr3'), form_var.get('cy_xm1'),
                     form_var.get('cy_gx1'), form_var.get('cy_dw1'), form_var.get('cy_dh1'), form_var.get('cy_xm2'),
                     form_var.get('cy_gx2'), form_var.get('cy_dw2'), form_var.get('cy_dh2'),
                     str(form_var.get('media_source')), form_var.get('source_desc'), form_var.get('zwpj'),
                     form_var.get('hr_evaluate'))
        cur.execute(sql, sql_value)
        cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "100010", "更新数据失败!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 插入主表
        less_id = row[0]
        sql = "insert into sys_staff_info (job_number, staff_name, name_spell, id_number, personal_phone, " \
              "attend_number, gender, nation, birthday, address, hometown, degree, graduate_school, " \
              "graduate_date, major, politic_face, height, weight, health_state, marital_status, exp_salary, postbox, " \
              "emergency_contact, relationship, emergency_contact_phone, entry_date, work_state, less_id,address,photo)" \
              "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        job_number = public_db.Get_SeqNo('PERSONNEL.JOB_NUM')
        name_spell = public.pinyin(form_var.get('staff_name'))
        sql_value = (
        job_number, form_var.get('staff_name'), name_spell, form_var.get('id_number'), form_var.get('personal_phone'),
        form_var.get('attend_number'), form_var.get('gender'), form_var.get('nation'), form_var.get('birthday'),
        form_var.get('address'), form_var.get('hometown'), form_var.get('degree'), form_var.get('graduate_school'),
        form_var.get('graduate_date'), form_var.get('major'), form_var.get('politic_face'), form_var.get('height'),
        form_var.get('weight'), form_var.get('health_state'), form_var.get('marital_status'),
        form_var.get('exp_salary'), form_var.get('postbox'), form_var.get('emergency_contact'),
        form_var.get('relationship'), form_var.get('emergency_contact_phone'), form_var.get('entry_date'), '1', less_id,
        form_var.get('address'), form_var.get('photo'))
        cur.execute(sql, sql_value)
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
    finally:
        cur.close()  # 关闭游标


def position_fix_apply_commit(request):
    """定岗申请"""
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        param_not_null = {
            "user_name": "姓名",
            "department": "部门",
            "position_name": "岗位名称",
            "position_number": "岗位人数",
            "min_salary": "薪酬范围",
            "celling_wage": "薪酬范围",
            "position_duty": "岗位职责"
        }
        for k in param_not_null:
            if not form_var.get(k):
                public.respcode, public.respmsg = "320430", param_not_null.get(k) + '不可为空'
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        cur = connection.cursor()
        # 薪酬必须为数字且范围正确
        try:
            min_sal = float(form_var.get('min_salary'))
            max_sal = float(form_var.get('celling_wage'))
            if min_sal > max_sal:
                public.respcode, public.respmsg = "335102", "薪酬范围有误!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        except:
            public.respcode, public.respmsg = "335102", "薪酬范围格式异常，请输入正确数字"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 岗位名称不允许重复
        if not form_var.get('id'):
            sql = "select 1 from yw_personnel_position_apply where position_name=%s"
            cur.execute(sql, form_var.get('position_name'))
            row = cur.fetchone()
            if row:
                public.respcode, public.respmsg = "335102", "岗位名称已存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        # 生成order_number,position_no
        form_var['order_number'] = public_db.Get_SeqNo('COMMON')
        form_var['position_no'] = public_db.Get_SeqNo('PERSONNEL.POSITION')
        form_var['apply_user'] = form_var.get('user_name')
        form_var['user_id'] = public.user_id
        # 更新数据
        c, errmsg = public_db.insert_or_update_table(cur, 'yw_personnel_position_apply', **form_var)
        if not c:
            public.respcode, public.respmsg = "335103", errmsg
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
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
            "BODY": body,
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
        return public.respinfo
