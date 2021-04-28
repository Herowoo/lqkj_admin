import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
from admin_app.sys import public_db
import os
import requests
import openpyxl

###########################################################################################################
#生产车间个性化函数
#add by litz, 2020.05.08
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


#生产日报表-新增
def gen_diary_report( request ):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    # 查询生产计划表计划号，制令单号
    def getplaninfo(nowdate, orderid, prodline):
        # 查询生产计划表计划号，制令单号
        sql = "select concat(plan_id,'-',order_id) as planorder, prd_no, prd_name from yw_project_plan_info " \
              "where order_id='%s' order by prod_date desc LIMIT 1" % (orderid)
        log.info("查询生产计划表计划号,制令单号:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            return row[0], row[1], row[2]
        else:
            return '0', '', ''

    try:
        prod_date = datetime.datetime.now().strftime('%Y-%m-%d')  # 报表查询日期
        begin_time =  form_var.get('begin_time')
        end_time = form_var.get('end_time')
        if not begin_time or not end_time:
            public.respcode, public.respmsg = "303310", "开始时间和结束时间必输!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        # 获取线别字典
        syscfg_prodline_dict = {}
        sql = "select dict_code, dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PLAN_INFO.PROD_LINE'"
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            syscfg_prodline_dict[item[0]] = item[1]

        #先删除历史数据--避免更新时重复增加数据
        sql = "insert into yw_project_prod_report_his select * from yw_project_prod_report where prod_date='%s' " \
              % (prod_date)  # 当天报表不重复就行
        log.info("先备份历史数据1:" + sql)
        cur.execute(sql)
        sql = "delete from yw_project_prod_report where prod_date='%s' " % (prod_date) #当天报表不重复就行
        log.info( "先删除历史数据2:" + sql )
        cur.execute(sql)

        #产测信息收集
        sql = "select Batch_Num, prod_line, Test_Result, count(1), min(insert_date), max(insert_date) " \
              "from yw_project_product_test_info where insert_date BETWEEN '%s' and '%s' " \
              "group by Batch_Num, prod_line, Test_Result" % (begin_time, end_time)
        log.info("产测信息收集:" + sql)
        cur.execute(sql)
        rows=cur.fetchall()
        for item in rows:
            db_order_id =item[0]
            db_prod_line = item[1]
            db_pass_flag = item[2]
            if db_pass_flag == "Pass":
                db_prod_num = item[3]
                db_prod_err_num = 0
            else:
                db_prod_num = 0
                db_prod_err_num = item[3]
            db_begin_prodtime= item[4]
            db_end_prodtime= item[5]

            db_planorder, db_prodcode, db_prodname = getplaninfo(prod_date, db_order_id, db_prod_line)
            if db_planorder != '0': #当日有生产计划
                insql = "insert into yw_project_prod_report(prod_date,plan_order,prod_line,prod_code,prod_name, prodtest_num, prodbad_num, " \
                        "operate_userid, operate_time, state, begin_prodtime, end_prodtime ) values('%s','%s','%s','%s','%s','%s','%s','%s','%s','0','%s','%s')" \
                          % (prod_date, db_planorder, db_prod_line, db_prodcode, db_prodname, db_prod_num, db_prod_err_num,
                             public.user_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), db_begin_prodtime, db_end_prodtime )
                cur.execute(insql)

        # 抄表信息收集
        sql = "select Batch_Num, prod_line, Test_Result, count(1), min(insert_date), max(insert_date) " \
              "from yw_project_meterread_test_info where insert_date BETWEEN '%s' and '%s' " \
              "group by Batch_Num, prod_line, Test_Result" % (begin_time, end_time)
        log.info("抄表信息收集:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            db_order_id = item[0]
            db_prod_line = item[1]
            db_pass_flag = item[2]
            if db_pass_flag == "Pass":
                db_prod_num = item[3]
                db_prod_err_num = 0
            else:
                db_prod_num = 0
                db_prod_err_num = item[3]
            db_begin_prodtime = item[4]
            db_end_prodtime = item[5]

            db_planorder, db_prodcode, db_prodname = getplaninfo(prod_date, db_order_id, db_prod_line)
            if db_planorder != '0':  # 当日有生产计划
                insql = "insert into yw_project_prod_report(prod_date,plan_order,prod_line,prod_code,prod_name, prodmeter_num, prodbad_num, " \
                        "operate_userid, operate_time, state, begin_prodtime, end_prodtime ) values('%s','%s','%s','%s','%s','%s','%s','%s','%s','0','%s','%s')" \
                        % ( prod_date, db_planorder, db_prod_line, db_prodcode, db_prodname, db_prod_num, db_prod_err_num,
                        public.user_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), db_begin_prodtime, db_end_prodtime)
                cur.execute(insql)

        # 装壳信息收集
        sql = "select order_id, prod_line, state, count(1), min(tran_date), max(tran_date) " \
              "from yw_project_snid_detail where tran_date BETWEEN '%s' and '%s' " \
              "group by order_id, prod_line, state" % (begin_time, end_time)
        log.info("装壳信息收集:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            db_order_id = item[0]
            db_prod_line = item[1]
            db_pass_flag = item[2]
            if db_pass_flag == "1":
                db_prod_num = item[3]
                db_prod_err_num = 0
            else:
                db_prod_num = 0
                db_prod_err_num = item[3]
            db_begin_prodtime = item[4]
            db_end_prodtime = item[5]

            db_planorder, db_prodcode, db_prodname = getplaninfo(prod_date, db_order_id, db_prod_line)
            if db_planorder != '0':  # 当日有生产计划
                insql = "insert into yw_project_prod_report(prod_date, plan_order, prod_line, prod_code, prod_name, prodsnid_num, prodbad_num," \
                        "operate_userid, operate_time, state, begin_prodtime, end_prodtime ) values('%s','%s','%s','%s','%s','%s','%s','%s','%s','0','%s','%s')" \
                        % ( prod_date, db_planorder, db_prod_line, db_prodcode, db_prodname, db_prod_num, db_prod_err_num, public.user_id,
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), db_begin_prodtime, db_end_prodtime)
                cur.execute(insql)

        # 装箱信息收集
        sql = "select order_id, prod_line, state, count(1), min(tran_date), max(tran_date) " \
              "from yw_project_boxing_info where tran_date BETWEEN '%s' and '%s' " \
              "group by order_id, prod_line, state" % (begin_time, end_time)
        log.info("装箱信息收集:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            db_order_id = item[0]
            db_prod_line = item[1]
            db_pass_flag = item[2]
            if db_pass_flag == "1":
                db_prod_num = item[3]
                db_prod_err_num = 0
            else:
                db_prod_num = 0
                db_prod_err_num = item[3]
            db_begin_prodtime = item[4]
            db_end_prodtime = item[5]

            db_planorder, db_prodcode, db_prodname = getplaninfo(prod_date, db_order_id, db_prod_line)
            if db_planorder != '0':  # 当日有生产计划
                insql = "insert into yw_project_prod_report(prod_date, plan_order, prod_line, prod_code, prod_name, prodbox_num, prodbad_num," \
                        "operate_userid, operate_time, state, begin_prodtime, end_prodtime ) values('%s','%s','%s','%s','%s','%s','%s','%s','%s','0','%s','%s')" \
                        % (prod_date, db_planorder, db_prod_line, db_prodcode, db_prodname, db_prod_num, db_prod_err_num, public.user_id,
                           datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), db_begin_prodtime, db_end_prodtime )
                cur.execute(insql)

        # 汇总信息查询
        tableData = []
        sql = "select plan_order, prod_line, prod_code,prod_name, min(begin_prodtime),max(end_prodtime), " \
              "sum(prodtest_num), sum(prodsnid_num), sum(prodmeter_num), sum(prodbox_num), sum(prodbad_num) " \
              "from yw_project_prod_report where prod_date='%s' and operate_userid='%s' " \
              "group by plan_order, prod_line, prod_code, prod_name" % (prod_date, public.user_id)
        log.info("汇总信息查询:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        line_info=[]
        line_prod=[]
        for item in rows:
            info_item={}
            info_item['plan_order'] = item[0]
            # info_item['prod_line'] = item[1]
            info_item['prod_line'] = syscfg_prodline_dict.get(item[1], '多功能线')
            info_item['prod_code'] = item[2]
            info_item['prod_name'] = item[3]
            info_item['prod_lineleader'] = '胡广辉'
            info_item['ipqcer'] = '吴占垒'
            info_item['person_num'] = '0' #使用人数

            #计划生产数量
            info_item['prod_plannum'] = '0'
            if '-' in info_item['plan_order']:
                orderid = info_item['plan_order'].split('-')[1]

                sql = "select sum(today_plan_num) from yw_project_plan_info " \
                      "where order_id='%s'and prod_date BETWEEN '%s' and '%s' " % (orderid, begin_time, end_time)
                log.info(sql)
                cur.execute(sql)
                row = cur.fetchone()
                if row and row[0]:
                    info_item['prod_plannum'] = str(row[0])
            else:
                orderid = '0'
                #标准产能
            if  info_item['prod_line'] == '产测一线':
                info_item['stand_cap'] = '600'
            elif info_item['prod_line'] == '产测二线':
                info_item['stand_cap'] = '1200'
            elif info_item['prod_line'] == '产测三线':
                info_item['stand_cap'] = '1100'
            elif info_item['prod_line'] == '产测四线':
                info_item['stand_cap'] = '500'
            elif info_item['prod_line'] == '产测五线':
                info_item['stand_cap'] = '400'
            elif info_item['prod_line'] == '产测六线':
                info_item['stand_cap'] = '100'
            else:
                info_item['stand_cap'] = '0'

            #实际产能
            #计算开始时间和结束时间的时间差：
            diffsec = ( item[5] - item[4] ).seconds
            usehour = round( diffsec/3600, 1)
            #中午1.5h，晚上0.5h，休息时长扣除
            if usehour > 1.5 \
                    and "11:30:00" < item[4].strftime('%H:%M:%S') and "13:30:00" > item[5].strftime('%H:%M:%S'):
                usehour = usehour - 1.5
            if usehour > 0.5 \
                    and "18:00:00" < item[4].strftime('%H:%M:%S') and "18:30:00" > item[5].strftime('%H:%M:%S'):
                usehour = usehour - 0.5
            if item[9] and item[9] > 0 and usehour> 0:
                info_item['act_cap'] = str( round( int(item[9])/usehour, 0) )
            else:
                info_item['act_cap'] = '0'
            line_info.append(info_item)

            prod_item = {}
            prod_item['plan_order'] = orderid
            prod_item['prod_line'] = syscfg_prodline_dict.get(item[1], '多功能线')
            # prod_item['prod_line'] = item[1]
            prod_item['prod_code'] = item[2]
            prod_item['begin_prodtime'] = item[4].strftime('%m-%d %H:%M:%S')
            prod_item['end_prodtime'] = item[5].strftime('%m-%d %H:%M:%S')

            #使用时长：
            prod_item['time_long'] = str(usehour) + '小时'
            prod_item['invest_num'] = '0' #投板数量
            if item[6]:
                prod_item['prodtest_num'] = item[6]
            else:
                prod_item['prodtest_num'] = '0'
            if item[7]:
                prod_item['prodsnid_num'] = item[7]
            else:
                prod_item['prodsnid_num'] = '0'
            if item[8]:
                prod_item['prodmeter_num'] = item[8]
            else:
                prod_item['prodmeter_num'] = '0'
            if item[9]:
                prod_item['prodbox_num'] = item[9]
            else:
                prod_item['prodbox_num'] = '0'
            if item[10]:
                prod_item['prodbad_num'] = item[10]
            else:
                prod_item['prodbad_num'] = '0'

            #计算直通率
            sql = "select sum(prod_num),sum(prod_direct_num) from yw_project_collect_info_direct_err " \
                  "where order_id='%s' and prod_line='%s' and time_day BETWEEN '%s' and '%s'" \
                  % (orderid, item[1], begin_time[0:10], end_time[0:10])
            log.info('计算直通率:'+sql, extra={'ptlsh':public.req_seq})
            cur.execute(sql)
            row =  cur.fetchone()
            if row and row[0]:
                prod_item['prod_directrate'] = str( round(row[1]*100/row[0], 2) )
            else:
                prod_item['prod_directrate'] = '0'
            line_prod.append(prod_item)

        #必须先打印生产巡线问题报表
        sql = "select 1 from yw_project_prod_problem_print where DATE_FORMAT(tran_date,'%%Y-%%m-%%d')='%s'" \
              % datetime.datetime.now().strftime("%Y-%m-%d")
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            print_power = {"show": True, "disabled": True}
        else:
            print_power = {"show": True, "disabled": False}  # 放开提交按钮

        cur.close()
        create_user = '编制：' + public_db.get_username( public.user_id) + '   ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


        form_var['line_prod'] = line_prod
        form_var['line_info'] = line_info
        form_var['create_user'] = create_user
        form_var['print_power'] = print_power
        body['form_var'] = form_var

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "生成数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 生产日报表-提交
def save_diary_report(request):
    log = public.logger
    body=public.req_body
    form_var=body.get('form_var')
    tableData = form_var.get('tableData')

    try:
        prod_date = form_var.get('prod_date')  # 生产日期
        cur = connection.cursor()  # 创建游标
        sql="update yw_project_prod_report set state='1' where prod_date='%s' " % (prod_date)
        cur.execute(sql)
        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": {
                "prod_date": form_var.get("prod_date"),
                "tableData": tableData,
            }
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 生产日报表-查询
def get_diary_report( request ):
    log = public.logger
    body=public.req_body
    form_var=body.get('form_var')

    try:
        prod_date = form_var.get('prod_date')  # 生产日期
        prod_state = '0' #是否已打印
        create_user='制单人：'
        cur = connection.cursor()  # 创建游标

        # 获取线别字典
        syscfg_prodline_dict = {}
        sql = "select dict_code, dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PLAN_INFO.PROD_LINE'"
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            syscfg_prodline_dict[item[0]] = item[1]

        # 汇总信息查询
        tableData = []
        sql = "select plan_order,prod_line,prod_code,prod_name, begin_prodtime , end_prodtime, prodtest_num,prodmeter_num," \
              "prodsnid_num, prodbox_num, prodbad_num, state, operate_userid, operate_time, check_userid, check_time " \
              "from yw_project_prod_report where prod_date='%s' " % (
              prod_date)
        log.info("汇总信息查询:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        create_time = None
        check_time = None
        for item in rows:
            prod_item = {}
            prod_item['prod_date'] = prod_date
            prod_item['plan_order'] = item[0]
            prod_item['prod_line'] = syscfg_prodline_dict.get(item[1], '未配置线别')
            prod_item['prod_code'] = item[2]
            prod_item['prod_name'] = item[3]
            prod_item['begin_prodtime'] = item[4]
            prod_item['end_prodtime'] = item[5]
            prod_item['prodtest_num'] = item[6]
            prod_item['prodmeter_num'] = item[7]
            prod_item['prodsnid_num'] = item[8]
            prod_item['prodbox_num'] = item[9]
            prod_item['prodbad_num'] = item[10]
            prod_state = item[11]
            create_user = item[12]
            create_time = item[13]
            check_user = item[12]
            check_time = item[13]
            tableData.append(prod_item)

        #根据user_id获取user_name
        if create_time:
            create_user = '编制：' + public_db.get_username(create_user) + '   ' + create_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            create_user = '编制：'
        if check_time:
            check_user = '复核：' + public_db.get_username(check_user) + '   ' + check_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            check_user = '复核：'

        public.respcode, public.respmsg = "000000", "交易成功!"
        if prod_state in ['2','3']: #已审核或已打印
            print_power = {"show": True, "disabled": False}
            apply_power = {"show": True, "disabled": True}
        if prod_state in ['0']: #制单人未提交审核
            public.respcode, public.respmsg = "000000", "制单人未提交审核!"
            create_user = '编制：'
            check_user = '复核：'
            print_power = {"show": True, "disabled": True}
            apply_power = {"show": True, "disabled": True}
        else:
            check_user = '复核：'
            print_power = {"show": True, "disabled": True}
            apply_power = {"show": True, "disabled": False}

        #必须先打印生产巡线问题报表
        sql = "select 1 from yw_project_prod_problem_print where DATE_FORMAT(t.tran_date,'%%Y-%%m-%%d')='%s'" \
              % datetime.datetime.now().strftime("%Y-%m-%d")
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            print_power = {"show": True, "disabled": True}

        cur.close()

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY":{
            "form_var": {
                "prod_date": form_var.get("prod_date"),
                "tableData": tableData,
                "apply_power": apply_power,
                "print_power": print_power,
                "print_date": "打印时间：" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "create_user": create_user,
                "check_user":check_user,
            }
        }
    }

    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 生产日报表-审核
