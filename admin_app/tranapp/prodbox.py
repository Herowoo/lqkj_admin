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
#生产自动化包装..
#add by litz, 2020.10.23
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


#装箱信息导入
def boxinfo_import(request):
    log = public.logger
    body=public.req_body
    form_var=body.get('form_var')
    excelfile = form_var.get('excelfile')
    if not excelfile:
        public.respcode, public.respmsg = "300332", "请先选择文件!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        model_box_count = int( form_var.get('model_box_count') ) #每箱包装模块数量
        tray_count = int(form_var.get('model_tray_count'))  #每托盘存放数量

        cur = connection.cursor()
        # 创建游标#根据fileid查询文件
        sql = "select md5_name from sys_fileup where file_id=%s"
        log.info(sql % (excelfile) )
        cur.execute(sql, (excelfile) )
        row = cur.fetchone()
        if not row:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "300333", "文件不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        file_md5name = row[0]

        #检查文件是否存在
        fullpathfile = public.localhome + "fileup/" + file_md5name
        log.info("检查文件是否存在!" + str(fullpathfile), extra={'ptlsh': public.req_seq})
        if not os.path.exists(fullpathfile):
            public.respcode, public.respmsg = "100134", "文件已过期!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 读取excel数据并处理
        try:
            wb = openpyxl.load_workbook(filename=fullpathfile)
        except FileNotFoundError:
            cur.close()  # 关闭游标
            log.error('文件不存在', exc_info=True, extra={'ptlsh': public.req_seq})
            public.respcode, public.respmsg = "360001", "文件不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        except:
            cur.close()  # 关闭游标
            log.error('打开文件错误', exc_info=True, extra={'ptlsh': public.req_seq})
            public.respcode, public.respmsg = "360002", "打开文件错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        ws = wb.active

        #读取excel明细，插得装箱信息表
        insertsql = "insert into yw_project_boxing_info(box_id, box_code,model_id, order_id, plan_id, state, " \
                    "tray_code, model_tray_seq, model_box_seq) " \
                    "values('%s', '%s', '%s', '%s', '%s', '0', '%s', '%s', '%s') "
        i = 0;
        k = 0;  # 数据行数,第几条真正的数据数据
        model_box_seq = 1  # 模块在箱中的序号
        model_tray_seq = 1  # 模块在托盘中的序号
        tray_code = 1  # 托盘号
        for item in ws.rows:
            i = i + 1
            if i == 1:  # 第一行标题不处理
                continue

            k = k + 1
            # 自动分配托盘号和箱号
            if k == 1:  # 第一条数据
                model_box_seq = 1  # 模块在箱中的序号
                model_tray_seq = 1  # 模块在托盘中的序号
                tray_code = 1  # 托盘号
            else:  # 以后的数据
                if k % (tray_count) == 1:  # 每一托盘的第一个,托盘号自动加1
                    tray_code = tray_code + 1

                if k % (model_box_count) == 1:
                    model_box_seq = 1
                else:
                    model_box_seq = model_box_seq + 1

                if k % (tray_count) == 1:
                    model_tray_seq = 1
                else:
                    model_tray_seq = model_tray_seq + 1

            # log.info(insertsql % (item[0].value, item[1].value, item[2].value, item[4].value, item[5].value) )
            cur.execute(insertsql % (item[0].value, item[1].value, item[2].value, item[4].value, item[5].value,
                                     tray_code, model_tray_seq, model_box_seq) )

        wb.close() #关闭文件
        cur.close()  # 关闭游标
        form_var['importvalue']='共导入成功 [%s] 条数据' % (i-1)

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

