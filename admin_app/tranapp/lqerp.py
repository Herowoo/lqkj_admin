import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
from admin_app.sys import public_db
import pymssql
import os
import xlrd

###########################################################################################################
#ERP处理函数
#add by litz, 2020.05.25
#
###########################################################################################################

#增删改查配置数据操作主流程
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


#ERP数据每日审核校验，--获取配置项列表
def erp_check_everyday_getlist( request ):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    form_data = body.get('form_data')
    try:
        cur = connection.cursor()  # 创建游标
        # 获取线别字典
        tableData=[]
        sql = "select id,check_name,check_date,check_sql,check_state,check_msg from yw_lqerp_check_everyday order by id desc"
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            dataitem={}
            dataitem['id']=item[0]
            dataitem['check_name'] = item[1]
            dataitem['check_date'] = item[2]
            dataitem['check_sql'] = item[3]
            dataitem['check_state'] = item[4]
            dataitem['check_msg'] = item[5]
            tableData.append(dataitem)
        cur.close()

        submit_power = {"show": True, "disabled": False} #放开提交按钮

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": {
                "tableData": tableData,
                "submit_power": submit_power,
            },
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#ERP数据每日审核校验，--获取配置项明细
def erp_check_everyday_getdata( request ):
    log = public.logger
    body = public.req_body
    form_data = body.get('form_data')
    if not form_data:  #未上传数据，估计是新增
        selectd_data = {}
        form_data={}
    else:
        selectd_data = form_data.get('selectd_data')

    try:
        cur = connection.cursor()  # 创建游标

        # 赋值返回数据
        data = {}
        if selectd_data:
            selectd=selectd_data[0]
            data['id'] = selectd.get('id')
            data['check_name'] = selectd.get('check_name')
            data['check_date'] = selectd.get('check_date')
            data['check_sql'] = selectd.get('check_sql')
            data['check_state'] = selectd.get('check_state')
            data['check_msg'] = selectd.get('check_msg')
        cur.close()

        data["check_state_options"]=[{"key":"0","value":"停用"},{"key":"1","value":"启用"}]
        # submit_power = {"show": True, "disabled": False} #放开提交按钮

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": data,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#ERP数据每日审核校验，--新增或修改配置项
def erp_check_everyday_savedata( request ):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        cur = connection.cursor()  # 创建游标

        if form_var.get('id'):
            sql = "update yw_lqerp_check_everyday set check_name=%s,check_date=%s,check_sql=%s,check_state=%s," \
                  "check_msg=%s where id=%s "
            cur.execute(sql, (form_var.get('check_name'), form_var.get('check_date'), form_var.get('check_sql'),
                              form_var.get('check_state'), form_var.get('check_msg'),form_var.get('id')))
        else:
            sql = "insert into yw_lqerp_check_everyday(check_name,check_date,check_sql,check_state,check_msg) " \
                  "values(%s, %s, %s, %s, %s)"
            cur.execute(sql,(form_var.get('check_name'), form_var.get('check_date'), form_var.get('check_sql'),
                             form_var.get('check_state'), form_var.get('check_msg') ) )

        cur.close()
    except Exception as ex:
        log.error("保存数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "保存数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

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

#ERP数据每日审核校验，--执行检查
def erp_check_everyday_check( request ):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    def SqlServer_Conn():
        sqlserver_conn = None
        try:
            sqlserver_conn = pymssql.connect(server='10.10.1.250', user='sa', password='luyao123KEJI',
                                             database="db_18",
                                             timeout=20, autocommit=True)  # 获取连接  #sqlserver数据库链接句柄
        except Exception as ex:
            log.info(str(ex))

        return sqlserver_conn

    try:
        sqlserver_conn = SqlServer_Conn()

        cur = connection.cursor()  # 创建游标
        # 获取线别字典
        tableData=[]
        sql = "select id,check_name,check_date,check_sql,check_state,check_msg " \
              "from yw_lqerp_check_everyday order by id desc"
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            db_id=item[0]
            db_check_name = item[1]
            db_check_date = item[2]
            db_check_sql = item[3]
            db_check_state = item[4]
            db_check_msg = item[5]
            result_list = []
            cursor = sqlserver_conn.cursor()  # 获取光标
            log.info(db_check_sql)
            try:
                cursor.execute(db_check_sql)
                rows = cursor.fetchall()
                for item in rows:
                    result_list.append(str(item))
            except Exception as ex:
                result_list.append( '执行SQL语句失败!'+ str(ex) )

            if len(str(result_list)) > 1000:
                checkmsg = str(result_list)[0:990]+"..."
            else:
                checkmsg = str(result_list)

            sql = "update yw_lqerp_check_everyday set check_date=%s, check_msg=%s where id=%s "
            cur.execute(sql, (datetime.datetime.now(), checkmsg, db_id))
        sqlserver_conn.close()

        sql="insert into yw_lqerp_check_everyday_his select * from yw_lqerp_check_everyday where check_state='1'"
        cur.execute(sql)
        cur.close()

        submit_power = {"show": True, "disabled": False} #放开提交按钮

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": {
                "tableData": tableData,
                "submit_power": submit_power,
            },
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#产品送样台账新增--
def sy_list_add( request ):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    def SqlServer_Conn():
        sqlserver_conn = None
        try:
            sqlserver_conn = pymssql.connect(server='10.10.1.250', user='sa', password='luyao123KEJI',
                                             database="db_18",
                                             timeout=20, autocommit=True)  # 获取连接  #sqlserver数据库链接句柄
        except Exception as ex:
            log.info(str(ex))

        return sqlserver_conn

    try:

        cur = connection.cursor()  # 创建游标

        sql="insert into yw_lqerp_sy_list(tran_date,user_id,bom_no,prd_name,pcb_version,install_version,plan_no,cust_name," \
            "send_date,use_zone, prd_num, change_flag, gw_id_relation, pilot_test_report, prodtest_log, metertest_log, note, state ) " \
            "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ) "
        cur.execute(sql, (datetime.datetime.now(), public.user_id, form_var.get('bom_no'), form_var.get('prd_name'),
                    form_var.get('pcb_version'), form_var.get('install_version'), form_var.get('plan_no'),
                    form_var.get('cust_name'), form_var.get('send_date'), form_var.get('use_zone'), form_var.get('prd_num'),
                    form_var.get('change_flag'), str(form_var.get( 'gw_id_relation')), str(form_var.get('pilot_test_report')),
                    str(form_var.get('prodtest_log')), str(form_var.get('metertest_log')), form_var.get('note'), '0' ) )
        cur.close()
        form_var['state'] = '0'
        form_var['submit_power'] = {"show": True, "disabled": False} #放开提交按钮

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

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


#送样台账更新--
def sy_list_update( request ):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    try:
        cur = connection.cursor()  # 创建游标
        # 获取用户所属的机构
        sql = "select distinct b.org_name from sys_user_org a, sys_org b where a.org_id=b.ORG_ID and a.user_id='%s'" % public.user_id
        cur.execute(sql)
        rows = cur.fetchall()
        orglist=[]
        for item in rows:
            orglist.append(item[0])

        log.info('所属机构列表:' + str(orglist), extra={'ptlsh': public.req_seq})
        flag = False
        if '中试部' in  orglist:
            sql="update yw_lqerp_sy_list set tran_date='%s', user_id=%s ,prd_num=%s, send_date='%s', change_flag='%s', gw_id_relation='%s', " \
                "pilot_test_report='%s',prodtest_log='%s',metertest_log='%s', state='1', note='%s' where id= %s " % \
                (datetime.datetime.now(), public.user_id, form_var.get('prd_num'), form_var.get('send_date'), form_var.get('change_flag'),
                 str(form_var.get('gw_id_relation')), str(form_var.get('pilot_test_report')), str(form_var.get('prodtest_log')),
                 str(form_var.get('metertest_log')), form_var.get('note') , form_var.get('id'))
            log.info('中试部更新SQL:' + sql, extra={'ptlsh':public.req_seq})
            cur.execute(sql)
            flag = True
        if '质控部' in orglist:
            sql = "update yw_lqerp_sy_list set tran_date='%s', user_id=%s ,prd_num=%s, send_date='%s', change_flag='%s'," \
                  "prd_picture='%s', pack_picture='%s',deli_insp_report='%s', state='2', note='%s' where id= %s " % \
                  (datetime.datetime.now(), public.user_id, form_var.get('prd_num'), form_var.get('send_date'),
                   form_var.get('change_flag'), str(form_var.get('prd_picture')), str(form_var.get('pack_picture')),
                   str(form_var.get('deli_insp_report')), form_var.get('note'), form_var.get('id'))
            log.info('质控部更新SQL:' + sql, extra={'ptlsh':public.req_seq})
            cur.execute(sql)
            flag = True
        if '市场部' in orglist:
            sql = "update yw_lqerp_sy_list set tran_date='%s', user_id=%s , saler='%s', consignee_name='%s', " \
                  "consignee_tel='%s',consignee_addr='%s', state='3', note='%s' where id= %s " % \
                  (datetime.datetime.now(), public.user_id, form_var.get('saler'), form_var.get('consignee_name'),
                   form_var.get('consignee_tel'), str(form_var.get('consignee_addr')), form_var.get('note'), form_var.get('id'))
            log.info('市场部更新SQL:' + sql, extra={'ptlsh':public.req_seq})
            cur.execute(sql)
            flag = True
        if not flag: #其它部门只有查询权限
            public.respcode, public.respmsg = "500293", "无更新数据权限!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur.close()

        body['form_var'] = form_var

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#根据BOM号查询关键元器件清单
def CriticalCompList_Gen( request ):
    log = public.logger
    body = public.req_body

    form_data = body.get('form_data')
    form_var = body.get('form_var')
    if not form_var and not form_data:
        form_var = {}
        form_var['bomfile_model'] = 'ZH'
        form_var["bomfile_model_options"] = [
            {
                "key": "ZH",
                "value": "中慧模板"
            },
            {
                "key": "HT",
                "value": "航天模板"
            }
        ]
        form_var['bom_no'] = ""
        form_var['plan_no'] = ""
        form_var['use_zone'] = ""
        form_var['bom_name'] = ""
        form_var['bom_spc'] = ""
        for i in range(1,11):
            form_var['prd_made%s' % i] = "-"
            form_var['prd_type%s' % i] = "-"
            form_var['prd_spc%s' % i] = "-"
            form_var['prd_nature%s' % i] = "-"
        body['form_var'] = form_var
        body['form_data'] = form_var
        public.respcode, public.respmsg = "000000", "交易成功!"
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body,
        }
        s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
        public.respinfo = HttpResponse(s)
        return public.respinfo

    if form_var:
        bom_no = form_var.get('bom_no')
    if form_data:
        form_var={}
        form_var['bomfile_model']='ZH'
        form_var["bomfile_model_options"] = [
            {
                "key": "ZH",
                "value": "中慧模板"
            },
            {
                "key": "HT",
                "value": "航天模板"
            }
        ]
        bom_no = form_data.get('prd_key_components')

    form_var['bom_no']=bom_no

    if not form_var['bom_no']:
        public.respcode, public.respmsg = "303010", "配方号不可为空!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo
    #获取电阻电容的区间
    def getdzdrinfo(bom_dict={}):
        log = public.logger
        # 片式电阻, 贴片电容
        dz_maxfz = ''
        dz_minfz = ''
        dz_maxgg = ''
        dz_mingg = ''

        dr_maxfz = ''
        dr_minfz = ''
        dr_maxgg = ''
        dr_mingg = ''
        try:
            for item in bom_dict:
                if bom_dict[item][0] == '贴片电阻':
                    itemtemp = bom_dict[item][1].upper()
                    # 获取最大封装和最小封装
                    tempfz = itemtemp.split('-')[0]
                    if not dz_maxfz:
                        dz_maxfz = tempfz
                    if not dz_minfz:
                        dz_minfz = tempfz
                    if float(dz_maxfz) < float(tempfz):
                        dz_maxfz = tempfz
                    if float(dz_minfz) > float(tempfz):
                        dz_minfz = tempfz

                    # 获取最大规格和最小规格
                    tempgg = itemtemp.split('-')[1].split('Ω')[0]
                    if not dz_maxgg:
                        dz_maxgg = tempgg
                    if not dz_mingg:
                        dz_mingg = tempgg

                    if 'K' not in tempgg and 'M' not in tempgg:  # 是最小单位
                        if 'K' not in dz_maxgg and 'M' not in dz_maxgg:  # 也是最小单位
                            if float(dz_maxgg) < float(tempgg):
                                dz_maxgg = tempgg
                        if 'K' not in dz_mingg and 'M' not in dz_mingg:  # 也是最小单位
                            if float(dz_mingg) > float(tempgg):
                                dz_mingg = tempgg
                        else:
                            dz_mingg = tempgg
                    elif tempgg[-1] in ['K']:  # 当前规格的单位是K
                        if 'K' not in dz_maxgg and 'M' not in dz_maxgg:  # 最大规格是K或者M
                            dz_maxgg = tempgg
                        elif 'K' in dz_maxgg:  # 最大规格都是K
                            if float(dz_maxgg[:-1]) < float(tempgg[:-1]):
                                dz_maxgg = tempgg

                        if 'K' in dz_mingg:
                            if float(dz_mingg[:-1]) > float(tempgg[:-1]):
                                dz_mingg = tempgg
                        elif 'M' in dz_mingg:
                            dz_mingg = tempgg

                    elif tempgg[-1] in ['M']:
                        if 'M' not in dz_maxgg:  # 最大规格不是M
                            dz_maxgg = tempgg
                        elif 'M' in dz_maxgg:  # 最大规格都是M
                            if float(dz_maxgg[:-1]) < float(tempgg[:-1]):
                                dz_maxgg = tempgg

                        if 'M' in dz_mingg:
                            if float(dz_mingg[:-1]) > float(tempgg[:-1]):
                                dz_mingg = tempgg

                if bom_dict[item][0] == '贴片电容':
                    itemtemp = bom_dict[item][1].lower()
                    # 获取最大封装和最小封装
                    tempfz = itemtemp.split('-')[0]
                    if not dr_maxfz:
                        dr_maxfz = tempfz
                    if not dr_minfz:
                        dr_minfz = tempfz
                    if float(dr_maxfz) < float(tempfz):
                        dr_maxfz = tempfz
                    if float(dr_minfz) > float(tempfz):
                        dr_minfz = tempfz

                    # 获取最大规格和最小规格
                    tempgg = itemtemp.split('-')[1].split('/')[0].lower()
                    if not dr_maxgg:
                        dr_maxgg = tempgg
                    if not dr_mingg:
                        dr_mingg = tempgg

                    if (dr_maxgg[-2:] == 'pf' and tempgg[-2:] in ['nf', 'uf']) \
                            or (dr_maxgg[-2:] == 'nf' and tempgg[-2:] == 'uf'):
                        dr_maxgg = tempgg
                    elif dr_maxgg[-2:] == tempgg[-2:]:
                        if float(dr_maxgg[:-2]) < float(tempgg[:-2]):
                            dr_maxgg = tempgg

                    if (dr_mingg[-2:] == 'uf' and tempgg[-2:] in ['nf', 'pf']) or (
                                    dr_mingg[-2:] == 'nf' and tempgg[-2:] == 'pf'):
                        dr_mingg = tempgg
                    elif dr_mingg[-2:] == tempgg[-2:]:
                        if dr_mingg[:-2] == '0':
                            dr_mingg = tempgg
                        elif float(dr_mingg[:-2]) > float(tempgg[:-2]):
                            dr_mingg = tempgg
            if dr_maxgg:
                dr_maxgg = dr_maxgg.replace('f', 'F')
            if dr_mingg:
                dr_mingg = dr_mingg.replace('f', 'F')

        except Exception as ex:
            log.info("获取电阻电容数据失败：" + str(ex) + "，原数据:" + itemtemp, exc_info=True)

        dzfz = '0402-1206'
        dzgg = '0Ω-1MΩ'
        drfz = '0402-0805'
        drgg = '18pF-22uF'

        if dz_maxfz and dz_minfz:
            if dz_maxfz == dz_minfz:
                dzfz = dz_maxfz
            else:
                dzfz = dz_minfz + '-' + dz_maxfz
        if dr_maxfz and dr_minfz:
            if dr_maxfz == dr_minfz:
                drfz = dr_maxfz
            else:
                drfz = dr_minfz + '-' + dr_maxfz
        if dz_maxgg and dz_mingg:
            if dz_maxgg == dz_mingg:
                dzgg = dz_maxgg + 'Ω'
            else:
                dzgg = dz_mingg + 'Ω' + '-' + dz_maxgg + 'Ω'
        if dr_maxgg and dr_mingg:
            if dr_maxgg == dr_mingg:
                drgg = dr_maxgg
            else:
                drgg = dr_mingg + '-' + dr_maxgg

        return dzfz, dzgg, drfz, drgg

    #连接erp数据库
    try:
        sqlserver_conn = pymssql.connect(server='10.10.1.250',
                                         user='sa',
                                         password='luyao123KEJI',
                                         database="db_18",
                                         timeout=20,
                                         autocommit=True)  # sqlserver数据库链接句柄
        cursor = sqlserver_conn.cursor()  # 获取光标
    except Exception as ex:
        log.info(str(ex))
        # log.info('连接远程数据库成功:' + str(datetime.datetime.now()))

    try:
        # 查询货品名称和规格：
        sql = "select name, spc, cls_date from MF_BOM where BOM_NO=%s "
        cursor.execute(sql, bom_no)
        row = cursor.fetchone()
        if not row:
            sqlserver_conn.close()
            log.error("配方号不存在!", exc_info=True, extra={'ptlsh':public.req_seq})
            public.respcode, public.respmsg = "672722", "配方号不存在!"
            public.respinfo = HttpResponse( public.setrespinfo() )
            return public.respinfo

        form_var['bom_name'] = row[0]
        form_var['bom_spc'] = row[1]
        if row[2]:
            db_cls_date = row[2].strftime("%Y-%m-%d")
        else:
            db_cls_date = '2000-01-01'

            #递归 查询节点层级
        sql = " WITH CTE AS ( SELECT *,1 AS [Level] FROM TF_BOM WHERE id_no is not null and BOM_NO='%s' " \
              " UNION ALL " \
              " SELECT G.*,CTE.Level+1 FROM TF_BOM as G JOIN CTE ON CTE.ID_NO =G.BOM_NO ) " \
              " SELECT a.prd_no, b.name, b.SPC, a.id_no,level FROM CTE a, prdt b where a.prd_no=b.prd_no" % (bom_no)
        log.info(sql, extra={'ptlsh':public.req_seq})
        cursor.execute(sql)
        rows = cursor.fetchall()
        print(rows)
        if not rows:
            sqlserver_conn.close()
            log.error("配方号不存在!", exc_info=True, extra={'ptlsh':public.req_seq})
            public.respcode, public.respmsg = "672722", "配方号不存在!"
            public.respinfo = HttpResponse( public.setrespinfo() )
            return public.respinfo

        bom_dict={}
        for item in rows:
            bom_dict[ item[0] ] = [item[1], item[2]]

        sqlserver_conn.close()
    except Exception as ex:
        log.error("查询ERP数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        sqlserver_conn.close()
        public.respcode, public.respmsg = "672729", "查询ERP数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    cur = connection.cursor()  # 创建游标

    try:
        CriticalCompList=[]
        #开始对元器件清单赋值:
        if db_cls_date > '2020-11-23': #在这个日期之前的电源芯片是时科的，之后的是钰泰的
            sql="select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg " \
                "where prd_name='电源' order by insert_time desc"
        else:
            sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg " \
                  "where prd_name='电源' order by insert_time asc"

        cur.execute(sql)
        rows = cur.fetchall()
        flag=False
        for item in rows:
            if item[0] in bom_dict.keys():
                flag = True
                form_var['prd_made1'] = item[2]
                form_var['prd_type1'] = item[3]
                form_var['prd_spc1'] = item[4]
                form_var['prd_nature1'] = item[5]
                break
        if flag == False:
            form_var['prd_made1'] = "-"
            form_var['prd_type1'] = "-"
            form_var['prd_spc1'] = "-"
            form_var['prd_nature1'] = "-"

        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='主控CPU'"
        cur.execute(sql)
        rows = cur.fetchall()
        flag = False
        for item in rows:
            if item[0] in bom_dict.keys():
                flag = True
                # temdict = {"seq_no": 2, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                #            "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级"}
                # CriticalCompList.append(temdict)
                form_var['prd_made2'] = item[2]
                form_var['prd_type2'] = item[3]
                form_var['prd_spc2'] = item[4]
                form_var['prd_nature2'] = item[5]
                break
        if flag == False:
            # temdict = {"seq_no": 2, "prd_no": "2", "prd_name": "主控CPU", "prd_made": "-", "prd_type": "-",
            #            "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
            # CriticalCompList.append(temdict)
            form_var['prd_made2'] = "-"
            form_var['prd_type2'] = "-"
            form_var['prd_spc2'] = "-"
            form_var['prd_nature2'] = "-"


        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='存储器'"
        cur.execute(sql)
        rows = cur.fetchall()
        flag = False
        for item in rows:
            if item[0] in bom_dict.keys():
                flag = True
                form_var['prd_made3'] = item[2]
                form_var['prd_type3'] = item[3]
                form_var['prd_spc3'] = item[4]
                form_var['prd_nature3'] = item[5]
                break
        if flag == False:
            form_var['prd_made3'] = "-"
            form_var['prd_type3'] = "-"
            form_var['prd_spc3'] = "-"
            form_var['prd_nature3'] = "-"

        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='超级电容'"
        cur.execute(sql)
        rows = cur.fetchall()
        flag = False
        for item in rows:
            if item[0] in bom_dict.keys():
                flag = True
                form_var['prd_made4'] = item[2]
                form_var['prd_type4'] = item[3]
                form_var['prd_spc4'] = item[4]
                form_var['prd_nature4'] = item[5]
                break
        if flag == False:
            form_var['prd_made4'] = "-"
            form_var['prd_type4'] = "-"
            form_var['prd_spc4'] = "-"
            form_var['prd_nature4'] = "-"

        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='电解电容'"
        cur.execute(sql)
        rows = cur.fetchall()
        flag = False
        for item in rows:
            if item[0] in bom_dict.keys():
                flag = True
                form_var['prd_made5'] = item[2]
                form_var['prd_type5'] = item[3]
                form_var['prd_spc5'] = item[4]
                form_var['prd_nature5'] = item[5]
                break
        if flag == False:
            form_var['prd_made5'] = "-"
            form_var['prd_type5'] = "-"
            form_var['prd_spc5'] = "-"
            form_var['prd_nature5'] = "-"

        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='晶振'"
        cur.execute(sql)
        rows = cur.fetchall()
        flag = False
        for item in rows:
            if item[0] in bom_dict.keys():
                flag = True
                form_var['prd_made6'] = item[2]
                form_var['prd_type6'] = item[3]
                form_var['prd_spc6'] = item[4]
                form_var['prd_nature6'] = item[5]
                break
        if flag == False:
            form_var['prd_made6'] = "-"
            form_var['prd_type6'] = "-"
            form_var['prd_spc6'] = "-"
            form_var['prd_nature6'] = "-"

        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='片式二极管'"
        cur.execute(sql)
        rows = cur.fetchall()
        flag = False
        for item in rows:
            if item[0] in bom_dict.keys():
                flag = True
                form_var['prd_made7'] = item[2]
                form_var['prd_type7'] = item[3]
                form_var['prd_spc7'] = item[4]
                form_var['prd_nature7'] = item[5]
                break
        if flag == False:
            form_var['prd_made7'] = "-"
            form_var['prd_type7'] = "-"
            form_var['prd_spc7'] = "-"
            form_var['prd_nature7'] = "-"


        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='光耦'"
        cur.execute(sql)
        rows = cur.fetchall()
        flag = False
        for item in rows:
            if item[0] in bom_dict.keys():
                flag = True
                form_var['prd_made8'] = item[2]
                form_var['prd_type8'] = item[3]
                form_var['prd_spc8'] = item[4]
                form_var['prd_nature8'] = item[5]
                break
        if flag == False:
            form_var['prd_made8'] = "-"
            form_var['prd_type8'] = "-"
            form_var['prd_spc8'] = "-"
            form_var['prd_nature8'] = "-"

        dz_fz,dz_gg,dr_fz,dr_gg = getdzdrinfo(bom_dict)

        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_no='99999998'" #片式电阻
        cur.execute(sql)
        row = cur.fetchone()
        # temdict = {"seq_no": 9, "prd_no": rows[0], "prd_name": rows[1], "prd_made": rows[2], "prd_type": "%s" % (dz_fz),
        #            "prd_spc":  "%s" % ( dz_gg ), "prd_nature": rows[5], "prd_level": "工业级"}
        # CriticalCompList.append(temdict)
        form_var['prd_made9'] = row[2]
        form_var['prd_type9'] = "%s" % (dz_fz)
        form_var['prd_spc9'] = "%s" % ( dz_gg )
        form_var['prd_nature9'] = row[5]


        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_no='99999999'" #片式电容
        cur.execute(sql)
        row = cur.fetchone()
        # temdict = {"seq_no": 10, "prd_no": rows[0], "prd_name": rows[1], "prd_made": rows[2], "prd_type":  "%s" % ( dr_fz ),
        #            "prd_spc":  "%s" % ( dr_gg ), "prd_nature": rows[5], "prd_level": "工业级"}
        # CriticalCompList.append(temdict)
        # form_var['criticalcomplist'] = CriticalCompList
        form_var['prd_made10'] = row[2]
        form_var['prd_type10'] = "%s" % (dr_fz)
        form_var['prd_spc10'] = "%s" % ( dr_gg )
        form_var['prd_nature10'] = row[5]

        form_var['plan_no'] = '-'
        form_var['use_zone'] = '-'
        if form_data and form_data.get('id'):
            #获取计划号和使用地区
            sql="select delivery_plan_no from yw_bill_stockup_body where id=%s"
            cur.execute(sql, form_data.get('id'))
            row = cur.fetchone()
            if row:
                form_var['plan_no'] = row[0]
        cur.close()


        body['form_var'] = form_var

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#ERP暂估数据导入
def erp_zgdata_excel_import(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var') #可能为空

    zgrk_file_id = form_var.get('zgrk_file')
    zgwjh_file_id = form_var.get('zgwjh_file')

    if  len(zgrk_file_id) == 0 or len(zgwjh_file_id) == 0:
        public.respcode, public.respmsg = "352991", "暂估入库文件和暂估未进货文件必须上传!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo
    zgwjh_file_id=zgwjh_file_id[0]
    zgrk_file_id = zgrk_file_id[0]

    try:
        cur = connection.cursor()  # 创建游标
        # 创建游标#根据fileid查询文件
        sql = "select md5_name from sys_fileup where file_id=%s"
        log.info(sql % (zgwjh_file_id) )
        cur.execute(sql, (zgwjh_file_id) )
        row = cur.fetchone()
        if not row:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "300333", "文件不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        zgwjh_file_md5name = row[0]
        #检查文件是否存在
        zgwjh_fullpathfile = public.localhome + "fileup/" + zgwjh_file_md5name
        log.info("检查文件是否存在!" + str(zgwjh_fullpathfile), extra={'ptlsh': public.req_seq})
        if not os.path.exists(zgwjh_fullpathfile):
            public.respcode, public.respmsg = "100134", "文件已过期!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 创建游标#根据fileid查询文件
        sql = "select md5_name from sys_fileup where file_id=%s"
        log.info(sql % (zgrk_file_id) )
        cur.execute(sql, (zgrk_file_id) )
        row = cur.fetchone()
        if not row:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "300333", "文件不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        zgrk_file_md5name = row[0]
        #检查文件是否存在
        zgrk_fullpathfile = public.localhome + "fileup/" + zgrk_file_md5name
        log.info("检查文件是否存在!" + str(zgrk_fullpathfile), extra={'ptlsh': public.req_seq})
        if not os.path.exists(zgrk_fullpathfile):
            public.respcode, public.respmsg = "100134", "文件已过期!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        #开始导入暂估入库数据
        sql = "delete from yw_payable_zg_rk"
        cur.execute(sql) #先清一下数据

        excel = xlrd.open_workbook(zgrk_fullpathfile, formatting_info=True)
        ws = excel.sheet_by_index(0)
        # 获取行列数
        row = ws.nrows
        start_row = 1;  # 从第二行开始读取数据 0是第一行
        total_row = row-1;  # 总行数
        for i in range(start_row, total_row):
            sql = "insert into yw_payable_zg_rk(cust_no, zg_dd, zg_no, prd_no, num, up, amt) values(%s, %s, %s, %s, %s, %s, %s)"
            tuple_date=[]
            for j in range(0,7):
                tmp = ws.cell_value(rowx=i, colx=j)
                if not tmp:
                    tmp = 0
                tuple_date.append( tmp )
            tuple_date=tuple(tuple_date)
            # log.info(sql % tuple_date)
            cur.execute(sql, tuple_date)
        zjrk_total = total_row

        # 开始导入暂估未进货数据
        sql = "delete from yw_payable_zg_wjh"
        cur.execute(sql)  # 先清一下数据

        excel = xlrd.open_workbook(zgwjh_fullpathfile, formatting_info=True)
        ws = excel.sheet_by_index(0)
        # 获取行列数
        row = ws.nrows
        start_row = 1;  # 从第二行开始读取数据 0是第一行
        total_row = row - 1;  # 总行数
        for i in range(start_row, total_row):
            sql = "insert into yw_payable_zg_wjh(cust_no, zg_dd, zg_no, prd_no, num, up) values(%s, %s, %s, %s, %s, %s)"
            tuple_date = []
            for j in range(0, 6):
                tmp = ws.cell_value(rowx=i, colx=j)
                if not tmp:
                    tmp = 0
                tuple_date.append(tmp)
            tuple_date = tuple(tuple_date)
            # log.info(sql % tuple_date)
            cur.execute(sql, tuple_date)
        zjwjh_total = total_row
        form_var['result']='导入结果：导入成功!共导入暂估入库明细[%s]条，暂估未进货明细[%s]条' % (zjrk_total, zjwjh_total)

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