def check_diary_report(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    tableData = form_var.get('tableData')
    try:
        prod_date = form_var.get('prod_date')  # 生产日期
        cur = connection.cursor()  # 创建游标
        sql="update yw_project_prod_report set state='2' where prod_date='%s' " % (prod_date)
        cur.execute(sql)

        cur.close()  # 关闭游标

        print_power = {"show": True, "disabled": False}
    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": form_var,
        }
    }
    json_data["BODY"]["form_var"]["print_power"] = print_power
    json_data["BODY"]["form_var"]["check_user"] =  '复核：' + public_db.get_username(public.user_id) + '   ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_data["BODY"]["form_var"]["print_date"] = "打印时间：" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 生产日报表-打印
def print_diary_report(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')
    tableData = form_var.get('tableData')
    try:
        prod_date = form_var.get('prod_date')  # 生产日期
        cur = connection.cursor()  # 创建游标

        sql="update yw_project_prod_report set state='3' where prod_date='%s' " % (prod_date)
        cur.execute(sql)
        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var": form_var,
        }
    }
    json_data["BODY"]["form_var"]["print_date"]="打印时间："+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 工站员工登陆,员工操作时先登陆
def prod_station_login(request):
    log = public.logger
    body = public.req_body
    user_id = body.get('user_id')
    user_passwd = body.get('user_passwd')
    computer_name = body.get('computer_name')
    computer_ip = body.get('computer_ip')

    try:

        cur = connection.cursor()  # 创建游标
        sql="select login_userpwd, login_username, state from yw_project_prodline_term_userinfo where login_userid=%s "
        cur.execute(sql, user_id)
        row=cur.fetchone()

        if not row:
            public.respcode, public.respmsg = "308921", "员工号不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        if user_passwd!=row[0]:
            public.respcode, public.respmsg = "308921", "密码错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if row[2] != '1':
            public.respcode, public.respmsg = "308921", "员工状态异常!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        user_name=row[1]


        #先强制签退原来的登陆信息
        sql = "update yw_project_prodline_term_login set state='0', logout_time=%s, snote=%s where computer_name=%s "
        cur.execute(sql, (datetime.datetime.now(), '有新登陆,强制签退!' ,computer_name) )
        # 登记新的登陆信息
        sql = "insert into yw_project_prodline_term_login(computer_name, computer_ip, prod_line, station_type, login_userid, login_username, login_ip, state)" \
              "values(%s,%s,%s,%s,%s,%s,%s,'1')"
        cur.execute(sql, (computer_name, computer_ip, body.get('prod_line'), body.get('station_type'), user_id, user_name, public.req_ip) )

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
        "BODY": {
            "user_name": user_name,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 管理员登陆操作
def prod_admin_login(request):
    log = public.logger
    body = public.req_body
    adminId = body.get('adminId')
    adminpwd = body.get('adminpwd')
    computer_name = body.get('computer_name')
    computer_ip = body.get('computer_ip')

    try:

        cur = connection.cursor()  # 创建游标
        sql="select login_userpwd, login_username, state " \
            "from yw_project_prodline_term_userinfo where user_type='admin' and login_userid=%s "
        cur.execute(sql, adminId)
        row=cur.fetchone()

        if not row:
            public.respcode, public.respmsg = "308921", "管理员不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        if adminpwd!=row[0]:
            public.respcode, public.respmsg = "308921", "密码错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if row[2] != '1':
            public.respcode, public.respmsg = "308921", "管理员状态异常!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        user_name=row[1]

        #
        # #先强制签退原来的登陆信息
        # sql = "update yw_project_prodline_term_login set state='0', logout_time=%s, snote=%s where computer_name=%s "
        # cur.execute(sql, (datetime.datetime.now(), '有新登陆,强制签退!' ,computer_name) )
        # # 登记新的登陆信息
        # sql = "insert into yw_project_prodline_term_login(computer_name, computer_ip, prod_line, station_type, login_userid, login_username, login_ip, state)" \
        #       "values(%s,%s,%s,%s,%s,%s,%s,'1')"
        # cur.execute(sql, (computer_name, computer_ip, body.get('prod_line'), body.get('station_type'), user_id, user_name, public.req_ip) )

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
        "BODY": {
            "user_name": user_name,
            "flags":"1", #0-密码错误, 1-密码正确
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 工站员工退出,员工下岗或换班
def prod_station_logout(request):
    log = public.logger
    body = public.req_body
    computer_name = body.get('computer_name')
    computer_ip = body.get('computer_ip')

    try:
        cur = connection.cursor()  # 创建游标
        sql="select login_username from yw_project_prodline_term_login where computer_name=%s and state='1'"
        cur.execute(sql, computer_name)
        row=cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "308922", "此工站未找到上岗数据!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        user_name=row[0]

        #签退登陆信息
        sql = "update yw_project_prodline_term_login set state='0', logout_time=%s, snote=%s where computer_name=%s and state='1'"
        cur.execute(sql, (datetime.datetime.now(), '用户主动签退!' ,computer_name) )

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
        "BODY": {
            "user_name": user_name,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 工站终端自启动后注册自己
def term_register(request):
    log = public.logger
    body = public.req_body
    computer_name = body.get('computer_name')
    computer_ip = body.get('computer_ip')

    try:
        cur = connection.cursor()  # 创建游标
        sql="select prod_line, station_type, app_filepath, cfg_filepath, state from yw_project_prodline_term_info " \
            "where computer_name=%s "
        cur.execute(sql, computer_name)
        row=cur.fetchone()

        if not row: #新终端，直接插入一条数据
            prod_line = ''
            station_type = ''
            app_filepath = ''
            cfg_filepath = ''
            sql = "insert into yw_project_prodline_term_info(computer_name, computer_ip, login_ip,state ) values( %s, %s, %s, %s)"
            cur.execute(sql, (computer_name, computer_ip, public.req_ip,'2') )
        else:
            prod_line = row[0]
            station_type = row[1]
            app_filepath = row[2]
            cfg_filepath = row[3]
            sql = "update yw_project_prodline_term_info set upd_time=%s, computer_ip=%s, login_ip=%s where computer_name=%s "
            cur.execute(sql, (datetime.datetime.now(), computer_ip, public.req_ip, computer_name) )

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
        "BODY": {
            "prod_line":prod_line,
            "station_type": station_type,
            "app_filepath": app_filepath,
            "cfg_filepath": cfg_filepath,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def cfgfile_show(request):
    log = public.logger
    body = public.req_body
    # form_data = body.get('form_data')
    # if not form_data:
    #     public.respcode, public.respmsg = "308932", "请求数据异常,无FORM_DATA!"
    #     public.respinfo = HttpResponse(public.setrespinfo())
    #     return public.respinfo
    try:
        cur = connection.cursor()  # 创建游标
        # if form_data.get('cfg_file'):
        #     file_id=form_data.get('cfg_file')[0]
        # sql = "select prod_line, station_type, app_filepath, cfg_filepath, state from yw_project_prodline_term_info " \
        #       "where computer_name=%s "
        # cur.execute(sql, computer_name)
        # row = cur.fetchone()
        md5filename="/home/admin/lqkj_admin/fileup/a9970a8fc08d46d0cace542782b5881c.ini"
        # 判断文件是否存在,存在不处理，不存在则写处
        if not os.path.exists(public.localhome + "fileup/" + md5filename):
            cur.close()  # 关闭游标
        file_object = open(md5filename)
        file_context = file_object.read()
        file_object.close()

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
        "BODY": {
            "form_var":{
                "file_id": 625,
                "file_context": file_context,
            }
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 工站开线
def prod_station_start(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    computer_name = form_var.get('computer_name')
    computer_ip = form_var.get('computer_ip')
    if not computer_name:
        public.respcode, public.respmsg = "308922", "工站电脑名称必须上送!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:

        cur = connection.cursor()  # 创建游标
        sql = "select computer_ip, computer_port from yw_project_prodline_term_info where computer_name=%s "
        cur.execute(sql, computer_name)
        row = cur.fetchone()

        if not row:
            public.respcode, public.respmsg = "308930", "终端不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        computer_ip = row[0]
        computer_port = row[1]
        if not computer_ip or not computer_port:
            public.respcode, public.respmsg = "308931", "终端IP或端口错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        body['sta_flag'] = '1'  # 1-启动,2-停止，3-暂停
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        url = 'http://' + str(computer_ip) + ':' + str(computer_port)
        json_data = json.dumps(json_data)
        resp_pkg = requests.post(url, json_data)
        log.info(resp_pkg.text, extra={'ptlsh': public.req_seq})
        resp_pkg = json.loads(resp_pkg.text)
        public.respcode, public.respmsg = resp_pkg['HEAD'].get('respcode'), resp_pkg['HEAD'].get('respmsg')

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

# 工站停线
def prod_station_stop(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    computer_name = form_var.get('computer_name')
    computer_ip = form_var.get('computer_ip')
    if not computer_name:
        public.respcode, public.respmsg = "308922", "工站电脑名称必须上送!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    try:

        cur = connection.cursor()  # 创建游标
        sql = "select computer_ip, computer_port from yw_project_prodline_term_info where computer_name=%s "
        cur.execute(sql, computer_name)
        row = cur.fetchone()

        if not row:
            public.respcode, public.respmsg = "308930", "终端不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        computer_ip = row[0]
        computer_port = row[1]
        if not computer_ip or not computer_port:
            public.respcode, public.respmsg = "308931", "终端IP或端口错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        body['sta_flag'] = '2'  # 1-启动,2-停止，3-暂停
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        url = 'http://' + str(computer_ip) + ':' + str(computer_port)
        json_data = json.dumps(json_data)
        resp_pkg = requests.post(url, json_data)
        log.info(resp_pkg.text, extra={'ptlsh': public.req_seq})
        resp_pkg = json.loads(resp_pkg.text)
        public.respcode, public.respmsg = resp_pkg['HEAD'].get('respcode'), resp_pkg['HEAD'].get('respmsg')

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

# 工站暂停
def prod_station_pause(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    computer_name = form_var.get('computer_name')
    computer_ip = form_var.get('computer_ip')
    if not computer_name:
        public.respcode, public.respmsg = "308922", "工站电脑名称必须上送!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    try:

        cur = connection.cursor()  # 创建游标
        sql = "select computer_ip, computer_port from yw_project_prodline_term_info where computer_name=%s "
        cur.execute(sql, computer_name)
        row = cur.fetchone()

        if not row:
            public.respcode, public.respmsg = "308930", "终端不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        computer_ip = row[0]
        computer_port = row[1]
        if not computer_ip or not computer_port:
            public.respcode, public.respmsg = "308931", "终端IP或端口错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        body['sta_flag'] = '3'  # 1-启动,2-停止，3-暂停
        json_data = {
            "HEAD": public.resphead_setvalue(),
            "BODY": body
        }
        url = 'http://' + str(computer_ip) + ':' + str(computer_port)
        json_data = json.dumps(json_data)
        resp_pkg = requests.post(url, json_data)
        log.info(resp_pkg.text, extra={'ptlsh': public.req_seq})
        resp_pkg = json.loads(resp_pkg.text)
        public.respcode, public.respmsg = resp_pkg['HEAD'].get('respcode'), resp_pkg['HEAD'].get('respmsg')

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

# 生产日报表明细--直通率统计
def get_directreport_detail(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        begin_date = form_var.get('begin_date', '2019-01-01')
        end_date = form_var.get('end_date', '2099-12-31')
        prod_line  = form_var.get('prod_line')
        station_type = form_var.get('station_type')


        cur = connection.cursor()  # 创建游标
        #先获取线别信息
        sql = "select dict_code, dict_target from sys_ywty_dict where dict_name='YW_PROJECT_PLAN_INFO.PROD_LINE'"
        cur.execute(sql)
        rows = cur.fetchall()
        dict_prodline = {}
        for item in rows:
            if prod_line:
                if prod_line == item[0]:
                    dict_prodline[item[0]]=item[1]
            else:
                dict_prodline[item[0]] = item[1]

        if not dict_prodline: #线别信息不存在
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "381922", "线别信息不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        direct_data = []
        for prodline in dict_prodline.keys():
            prodtest_direct_rate = 100
            if not station_type or station_type=='prodtest':  #产测直通率统计
                sql = "select count(1) from (select min(id),Board_SN,Test_Result,Test_Value from yw_project_product_test_info_his " \
                      "where DATE_FORMAT(insert_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(insert_date,'%%Y-%%m-%%d')<='%s' " \
                      "and prod_line='%s' group by Board_SN ) temp " \
                      "where (Test_Result!='Pass' and Test_Value!='unknown') " % (begin_date, end_date, prodline)
                cur.execute(sql)
                row = cur.fetchone()
                prodtest_firsterr_num = row[0]
                log.info('产测第一次失败数量:' + str(prodtest_firsterr_num), extra={'ptlsh': public.req_seq})

                sql = "select count(distinct Board_SN) from yw_project_product_test_info a where not EXISTS " \
                      "(select 1 from yw_project_product_test_info_his b where a.Board_SN=b.Board_SN) and " \
                      "DATE_FORMAT(a.insert_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(a.insert_date,'%%Y-%%m-%%d')<='%s' " \
                      "and a.prod_line='%s' and (a.Test_Result!='Pass' and a.Test_Value!='unknown')" % (begin_date, end_date, prodline)
                cur.execute(sql)
                row = cur.fetchone()
                prodtest_firsterr_num = prodtest_firsterr_num+row[0]
                log.info('产测第一次失败数量(+当前表不在历史表):' + str(prodtest_firsterr_num), extra={'ptlsh': public.req_seq})

                sql = "select count( DISTINCT t.Board_SN ) from yw_project_product_test_info t " \
                      "where DATE_FORMAT(t.insert_date,'%%Y-%%m-%%d')>='%s' and  DATE_FORMAT(t.insert_date,'%%Y-%%m-%%d')<='%s' " \
                      "and t.prod_line='%s'"  % (begin_date, end_date, prodline)
                cur.execute(sql)
                row = cur.fetchone()
                prodtest_all_num = row[0]
                log.info('产测投产总数量:' + str(prodtest_all_num), extra={'ptlsh': public.req_seq})
                if prodtest_all_num > prodtest_firsterr_num:
                    prodtest_direct_rate = ((prodtest_all_num - prodtest_firsterr_num) / prodtest_all_num) * 100
                else:
                    prodtest_direct_rate = 100
                prodtest_direct_rate=round(prodtest_direct_rate, 2)
                log.info('产测直通率:' + str(prodtest_direct_rate), extra={'ptlsh': public.req_seq})

                dataitem = {
                    "prod_line": dict_prodline[prodline],
                    "station_type": "产测",
                    "prod_allnum": prodtest_all_num,
                    "direct_num": prodtest_all_num - prodtest_firsterr_num,
                    "direct_rate": prodtest_direct_rate,
                    "notes": ""
                }
                direct_data.append(dataitem)

            meterread_direct_rate = 100
            if not station_type or station_type == 'meterread':  # 抄表直通率统计
                sql = "select count(1) from (select min(id),Board_SN,Test_Result, Test_Value from yw_project_meterread_test_info_his " \
                      "where DATE_FORMAT( insert_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT( insert_date,'%%Y-%%m-%%d')<='%s'" \
                      " and prod_line='%s' group by Board_SN ) temp " \
                      "where (Test_Result!='Pass' and Test_Value!='unknown') " % (begin_date, end_date, prodline)
                log.info("抄表第一次失败数量:" + sql, extra={'ptlsh': public.req_seq})
                cur.execute(sql)
                row = cur.fetchone()
                meterread_firsterr_num = row[0]
                log.info('抄表第一次失败数量:'+ str(meterread_firsterr_num), extra={'ptlsh': public.req_seq})

                sql = "select count(distinct Board_SN) from yw_project_meterread_test_info a where not EXISTS " \
                      "(select 1 from yw_project_meterread_test_info_his b where a.Board_SN=b.Board_SN) and " \
                      "DATE_FORMAT(a.insert_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(a.insert_date,'%%Y-%%m-%%d')<='%s' " \
                      "and a.prod_line='%s' and (a.Test_Result!='Pass' and a.Test_Value!='unknown')" % (begin_date, end_date, prodline)
                cur.execute(sql)
                row = cur.fetchone()
                meterread_firsterr_num = meterread_firsterr_num + row[0]
                log.info('抄表第一次失败数量(+当前表不在历史表):' + str(prodtest_firsterr_num), extra={'ptlsh': public.req_seq})

                sql = "select count( DISTINCT t.Board_SN ) from yw_project_meterread_test_info t " \
                      "where DATE_FORMAT(t.insert_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(t.insert_date,'%%Y-%%m-%%d')<='%s' " \
                      "and t.prod_line='%s' " % (begin_date, end_date, prodline)
                log.info("抄表投产总数量:" + sql)
                cur.execute(sql)
                row = cur.fetchone()
                meterread_all_num = row[0]
                log.info('抄表投产总数量:'+ str(meterread_all_num), extra={'ptlsh': public.req_seq})
                if meterread_all_num > meterread_firsterr_num:
                    meterread_direct_rate = ((meterread_all_num - meterread_firsterr_num) / meterread_all_num) * 100
                else:
                    meterread_direct_rate = 100
                meterread_direct_rate = round(meterread_direct_rate, 2)
                log.info('抄表直通率:'+ str(meterread_direct_rate), extra={'ptlsh': public.req_seq})

                dataitem = {
                    "prod_line": dict_prodline[prodline],
                    "station_type": "抄表",
                    "prod_allnum": meterread_all_num,
                    "direct_num": meterread_all_num - meterread_firsterr_num,
                    "direct_rate": meterread_direct_rate,
                    "notes": ""
                }
                direct_data.append(dataitem)

            snid_direct_rate = 100
            if not station_type or station_type == 'egsnid':  # 装壳直通率统计
                sql = "select count(DISTINCT pcb_sn) from yw_project_snid_detail_error where DATE_FORMAT(tran_date,'%%Y-%%m-%%d')>='%s' " \
                      "and DATE_FORMAT(tran_date,'%%Y-%%m-%%d')<='%s' and prod_line='%s' " % (begin_date, end_date, prodline)
                log.info("装壳第一次失败数量:" + sql)
                cur.execute(sql)
                row = cur.fetchone()
                snid_firsterr_num = row[0]
                log.info('装壳第一次失败数量:'+ str(snid_firsterr_num), extra={'ptlsh': public.req_seq})

                sql = "select count( DISTINCT t.pcb_sn ) from yw_project_snid_detail t  " \
                      "where DATE_FORMAT(t.tran_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(t.tran_date,'%%Y-%%m-%%d')<='%s' " \
                      "and t.prod_line='%s'" % (begin_date, end_date, prodline)
                log.info("装壳投产总数量:" + sql, extra={'ptlsh': public.req_seq})
                cur.execute(sql)
                row = cur.fetchone()
                snid_all_num = row[0]
                log.info('装壳投产总数量:'+ str( snid_all_num), extra={'ptlsh': public.req_seq})
                if snid_all_num > snid_firsterr_num:
                    snid_direct_rate = ((snid_all_num - snid_firsterr_num) / snid_all_num) * 100
                else:
                    snid_direct_rate = 100
                snid_direct_rate = round(snid_direct_rate, 2)
                log.info('装壳直通率:'+ str( snid_direct_rate), extra={'ptlsh': public.req_seq})

                dataitem = {
                    "prod_line": dict_prodline[prodline],
                    "station_type": "装壳",
                    "prod_allnum": snid_all_num,
                    "direct_num": snid_all_num - snid_firsterr_num,
                    "direct_rate": snid_direct_rate,
                    "notes": ""
                }
                direct_data.append(dataitem)

            box_direct_rate = 100
            if not station_type or station_type == 'box':  # 装箱直通率统计
                sql = "select count(DISTINCT model_id) from yw_project_boxing_info_error where DATE_FORMAT(tran_date,'%%Y-%%m-%%d')>='%s' " \
                      " and DATE_FORMAT(tran_date,'%%Y-%%m-%%d')<='%s' and prod_line='%s' " % ( begin_date, end_date, prodline)
                log.info("装箱第一次失败数量:" + sql, extra={'ptlsh': public.req_seq})
                cur.execute(sql)
                row = cur.fetchone()
                box_firsterr_num = row[0]
                log.info('装箱第一次失败数量:'+ str(box_firsterr_num), extra={'ptlsh': public.req_seq})

                sql = "select count( DISTINCT t.model_id ) from yw_project_boxing_info t  " \
                      "where DATE_FORMAT(t.tran_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(t.tran_date,'%%Y-%%m-%%d')<='%s' " \
                      "and t.prod_line='%s' " % (begin_date, end_date, prodline)
                log.info("装箱投产总数量:" + sql, extra={'ptlsh': public.req_seq})
                cur.execute(sql)
                row = cur.fetchone()
                box_all_num = row[0]
                log.info('装箱投产总数量:'+ str(box_all_num), extra={'ptlsh': public.req_seq})
                if box_all_num > box_firsterr_num:
                    box_direct_rate = ((box_all_num - box_firsterr_num) / box_all_num) * 100
                else:
                    box_direct_rate = 100
                box_direct_rate = round(box_direct_rate, 2)
                log.info('装箱直通率:'+ str(box_direct_rate), extra={'ptlsh': public.req_seq})

                dataitem = {
                    "prod_line": dict_prodline[prodline],
                    "station_type": "装箱",
                    "prod_allnum": box_all_num,
                    "direct_num": box_all_num - box_firsterr_num,
                    "direct_rate": box_direct_rate,
                    "notes": ""
                }
                direct_data.append(dataitem)

            total_direct_rate = prodtest_direct_rate * meterread_direct_rate * snid_direct_rate * box_direct_rate
            total_direct_rate =round(total_direct_rate / 1000000, 4)
            log.info('总直通率:' + str(total_direct_rate), extra={'ptlsh': public.req_seq})
            dataitem = {
                "prod_line": dict_prodline[prodline],
                "station_type": "==产线汇总==",
                "prod_allnum": "",
                "direct_num": "",
                "direct_rate": total_direct_rate,
                "notes": ""
            }
            direct_data.append(dataitem)

            log.info("---------------一次直通率数据收集完毕!-----------------", extra={'ptlsh': public.req_seq})


        body['form_var']["direct_data"] = direct_data

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


# 生产错误情况统计
def get_directreport_errinfo(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        begin_date = form_var.get('begin_date', '2019-01-01')
        end_date = form_var.get('end_date', '2099-12-31')
        prod_line  = form_var.get('prod_line')
        station_type = form_var.get('station_type')

        if not station_type:
            public.respcode, public.respmsg = "382901", "工站类别必输!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        tabledata=[]
        cur = connection.cursor()  # 创建游标

        if station_type =='prodtest':        #产测异常统计
            if prod_line == 'ALL':
                andsql = " and prod_line=prod_line"
            else:
                andsql = " and prod_line='%s'" % prod_line
            sql = "select tmp.Test_Value, dict.dict_target, count(1) from ( " \
                  "select Test_Value from yw_project_product_test_info_his where DATE_FORMAT(insert_date,'%%Y-%%m-%%d') " \
                  "BETWEEN '%s' and '%s' and Test_Value!='Pass' and Test_Value!='unknown' %s " \
                  "union all  " \
                  "select Test_Value from yw_project_product_test_info where DATE_FORMAT(insert_date,'%%Y-%%m-%%d') " \
                  "BETWEEN '%s' and '%s' and Test_Value!='Pass' and Test_Value!='unknown' %s " \
                  ") tmp LEFT JOIN sys_ywty_dict dict on dict.dict_name='YW_PROJECT_PRODUCT_VALUE.FAIL_MSG' " \
                  "and tmp.Test_Value=dict.dict_code group by tmp.Test_Value order by count(1) desc " % \
                  (begin_date, end_date, andsql, begin_date, end_date, andsql)
            log.info(sql)
            cur.execute(sql)
            rows = cur.fetchall()
            for item in rows:
                dataitem={
                    "err_num":item[2],
                    "err_code":item[0],
                    "err_msg":item[1],
                }
                tabledata.append(dataitem)
            log.info("---------------产测异常统计完毕!-----------------", extra={'ptlsh': public.req_seq})
        elif station_type =='egsnid':        #装壳异常统计
            if prod_line == 'ALL':
                andsql = " and prod_line=prod_line"
            else:
                andsql = " and prod_line='%s'" % prod_line
            sql = "select err_code, err_msg, count(1) from yw_project_snid_detail_error " \
                  "where DATE_FORMAT(tran_date,'%%Y-%%m-%%d') BETWEEN '%s' and '%s' %s " \
                  "group by err_code order by count(1) DESC" % \
                  ( begin_date, end_date, andsql )
            log.info(sql)
            cur.execute(sql)
            rows = cur.fetchall()
            for item in rows:
                dataitem={
                    "err_code":item[0],
                    "err_msg":item[1],
                    "err_num": item[2],
                }
                tabledata.append(dataitem)
            log.info("---------------装壳异常统计完毕!-----------------", extra={'ptlsh': public.req_seq})
        elif station_type =='meterread':        #抄表异常统计
            if prod_line == 'ALL':
                andsql = " and prod_line=prod_line"
            else:
                andsql = " and prod_line='%s'" % prod_line
            sql = "select tmp.Test_Value, dict.dict_target, count(1) from ( " \
                  "select Test_Value from yw_project_meterread_test_info_his where DATE_FORMAT(insert_date,'%%Y-%%m-%%d') " \
                  "BETWEEN '%s' and '%s' and Test_Value!='Pass' and Test_Value!='unknown' %s " \
                  "union all  " \
                  "select Test_Value from yw_project_meterread_test_info where DATE_FORMAT(insert_date,'%%Y-%%m-%%d') " \
                  "BETWEEN '%s' and '%s' and Test_Value!='Pass' and Test_Value!='unknown' %s " \
                  ") tmp LEFT JOIN sys_ywty_dict dict on dict.dict_name='YW_PROJECT_PRODUCT_VALUE.FAIL_MSG' " \
                  "and tmp.Test_Value=dict.dict_code group by tmp.Test_Value order by count(1) desc " % \
                  (begin_date, end_date, andsql, begin_date, end_date, andsql)
            log.info(sql)
            cur.execute(sql)
            rows = cur.fetchall()
            for item in rows:
                dataitem={
                    "err_num":item[2],
                    "err_code":item[0],
                    "err_msg":item[1],
                }
                tabledata.append(dataitem)
            log.info("---------------抄表异常统计完毕!-----------------", extra={'ptlsh': public.req_seq})
        elif station_type == 'box':  # 装箱异常统计
            if prod_line == 'ALL':
                andsql = " and prod_line=prod_line"
            else:
                andsql = " and prod_line='%s'" % prod_line
            sql = "select err_code, err_msg, count(1) from yw_project_boxing_info_error " \
                  "where DATE_FORMAT(tran_date,'%%Y-%%m-%%d') BETWEEN '%s' and '%s' %s " \
                  "group by err_code order by count(1) DESC" % \
                  ( begin_date, end_date, andsql )
            log.info(sql)
            cur.execute(sql)
            rows = cur.fetchall()
            for item in rows:
                dataitem={
                    "err_code":item[0],
                    "err_msg":item[1],
                    "err_num": item[2],
                }
                tabledata.append(dataitem)
            log.info("---------------装箱异常统计完毕!-----------------", extra={'ptlsh': public.req_seq})

        #汇总一下总数量
        totalnum=0
        for item in tabledata:
            print(type(item), item)
            totalnum=totalnum+item.get('err_num', 0)
        dataitem = {
                    "err_code": '  ',
                    "err_msg": "总计",
                    "err_num": totalnum,
                }
        tabledata.append(dataitem)

        body['form_var']["tabledata"] = tabledata

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

# 根据拼板号获取拼板明细
def SN_Laser_Carving_Select(request):
    log = public.logger
    body = public.req_body
    Platform_Num = body.get('Platform_Num')
    Prod_line = body.get('Prod_line')
    Batch_Num = body.get('Batch_Num')
    Entirety = body.get('Entirety')

    try:
        cur = connection.cursor()  # 创建游标

        sql = "select distinct Entirety_Location, SN_NO from yw_project_carving_info " \
              "where Prod_Line=%s and Batch_Num=%s and Entirety=%s order by Entirety_Location asc"
        log.info(sql % (Prod_line, Batch_Num, Entirety) )
        cur.execute(sql, (Prod_line, Batch_Num, Entirety) )
        rows= cur.fetchall()
        if not rows:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "303011", "无数据!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        Entirety_Info= []
        for item in rows:
            item_info={}
            item_info['Entirety_Location'] = item[0]  # 分板前位置标识,1-10
            item_info['SN_NO'] = item[1] # SN码
            Entirety_Info.append(item_info)

        body['Entirety_Info']=Entirety_Info

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

# 产测结果上传
def Product_Test(request):
    log = public.logger
    body = public.req_body
    Platform_Num = body.get('Platform_Num')
    prod_line = body.get('Prod_line')
    Batch_Num = body.get('Batch_Num')
    Entirety = body.get('Entirety')

    try:

        Info = body.get('Info', None)
        if not Info:
            public.respcode, public.respmsg = "500511", "上传数据错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        for item in Info:
            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            Ser_Num = item['Ser_Num']['Value']
            Test_Result = item['Test_Result']['Result']
            Test_Value = item['Test_Result']['Value']
            Board_SN_Result = item['Board_SN']['Result']
            Board_SN = item['Board_SN']['Value']
            Chip_mmid_Result = item['Chip_mmid']['Result']
            Chip_mmid = item['Chip_mmid']['Value']
            Aging_Test_Period_Result = item['Aging_Test_Period']['Result']
            Aging_Test_Period = item['Aging_Test_Period']['Value']
            Hw_Version_Result = item['Hw_Version']['Result']
            Hw_Version = item['Hw_Version']['Value']
            Fw_Version_Result = item['Fw_Version']['Result']
            Fw_Version = item['Fw_Version']['Value']
            Vendor_id_Result = item['Vendor_id']['Result']
            Vendor_id = item['Vendor_id']['Value']
            chip_id_Result = item['chip_id']['Result']
            chip_id = item['chip_id']['Value']

            # 测试失败次数超过3次，SN 码状态自动进入维修状态
            def insert_repair(log):
                # 查询SN 码最终状态表SQL
                snfail_sql = "SELECT * from yw_project_snid_final_status WHERE Board_SN = %s order by id desc limit 1  "
                insert_snfial_sql = "INSERT INTO yw_project_snid_final_status(id, Board_SN, insert_date, prod_prcesses, " \
                                    "fail_count, final_status) VALUES (%s, %s, %s, %s, %s, %s);"
                # 生产项目信息表
                proinfo_sql = "select distinct plan_id  from yw_project_plan_info where order_id= %s"
                # 插入维修信息
                repain_insert = "INSERT INTO yw_project_repair_info(id, tran_date, snid, fail_process, prod_date," \
                                " prod_line, Platform_Num, Batch_Num, Plan_Num, pro_test_result, pro_test_value, " \
                                "meter_test_result, meter_test_value, Hw_Version, Fw_Version, model_id, gw_id, " \
                                "Vendor_id, fault_description, repair_description,gconfirm_people,gconfirm_date," \
                                "repair_people, repaired_date, status) " \
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                flag = True
                if Test_Result == "Pass":
                    cur.execute(snfail_sql, Board_SN)
                    row = cur.fetchone()
                    if row:
                        snfail_tuple = (None, Board_SN, nowTime, '产测', 0, '0')
                        cur.execute(insert_snfial_sql, snfail_tuple)
                else:
                    cur.execute(snfail_sql, Board_SN)
                    row = cur.fetchone()
                    # SN 最终状态表中有记录
                    if row:
                        count = row[4] + 1
                        if count == 3:
                            snfail_tuple = (None, Board_SN, nowTime, '产测', 3, '1')
                            cur.execute(insert_snfial_sql, snfail_tuple)
                            # 此时连续测试失败超过三次，SN 自动转入维修状态
                            flag = False
                            plan_num = None
                            cur.execute(proinfo_sql, Batch_Num)
                            plan_row = cur.fetchone()
                            if plan_row:
                                plan_num = plan_row[0]
                            # 将该SN 相关记录信息插入维修记录表
                            repair_tuple = (None, nowTime, Board_SN, '产测', nowTime, prod_line,
                                            Platform_Num, Batch_Num, plan_num, Test_Result,
                                            Test_Value, '', '', Hw_Version, Fw_Version, None,
                                            Chip_mmid, Vendor_id, None, None, None, None, None, None, '9')
                            cur.execute(repain_insert, repair_tuple)
                        elif count < 3:
                            snfail_tuple = (None, Board_SN, nowTime, '产测', count, '0')
                            cur.execute(insert_snfial_sql, snfail_tuple)
                    # SN 最终状态表中无记录
                    else:
                        snfail_tuple = (None, Board_SN, nowTime, '产测', 1, '0')
                        cur.execute(insert_snfial_sql, snfail_tuple)

                return flag

            check_flag = insert_repair(log)
            if not check_flag:
                s = public.setrespinfo({"respcode": "500530", "respmsg": "测试已连续失败超过3次,该SN码对应模块已转入维修 !"})
                return HttpResponse(s)

            # 先把重复数据放入历史表
            sql = "insert into yw_project_product_test_info_his select * from yw_project_product_test_info where Board_SN='%s' " % (
            Board_SN)
            cur.execute(sql)
            sql = "delete from yw_project_product_test_info where Board_SN='%s' " % (Board_SN)
            cur.execute(sql)

            insert_sql = "INSERT INTO yw_project_product_test_info (id, insert_date, Batch_Num, Ser_Num, Platform_Num, Test_Result,Test_Value, Board_SN_Result, Board_SN, " \
                         "Chip_mmid_Result, Chip_mmid, Aging_Test_Period_Result, Aging_Test_Period, Hw_Version_Result, Hw_Version, Fw_Version_Result, Fw_Version," \
                         "Vendor_id_Result, Vendor_id, chip_id_Result, chip_id,prod_line) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"

            insert_tuple = ( None, nowTime, Batch_Num, Ser_Num, Platform_Num, Test_Result, Test_Value, Board_SN_Result, Board_SN,
            Chip_mmid_Result, Chip_mmid, Aging_Test_Period_Result, Aging_Test_Period, Hw_Version_Result,
            Hw_Version, Fw_Version_Result, Fw_Version, Vendor_id_Result, Vendor_id, chip_id_Result, chip_id, prod_line)
            cur.execute(insert_sql, insert_tuple)
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

# 根据模块ID查询相关信息
def model_snid_select(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        tag_no = form_var.get('tag_no_select')  # 模块ID
        model_id = form_var.get('model_id_select')  # 模块ID
        if not model_id:
            public.respcode, public.respmsg = "300331", "模块ID不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor() #打开游标

        # 获取装壳信息
        sql = "select order_id,sn_no,old_sn_no,tag_no,gwid, tran_date from yw_project_2cmac_info where model_id=%s"
        cur.execute(sql, model_id)
        row = cur.fetchone()
        if not row:
            cur.close() #关闭游标
            public.respcode, public.respmsg = "300332", "数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        form_var['order_id'] = row[0]
        form_var['sn_no'] = row[1]
        form_var['old_sn_no'] = row[2]
        form_var['tag_no'] = row[3]
        form_var['gwid'] = row[4]
        form_var['tran_date'] = row[5]

        form_var['model_id'] = model_id

        if tag_no:
            form_var['tag_no_select'] = tag_no
            if tag_no == row[3]:
                form_var['result'] = '正确，比较一致'
            else:
                form_var['result'] = '错误，比较不一致'

        if form_var['old_sn_no']:
            #查询原产测信息
            sql = "select insert_date, Test_Value from yw_project_product_test_info where Board_SN=%s"
            cur.execute(sql, form_var['old_sn_no'])
            row = cur.fetchone()
            if row:
                form_var['prodtest_time'] = row[0]
                form_var['prodtest_result'] = row[1]

        cur.close()  #关闭游标

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
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

# 生产问题明细查询
def prod_problem_select(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        tag_no = form_var.get('tag_no_select')  # 模块ID
        model_id = form_var.get('model_id_select')  # 模块ID
        if not model_id:
            public.respcode, public.respmsg = "300331", "模块ID不可为空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor() #打开游标

        # 获取装壳信息
        sql = "select s.id,(@i:=@i-1) seq_no, s.tran_date,s.prod_line,s.plan_no,s.prod_name,s.problem_type,s.problem_desc, " \
              "s.deal_method,s.charge_org,s.charge_user,s.check_user,s.exp_date,s.cmt_data,s.state,s.images " \
              "from yw_project_prod_problem_info s,(select @i:=1110) t  "
        cur.execute(sql, model_id)
        row = cur.fetchone()
        if not row:
            cur.close() #关闭游标
            public.respcode, public.respmsg = "300332", "数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        form_var['order_id'] = row[0]
        form_var['sn_no'] = row[1]
        form_var['old_sn_no'] = row[2]
        form_var['tag_no'] = row[3]
        form_var['gwid'] = row[4]
        form_var['tran_date'] = row[5]

        form_var['model_id'] = model_id

        if tag_no:
            form_var['tag_no_select'] = tag_no
            if tag_no == row[3]:
                form_var['result'] = '正确，比较一致'
            else:
                form_var['result'] = '错误，比较不一致'

        if form_var['old_sn_no']:
            #查询原产测信息
            sql = "select insert_date, Test_Value from yw_project_product_test_info where Board_SN=%s"
            cur.execute(sql, form_var['old_sn_no'])
            row = cur.fetchone()
            if row:
                form_var['prodtest_time'] = row[0]
                form_var['prodtest_result'] = row[1]

        cur.close()  #关闭游标

    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
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

# 生产问题保存
def prod_problem_save(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        cur = connection.cursor() #打开游标
        form_var['tran_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") #返回登记时间
        if not form_var.get('cmt_data'):
            form_var['cmt_data'] = None
        if form_var.get('id'): #有主键ID，更新数据
            sql = "update yw_project_prod_problem_info set tran_date=%s, prod_line=%s,plan_no=%s,prod_name=%s,problem_type=%s, " \
                  "problem_desc=%s, deal_method=%s,charge_org=%s,charge_user=%s,check_user=%s,exp_date=%s,cmt_data=%s," \
                  "state=%s,images=%s where id=%s"
            cur.execute(sql, (form_var.get('tran_date'), form_var.get('prod_line'),form_var.get('plan_no'),
                              form_var.get('prod_name'),form_var.get('problem_type'), form_var.get('problem_desc'),
                              form_var.get('deal_method'),form_var.get('charge_org'), form_var.get('charge_user'),
                              form_var.get('check_user'),form_var.get('exp_date'),form_var.get('cmt_data'),
                              form_var.get('state'), str(form_var.get('images')),form_var.get('id') ) )
        else:
            #新增数据
            sql = "insert into yw_project_prod_problem_info(tran_date, prod_line, plan_no, prod_name, problem_type, " \
                  "problem_desc, deal_method, charge_org, charge_user, check_user, exp_date, cmt_data, state, images) " \
                  "values(%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s)"
            cur.execute(sql, (form_var.get('tran_date'), form_var.get('prod_line'), form_var.get('plan_no'), form_var.get('prod_name'),
                              form_var.get('problem_type'), form_var.get('problem_desc'), form_var.get('deal_method'),
                              form_var.get('charge_org'), form_var.get('charge_user'), form_var.get('check_user'),
                              form_var.get('exp_date'), form_var.get('cmt_data'), form_var.get('state'),
                              str(form_var.get('images')) ))
            form_var['id'] = cur.lastrowid

        cur.close()  #关闭游标


    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
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


# 巡线问题打印
def prod_problem_print(request):
    log = public.logger
    body = public.req_body
    form_var = body.get('form_var')

    try:
        cur = connection.cursor() #打开游标

        #新增数据,增加打印记录
        sql = "insert into yw_project_prod_problem_print(user_id) values(%s)"
        cur.execute(sql,  public.user_id)
        cur.close()  #关闭游标


    except Exception as ex:
        log.error("生成数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!" + str(ex)
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