# 装箱信息查询
def get_autobox_info_bak20201123(request):
    log = public.logger
    body=public.req_body
    try:
        body['projectinfo'] = [ ]
        begin_model_id = body.get('begin_model_id')

        cur = connection.cursor()  # 创建游标
        time_now = datetime.datetime.now().strftime('%Y-%m-%d')
        sql = "select distinct order_id, plan_id, gwid_flag, prod_type, msg_info from yw_project_plan_info " \
              "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s' "  % (time_now)
        # sql = "select order_id, plan_id, gwid_flag, prod_type, msg_info from yw_project_plan_info " \
        #       "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s'" \
        #       " and state='1'" % (time_now)
        log.info("查询今日计划和昨日生产量:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        if len(rows) == 0:
            cur.close()
            public.respcode, public.respmsg = "500498", "无当日生产计划!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        for item in rows:
            dict_orderinfo={}
            dict_orderinfo['order_id'] = item[0]
            dict_orderinfo['plan_id'] = item[1]
            dict_orderinfo['order_msg'] = item[4]

            sql = "select distinct box_code from yw_project_boxing_info where order_id='%s' and state='0' " \
                  "order by box_code ASC" % (dict_orderinfo['order_id'])
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                dict_orderinfo['box_code'] = '0000000'  #当前箱号不存在
                continue #抛弃不显示
            else:
                dict_orderinfo['box_code'] = row[0]  # 当前箱号

            #获取总箱数
            sql = "select count(distinct box_code) from yw_project_boxing_info where order_id='%s'" % (dict_orderinfo['order_id'])
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                dict_orderinfo['total_box'] = 0  # 总箱号为0
            else:
                dict_orderinfo['total_box'] = row[0]  # 总箱号

            # 本箱应装数量
            sql = "select count(distinct model_id) from yw_project_boxing_info where order_id='%s'  and box_code='%s'" \
                  % ( dict_orderinfo['order_id'], dict_orderinfo['box_code'] )
            log.info(sql)
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                dict_orderinfo['total_mod'] = 0  # 本箱应装数量
            else:
                dict_orderinfo['total_mod'] = row[0]  # 本箱应装数量

            # 本箱已装数量
            sql = "select model_box_seq from yw_project_boxing_info where order_id='%s' and box_code='%s' and state='1'" \
                  % ( dict_orderinfo['order_id'], dict_orderinfo['box_code'] )
            cur.execute(sql)
            row_box_list = cur.fetchall()
            model_box_list = []
            for boxitem in row_box_list:
                model_box_list.append(boxitem)
            dict_orderinfo['count_mod'] = len( model_box_list )  # 已装箱数量

            # 号段起止位置
            sql = "select min(model_id), max(model_id) from yw_project_boxing_info " \
                  "where order_id='%s' and box_code='%s'" % ( dict_orderinfo['order_id'], dict_orderinfo['box_code'] )
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                dict_orderinfo['begin_id'] = ''  # 号段起始值
                dict_orderinfo['end_id'] = ''  # 号段结束值
            else:
                dict_orderinfo['begin_id'] = row[0]  #号段起始值
                dict_orderinfo['end_id'] = row[1]  # 号段结束值
            dict_orderinfo['model_box_list'] = model_box_list #已装箱列表

            dict_orderinfo['model_ng_list'] = model_ng_list #NG列表

            body['projectinfo'].append(dict_orderinfo)
        cur.close()  # 关闭游标

        if len(body['projectinfo']) == 0:
            public.respcode, public.respmsg = "500499", "装箱信息未导入!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo


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

# 装箱信息查询
def get_autobox_info(request):
    log = public.logger
    body = public.req_body
    try:
        body['projectinfo'] = []
        begin_model_id = body.get('begin_model_id')

        cur = connection.cursor()  # 创建游标

        sql = "select order_id, box_code, tray_code, state from yw_project_boxing_info where model_id=%s "
        cur.execute(sql, begin_model_id)
        row = cur.fetchone()
        if not row:
            cur.close()
            public.respcode, public.respmsg = "554902", "此模块ID查不询装箱信息!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        else:
            db_order_id = row[0]
            db_box_code = row[1]
            db_tray_code = row[2]
            db_state = row[3]

        if db_state == '1':
            cur.close()
            public.respcode, public.respmsg = "554903", "此模块ID已装箱!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        #查询工单信息
        time_now = datetime.datetime.now().strftime('%Y-%m-%d')
        sql = "select distinct order_id, plan_id, gwid_flag, prod_type, msg_info from yw_project_plan_info " \
              "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s' and  order_id='%s'" % (time_now, db_order_id)
        log.info("查询工单信息:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            cur.close()
            public.respcode, public.respmsg = "500498", "无当日生产计划!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        dict_orderinfo = {}
        dict_orderinfo['order_id'] = row[0]
        dict_orderinfo['plan_id'] = row[1]
        dict_orderinfo['order_msg'] = row[4]

        dict_orderinfo['box_code'] = db_box_code  # 当前箱号

        # 获取总箱数
        sql = "select count(distinct box_code) from yw_project_boxing_info where order_id='%s'" % (
        dict_orderinfo['order_id'])
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            dict_orderinfo['total_box'] = 0  # 总箱号为0
        else:
            dict_orderinfo['total_box'] = row[0]  # 总箱号

        # 本箱应装数量
        sql = "select count(distinct model_id) from yw_project_boxing_info where order_id='%s'  and box_code='%s'" \
              % (dict_orderinfo['order_id'], dict_orderinfo['box_code'])
        log.info(sql)
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            dict_orderinfo['total_mod'] = 0  # 本箱应装数量
        else:
            dict_orderinfo['total_mod'] = row[0]  # 本箱应装数量

        # 本箱号段起止位置
        sql = "select min(model_id), max(model_id) from yw_project_boxing_info " \
              "where order_id='%s' and box_code='%s'" % (dict_orderinfo['order_id'], dict_orderinfo['box_code'])
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            dict_orderinfo['begin_id'] = ''  # 号段起始值
            dict_orderinfo['end_id'] = ''  # 号段结束值
        else:
            dict_orderinfo['begin_id'] = row[0]  # 号段起始值
            dict_orderinfo['end_id'] = row[1]  # 号段结束值

        # 本箱已装数量
        sql = "select model_box_seq from yw_project_boxing_info where order_id='%s' and box_code='%s' and state='1'" \
              % (dict_orderinfo['order_id'], dict_orderinfo['box_code'])
        cur.execute(sql)
        row_box_list = cur.fetchall()
        model_box_list = []
        for boxitem in row_box_list:
            model_box_list.append(boxitem)
        dict_orderinfo['count_mod'] = len(model_box_list)  # 已装箱数量
        dict_orderinfo['model_box_list'] = model_box_list  # 已装箱列表

        # 本箱NG模块数量
        sql = "select distinct b.model_box_seq from yw_project_boxing_info_autoput_detail a, yw_project_boxing_info b " \
              "where a.order_id=b.order_id and a.model_id=b.model_id and a.order_id='%s'and a.box_code='%s' and a.state='NG'" \
              % (dict_orderinfo['order_id'], dict_orderinfo['box_code'])
        cur.execute(sql)
        row_box_list = cur.fetchall()
        model_ng_list = []
        for boxitem in row_box_list:
            model_ng_list.append(boxitem)
        dict_orderinfo['model_ng_list'] = model_ng_list  # NG列表

        body['projectinfo'].append(dict_orderinfo)
        cur.close()  # 关闭游标

        if len(body['projectinfo']) == 0:
            public.respcode, public.respmsg = "500499", "装箱信息未导入!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo


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

# 装箱位置查询-自动装箱
def put_autobox_info(request):
    log = public.logger
    body = public.req_body
    try:
        model_info=body.get('model_info')

        #按照模块ID从小到大排序
        new_modelid_list = sorted(model_info, key=lambda k: k['model_id'])
        # new_modelid_list = model_info
        #先获取模块ID列表, 查询时只用一条sql语句。
        model_list=[]
        for item in new_modelid_list:
            model_list.append(item.get("model_id")) #模块ID
        model_tuple = tuple(model_list)

        #获取每托盘最大的数量
        def GetMaxTrayNum():
            sql = "select max(model_tray_seq) from yw_project_boxing_info where order_id='%s'" % (body.get('order_id'))
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                return 0
            else:
                return row[0]

        #获取当前应该装箱的托盘号，和已装数量，包括失败的model_id.
        def GetNowTrayCode( db_maxtray_num):
            # 获取当前正在装箱的托盘号
            sql = "select tray_code, state from yw_project_boxing_info_lasttray " \
                  "where order_id='%s' order by id desc limit 1" % ( body.get('order_id') )
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                db_last_tray_code = row[0]
                # if not row[1]: #管理台设置的当前开始装箱托盘号
                #     db_last_tray_code = row[0]
                # else:
                #     db_last_tray_code = row[0] + 1  #自动包装程序运行的托盘号，是指最后的托盘号。
                #当前托盘已装数量
                sql = "select count( distinct model_id ) from yw_project_boxing_info_autoput_detail " \
                      "where order_id='%s' and tray_code='%s' " % ( body.get('order_id'), db_last_tray_code )
                cur.execute(sql)
                row = cur.fetchone()
                db_nowbox_num = row[0]
                if db_nowbox_num >= db_maxtray_num:
                    db_last_tray_code = db_last_tray_code +1
            else: #无数据，查询box_info表当前正在装的托盘号
                # 查询最近正在装的一个托盘
                sql = "select tray_code from yw_project_boxing_info where order_id='%s' and state='0' " \
                      "order by tray_code asc limit 1 " % (body.get('order_id'))
                cur.execute(sql)
                row = cur.fetchone()
                if not row:
                    cur.close()
                    public.respcode, public.respmsg = "553942", "此订单没有待装箱的模块!"
                    public.respinfo = HttpResponse(public.setrespinfo())
                    return public.respinfo
                db_last_tray_code = row[0]
                db_nowbox_num = 0

            return db_last_tray_code, db_nowbox_num
        # 获取当前正在装箱的托盘号, 已经装过的数量

        cur = connection.cursor()  # 创建游标

        db_maxtray_num = GetMaxTrayNum() #获取每托盘最大的数量
        now_tray_code, db_nowbox_num = GetNowTrayCode(db_maxtray_num) # 获取当前正在装箱的托盘号和此托盘已装数量
        log.info("当前托盘号:" + str(now_tray_code)+",每托盘数量:" + str(db_maxtray_num) +",托盘已装数量:" + str(db_nowbox_num))
        # 查询抄表是否通过
        sql = "select Module_ID, Test_Value, Board_SN, Chip_mmid from yw_project_meterread_test_info " \
              "where Batch_Num='%s' and Module_ID in %s" % ( body.get('order_id'), model_tuple )
        log.info(sql)
        cur.execute(sql)
        rows = cur.fetchall()
        model_meterread_dict={}
        for item in rows:
            model_meterread_dict[item[0]]=[ item[1], item[2], item[3] ]  #抄表结果

        #查询最近8个待装箱的模块是否在当前托盘中，如果全不在，则推出托盘
        # sql = "select count(1) from yw_project_boxing_info " \
        #       "where order_id='%s' and state='0' and tray_code='%s' and model_id in %s " \
        #       % ( body.get('order_id'), now_tray_code, model_tuple )
        # cur.execute(sql)
        # row = cur.fetchone()
        # if row and row[0]:
        #     if row[0]> 0:
        #         body['fix_out'] = False  # 是否推出托盘, True-推出, False-不推出, 装满箱，或者治具上的8个模块在下一托盘。
        #     else:
        #         body['fix_out'] = True  # 是否推出托盘, True-推出, False-不推出, 装满箱，或者治具上的8个模块在下一托盘。
        # else:
        #     body['fix_out'] = True  # 是否推出托盘, True-推出, False-不推出, 装满箱，或者治具上的8个模块在下一托盘。
        #
        # if body['fix_out'] == True:
        #     now_tray_code = now_tray_code + 1
        #     db_nowbox_num = 0
        #     # 登记当前装箱临时表
        #     sql = "insert into yw_project_boxing_info_lasttray(order_id, tray_code, fix_out ) " \
        #           "values( '%s', '%s', '%s')" % ( body.get('order_id'), now_tray_code,  body['fix_out'] )
        #     cur.execute(sql)
        body['fix_out'] = False

        model_info_new = [] #结果返回列表
        now_modelid_list = [] #已装箱模块ID列表
        now_box_code = None #最后一条的箱号
        i = 0
        for item in new_modelid_list:  #循环处理每个模块的数据
            i=i+1

            #获取当前治具数据并且判断数据
            dict_modelinfo= { }
            dict_modelinfo["state"] = "OK"
            dict_modelinfo["fix_place"] = '0'
            dict_modelinfo["box_model_seq"] = '0'
            dict_modelinfo['box_code'] = '0000000'
            dict_modelinfo["tray_code"] = '0'
            dict_modelinfo["fix_out"] = False  # 是否推出托盘, True-推出, False-不推出
            dict_modelinfo["place_id"] = item.get("place_id") #治具位置
            dict_modelinfo["model_id"] = item.get("model_id") #模块ID
            dict_modelinfo["errinfo"] = "装箱成功"

            if dict_modelinfo["model_id"] == 'NG':
                dict_modelinfo["state"] = "BD"  #模块状态 'NG'-不通过
                dict_modelinfo["errinfo"] = "模块ID错误"
                dict_modelinfo["box_code"] = "0000000"  # 找不到箱号

            # 测试---不判断抄表。。
            log.info(dict_modelinfo["state"] + '--' + model_meterread_dict.get(dict_modelinfo["model_id"],['0','0','0'])[0] )
            if  model_meterread_dict.get(dict_modelinfo["model_id"],['0','0','0'])[0] != 'Pass' \
                    and dict_modelinfo["state"] == "OK":
                dict_modelinfo["state"] = "NG"  #模块状态 'NG'-抄表不通过
                dict_modelinfo["errinfo"] = "抄表不通过"


            #获取当前模块数据
            sql = "select model_id, box_code, tray_code, model_tray_seq, model_box_seq,state from yw_project_boxing_info " \
                  "where order_id = '%s' and model_id='%s' " % ( body.get('order_id'),dict_modelinfo["model_id"] )
            cur.execute(sql)
            row = cur.fetchone()
            if not row :
                if dict_modelinfo["state"]=='OK':
                    dict_modelinfo["state"] = "BD"  # 模块状态 'BD'-不安装
                    dict_modelinfo["box_code"] = "0000000" #找不到箱号
                    dict_modelinfo["errinfo"] = "找不到箱号"
            else:
                dict_modelinfo["box_code"] = row[1]  # 模块所属箱号
                dict_modelinfo["tray_code"] = row[2]  # 托盘编号
                dict_modelinfo["fix_place"] = row[3]  # 放在托盘中的位置
                dict_modelinfo["box_model_seq"] = row[4]  # 此模块在箱中的序号
                modelbox_state= row[5] #是否已装箱


                log.info("模块ID:"+str(dict_modelinfo["model_id"]) + ",当前托盘号:" + str(now_tray_code) + ",模块所在托盘号:" + str(
                    dict_modelinfo["tray_code"]),
                         extra={'ptlsh': public.req_seq})

                # 查询本托盘对应的箱号
                sql = "select distinct box_code from yw_project_boxing_info where order_id='%s' and tray_code='%s' " \
                      % (body.get('order_id'), now_tray_code)
                cur.execute(sql)
                rowitem = cur.fetchone()
                if not rowitem:
                    cur.close()
                    public.respcode, public.respmsg = "553922", "此订单没有待装箱的模块!"
                    public.respinfo = HttpResponse(public.setrespinfo())
                    return public.respinfo
                now_box_code = rowitem[0]

                # if now_box_code != dict_modelinfo["box_code"] and dict_modelinfo["state"]=='OK': #箱号不在所属列表，不安装
                #     dict_modelinfo["state"] = "BD"  # 模块状态 'BD'-不安装
                #     dict_modelinfo["errinfo"] = "不在此箱"

                if modelbox_state== '1'  and dict_modelinfo["state"]=='OK':
                    dict_modelinfo["state"] = "BD"  # 模块状态 'BD'-不安装
                    dict_modelinfo["errinfo"] = "该模块已装箱"

                if dict_modelinfo["tray_code"] != now_tray_code and dict_modelinfo["state"]=='OK':
                    dict_modelinfo["state"] = "BD"  # 模块状态 'BD'-不安装
                    dict_modelinfo["errinfo"] = "不在此托盘"

                if dict_modelinfo["model_id"] in now_modelid_list and dict_modelinfo["state"]=='OK':
                    dict_modelinfo["state"] = "BD"  # 模块状态 'BD'-不安装
                    dict_modelinfo["errinfo"] = "模块ID重复"

                #可以装入托盘，更新表。
                if dict_modelinfo["state"] in ("OK", "BD") and dict_modelinfo["model_id"] != 'NG' :
                    pcbsn = model_meterread_dict.get(dict_modelinfo["model_id"], ['0', '0', '0'])[1]
                    gwid=model_meterread_dict.get(dict_modelinfo["model_id"],['0','0','0'])[2]
                    now_modelid_list.append( dict_modelinfo["model_id"] )
                    sql = "update yw_project_boxing_info set win_id='%s',tran_date='%s',state='%s',gw_id='%s',pcb_sn='%s', " \
                          "prod_line='%s' where model_id='%s'" \
                          % (body.get('win_id', 'autobox'), datetime.datetime.now(), '1', gwid, pcbsn, body.get('prod_line', 'AutoLine2'),
                             dict_modelinfo["model_id"])
                    cur.execute(sql)

                if dict_modelinfo["model_id"] != 'NG':
                    #登记当前装箱临时表
                    sql = "insert into yw_project_boxing_info_autoput_detail" \
                          "(order_id, box_code,tray_code, model_id, place_id, state,errinfo,fix_place, fix_out ) " \
                          "values( '%s','%s','%s','%s','%s','%s','%s','%s','%s' )" \
                          % (body.get('order_id'), dict_modelinfo["box_code"], dict_modelinfo["tray_code"],
                             dict_modelinfo["model_id"], dict_modelinfo["place_id"], dict_modelinfo["state"],
                             dict_modelinfo["errinfo"], dict_modelinfo["fix_place"], dict_modelinfo["fix_out"] )
                    cur.execute(sql)

                #当获当前托盘摆放数据。
                sql = "select count(distinct model_id) from yw_project_boxing_info_autoput_detail " \
                      "where order_id='%s' and tray_code='%s' " % (body.get('order_id'), now_tray_code)
                cur.execute(sql)
                rowitem = cur.fetchone()
                db_nowbox_num = rowitem[0]

                log.info("模块ID:" + str(dict_modelinfo["model_id"]) + ",当前托盘号:" + str(now_tray_code)
                         + ",当装摆放数量:" + str( db_nowbox_num)+ ",最大摆放数量:" + str( db_maxtray_num), extra={'ptlsh': public.req_seq})
                if db_nowbox_num >= db_maxtray_num:
                    dict_modelinfo["fix_out"] = True  # 是否推出托盘, True-推出, False-不推出
                    now_tray_code = now_tray_code +1
                else:
                    dict_modelinfo["fix_out"] = False  # 是否推出托盘, True-推出, False-不推出

                #如果有换托盘，登记一下lasttray表
                if dict_modelinfo["fix_out"] == True:
                    # 登记当前装箱临时表
                    sql = "insert into yw_project_boxing_info_lasttray" \
                          "(order_id, box_code,tray_code, model_id, place_id, state,errinfo,fix_place, fix_out ) " \
                          "values( '%s','%s','%s','%s','%s','%s','%s','%s','%s' )" \
                          % (body.get('order_id'), dict_modelinfo["box_code"], dict_modelinfo["tray_code"],
                             dict_modelinfo["model_id"], dict_modelinfo["place_id"], dict_modelinfo["state"],
                             dict_modelinfo["errinfo"], dict_modelinfo["fix_place"], dict_modelinfo["fix_out"])
                    cur.execute(sql)

            log.info(str(dict_modelinfo), extra={'ptlsh': public.req_seq})
            model_info_new.append(dict_modelinfo)

        #生成抓取顺序
        grab_order=[]
        for item in model_info_new:
            grab_order.append(item.get('place_id'))
        log.info('抓取顺序'+str(grab_order))
        body['grab_order'] = grab_order
        #按照治具位置重新排序一下。
        # model_info_new = sorted(model_info_new, key=lambda k: k['place_id'], reverse=False)
        body['model_info'] = model_info_new

        if not now_box_code:
            cur.close()
            public.respcode, public.respmsg = "553923", "制令单号或模块ID错误!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 本箱应装数量
        sql = "select count(distinct model_id) from yw_project_boxing_info where order_id='%s'  and box_code='%s'" \
              % (body.get('order_id'), now_box_code)
        log.info(sql)
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            body['total_mod'] = 0  # 本箱应装数量
        else:
            body['total_mod'] = row[0]  # 本箱应装数量

        # 本箱号段起止位置
        sql = "select min(model_id), max(model_id) from yw_project_boxing_info " \
              "where order_id='%s' and box_code='%s'" % (body.get('order_id'), now_box_code)
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            body['begin_id'] = ''  # 号段起始值
            body['end_id'] = ''  # 号段结束值
        else:
            body['begin_id'] = row[0]  # 号段起始值
            body['end_id'] = row[1]  # 号段结束值

        # 查询已装箱总数量
        sql = "select model_box_seq from yw_project_boxing_info where order_id = '%s' and box_code='%s' and state='1' " \
              % (body.get('order_id'), now_box_code)
        log.info("查询已装箱总数量:"+sql)
        cur.execute(sql)
        row_box_list = cur.fetchall()
        body['model_box_list'] = []
        for boxitem in row_box_list:
            body['model_box_list'].append(boxitem)
        body['count_mod'] = len(body["model_box_list"])  # 已装箱数量

        # 本箱NG模块数量
        sql = "select distinct b.model_box_seq from yw_project_boxing_info_autoput_detail a, yw_project_boxing_info b " \
              "where a.order_id=b.order_id and a.model_id=b.model_id   and a.order_id='%s' " \
              "and a.box_code='%s' and a.state='NG'" % (body.get('order_id'), now_box_code)
        cur.execute(sql)
        row_box_list = cur.fetchall()
        model_ng_list = []
        for boxitem in row_box_list:
            model_ng_list.append(boxitem)
        body['model_ng_list'] = model_ng_list  # NG列表

        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
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

# 装箱测试数据清理
def test_boxdata_clear(request):
    log = public.logger
    body=public.req_body
    try:
        cur = connection.cursor()  # 创建游标
        orderid= 'MO2012A129'
        sql = "update yw_project_boxing_info set state='0' where order_id = '%s' " % orderid
        cur.execute(sql)

        sql = "delete from yw_project_meterread_test_info where Batch_Num = '%s' " % orderid
        cur.execute(sql)

        sql = "delete from yw_project_snid_detail where order_id = '%s' " % orderid
        cur.execute(sql)

        sql = "delete from yw_project_boxing_info_autoput_detail where order_id = '%s' " % orderid
        cur.execute(sql)

        sql = "delete from yw_project_boxing_info_lasttray where order_id = '%s' " % orderid
        cur.execute(sql)

        cur.close()

        body['form_var']['result']='清理数据完成！'
    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
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


# 开始装箱设置
def boxing_begin_set(request):
    log = public.logger
    body=public.req_body
    try:
        form_var = body.get('form_var')
        orderid = form_var.get('order_id')
        modelid = form_var.get('model_id')

        cur = connection.cursor()  # 创建游标

        sql = "select box_code, tray_code, model_box_seq, model_tray_seq, state from yw_project_boxing_info " \
              "where order_id=%s and model_id=%s "
        cur.execute(sql, (orderid, modelid) )
        row = cur.fetchone()
        if not row:
            cur.close()
            public.respcode, public.respmsg = "554901", "此工单没有待装箱的模块!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        now_box_code = row[0]
        now_tray_code = row[1]
        model_box_seq = row[2]
        model_tray_seq = row[3]
        db_state = row[4]
        if db_state == '1':
            cur.close()
            public.respcode, public.respmsg = "554903", "此模块ID已装箱!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        fix_out = True
        sql = "insert into yw_project_boxing_info_lasttray(order_id, box_code,tray_code,model_id, fix_out,errinfo ) " \
              "values( '%s', '%s', '%s', '%s', '%s', '%s')" \
              % (orderid, now_box_code, now_tray_code, modelid, fix_out, '管理台设置装箱数据')
        cur.execute(sql)

        cur.close()

        form_var['box_code'] = now_box_code
        form_var['tray_code'] = now_tray_code
        form_var['model_box_seq'] = model_box_seq
        form_var['model_tray_seq'] = model_tray_seq
    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
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


# 获取工装项目信息
def getprojectinfo(request):
    log = public.logger
    body = public.req_body
    try:

        cur = connection.cursor()  # 创建游标
        # 根据制令单号获取计划号
        time_now = datetime.datetime.now().strftime('%Y-%m-%d')
        sql = "select order_id, plan_id, gwid_flag, prod_type,msg_info from yw_project_plan_info where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s'" \
              " and state='1'" % (time_now)
        log.info("查询今日计划和昨日生产量:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        if len(rows) == 0:
            cur.close()
            s = public.setrespinfo({"respcode": "500498", "respmsg": "无当日生产计划!"})
            return HttpResponse(s)

        jsondata = { "projectinfo": []  }
        for item in rows:
            log.info(str(item))
            projinfo = {}
            orderid = item[0]
            planid = item[1]
            projinfo["gwid_flag"] = item[2]
            projinfo["order_id"] = orderid
            projinfo["prod_type"] = item[3]
            ordermsginfo = item[4]

            # 根据计划号获取生产信息
            sql = "select order_id,spc_name,begin_id,end_id from yw_project_info where order_id='%s' " % orderid
            log.info(sql)
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                projinfo["plan_id"] = planid
                projinfo["order_msg"] = row[1]
                projinfo["begin_id"] = row[2]
                projinfo["end_id"] = row[3]
                jsondata["projectinfo"].append(projinfo)
            else:
                projinfo["plan_id"] = planid
                projinfo["order_msg"] = ordermsginfo
                projinfo["begin_id"] = ''
                projinfo["end_id"] = ''
                jsondata["projectinfo"].append(projinfo)
        # 增加线体参数获取-add by litz, 2020.10.22
        sql = "select DICT_CODE,DICT_TARGET from sys_ywty_dict where DICT_NAME='YW_PROJECT_PLAN_INFO.PROD_LINE'"
        log.info("查询线别信息:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        line_list = []
        for item in rows:
            line_list.append({
                'name': item[1],
                'value': item[0]
            })
        jsondata["line_list"] = line_list

        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": jsondata
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 装箱信息查询,根据制令单号查询装箱信息
def get_traybox_info(request):
    log = public.logger
    body = public.req_body
    try:
        order_id = body.get('order_id')

        cur = connection.cursor()  # 创建游标

        sql = "select box_code from yw_project_boxing_info where order_id=%s and state='0' order by model_id asc"
        cur.execute(sql, order_id)
        row = cur.fetchone()
        if not row:
            cur.close()
            public.respcode, public.respmsg = "554902", "此制令单号查询不到装箱信息!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        else:
            db_box_code = row[0]

        body['now_box_code'] = db_box_code  # 当前箱号

        # 本箱应装数量
        sql = "select count(1) from yw_project_boxing_info where order_id='%s'  and box_code='%s'" \
              % (order_id, db_box_code)
        log.info(sql)
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            body['total_mod'] = 0  # 本箱应装数量
        else:
            body['total_mod'] = row[0]  # 本箱应装数量

        # 本箱号段起止位置
        sql = "select min(model_id), max(model_id) from yw_project_boxing_info " \
              "where order_id='%s' and box_code='%s'" % (order_id, db_box_code)
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            body['begin_model_id'] = ''  # 号段起始值
            body['end_model_id'] = ''  # 号段结束值
        else:
            body['begin_model_id'] = row[0]  # 号段起始值
            body['end_model_id'] = row[1]  # 号段结束值

        # 本箱已装数量
        sql = "select count(1) from yw_project_boxing_info where order_id='%s' and box_code='%s' and state='1'" \
              % (order_id, db_box_code)
        cur.execute(sql)
        row = cur.fetchone()
        body['boxed_num'] = row[0] # 已装箱数量
        body['unbox_num'] = int(body['total_mod'] ) - int(body['boxed_num'])  # 未装箱数量
        cur.close()

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

# 手工线整托盘扫码装箱
def put_traybox_info(request):
    log = public.logger
    body = public.req_body
    try:
        order_id = body.get('order_id')
        prod_line = body.get('prod_line')
        win_id = body.get('win_id') #机台名称
        model_info=body.get('model_info')
        cur = connection.cursor()  # 创建游标

        modelid_list=[]
        for item in model_info:
            modelid_list.append(item.get('model_id'))

        # 查询抄表是否通过
        sql = "select Module_ID, Test_Value, Board_SN, Chip_mmid from yw_project_meterread_test_info " \
              "where Batch_Num='%s' and Module_ID in %s" % ( order_id, str(tuple(modelid_list)) )
        log.info(sql)
        cur.execute(sql)
        rows = cur.fetchall()
        model_meterread_dict={}
        for item in rows:
            model_meterread_dict[item[0]]=[ item[1], item[2], item[3] ]  #抄表结果

        #查询数据库装箱信息配置
        sql="select model_id, order_id, state, tray_code, model_tray_seq, box_code from yw_project_boxing_info " \
            "where model_id in %s" % str(tuple(modelid_list))
        cur.execute( sql )
        rows = cur.fetchall()
        dbdict={}
        now_tray_code = '' #当前托盘号
        now_box_code = '' #当前箱号
        for dbitem in rows:
            dbdict[dbitem[0]]={"order_id":dbitem[1], "state":dbitem[2], "tray_code":dbitem[3], "model_tray_seq":dbitem[4]}
            if not now_tray_code or not now_box_code:
                now_tray_code = dbitem[3]
                now_box_code = dbitem[5]
        log.info("DB-INFO:"+str(dbdict), extra={'ptlsh': public.req_seq})

        if not now_tray_code or not now_box_code:
            cur.close()
            public.respcode, public.respmsg = "555901", "根据模块ID找不到托盘号!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        body['now_box_code'] = now_box_code

        for item in model_info:
            item['result'] = False
            dbmodelinfo=dbdict.get(item.get('model_id'))
            if not dbmodelinfo:
                item['showinfo'] = str(item.get('model_tray_seq')) + '\n\r\n\r' + item.get(
                    'model_id') + '\n\r' + '模块ID配置不存在'
                continue
            if not dbmodelinfo.get('order_id') or dbmodelinfo.get('order_id') != order_id:
                item['showinfo'] = str(item.get('model_tray_seq')) + '\n\r\n\r' + item.get(
                    'model_id') + '\n\r' + '模块ID对应的制令单号错误'
                continue
            if dbmodelinfo.get('state') == '1':
                item['showinfo'] = str(item.get('model_tray_seq')) + '\n\r\n\r' + item.get(
                    'model_id') + '\n\r' + '模块ID已装箱'
                continue
            if now_tray_code != dbmodelinfo.get('tray_code'):
                item['showinfo'] = str(item.get('model_tray_seq')) + '\n\r\n\r' + item.get(
                    'model_id') + '\n\r' + '模块ID不在此托盘'
                continue
            if str(item.get('model_tray_seq')) != str(dbmodelinfo.get('model_tray_seq')):
                item['showinfo'] = str(item.get('model_tray_seq')) + '\n\r\n\r' + item.get(
                    'model_id') + '\n\r' + '模块ID位置错误'
                continue
            # 测试---不判断抄表。。
            if  model_meterread_dict.get(item.get('model_id'),['0','0','0'])[0] != 'Pass':
                item['showinfo'] = str(item.get('model_tray_seq')) + '\n\r\n\r' + item.get(
                    'model_id') + '\n\r' + '抄表不通过'
                continue

            #校验无误,模块ID正常
            item['result'] = True
            item['showinfo'] = str(item.get('model_tray_seq')) + '\n\r\n\r' + item.get(
                'model_id')+ '\n\r' + '正确'

        #判断校验成功个数和失败个数
        err_num=0
        succ_num=0
        for item in model_info:
            if item.get('result') == True:
                succ_num = succ_num + 1
            else:
                err_num = err_num + 1

        public.respcode, public.respmsg = "000000", "交易成功!"
        #查询数据库此托盘应装多少个
        sql="select count(1) from yw_project_boxing_info " \
            "where order_id='%s' and box_code='%s' and tray_code='%s'" % (order_id, now_box_code, now_tray_code)
        cur.execute( sql )
        row = cur.fetchone()
        if row[0] == succ_num and err_num == 0: #整托盘无误，可以安装
            for item in model_info:
                pcbsn = model_meterread_dict.get(item["model_id"], ['0', '0', '0'])[1]
                gwid = model_meterread_dict.get(item["model_id"], ['0', '0', '0'])[2]
                sql = "update yw_project_boxing_info set win_id='%s',tran_date='%s', state='%s'," \
                      "gw_id='%s',pcb_sn='%s',prod_line='%s' where order_id='%s' and model_id ='%s'" \
                      % (win_id, datetime.datetime.now(), '1', gwid, pcbsn, prod_line, order_id, item["model_id"] )
                log.info(sql)
                cur.execute(sql)
        else:
            public.respcode, public.respmsg = "555903", "本托盘应装{%s}个,当前{%s}个!" % ( row[0], succ_num )

        #获取当前箱的已装箱数据和未装箱数量
        sql = "select count(1) from yw_project_boxing_info " \
              "where order_id='%s' and box_code='%s' and state='0'" % ( order_id, now_box_code)
        cur.execute(sql)
        row = cur.fetchone()
        body['unbox_num'] = row[0]

        sql = "select count(1) from yw_project_boxing_info " \
              "where order_id='%s' and box_code='%s' and state='1'" % (order_id, now_box_code)
        cur.execute(sql)
        row = cur.fetchone()
        body['boxed_num'] = row[0]

        #获取本箱起止号段
        sql = "select min(model_id),max(model_id) from yw_project_boxing_info " \
              "where order_id='%s' and box_code='%s'" % (order_id, now_box_code)
        cur.execute(sql)
        row = cur.fetchone()
        body['begin_model_id'] = row[0]
        body['end_model_id'] = row[1]

        cur.close()

    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo
