from admin_app.tranapp.formbutton import *
from admin_app.tranapp.transfer import *
from admin_app.tranapp.wamreport import *
from admin_app.tranapp.apply import *

###########################################################################################################
#表单自定义按钮，发起交易
#add by litz, 2020.04.10
#
###########################################################################################################

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
    # 特殊系统级交易,因为是配置出来的
    elif  public.tran_type in ['aboverole_cfg_select','role_cfg_select','role_cfg_create', 'role_fieldcfg_select',
                               'role_fieldcfg_create']:
        from admin_app.sys import userauth
        func_name = 'userauth.%s(request)' % public.tran_type
        log.info('---[%s]-begin---' % (func_name), extra={'ptlsh': public.req_seq})
        public.respinfo = eval(func_name)
        log.info('---[%s]-end----' % (func_name), extra={'ptlsh': public.req_seq})
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

#通用交易，执行配置的sql语句
def FORMTRAN_EXESQL(request ):
    log = public.logger
    body=public.req_body
    form_id = body.get('form_id')
    form_var = body.get('form_var')
    button_id = body.get('button_id')
    result_rowcount = 0 #最终影响行数
    if not button_id:
        log.info("按钮ID不存在!", extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "200011", "按钮ID不存在!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select form_sql from sys_form_cfg_info where form_id=%s"
        cur.execute(sql, form_id)
        row = cur.fetchone()
        form_sql=row[0]
        if form_sql:
            form_sql=json.loads(form_sql)
        sqllist=form_sql.get(button_id)
        for sql_item in sqllist.split(';'):
            log.info('初期SQL:'+str(sql_item), extra={'ptlsh': public.req_seq})
            if not sql_item:
                continue
            sql = public.SqlKeywordConver( sql_item, form_var )
            log.info('最终SQL:' + str(sql), extra={'ptlsh': public.req_seq})
            cur.execute( sql )
            if cur.rowcount > 0:
                result_rowcount = result_rowcount + cur.rowcount
        cur.close()
    except Exception as ex:
        log.error("SQL执行失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        if 'Duplicate' in str(ex) and 'PRIMARY' in str(ex):
            public.respcode, public.respmsg = "100200", "SQL执行失败!" + str(ex)
        else:
            public.respcode, public.respmsg = "100200", "SQL执行失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if result_rowcount > 0:
        public.respcode, public.respmsg = "000000", "交易成功!"
    else:
        public.respcode, public.respmsg = "200012", "无数据操作!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {}
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#通用删除交易，执行配置的sql语句
def TableDelete_EXESQL(request ):
    log = public.logger
    body=public.req_body
    # delete_append_sql = body.get('delete_append_sql') #删除的sql语句
    selected = body.get('selected') #删除的记录
    form_id =  body.get('form_id') #表单ID
    table_id =  body.get('table_id') #表格ID

    result_rowcount = 0 #最终影响行数
    if not selected:
        public.respcode, public.respmsg = "200311", "没有上送需要删除的记录!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_id:
        public.respcode, public.respmsg = "200311", "表单ID必须上送!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标

        sql = "select form_cfg from sys_form_cfg_info where form_id = %s"
        log.info(sql % form_id, extra={'ptlsh': public.req_seq})
        cur.execute(sql, form_id)
        row = cur.fetchone()
        if not row:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "100212", "表单配置不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        form_cfg = json.loads(row[0])

        # 递归获取表单中指定的表格删除数据的sql, 多个删除操作用分号分隔开
        def GetDelSQL(form_cfg, table_id):
            deletesql = ""
            for comp_item in form_cfg:
                if comp_item.get('children'):
                    deletesql = GetDelSQL( comp_item['children'], table_id )
                    if not deletesql:
                        continue
                    else:
                        return deletesql
                elif comp_item['type'] == 'null':
                    continue
                elif comp_item['id'] == table_id:
                    deletesql = comp_item['attrs'].get('delete_append_sql')
                    return deletesql
            return deletesql  # 没找到

        delete_append_sql = GetDelSQL(form_cfg, table_id)
        for data_item in selected:
            for sql_item in delete_append_sql.split(';'):
                log.info('初期SQL:'+str(sql_item), extra={'ptlsh': public.req_seq})
                if not sql_item:
                    continue
                sql = public.SqlKeywordConver( sql_item, data_item )

                for sqlitm in data_item:
                    old = "$[" + sqlitm + "]"
                    if sqlitm in data_item.keys():
                        new = "'" + str(data_item.get(sqlitm)) + "'"
                    else:
                        new = "''"
                    sql = sql.replace(old, new)
                log.info('real sql=' + str(sql), extra={'ptlsh': public.req_seq})

                log.info('最终SQL:' + str(sql), extra={'ptlsh': public.req_seq})
                cur.execute( sql )
                if cur.rowcount > 0:
                    result_rowcount = result_rowcount + cur.rowcount
        cur.close()
        log.info('影响记录行数:' + str(result_rowcount), extra={'ptlsh': public.req_seq})

    except Exception as ex:
        log.error("SQL执行失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        if 'Duplicate' in str(ex) and 'PRIMARY' in str(ex):
            public.respcode, public.respmsg = "100200", "SQL执行失败!" + str(ex)
        else:
            public.respcode, public.respmsg = "100200", "SQL执行失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    if result_rowcount > 0:
        public.respcode, public.respmsg = "000000", "交易成功!"
    else:
        public.respcode, public.respmsg = "200012", "无数据操作!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {}
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 根据选中的线别返回产线编号
def SN_Cfg_Select1(request):
    log = public.logger
    body = public.req_body
    prod_line = body.get('select_key')
    try:
        form_var=body.get('form_var')
        form_var['prod_line_num'] = '' #先清空

        cur = connection.cursor()  # 创建游标

        sql = "select dict_target from sys_ywty_dict where dict_name='Line_Num' and dict_code=%s"
        log.info(sql % (prod_line) )
        cur.execute(sql, (prod_line) )
        row = cur.fetchone()
        if not row:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "303011", "产线参数配置有误!"

            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo


        form_var['prod_line_num'] = row[0]

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


# 根据选中的配置项返回配置表达式
def SN_Cfg_Select2(request):
    log = public.logger
    body = public.req_body
    cfg_config = body.get('select_key')

    try:
        form_var=body.get('form_var')
        if cfg_config == 'LQ':
            form_var['sn_param'] = '[FF][YY][L]xxxxxxx'
            form_var['sn_ds'] = 'hex'
            sn_ds_power = {"show": True, "disabled": True}  # 不可选择
            form_var['sn_ds_power'] = sn_ds_power
            sn_param_power = {"show": True, "disabled": True}
            form_var['sn_param_power'] = sn_param_power
        elif cfg_config == 'ZH':
            form_var['sn_param'] = '[FF1]xxxxxxxxx'
            form_var['sn_ds'] = 'hex'
            sn_ds_power = {"show": True, "disabled": True}  # 不可选择
            form_var['sn_ds_power'] = sn_ds_power
            sn_param_power = {"show": True, "disabled": True}
            form_var['sn_param_power'] = sn_param_power
        else:
            form_var['sn_param'] = ''
            sn_ds_power = {"show": True, "disabled": False}  # 放开
            form_var['sn_ds_power'] = sn_ds_power
            sn_param_power = {"show": True, "disabled": False}
            form_var['sn_param_power'] = sn_param_power

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
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


#根据机构号获取此机构的有效用户信息
def Get_Org_UserList(request ):
    log = public.logger
    body=public.req_body
    form_id = body.get('form_id')
    form_var = body.get('form_var')
    select_key = body.get('select_key')

    if not select_key:
        log.info("选中机构不存在!", extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300011", "选中机构不存在!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select distinct b.USER_ID, c.USER_NAME from sys_org a, sys_user_org b, sys_user c " \
              "where a.org_id=b.org_id and c.USER_ID=b.USER_ID and a.ORG_SPELL='%s' " \
              "and a.ORG_SPELL is not null and c.STATE='1' " % (select_key)
        cur.execute(sql)
        rows = cur.fetchall()
        receiver_options = []

        for item in rows:
            subdict={ "key":item[0],"value":item[1] }
            receiver_options.append(subdict)
        cur.close()

        form_var['receiver_options']=receiver_options
    except Exception as ex:
        log.error("SQL执行失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        if 'Duplicate' in str(ex) and 'PRIMARY' in str(ex):
            public.respcode, public.respmsg = "100200", "SQL执行失败!" + str(ex)
        else:
            public.respcode, public.respmsg = "100200", "SQL执行失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "" #界面无感操作
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 根据月份获取该月考勤报表
def get_attend_report(request):
    log = public.logger
    body = public.req_body
    form_id = body.get('form_id')
    form_var = body.get('form_var')
    month_id = body.get('month_id')

    if not month_id:
        log.info("请先选择月份!", extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300012", "请先选择月份!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "SELECT department,job_num,user_name,state from yw_workflow_attend_report "\
              " where substr(natural_day,1,7) = %s"
        cur.execute(sql, month_id)
        rows = cur.fetchall()
        table_data = []

        for item in rows:

            subdict={ "key":item[0],"value":item[1] }
            table_data.append(subdict)
        cur.close()

        form_var['receiver_options']=table_data
    except Exception as ex:
        log.error("SQL执行失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        if 'Duplicate' in str(ex) and 'PRIMARY' in str(ex):
            public.respcode, public.respmsg = "100200", "SQL执行失败!" + str(ex)
        else:
            public.respcode, public.respmsg = "100200", "SQL执行失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "" #界面无感操作
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def attend_month_select(request):
    log = public.logger
    body = public.req_body
    month_id = body.get('select_key')
    user_id = public.user_id
    try:
        form_var = body.get('form_var')
        form_var['tabledata'] = []  # 先清空

        cur = connection.cursor()  # 创建游标

        sql = "SELECT department,job_num,user_name,natural_day,in_time,out_time,state " \
              "from yw_workflow_attend_report_mx "\
              "where SUBSTR(natural_day,1,7) = %s " \
              "AND job_num in (SELECT su.uid from sys_user su where su.user_id = %s)" \
              "ORDER BY natural_day"
        cur.execute(sql, (month_id, user_id))
        rows = cur.fetchall()
        if rows:
            tabledata = []
            for row in rows:
                dic_row = {
                   'department': row[0],
                   'job_num': row[1],
                   'user_name': row[2],
                   'natural_day': row[3],
                   'in_time': row[4],
                   'out_time': row[5],
                   'state': row[6]
                }
                tabledata.append(dic_row)
            form_var['tabledata'] = tabledata
            body['pageSize'] = 10
            body['table_total'] = len(tabledata)
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


def table_report_show(request):
    log = public.logger
    body = public.req_body
    month_id = body.get('select_key')
    user_id = public.user_id
    try:
        form_var = body.get('form_var')
        form_var['table_report_mx'] = []  # 先清空

        cur = connection.cursor()  # 创建游标

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


def staff_department_link(request):
    log = public.logger
    body = public.req_body
    staff_id = body.get('select_key')
    try:
        form_var = body.get('form_var')
        form_var['department'] = ''  # 先清空

        cur = connection.cursor()  # 创建游标

        sql = "select id,month_id,department,user_name,job_num,chid,zaot,gonx,tx,shij,bingj,chuc,sangj,cj,pcj," \
              "attend_days,work_days from yw_workflow_attend_report where month_id = %s limit 0,10"
        cur.execute(sql, staff_id)
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


def document_company_link_seclass(request):
    """文档参数配置，公司与二级目录联动"""
    log = public.logger
    body = public.req_body
    company = body.get('select_key')
    try:
        form_var = body.get('form_var')
        form_var['seclasstype'] = ''
        form_var['seclasstype_options'] = []
        form_var['trdclasstype'] = ''
        form_var['trdclasstype_options'] = []
        cur = connection.cursor()  # 创建游标
        sql = "select class_spell,class_name from yw_workflow_document_classtype where class_top = %s and class_rank=2"
        cur.execute(sql, company)
        rows = cur.fetchall()
        temp_dict_list = [{'key': k, 'value': v} for k, v in rows]
        form_var['seclasstype_options'] = temp_dict_list
        # 文件类型输入框
        form_var['file_type'] = company
    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    finally:
        cur.close()  # 关闭游标

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def document_seclass_link_trdclass(request):
    """文档参数配置，二级与三级目录联动"""
    log = public.logger
    body = public.req_body
    seclass = body.get('select_key')
    try:
        form_var = body.get('form_var')
        form_var['trdclasstype'] = ''
        form_var['trdclasstype_options'] = []

        cur = connection.cursor()  # 创建游标
        sql = "select class_spell,class_name from yw_workflow_document_classtype where class_top = %s and class_rank=3"
        cur.execute(sql, seclass)
        rows = cur.fetchall()
        temp_dict_list = [{'key': k, 'value': v} for k, v in rows]
        form_var['trdclasstype_options'] = temp_dict_list
        # 文件类型
        form_var['file_type'] = '%s_%s' % (form_var.get('company'), seclass)
    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    finally:
        cur.close()  # 关闭游标

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def document_trdclass_link_filetype(request):
    """文档参数配置，三级与文件类型联动"""
    log = public.logger
    body = public.req_body
    trdlass = body.get('select_key')
    try:
        form_var = body.get('form_var')
        # 文件类型
        form_var['file_type'] = '%s_%s_%s' % (form_var.get('company'), form_var.get('seclasstype'), trdlass)
    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
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