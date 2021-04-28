import sys
from django.shortcuts import render, redirect, HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
from admin_app.sys import public_db
from functools import reduce
from admin_app.tranapp import pubfunc
import decimal
import itertools

###########################################################################################################
# 客户订单管理模块
# add by litz, 2020.06.15
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


# 备货单查询
def custorder_stockup_show(request):
    log = public.logger
    form_data = public.req_body['form_data']
    try:
        total_num = 6  # 显示5条明细
        this_num = 0  # 当前记录数
        form_var = {}
        ht_info = []
        cp_info = []
        jq_info = []

        cur = connection.cursor()  # 创建游标

        if form_data.get('id'):  # 更新数据
            sql = "select tran_date,bill_no,tc_no,cust_name,salesperson,otherinfo,state from yw_bill_stockup_head where id=%s "
            cur.execute(sql, form_data.get('id'))
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "320331", "查询无数据!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

            # #重新赋值一些数据
            form_var['tran_date'] = row[0]
            form_var['bill_no'] = row[1]
            form_var['tc_no'] = row[2]
            form_var['cust_name'] = row[3]
            form_var['salesperson'] = row[4]
            form_var['otherinfo'] = row[5]
            form_var['state'] = row[6]
            form_var['id'] = form_data.get('id')

            # 查询备货单明细
            sql = "select prd_name, prd_num, prd_hardversion, prd_pcbversion, prd_shellinfo, prd_macinfo, " \
                  "prd_no, prd_blueprint_ver, prd_pcb_ver, prd_key_components,prd_otherinfo," \
                  "delivery_plan_no,delivery_comp_coll_time, delivery_pcba_return_time,delivery_cust_time, delivery_otherinfo," \
                  "sc_writer, sc_updtime, yf_writer, yf_updtime, pmc_writer, pmc_updtime, id " \
                  "from yw_bill_stockup_body where head_id=%s "
            # log.info("查询备货单明细:"+sql, extra={'ptlsh': public.req_seq})
            cur.execute(sql, form_data.get('id'))
            rows = cur.fetchall()

            for item in rows:
                this_num = this_num + 1
                # 获取表身明细
                ht_info_dict = {}
                cp_info_dict = {}
                jq_info_dict = {}

                ht_info_dict['prd_name'] = item[0]
                ht_info_dict['prd_num'] = item[1]
                ht_info_dict['prd_hardversion'] = item[2]
                ht_info_dict['prd_pcbversion'] = item[3]
                ht_info_dict['prd_shellinfo'] = item[4]
                ht_info_dict['prd_macinfo'] = item[5]
                ht_info_dict['id'] = item[22]

                cp_info_dict['prd_name'] = item[0]
                cp_info_dict['prd_no'] = item[6]
                cp_info_dict['prd_blueprint_ver'] = item[7]
                cp_info_dict['prd_pcb_ver'] = item[8]
                cp_info_dict['prd_key_components'] = item[9]
                cp_info_dict['prd_otherinfo'] = item[10]
                cp_info_dict['id'] = item[22]

                jq_info_dict['prd_name'] = item[0]
                jq_info_dict['delivery_plan_no'] = item[11]
                jq_info_dict['delivery_comp_coll_time'] = item[12]
                jq_info_dict['delivery_pcba_return_time'] = item[13]
                jq_info_dict['delivery_cust_time'] = item[14]
                jq_info_dict['delivery_otherinfo'] = item[15]
                jq_info_dict['id'] = item[22]

                ht_info.append(ht_info_dict)
                cp_info.append(cp_info_dict)
                jq_info.append(jq_info_dict)

                # form_var['sc_writer'] = item[16]
                # form_var['sc_updtime'] = item[17]
                # form_var['yf_writer'] = item[18]
                # form_var['yf_updtime'] = item[19]
                # form_var['pmc_writer'] = item[20]
                # form_var['pmc_updtime'] = item[21]

                if item[16] and (not form_var.get('sc_writer') or form_var['sc_writer'] < item[16]):
                    form_var['sc_writer'] = item[16]
                if item[17] and (not form_var.get('sc_updtime') or form_var['sc_updtime'] < item[17]):
                    form_var['sc_updtime'] = item[17]
                if item[18] and (not form_var.get('yf_writer') or form_var['yf_writer'] < item[18]):
                    form_var['yf_writer'] = item[18]
                if item[19] and (not form_var.get('yf_updtime') or form_var['yf_updtime'] < item[19]):
                    form_var['yf_updtime'] = item[19]
                # log.info("研发填写时间:" + str(form_var['yf_updtime']), extra={'ptlsh': public.req_seq})
                if item[20] and (not form_var.get('pmc_writer') or form_var['pmc_writer'] < item[20]):
                    form_var['pmc_writer'] = item[20]
                if item[21] and (not form_var.get('pmc_updtime') or form_var['pmc_updtime'] < item[21]):
                    form_var['pmc_updtime'] = item[21]

        else:  # 新增数据
            form_var['tran_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            form_var['bill_no'] = ''
            form_var['tc_no'] = ''
            form_var['cust_name'] = ''
            form_var['salesperson'] = ''
            form_var['otherinfo'] = ''
            form_var['state'] = ''
            form_var['id'] = form_data.get('id')

            form_var['sc_writer'] = ''
            form_var['sc_updtime'] = ''
            form_var['yf_writer'] = ''
            form_var['yf_updtime'] = ''
            form_var['pmc_writer'] = ''
            form_var['pmc_updtime'] = ''

        if this_num < total_num:
            for i in range(1, total_num - this_num):
                ht_info_dict = {}
                ht_info_dict['prd_hardversion'] = ''
                ht_info_dict['prd_macinfo'] = ''
                ht_info_dict['prd_name'] = ''
                ht_info_dict['prd_num'] = ''
                ht_info_dict['prd_pcbversion'] = ''
                ht_info_dict['prd_shellinfo'] = ''
                ht_info_dict['id'] = ''
                ht_info.append(ht_info_dict)

                cp_info_dict = {}
                cp_info_dict["prd_name"] = ''
                cp_info_dict["prd_no"] = ''
                cp_info_dict["prd_blueprint_ver"] = ''
                cp_info_dict["prd_pcb_ver"] = ''
                cp_info_dict["prd_key_components"] = ''
                cp_info_dict["prd_otherinfo"] = ''
                cp_info_dict['id'] = ''
                cp_info.append(cp_info_dict)

                jq_info_dict = {}
                jq_info_dict["prd_name"] = ''
                jq_info_dict["delivery_plan_no"] = ''
                jq_info_dict["delivery_comp_coll_time"] = ''
                jq_info_dict["delivery_pcba_return_time"] = ''
                jq_info_dict["delivery_cust_time"] = ''
                jq_info_dict["delivery_otherinfo"] = ''
                jq_info_dict['id'] = ''
                jq_info.append(jq_info_dict)

        form_var['ht_info'] = ht_info
        form_var['cp_info'] = cp_info
        form_var['jq_info'] = jq_info

        form_var['state_options'] = [
            {"key": "0", "value": "市场填写完毕"},
            {"key": "1", "value": "研发填写完毕"},
            {"key": "2", "value": "PMC填写完毕"},
            {"key": "3", "value": "单据锁定"},
            {"key": "4", "value": "单据作废"},
        ]

        # 保存按钮是否可用
        if form_var.get('state') in ('3', '4'):
            form_var['commit_power'] = {"show": True, "disabled": True}

        form_var['ht_info_power'] = {"show": True, "disabled": True}
        form_var['cp_info_power'] = {"show": True, "disabled": True}
        form_var['jq_info_power'] = {"show": True, "disabled": True}
        form_var['lock_power'] = {"show": False, "disabled": True}
        form_var['unlock_power'] = {"show": False, "disabled": True}
        form_var['nullify_power'] = {"show": False, "disabled": True}
        # 获取用户角色
        sql = "select DISTINCT role_id from sys_user_role where user_id=%s "
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        for item in rows:
            if item[0] in ('lqkj_shichang', 'root'):  # 市场
                form_var['ht_info_power'] = {"show": True, "disabled": False}
            if item[0] in ('lqkj_yanfa', 'root'):  # 研发
                form_var['cp_info_power'] = {"show": True, "disabled": False}
            if item[0] in ('lqkj_pmc', 'root'):  # PMC
                form_var['jq_info_power'] = {"show": True, "disabled": False}
                form_var['lock_power'] = {"show": True, "disabled": False}
                form_var['unlock_power'] = {"show": True, "disabled": False}
                form_var['nullify_power'] = {"show": True, "disabled": False}

        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("查询数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "查询数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_id": public.req_body.get('form_id'),
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)

    return public.respinfo


# 备货单信息新增或修改保存
def custorder_stockup_save(request):
    log = public.logger
    form_var = public.req_body['form_var']
    try:

        id = form_var.get('id')
        ht_info = form_var.get('ht_info')
        if not ht_info or len(ht_info) == 0:
            public.respcode, public.respmsg = "320330", "明细必输!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标

        # 获取用户角色
        sql = "select DISTINCT role_id from sys_user_role where user_id=%s "
        cur.execute(sql, public.user_id)
        rows = cur.fetchall()
        form_var['state'] = '9'
        for item in rows:
            if item[0] in ('lqkj_shichang'):  # 市场
                form_var['state'] = '0'
            if item[0] in ('lqkj_yanfa'):  # 研发
                form_var['state'] = '1'
            if item[0] in ('lqkj_pmc'):  # PMC
                form_var['state'] = '2'
        if form_var.get('state') == '9':
            cur.close()
            public.respcode, public.respmsg = "320333", "无操作权限!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        if not id:  # 新增数据
            # #重新赋值一些数据
            form_var['bill_no'] = public_db.Get_SeqNo('STOCKUP_SERIAL')  # 生成备货单号
            form_var['state'] = '0'  # 合同信息新录入

            sql = "insert into yw_bill_stockup_head(tran_date,bill_no,tc_no,cust_name,salesperson,state)  " \
                  "values(%s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (
                datetime.datetime.now(), form_var.get('bill_no'), form_var.get('tc_no'), form_var.get('cust_name'),
                form_var.get('salesperson'), form_var.get('state')))
            form_var['id'] = cur.lastrowid

        else:  # 更新记录
            sql = "update yw_bill_stockup_head set tran_date=%s,bill_no=%s,tc_no=%s,cust_name=%s,salesperson=%s,state=%s " \
                  "where id=%s"
            cur.execute(sql, (
                datetime.datetime.now(), form_var.get('bill_no'), form_var.get('tc_no'), form_var.get('cust_name'),
                form_var.get('salesperson'), form_var.get('state'), id))

        # 插入或更新的表身明细
        ht_info = form_var.get('ht_info')
        cp_info = form_var.get('cp_info')
        jq_info = form_var.get('jq_info')
        i = 0
        for ht_item in ht_info:
            cp_item = cp_info[i]
            jq_item = jq_info[i]
            i = i + 1
            print('ht_item=', ht_item)
            print('cp_item=', cp_item)
            print('jq_item=', jq_item)

            ht_info_dict = {}
            ht_info_dict['id'] = ht_item.get('id')
            ht_info_dict['prd_name'] = ht_item.get('prd_name')
            ht_info_dict['prd_num'] = ht_item.get('prd_num')
            ht_info_dict['prd_hardversion'] = ht_item.get('prd_hardversion')
            ht_info_dict['prd_pcbversion'] = ht_item.get('prd_pcbversion')
            ht_info_dict['prd_shellinfo'] = ht_item.get('prd_shellinfo')
            ht_info_dict['prd_macinfo'] = ht_item.get('prd_macinfo')

            cp_info_dict = {}
            cp_info_dict['id'] = cp_item.get('id')
            cp_info_dict['prd_name'] = cp_item.get('prd_name')
            cp_info_dict['prd_no'] = cp_item.get('prd_no')
            cp_info_dict['prd_blueprint_ver'] = cp_item.get('prd_blueprint_ver')
            cp_info_dict['prd_pcb_ver'] = cp_item.get('prd_pcb_ver')
            cp_info_dict['prd_key_components'] = cp_item.get('prd_key_components')
            cp_info_dict['prd_otherinfo'] = cp_item.get('prd_otherinfo')

            jq_info_dict = {}
            jq_info_dict['id'] = jq_item.get('id')
            jq_info_dict['prd_name'] = jq_item.get('prd_name')
            jq_info_dict['delivery_plan_no'] = jq_item.get('delivery_plan_no')
            jq_info_dict['delivery_comp_coll_time'] = jq_item.get('delivery_comp_coll_time')
            jq_info_dict['delivery_pcba_return_time'] = jq_item.get('delivery_pcba_return_time')
            jq_info_dict['delivery_cust_time'] = jq_item.get('delivery_cust_time')
            jq_info_dict['delivery_otherinfo'] = jq_item.get('delivery_otherinfo')

            if form_var.get('state') == '0':  # 市场填写
                form_var['sc_writer'] = public_db.get_username(public.user_id)
                form_var['sc_updtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if not ht_info_dict.get('id'):  # 新增数据
                    sql = "insert into yw_bill_stockup_body(head_id, tran_date, prd_name, prd_num, prd_hardversion,prd_pcbversion, " \
                          "prd_shellinfo, prd_macinfo, sc_writer, sc_updtime) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"
                    cur.execute(sql, (form_var.get('id'), datetime.datetime.now(), ht_info_dict.get('prd_name'),
                                      ht_info_dict.get('prd_num'),
                                      ht_info_dict.get('prd_hardversion'), ht_info_dict.get('prd_pcbversion'),
                                      ht_info_dict.get('prd_shellinfo'),
                                      ht_info_dict.get('prd_macinfo'), form_var.get('sc_writer'),
                                      form_var.get('sc_updtime')))
                else:  # 修改数据
                    sql = "update yw_bill_stockup_body set tran_date=%s, prd_name=%s, prd_num=%s, prd_hardversion=%s,prd_pcbversion=%s, " \
                          "prd_shellinfo=%s, prd_macinfo=%s, sc_writer=%s, sc_updtime=%s where id=%s"
                    cur.execute(sql,
                                (datetime.datetime.now(), ht_info_dict.get('prd_name'), ht_info_dict.get('prd_num'),
                                 ht_info_dict.get('prd_hardversion'), ht_info_dict.get('prd_pcbversion'),
                                 ht_info_dict.get('prd_shellinfo'), ht_info_dict.get('prd_macinfo'),
                                 form_var.get('sc_writer'),
                                 form_var.get('sc_updtime'), ht_info_dict.get('id')))
            elif form_var.get('state') == '1':  # 研发填写, 研发只能是update
                form_var['yf_writer'] = public_db.get_username(public.user_id)
                form_var['yf_updtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql = "update yw_bill_stockup_body set tran_date=%s, prd_no=%s, prd_blueprint_ver=%s, prd_pcb_ver=%s, " \
                      "prd_key_components=%s, prd_otherinfo=%s, yf_writer=%s, yf_updtime=%s  where id=%s "
                cur.execute(sql,
                            (datetime.datetime.now(), cp_info_dict.get('prd_no'), cp_info_dict.get('prd_blueprint_ver'),
                             cp_info_dict.get('prd_pcb_ver'), cp_info_dict.get('prd_key_components'),
                             cp_info_dict.get('prd_otherinfo'),
                             form_var.get('yf_writer'), form_var.get('yf_updtime'), ht_info_dict.get('id')))
            elif form_var.get('state') == '2':  # PMC填写, PMC只能是update
                form_var['pmc_writer'] = public_db.get_username(public.user_id)
                form_var['pmc_updtime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql = "update yw_bill_stockup_body set tran_date=%s, delivery_plan_no=%s, delivery_comp_coll_time=%s, " \
                      "delivery_pcba_return_time=%s, delivery_cust_time=%s, delivery_otherinfo=%s, pmc_writer=%s, pmc_updtime=%s  where id=%s "
                cur.execute(sql, (datetime.datetime.now(), jq_info_dict.get('delivery_plan_no'),
                                  jq_info_dict.get('delivery_comp_coll_time'),
                                  jq_info_dict.get('delivery_pcba_return_time'), jq_info_dict.get('delivery_cust_time'),
                                  jq_info_dict.get('delivery_otherinfo'),
                                  form_var.get('pmc_writer'), form_var.get('pmc_updtime'), ht_info_dict.get('id')))

        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "保存成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": {
                "form_id": public.req_body.get('form_id'),
                "form_var": form_var
            }
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


# cto订单信息新增或修改保存
def custorder_ctoinfo_save(request):
    log = public.logger
    body = public.req_body
    try:
        order_head = body.get('order_head')
        tech_info = body.get('tech_info')
        if not order_head or len(order_head) == 0:
            public.respcode, public.respmsg = "320430", "订单信息必输!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标

        head_id = order_head.get('head_id')
        if not head_id:
            # 查看订单号是否重复
            sql = "select id from yw_bill_ctoinfo_head where cust_orderid=%s and state!='2'"
            cur.execute(sql, order_head.get('cust_orderid'))
            row = cur.fetchone()
            if row:
                cur.close()
                public.respcode, public.respmsg = "320433", "客户订单号重复!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        if not head_id:  # 新增数据
            # #重新赋值一些数据
            # form_var['bill_no'] = public_db.Get_SeqNo('STOCKUP_SERIAL')  # 生成备货单号
            order_head['state'] = '0'  # 状态 0-未启用，1-正常, 2-作废
            sql = "insert into yw_bill_ctoinfo_head(tran_date,order_date,cust_orderid,term_orderid,order_specinfo,delivery_addr," \
                  "delivery_person,delivery_phone,checker,undertaker,state)  " \
                  "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (datetime.datetime.now(), order_head.get('order_date'), order_head.get('cust_orderid'),
                              order_head.get('term_orderid'), order_head.get('order_specinfo'),
                              order_head.get('delivery_addr'),
                              order_head.get('delivery_person'), order_head.get('delivery_phone'),
                              order_head.get('checker'),
                              order_head.get('undertaker'), order_head.get('state')))
            order_head['head_id'] = cur.lastrowid

        else:  # 更新记录
            sql = "update yw_bill_ctoinfo_head set tran_date=%s,order_date=%s,cust_orderid=%s,term_orderid=%s,order_specinfo=%s," \
                  "delivery_addr=%s, delivery_person=%s,delivery_phone=%s,checker=%s,undertaker=%s,state=%s where id=%s"
            cur.execute(sql, (datetime.datetime.now(), order_head.get('order_date'), order_head.get('cust_orderid'),
                              order_head.get('term_orderid'), order_head.get('order_specinfo'),
                              order_head.get('delivery_addr'),
                              order_head.get('delivery_person'), order_head.get('delivery_phone'),
                              order_head.get('checker'),
                              order_head.get('undertaker'), order_head.get('state'), order_head.get('head_id')))

        # 插入或更新head_sub表
        sql = "delete from yw_bill_ctoinfo_head_sub  where head_id=%s"
        cur.execute(sql, order_head.get('head_id'))
        for item in order_head.get('order_info'):
            sql = "insert into yw_bill_ctoinfo_head_sub(head_id, seq_no, ch_no, tc_no, cust_name, hard_version, prod_name, prod_spc," \
                  "prod_num, prod_wb, use_zone ) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (order_head.get('head_id'), item.get('seq_no'), item.get('ch_no'), item.get('tc_no'),
                              item.get('cust_name'), item.get('hard_version'), item.get('prod_name'),
                              item.get('prod_spc'), item.get('prod_num'), item.get('prod_wb'), item.get('use_zone')))

        # 插入或更新ctobody表
        sql = "delete from yw_bill_ctoinfo_body  where head_id=%s"
        cur.execute(sql, order_head.get('head_id'))
        for item in tech_info:
            sql = "insert into yw_bill_ctoinfo_body(head_id, ship_logo, ship_id, ship_id_file, ship_mac, ship_mac_begin_id,ship_mac_end_id,ship_note," \
                  "shell_cad, shell_cad_file, shell_supplier, shell_name, shell_spc, shell_fn, shell_fn_file, shell_barcode, shell_barcode_file, shel_note," \
                  "soft_in_ver,soft_in_file,soft_ex_ver, soft_hardcode,soft_spec,soft_note," \
                  "pack_specs,pack_specs_file,pack_delivery,pack_devliver_file,pack_note ) " \
                  "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"
            log.info(sql % (order_head.get('head_id'), item.get('ship_logo'), item.get('ship_id'),
                            str(item.get('ship_id_file')), item.get('ship_mac'), item.get('ship_mac_begin_id'),
                            item.get('ship_mac_end_id'), item.get('ship_note'), item.get('shell_cad'),
                            str(item.get('shell_cad_file')), item.get('shell_supplier'), item.get('shell_name'),
                            item.get('shell_spc'), item.get('shell_fn'), str(item.get('shell_fn_file')),
                            item.get('shell_barcode'), str(item.get('shell_barcode_file')), item.get('shel_note'),
                            item.get('soft_in_ver'), str(item.get('soft_in_file')), item.get('soft_ex_ver'),
                            item.get('soft_hardcode'), item.get('soft_spec'), item.get('soft_note'),
                            item.get('pack_specs'), str(item.get('pack_specs_file')), item.get('pack_delivery'),
                            str(item.get('pack_devliver_file')), item.get('pack_note')),
                     extra={'ptlsh': public.req_seq})
            cur.execute(sql, (order_head.get('head_id'), item.get('ship_logo'), item.get('ship_id'),
                              str(item.get('ship_id_file')), item.get('ship_mac'), item.get('ship_mac_begin_id'),
                              item.get('ship_mac_end_id'), item.get('ship_note'), item.get('shell_cad'),
                              str(item.get('shell_cad_file')), item.get('shell_supplier'), item.get('shell_name'),
                              item.get('shell_spc'), item.get('shell_fn'), str(item.get('shell_fn_file')),
                              item.get('shell_barcode'), str(item.get('shell_barcode_file')), item.get('shel_note'),
                              item.get('soft_in_ver'), str(item.get('soft_in_file')), item.get('soft_ex_ver'),
                              item.get('soft_hardcode'), item.get('soft_spec'), item.get('soft_note'),
                              item.get('pack_specs'), str(item.get('pack_specs_file')), item.get('pack_delivery'),
                              str(item.get('pack_devliver_file')), item.get('pack_note')))

        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "保存成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


# 客户CTO订单信息确认
def custorder_ctoinfo_confirm(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        if not form_var or len(form_var) == 0:
            public.respcode, public.respmsg = "320430", "订单信息必输!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        form_var['state'] = '1'  # 状态 0-未启用，1-正常, 2-作废
        sql = "update yw_bill_ctoinfo_head set tran_date=%s, state=%s where id=%s"
        cur.execute(sql, (datetime.datetime.now(), form_var.get('state'), form_var.get('id')))

        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "保存成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


# 客户CTO订单信息撤消
def custorder_ctoinfo_cancel(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        if not form_var or len(form_var) == 0:
            public.respcode, public.respmsg = "320430", "订单信息必输!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        form_var['state'] = '2'  # 状态 0-未启用，1-正常, 2-作废
        sql = "update yw_bill_ctoinfo_head set tran_date=%s, state=%s where id=%s"
        cur.execute(sql, (datetime.datetime.now(), form_var.get('state'), form_var.get('id')))

        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "保存成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


# cto订单信息获取详情
def custorder_ctoinfo_getinfo(request):
    log = public.logger
    body = public.req_body
    try:
        order_head = body.get('order_head')
        if not order_head or len(order_head) == 0:
            public.respcode, public.respmsg = "320430", "订单信息必输!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        head_id = order_head.get('head_id')
        if not head_id:
            public.respcode, public.respmsg = "320431", "HEAD_ID必输!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        # 查询head表
        fieldstr = "id,tran_date,order_date,cust_orderid,term_orderid,order_specinfo,delivery_addr,delivery_person,delivery_phone,checker,undertaker,state"
        sql = "select " + fieldstr + " from yw_bill_ctoinfo_head where id=%s "
        cur.execute(sql, head_id)
        row = cur.fetchone()
        if not row:
            cur.close()
            public.respcode, public.respmsg = "320435", "未查询到数据!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        order_head['head_id'] = row[0]
        fieldlist = fieldstr.split(',')
        for i in range(1, len(fieldlist)):
            order_head[fieldlist[i]] = row[i]
        body['order_head'] = order_head

        # 查询head_sub表
        fieldstr = "seq_no,ch_no,tc_no,cust_name,hard_version,prod_name,prod_spc,prod_num,prod_wb,use_zone"
        sql = "select " + fieldstr + " from yw_bill_ctoinfo_head_sub where head_id=%s "
        cur.execute(sql, head_id)
        rows = cur.fetchall()
        order_info = []
        fieldlist = fieldstr.split(',')
        for item in rows:
            order_info_item = {}
            for i in range(0, len(fieldlist)):
                order_info_item[fieldlist[i]] = item[i]
            order_info.append(order_info_item)
        body['order_info'] = order_info

        # 查询body表
        fieldstr = "ship_logo,ship_id,ship_id_file,ship_mac,ship_mac_begin_id,ship_mac_end_id,ship_note,shell_cad," \
                   "shell_cad_file,shell_supplier,shell_name,shell_spc,shell_fn,shell_fn_file,shell_barcode," \
                   "shell_barcode_file,shel_note,soft_in_ver,soft_in_file,soft_ex_ver,soft_hardcode,soft_spec," \
                   "soft_note,pack_specs,pack_specs_file,pack_delivery,pack_devliver_file,pack_note"
        sql = "select " + fieldstr + " from yw_bill_ctoinfo_body where head_id=%s "
        cur.execute(sql, head_id)
        rows = cur.fetchall()
        tech_info = []
        fieldlist = fieldstr.split(',')
        for item in rows:
            tech_info_item = {}
            for i in range(0, len(fieldlist)):
                if 'file' in fieldlist[i]:
                    if item[i]:
                        tech_info_item[fieldlist[i]] = eval(item[i])
                    else:
                        tech_info_item[fieldlist[i]] = []
                else:
                    tech_info_item[fieldlist[i]] = item[i]
            tech_info.append(tech_info_item)
        body['tech_info'] = tech_info

        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "查询成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


def shipping_notice_create(request):
    """发货通知单制表"""
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        id = form_var.get('id')
        log.info('ID = ' + str(id))
        if id:
            # 不允许修改
            public.respcode, public.respmsg = "335104", "暂不支持修改!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        param_not_null = {
            'supply_unit': '发货单位',
            'rec_unit': '收货单位',
            'supply_address': '发货方地址',
            'rec_address': '收货方地址',
            'sp_contact': '发货方联系人',
            'rec_contact': '收货方联系人',
            'supply_phone': '发货方电话',
            'rec_phone': '收货方电话',
            'ERP_no': 'ERP销货单号',
            'express_no': '货运单号',
            'notice_date': '通知时间',
            'send_date': '发货日期',
            'order_detail': '订单明细'
        }

        def check_not_null_param(**param):
            for k in param:
                if not form_var.get(k):
                    return param.get(k)

        resp_msg = check_not_null_param(**param_not_null)
        if resp_msg:
            public.respcode, public.respmsg = "320430", resp_msg + '不可为空'
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        order_seq_no = form_var.get('order_detail')[0].get('seql_no')
        if not order_seq_no:
            public.respcode, public.respmsg = "320431", '订单明细不可为空'
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 插入数据
        cur = connection.cursor()  # 创建游标
        sql = "insert into yw_workflow_shipnotice (supply_unit, rec_unit, supply_address, rec_address, sp_contact, " \
              "rec_contact, supply_phone, rec_phone, ERP_no, express_no, notice_date, send_date, order_detail," \
              " express_req, special_req, tab_man, tran_date, check_state,total_number) " \
              "values (%s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s)"
        sql_value = (form_var.get('supply_unit'), form_var.get('rec_unit'), form_var.get('supply_address'),
                     form_var.get('rec_address'), form_var.get('sp_contact'), form_var.get('rec_contact'),
                     form_var.get('supply_phone'), form_var.get('rec_phone'), form_var.get('ERP_no'),
                     form_var.get('express_no'), form_var.get('notice_date'), form_var.get('send_date'),
                     str(form_var.get('order_detail')), form_var.get('express_req'), form_var.get('special_req'),
                     form_var.get('tab_man'), form_var.get('tran_date'), 0, form_var.get('total_number'))

        cur.execute(sql, sql_value)
        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "查询成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


def shipping_notice_confirm(request):
    """发货通知单确认"""
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    # 品质确认人员
    qa_confirm_user = ('111115', '111191')
    store_confirm_user = ('111157', )
    try:
        ship_id = form_var.get('id')
        if not ship_id:
            public.respcode, public.respmsg = "320432", "无法定位该订单！"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 已确认订单不允许再次确认
        cur = connection.cursor()
        # sql = "select qa_confirm_date,store_confirm_date from yw_workflow_shipnotice where id = %s"
        # cur.execute(sql, ship_id)
        # row = cur.fetchone()
        # 查询当前操作员所属部门
        sql = "SELECT o.ORG_SPELL,u.user_name FROM sys_user_org uo,sys_org o,sys_user u " \
              "where uo.org_id = o.org_id and uo.user_id = u.user_id and uo.USER_ID = %s"
        cur.execute(sql, public.user_id)
        row = cur.fetchone()
        if row:
            department = row[0]
            user_name = row[1]
        # 需要特点人员确认
        if public.user_id in qa_confirm_user:
            sql = "update yw_workflow_shipnotice set qa_man = %s, qa_confirm_date = %s, check_state = check_state+1 " \
                  "where id = %s and qa_confirm_date is null"
        # 仓储
        elif public.user_id in store_confirm_user:
            sql = "update yw_workflow_shipnotice set store_man=%s,store_confirm_date=%s,check_state=check_state+2 " \
                  "where id = %s and store_confirm_date is null"
        else:
            public.respcode, public.respmsg = "320433", "您没有确认该通知单权限"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        cur.execute(sql, (user_name, datetime.datetime.now(), ship_id))

        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "查询成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


def price_check_create(request):
    """价格核定制表"""
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

        persent_set = {
            "utility": form_var.get('remark_utility'),
            'depre': form_var.get('remark_depre'),
            'loss': form_var.get('remark_loss'),
            'manage': form_var.get('remark_manage'),
            'profit': form_var.get('remark_profit'),
            'tax': form_var.get('remark_tax'),
            'suggest_price': form_var.get('remark_suggest_price')
        }
        param_value = {}
        for k, v in persent_set.items():
            temp_value = v.replace('%', '')
            temp_value = float(temp_value)
            # if not (isinstance(temp_value, float) or isinstance(temp_value, int)):
            #     public.respcode, public.respmsg = "320430", k+'百分比格式不正确！'
            #     public.respinfo = HttpResponse(public.setrespinfo())
            #     return public.respinfo
            # else:
            #     param_value[k] = temp_value * 0.01
            param_value[k] = temp_value * 0.01

        manual_value = {
            'amount_bom': form_var.get('amount_bom'),
            'amount_scfl': form_var.get('amount_scfl'),
            'amount_rgcb': form_var.get('amount_rgcb'),
            'amount_trans': form_var.get('amount_trans'),
            'market_price': form_var.get('market_price')
        }
        for k, v in manual_value.items():
            if not pubfunc.is_num(v):
                public.respcode, public.respmsg = "320430", str(v)+'输入金额格式不正确！'
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            else:
                manual_value[k] = float(v)
        cost_set = {
            # 材料成本
            'clcb': manual_value.get('amount_bom') + manual_value.get('amount_scfl'),
            # 人工成本
            'rgcb': manual_value.get('amount_rgcb'),
            # 制造成本
            'zzcb': (manual_value.get('amount_bom')
                     + manual_value.get('amount_scfl')
                     + manual_value.get('amount_rgcb')) * (param_value.get('depre') +
                                                           param_value.get('loss') +
                                                           param_value.get('utility')),
            # 管理费
            'glf': (manual_value.get('amount_bom') + manual_value.get('amount_scfl') + manual_value.get('amount_rgcb')) * param_value.get('manage'),
            # 运输费：
            'ysf': manual_value.get('amount_trans')
        }
        # 水电
        amount_utility = (cost_set.get('clcb') + cost_set.get('rgcb')) * param_value.get('utility')
        # 折旧
        amount_depre = (cost_set.get('clcb') + cost_set.get('rgcb')) * param_value.get('depre')
        # 损耗
        amount_loss = (cost_set.get('clcb') + cost_set.get('rgcb')) * param_value.get('loss')


        # 利润： (BOM材料成本+生产辅材+人工成本+水电+折旧+损耗+管理+运输)* profit
        amount_profit = reduce(lambda x, y: x+y, cost_set.values()) * param_value.get('profit')
        # 税费：
        amount_tax = (cost_set.get('rgcb')+cost_set.get('zzcb')+cost_set.get('glf')+cost_set.get('ysf')+amount_profit) * param_value.get('tax')
        # 建议售价：
        suggest_price = (reduce(lambda x, y: x+y, cost_set.values())+amount_profit+amount_tax)

        # 插入数据
        cur = connection.cursor()  # 创建游标
        sql = "insert into yw_workflow_chk_price (tab_no, tran_date, customer, prod_name, prod_type, prod_unit, " \
              "prod_count, remark_bom, amount_bom, remark_scfl, amount_scfl, remark_rgcb, amount_rgcb, " \
              "remark_utility, amount_utility, remark_depre, amount_depre, remark_loss, amount_loss, remark_manage, " \
              "amount_manage, remark_trans, amount_trans, remark_profit, amount_profit, remark_tax, amount_tax, " \
              "remark_market_price, market_price, remark_suggest_price, suggest_price, tab_man,check_state) " \
              "values (%s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s," \
              "%s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s)"

        sql_value = (public_db.Get_SeqNo("PRICE_CHK"), form_var.get('tran_date'), form_var.get('customer'),
                     form_var.get('prod_name'), form_var.get('prod_type'), form_var.get('prod_unit'),
                     form_var.get('prod_count'), form_var.get('remark_bom'), form_var.get('amount_bom'),
                     form_var.get('remark_scfl'), form_var.get('amount_scfl'), form_var.get('remark_rgcb'),
                     form_var.get('amount_rgcb'), form_var.get('remark_utility'), amount_utility,
                     form_var.get('remark_depre'), amount_depre, form_var.get('remark_loss'),
                     amount_loss, form_var.get('remark_manage'), cost_set.get('glf'),
                     form_var.get('remark_trans'), form_var.get('amount_trans'), form_var.get('remark_profit'),
                     amount_profit, form_var.get('remark_tax'), amount_tax,
                     form_var.get('remark_market_price'), form_var.get('market_price'),
                     form_var.get('remark_suggest_price'), suggest_price,
                     form_var.get('tab_man'), '0')
        log.info(sql % sql_value)
        cur.execute(sql, sql_value)
        # 查询刚刚插入的ID
        cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
        row = cur.fetchone()
        if row:
            body['form_var']['id'] = row[0]
        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "查询成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


def price_check_confirm(request):
    """价格核定单_核价"""
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    # 确认人员，魏文重， 陈总
    user = str(public.user_id)
    confirm_user = ('111122', '111149')
    try:
        id = form_var.get('id')
        if not id:
            public.respcode, public.respmsg = "320432", "无法定位该订单！"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()
        # 查询当前操作员所属部门
        sql = "SELECT o.ORG_SPELL,u.user_name FROM sys_user_org uo,sys_org o,sys_user u " \
              "where uo.org_id = o.org_id and uo.user_id = u.user_id and uo.USER_ID = %s"
        cur.execute(sql, public.user_id)
        row = cur.fetchone()
        if row:
            department = row[0]
            user_name = row[1]
        # 核对
        log.info(public.user_id)
        log.info(confirm_user)
        if user in confirm_user:
            #
            confirm_price = form_var.get('confirm_price')
            if not pubfunc.is_num(confirm_price):
                public.respcode, public.respmsg = "320433", "请输入核定价格！"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            remark_profit = form_var.get('remark_profit').replace('%', '')
            if not pubfunc.is_num(remark_profit):
                public.respcode, public.respmsg = "320433", "请输入利润百分比！"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            sql = "select remark_profit,amount_bom,amount_scfl,amount_rgcb,amount_depre,amount_utility,amount_depre,amount_loss,amount_manage," \
                  "amount_trans,remark_tax from yw_workflow_chk_price where id = %s"
            cur.execute(sql, id)
            row = cur.fetchone()
            profit_percent = decimal.Decimal(row[0].replace('%', '')) / 100
            profit = (row[1]+row[2]+row[3]+row[4]+row[5]+row[6]+row[7]+row[8]+row[9]) * profit_percent
            tax_percent = decimal.Decimal(row[10].replace('%', '')) / 100
            tax = (row[3]+row[4]+row[5]+row[6]+row[7]+row[8]+row[9]+profit) * tax_percent
            sg_price = row[1]+row[2]+row[3]+row[4]+row[5]+row[6]+row[7]+row[8]+row[9]+profit+tax

            sql = "update yw_workflow_chk_price set confirm_man = %s, confirm_date = %s,confirm_price = %s," \
                  "remark_profit=%s, amount_profit=%s," \
                  "amount_tax=%s, suggest_price = %s," \
                  "check_state = check_state+1 " \
                  "where id = %s and yw_workflow_chk_price.confirm_date is null"
            sql_value = (user_name, datetime.datetime.now(), form_var.get('confirm_price'),
                         form_var.get('remark_profit'), profit, tax, sg_price, id)
            cur.execute(sql, sql_value)
        else:
            public.respcode, public.respmsg = "320433", "您没有核对该单权限！"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 查询刚刚插入的ID
        cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
        row = cur.fetchone()
        if row:
            body['form_var']['id'] = row[0]
        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "查询成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo


def price_verif_confirm(request):
    """价格核定单_核批"""
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    # 确认人员，魏文重， 陈总
    user = str(public.user_id)
    confirm_user = ('111122', '111149')
    try:
        id = form_var.get('id')
        if not id:
            public.respcode, public.respmsg = "320432", "无法定位该订单！"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()
        # 查询当前操作员所属部门
        sql = "SELECT o.ORG_SPELL,u.user_name FROM sys_user_org uo,sys_org o,sys_user u " \
              "where uo.org_id = o.org_id and uo.user_id = u.user_id and uo.USER_ID = %s"
        cur.execute(sql, public.user_id)
        row = cur.fetchone()
        if row:
            department = row[0]
            user_name = row[1]
        # 核批
        if user in confirm_user:
            #
            sql = "update yw_workflow_chk_price set check_man = %s, check_date = %s, check_state = check_state+2 " \
                  "where id = %s and check_date is null"
        else:
            public.respcode, public.respmsg = "320433", "您没有核对该单权限！"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        cur.execute(sql, (user_name, datetime.datetime.now(), id))
        # 查询刚刚插入的ID
        cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
        row = cur.fetchone()
        if row:
            body['form_var']['id'] = row[0]
        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())

    else:
        public.respcode, public.respmsg = "000000", "查询成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
    return public.respinfo
