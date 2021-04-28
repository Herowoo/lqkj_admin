
from django.shortcuts import HttpResponse
from django.db import connection
import json
from admin_app import public
from admin_app import models
import datetime
import pymssql

def main(request):
    log = public.logger
    log.info('----------------------lqkjmes_showdata_begin---------------------------')

    if request.method == "POST": #POST请求
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        reqest_body=json.loads(tmp)

        trantype=reqest_body['trantype']
        # print('-' * 20, trantype, '-' * 20)
        log.info('trantype=[%s]' % trantype)
        # if  trantype == 'getprojinfo':  #获取项目信息
        #     resp = getprojinfo(request, reqest_body)
        if  trantype == 'getcollectinfo':  #获取汇总信息
            resp = getcollectinfo(request, reqest_body)
        elif  trantype == 'getwarninfo':  #获取预警信息
            resp = getwarninfo(request, reqest_body)
        elif  trantype == 'getmaterialinfo':  #获取制令单领料情况
            resp = getmaterialinfo(request, reqest_body)
        elif  trantype == 'gethourinfo':  #获取每小时生产情况
            resp = gethourinfo(request, reqest_body)
        elif trantype == 'getprocinfo':  # 获取制程生产信息
            resp = getprocinfo(request, reqest_body)
        # elif trantype == 'getprojlist':  # 获取项目信息列表--MESNEW使用
        #     resp = getprojlist(request, reqest_body)
        elif trantype == 'getstationinfo':  # 获取各工站生产信息
            resp = getstationinfo(request, reqest_body)
        elif trantype == 'getprojectlist':  # 根据日期段获取项目信息列表
            resp = getprojectlist(request, reqest_body)
        elif trantype == 'getproform':  # 根据日期段获取项目信息列表
            resp = getproform(request, reqest_body)

        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET": #GET请求
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    log.info('----------------------lqkjmes_showdata_end---------------------------')

    return resp

#获取项目信息
def getprojinfo(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_getprojinfo_begin---------------------------')

    #返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "projectlist":[]
    }
    #当前日期
    time_now = datetime.datetime.now().strftime('%Y-%m-%d')
    begin_date = reqest_body.get('begin_date', time_now)  # 开始日期
    end_date = reqest_body.get('end_date', time_now)  # 结束日期

    #查询项目信息表
    cur = connection.cursor()

    sql = "select order_id, plan_id, prd_name, prod_line, plan_num, finish_num from yw_project_plan_info " \
          "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(prod_date,'%%Y-%%m-%%d') <= '%s' " \
          "and sync_flag='1' and state='1'"  # order by ID desc
    sql = sql % (time_now)
    log.info("查询项目计划信息:" + sql )
    cur.execute( sql )
    rows = cur.fetchall()

    for item in rows:
        orderid = item[0]
        planid = item[1]
        prdname = item[2]
        prodline = item[3]
        plannum = item[4]
        templist = []
        tempdict = { "name": "制令单号", "value": str(orderid) }
        templist.append(tempdict)
        tempdict = { "name": "计划号", "value": str(item[1]) }
        templist.append(tempdict)
        tempdict = {"name": "制品名称", "value": str(prdname) }
        templist.append(tempdict)

        sql="select dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PLAN_INFO.PROD_LINE' and dict_code='%s'" \
            % (prodline)
        cur.execute(sql)
        row=cur.fetchone()
        if row:
            prodlinename=row[0]
        else:
            prodlinename=prodline
        tempdict = { "name": "线别", "value": str(prodlinename) }
        templist.append(tempdict)
        tempdict = {"name": "计划生产量", "value": plannum}
        templist.append(tempdict)

        # 查询已生产总数量,成装箱数据为准
        sql = "select count(1) from yw_project_boxing_info where order_id='%s' and state='1'" % (orderid)
        log.info("查询已生产总数量:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            act_num = row[0]
            log.info("已生产总数量:" + str(act_num))
            sql = "update yw_project_info set finish_num='%s' where order_id='%s' " % (str(act_num), orderid)
            log.info("更新已生产总数量:" + sql)
            cur.execute(sql)
            # sql = "update yw_project_plan_info set finish_num='%s' where order_id='%s' " % (str(act_num), orderid)
            # log.info("更新已生产总数量:" + sql)
            # cur.execute(sql)
        else:
            act_num = 0

        tempdict = {"name": "实际生产量", "value": act_num}
        templist.append(tempdict)

        jsondata["projectlist"].append(templist)

    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------mesapp_getprojinfo_end---------------------------')
    return HttpResponse(s)

#MES看板获取汇总信息
def getcollectinfo(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_getcollectinfo_begin---------------------------')

    #当前日期
    time_now = datetime.datetime.now().strftime('%Y-%m-%d')
    begin_date = reqest_body.get('begin_date', time_now)  # 开始日期
    end_date = reqest_body.get('end_date', time_now)  # 结束日期
    planid = reqest_body.get('plan_id')
    orderid = reqest_body.get('order_id')
    prodline = reqest_body.get('prod_line')

    #返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "collectinfo":{
            "plan_num": 120,  # 计划生产总数
            "act_num": 100,  # 实际生产总数
            "act_rate": 0,  # 完成率(2位小数的)
            "direct_rate": 0,  #一次直通率(2位小数的)
            "bad_rate": 0,   #不良率(4位小数的)
        },
    }

    cur = connection.cursor()  #创建数据库游标
    #获取计划实际生产总数
    sql = "select sum(plan_num), sum(finish_num) from yw_project_plan_info " \
          "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(prod_date,'%%Y-%%m-%%d')<='%s' " \
          "and plan_id='%s' and order_id='%s' and prod_line='%s' " % (begin_date, end_date, planid, orderid, prodline)
    # log.info("获取计划实际生产总数:"+sql)
    cur.execute(sql)
    row = cur.fetchone()
    if row and row[0]:
        jsondata['collectinfo']['plan_num'] = row[0]
        jsondata['collectinfo']['act_num'] = row[1]
        jsondata['collectinfo']['act_rate'] = round(float(row[1]/row[0])* 100.00, 2)

    else:
        jsondata['collectinfo']['plan_num'] = 0
        jsondata['collectinfo']['act_num'] = 0
        jsondata['collectinfo']['act_rate'] = 0

    # 实际生产总数,不良数
    sql = "select coll_type, sum(prod_num), sum(prod_direct_num), sum(prod_err_num) from yw_project_collect_info_direct_err " \
          "where time_day >='%s' and time_day <='%s' " \
          "and order_id='%s' and prod_line='%s' and coll_type!='box' group by coll_type" % (begin_date, end_date, orderid, prodline)
    log.info("获取各制程生产总数,不良数:" + sql)
    cur.execute(sql)
    rows = cur.fetchall()
    succ_rate = 1
    jsondata['collectinfo']['direct_rate'] = 1
    for item in rows:
        itm_direct_rate = float( item[2]/item[1] )
        itm_succ_rate = float( (item[1]-item[3])/item[1] )
        if itm_direct_rate>0:
            jsondata['collectinfo']['direct_rate'] = jsondata['collectinfo']['direct_rate'] * itm_direct_rate
        if itm_succ_rate>0:
            succ_rate = succ_rate * itm_succ_rate

    # #应付省长检查，临时提高生产效率， 20201222
    # if jsondata['collectinfo']['direct_rate'] < 0.91:
    #     jsondata['collectinfo']['direct_rate'] = (1 - jsondata['collectinfo']['direct_rate']) * 0.7 + \
    #                                              jsondata['collectinfo']['direct_rate']
    # if succ_rate < 0.95:
    #     succ_rate = (1 - succ_rate) * 0.8 + succ_rate

    jsondata['collectinfo']['direct_rate'] = round(jsondata['collectinfo']['direct_rate']* 100.00, 2)
    jsondata['collectinfo']['bad_rate'] =  round( (1-succ_rate)* 100.00, 2)

    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------mesapp_getcollectinfo_end---------------------------')
    return HttpResponse(s)

#获取预警信息
def getwarninfo(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_getwarninfo_begin---------------------------')

    #返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "warninfo":[]
    }

    orderid = reqest_body.get('order_id')

    #查询项目信息表
    cur = connection.cursor()
    sql = "select tran_date, warning from yw_project_warning  where order_id=%s and state='1' "  # order by ID desc
    #log.info(sql % orderid )
    cur.execute(sql, orderid )
    rows = cur.fetchall()
    cur.close()

    for item in rows:
        temp = item[0].strftime('%Y-%m-%d %H:%M:%S')+''+item[1]
        jsondata["warninfo"].append(temp)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------mesapp_getwarninfo_end---------------------------')
    return HttpResponse(s)

# 获取最近6小时产出量信息
def gethourinfo(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_gethourinfo_begin---------------------------')

    #当前日期
    time_now = datetime.datetime.now().strftime('%Y-%m-%d')
    begin_date = reqest_body.get('begin_date', time_now)  # 开始日期
    end_date = reqest_body.get('end_date', time_now)  # 结束日期
    planid = reqest_body.get('plan_id') #计划号
    orderid = reqest_body.get('order_id')  #制令单号
    prodline = reqest_body.get('prod_line')  #线别

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "hourlist": {
            # "xdata":["10点","11点","12点","13点","14点","15点"],
            # "ydata": [300, 300, 200, 300, 300, 150]
            "xdata": [],
            "ydata": []
        }
    }

    cur = connection.cursor() #创建游标

    #获取最近6个小时的产测数量
    now_time = datetime.datetime.now()
    k, rangenum=0, 8  #最近N-1小时的数据
    for i in range(rangenum):
        k=1+i-rangenum
        this_time_hour = (now_time + datetime.timedelta(hours=k)).strftime("%H")
        this_time_day_sel = (now_time + datetime.timedelta(hours=k)).strftime("%Y-%m-%d")

        sql = "select prod_num, snid_num, prodtest_num, meterread_num  from yw_project_collect_info_hh " \
              "where order_id='%s' and prod_line='%s' and time_day='%s' and time_hour= '%s' " \
              % (orderid, prodline, this_time_day_sel, this_time_hour)
        log.info("获取最近6个小时的产测数量:"+sql)
        cur.execute(sql)
        coll_row = cur.fetchone()
        if coll_row:
            rownum = coll_row[2]
        else:
            rownum = 0

        jsondata['hourlist']['xdata'].append(this_time_hour)
        jsondata['hourlist']['ydata'].append(rownum)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------mesapp_gethourinfo_end---------------------------')
    return HttpResponse(s)

#获取领料情况信息
def getmaterialinfo(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_getmaterialinfo_begin---------------------------')

    orderid = reqest_body.get('order_id')

    #返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "materiallist":{
            "clname":[],
            "totaldata": [],
            "revdata": [],
        }
    }

    try:
        sqlserver_conn = pymssql.connect(server='10.10.1.250', user='sa', password='luyao123KEJI',
                                         database="db_18",
                                         timeout=20, autocommit=True)  # 获取连接  #sqlserver数据库链接句柄
    except Exception as ex:
        log.info(str(ex))
    try:
        cursor = sqlserver_conn.cursor()  # 获取光标
        selsql = "select PRD_NO, QTY_RSV, QTY, PRD_NAME from TF_MO where MO_NO = '%s' order by itm asc" % orderid
        log.info(selsql)
        cursor.execute(selsql)
        rows = cursor.fetchall()
        for item in rows:
            jsondata['materiallist']['clname'].append(item[3])
            jsondata['materiallist']['totaldata'].append(item[1])
            jsondata['materiallist']['revdata'].append(item[2])

    except Exception as e:
        log.info( str(e) )
    finally:
        cursor.close()
        sqlserver_conn.close()

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------mesapp_getmaterialinfo_end---------------------------')
    return HttpResponse(s)


#获取制程生产信息
def getprocinfo(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_getprocinfo_begin---------------------------')

    #当前日期
    time_now = datetime.datetime.now().strftime('%Y-%m-%d')
    begin_date = reqest_body.get('begin_date', time_now)  # 开始日期
    end_date = reqest_body.get('end_date', time_now)  # 结束日期
    planid = reqest_body.get('plan_id') #计划号
    orderid = reqest_body.get('order_id')  #制令单号
    prodline = reqest_body.get('prod_line')  #线别


    #返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "proclist":{
            "xdata": [],
            "ydata": []
        }
    }

    cur = connection.cursor()  # 创建游标
    #如果没有壳体条码，那么也不需要装壳和装箱柱状显示了
    sql = "SELECT * from yw_project_info where order_id='%s'" % orderid
    cur.execute(sql)
    modelid_row = cur.fetchone()

    sql = "select coll_type, sum(prod_num) from yw_project_collect_info_direct_err  " \
          "where time_day>='%s'  and time_day<='%s' " % (begin_date, end_date )
    if orderid:
        sql = sql + " and order_id='%s' " % orderid
    if prodline:
        sql = sql + " and prod_line='%s' " % prodline
    sql = sql + "group by coll_type"
    log.info("获取各制程生产数量："+sql)
    cur.execute(sql)
    coll_row = cur.fetchall()
    colldate={}
    if coll_row:
        for item in coll_row:
            colldate[item[0]]=item[1]


    if colldate.get('flashburn')  and colldate.get('flashburn','0') > 0:
        jsondata['proclist']['xdata'].append("烧录")  # 获取烧录总数
        jsondata['proclist']['ydata'].append( colldate.get('flashburn','0') )

    jsondata['proclist']['xdata'].append("产测")     #获取产测总数
    jsondata['proclist']['ydata'].append(colldate.get('prodtest','0'))

    if modelid_row:
        jsondata['proclist']['xdata'].append("装壳")      #获取抄表总数
        jsondata['proclist']['ydata'].append(colldate.get('egsnid','0'))

    jsondata['proclist']['xdata'].append("抄表")     #获取装壳总数
    jsondata['proclist']['ydata'].append(colldate.get('meterread','0'))

    if modelid_row:
        jsondata['proclist']['xdata'].append("装箱")      #获取装箱总数
        jsondata['proclist']['ydata'].append(colldate.get('box','0'))

    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------mesapp_getprocinfo_end---------------------------')
    return HttpResponse(s)

# 获取项目信息列表--MES第一层，根据时间段获取排产的计划信息
def getprojectlist(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_getprojlist_begin---------------------------')

    planid = reqest_body.get('plan_id') #计划号
    orderid = reqest_body.get('order_id')  #制令单号
    prodline = reqest_body.get('prod_line')  #线别

    #当前日期
    time_now = datetime.datetime.now().strftime('%Y-%m-%d')
    begin_date = reqest_body.get('begin_date', time_now)  # 开始日期
    end_date = reqest_body.get('end_date', time_now)  # 结束日期

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "projectlist": [],
        "prodlinelist": []
    }

    cur = connection.cursor()

    # 获取线别字典
    syscfg_prodline_dict = {}
    sql = "select dict_code, dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PLAN_INFO.PROD_LINE'"
    cur.execute(sql)
    rows = cur.fetchall()
    for item in rows:
        syscfg_prodline_dict[item[0]] = item[1]

    # 查询计划信息表
    sql = "select distinct plan_id from yw_project_plan_info " \
          "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(prod_date,'%%Y-%%m-%%d')<='%s' " \
          "and sync_flag='1' and state='1' " % (begin_date, end_date)
    if planid:
        sql = sql + " and plan_id='%s' " % planid
    log.info("查询生产计划信息:" + sql)
    cur.execute(sql)
    plan_rows = cur.fetchall()
    projectlist = []
    for plan_item in plan_rows:
        db_planid=plan_item[0]
        # 根据计划号查询制令信息
        sql = "select distinct order_id from yw_project_plan_info " \
              "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(prod_date,'%%Y-%%m-%%d')<='%s'  " \
              "and plan_id='%s' and sync_flag='1' and state='1'" % (begin_date, end_date, db_planid)
        log.info("根据计划号查询制令信息:" + sql)
        cur.execute(sql)
        mo_rows = cur.fetchall()
        mo_list = []
        for mo_item in mo_rows:
            db_orderid = mo_item[0]
            # 制令号查询线别信息
            sql = "select prod_line, prd_name, sum(today_plan_num), sum(finish_num)  from yw_project_plan_info " \
                  "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')>='%s' and DATE_FORMAT(prod_date,'%%Y-%%m-%%d')<='%s' " \
                  "and plan_id='%s' and order_id='%s' and sync_flag='1' and state='1' group by prod_line, prd_name " \
                  % (begin_date, end_date, db_planid, db_orderid)
            log.info("根据计划号+制令号查询线别信息:" + sql)
            cur.execute(sql)
            prodline_rows = cur.fetchall()
            prodline_list = []

            for prodline_item in prodline_rows:
                db_prodline = prodline_item[0]
                db_spcname = prodline_item[1]
                db_plannum = prodline_item[2]
                act_allcount = prodline_item[3]
                prodlineitem_list = []
                tabledata = []
                tabledata.append({'name': '线别名称', 'value': syscfg_prodline_dict.get(db_prodline, '未知线别')})
                tabledata.append({'name': '制品名称', 'value': db_spcname})
                tabledata.append({'name': '计划生产总数', 'value': db_plannum})
                tabledata.append({'name': '已生产总数', 'value': act_allcount})

                #获取今日计划生产总数
                sql = "select today_plan_num, finish_num  from yw_project_plan_info " \
                      "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s' and plan_id='%s' and order_id='%s' and prod_line='%s' " \
                      "and sync_flag='1' and state='1'" \
                      % (time_now, db_planid, db_orderid, db_prodline)
                cur.execute(sql)
                today_row = cur.fetchone()
                if today_row:
                    db_today_plannum = today_row[0]
                    db_today_actnum = today_row[1]
                else:
                    db_today_plannum = 0
                    db_today_actnum = 0
                tabledata.append({'name': '今日计划生产数', 'value': db_today_plannum})
                tabledata.append({'name': '今日实际生产数', 'value': db_today_actnum})

                prodline_dict={}
                prodline_dict['tabledata'] = tabledata
                prodline_dict['finished_num'] = act_allcount
                prodline_dict['unfinished_num'] = db_plannum - act_allcount
                if db_plannum:
                    prodline_dict['finished_scale'] = int(act_allcount * 100 / db_plannum)
                else:
                    prodline_dict['finished_scale'] = 0
                prodlineitem_list.append(prodline_dict) #线别信息

                # 线别信息
                prodline_list.append( {"name": db_prodline,  "value": prodlineitem_list} )
            #制令信息
            mo_list.append( {"name": db_orderid, "value": prodline_list} )
        #计划信息
        projectlist.append( {"name": db_planid, "value": mo_list} )
    #结果赋值
    jsondata["projectlist"] = projectlist

    # 获取线别
    prodlinelist = []
    sql = "select distinct prod_line from yw_project_plan_info where  DATE_FORMAT(prod_date,'%%Y-%%m-%%d')>='%s' " \
          "and DATE_FORMAT(prod_date,'%%Y-%%m-%%d')<='%s' and sync_flag='1' and state='1' order by prod_line asc" \
          % (begin_date, end_date)
    cur.execute(sql)
    rows = cur.fetchall()
    for item in rows:
        prodlinelist.append({item[0]: syscfg_prodline_dict.get(item[0], '未知线别')})
    jsondata["prodlinelist"] = prodlinelist

    cur.close()  # 主动关闭游标

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------mesapp_getprojlist_end---------------------------')
    return HttpResponse(s)


# 根据时间段获取各工站的生产信息
def getstationinfo(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_getprojlist_begin---------------------------')

    # 当前日期
    time_now = datetime.datetime.now().strftime('%Y-%m-%d')
    begin_date = reqest_body.get('begin_date', time_now)  # 开始日期
    end_date = reqest_body.get('end_date', time_now)  # 结束日期
    planid = reqest_body.get('plan_id') #计划号
    orderid = reqest_body.get('order_id')  #制令单号
    prodline = reqest_body.get('prod_line')  #线别

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "allstation": [],
        "infolist": [
            # {
            #     "name": '产测不良数量',
            #     "value": '62'
            # },
        ]
    }

    cur = connection.cursor()

    #获取所有配置的工站-参数
    sql = "select Platform_win_num, station_num, station_type, prod_line from yw_project_prodline_term where station_type is not null "
    log.info('获取所有配置的工站:' + sql)
    cur.execute(sql)
    rows = cur.fetchall()
    stationinfo = {}
    for item in rows:
        stationinfo[item[0]]={ "station_num":item[1], "station_type":item[2], "prod_line":item[3] }
    log.info("获取所有配置的工站:" + str(stationinfo) )

    total_flashburn_err_num = 0  # 获取烧录不良数量
    total_prodtest_err_num = 0  # 获取产测不良数量
    total_meterread_err_num = 0  # 抄表不良数量
    total_egsnid_err_num = 0  # 装壳不良数量
    total_box_err_num = 0  # 装箱不良数量
    # 获取工站生产信息
    sql = "select coll_type, station, sum(prod_num), sum(prod_direct_num), sum(prod_err_num) from yw_project_collect_info_direct_err " \
          "where time_day>='%s' and time_day<='%s' " \
          % (begin_date, end_date)
    if orderid:
        sql = sql + " and order_id='%s' " % orderid
    if prodline:
        sql = sql + " and prod_line='%s' " % prodline
    sql = sql + " group by coll_type, station "
    log.info("获取工站生产信息:" + sql)
    cur.execute(sql)
    rows = cur.fetchall()
    workstation_keys=[]
    for item in rows:
        ProdStationInfo = {}
        ProdStationInfo['prod_num'] = item[2]
        prod_direct_num = item[3]
        ProdStationInfo['fail_num'] = item[4]
        ProdStationInfo['misdetect_num'] = ProdStationInfo['prod_num'] - prod_direct_num - ProdStationInfo['fail_num']
        if ProdStationInfo['misdetect_num'] < 0:
            ProdStationInfo['misdetect_num'] = 0
        ProdStationInfo['prod_type'] = str(item[0])

        #根据台机名称获取工站名称
        station = item[1]
        workstation_keys.append(station)
        if stationinfo.get(station):
            station_name=stationinfo[station]['station_num']
        else:
            station_name='多功能工站'

        # 根据生产类型获取工站名称
        if ProdStationInfo['prod_type'] == 'flashburn':
            station_type = '烧录'
            ProdStationInfo['border_color'] = 'rgba(70,130,180,0.2)'
            total_flashburn_err_num = total_flashburn_err_num + ProdStationInfo['fail_num']  # 获取烧录不良数量
        elif ProdStationInfo['prod_type'] == 'prodtest':
            station_type = '产测'
            ProdStationInfo['border_color'] = 'rgba(19,208,178,0.2)'
            total_prodtest_err_num = total_prodtest_err_num + ProdStationInfo['fail_num']  # 获取产测不良数量
        elif ProdStationInfo['prod_type'] == 'meterread':
            station_type = '抄表'
            ProdStationInfo['border_color'] = 'rgba(255,235,59,0.2)'
            total_meterread_err_num = total_meterread_err_num + ProdStationInfo['fail_num']  # 获取抄表不良数量
        elif ProdStationInfo['prod_type'] == 'egsnid':
            station_type = '装壳'
            ProdStationInfo['border_color'] = 'rgba(33,150,243,0.3)'
            total_egsnid_err_num = total_egsnid_err_num + ProdStationInfo['fail_num']  # 获取装壳不良数量
        elif ProdStationInfo['prod_type'] == 'box':
            station_type = '装箱'
            ProdStationInfo['border_color'] = 'rgba(179,136,255,0.3)'
            total_box_err_num = total_box_err_num + ProdStationInfo['fail_num']  # 获取装箱不良数量
        else:
            station_type = '特殊工序'
            ProdStationInfo['border_color'] = 'rgba(179,136,255,0.3)'

        ProdStationInfo['station_num'] = station_type+'-'+station_name #界面展示的机台名称

        ProdStationInfo['misdetect_percentage'] = round( float(ProdStationInfo['misdetect_num'] / ProdStationInfo['prod_num']) * 100.00, 2)
        ProdStationInfo['fail_percentage'] = round(float(ProdStationInfo['fail_num'] / ProdStationInfo['prod_num']) * 100.00, 2)
        if ProdStationInfo['fail_percentage'] > 5:
            ProdStationInfo['status'] = 3  # 工位状态0:无工作 1：绿灯、2：黄灯、3：红灯
        elif ProdStationInfo['fail_percentage'] > 1:
            ProdStationInfo['status'] = 2
        else:
            ProdStationInfo['status'] = 1

        jsondata['allstation'].append(ProdStationInfo)

        # ProdStationInfo['status'] = 0  # 工位状态0:无工作
    cur.close()  # 主动关闭游标

    #今天未投入使用的工站也显示出来
    # { "station_num":item[1], "station_type":item[2], "prod_line":item[3] }
    for item in stationinfo:
        log.info(str(item))
        if item not in workstation_keys and prodline == stationinfo[item]["prod_line"]:
            # 无数据, 停工状态
            ProdStationInfo={}
            ProdStationInfo['prod_num'] = 0
            ProdStationInfo['misdetect_num'] = 0
            ProdStationInfo['fail_num'] = 0
            ProdStationInfo['misdetect_percentage'] = 0
            ProdStationInfo['fail_percentage'] = 0
            ProdStationInfo['status'] = 0  # 工位状态0:无工作
            ProdStationInfo['prod_type'] = stationinfo[item]["station_type"]
            # 根据生产类型获取工站名称
            if ProdStationInfo['prod_type'] == 'flashburn':
                station_type = '烧录'
                ProdStationInfo['border_color'] = 'rgba(70,130,180,0.2)'
            elif ProdStationInfo['prod_type'] == 'prodtest':
                station_type = '产测'
                ProdStationInfo['border_color'] = 'rgba(19,208,178,0.2)'
            elif ProdStationInfo['prod_type'] == 'meterread':
                station_type = '抄表'
                ProdStationInfo['border_color'] = 'rgba(255,235,59,0.2)'
            elif ProdStationInfo['prod_type'] == 'egsnid':
                station_type = '装壳'
                ProdStationInfo['border_color'] = 'rgba(33,150,243,0.3)'
            elif ProdStationInfo['prod_type'] == 'box':
                station_type = '装箱'
                ProdStationInfo['border_color'] = 'rgba(179,136,255,0.3)'
            else:
                station_type = '特殊工序'
                ProdStationInfo['border_color'] = 'rgba(179,136,255,0.3)'

            ProdStationInfo['station_num'] = station_type + '-' +  stationinfo[item]["station_num"]  # 界面展示的机台名称
            log.info(str(ProdStationInfo))
            jsondata['allstation'].append(ProdStationInfo)
        else:
            continue



    jsondata['infolist'].append({"name": "产测不良数量", "value": total_prodtest_err_num})
    jsondata['infolist'].append({"name": "抄表不良数量", "value": total_meterread_err_num})
    jsondata['infolist'].append({"name": "装壳不良数量", "value": total_egsnid_err_num})
    jsondata['infolist'].append({"name": "装箱不良数量", "value": total_box_err_num})
    jsondata['infolist'].append({"name": "维修数量", "value": 0}) #暂无维修数据
    jsondata['infolist'].append({"name": "已修好数量", "value": 0})  # 暂无维修数据
    jsondata['infolist'].append({"name": "报废数量", "value": 0})  # 暂无维修数据

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------mesapp_getprojlist_end---------------------------')
    return HttpResponse(s)

# 获取生产统计表
def getproform(request, reqest_body):
    log = public.logger
    log.info('----------------------mesapp_getproform_begin---------------------------')

    begin_date = reqest_body.get('begin_date',None)  # 开始日期
    end_date = reqest_body.get('end_date',None)  # 结束日期
    planid = reqest_body.get('plan_id',None)  # 计划号
    orderid = reqest_body.get('order_id',None)  # 制令单号
    prodline = reqest_body.get('prod_line',None)  # 线别

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    def getformdata(sql1,sql2):
        data = {}
        cur = connection.cursor()
        if orderid:
            cur.execute(sql1, (begin_date, end_date, orderid, prodline))
            rows = cur.fetchall()
        else:
            cur.execute(sql2, (begin_date, end_date, prodline))
            rows = cur.fetchall()
        errlist = []
        if rows:
            for item in rows:
                data[item[0]] = {}
                errlist.append(item[1])
            for item in rows:
                data[item[0]][item[1]] = item[2]
        errlist = list(set(errlist))
        tablehead = [{'name': "err_type", 'label': "错误类型", 'width': 200}]
        tabledata = []
        flag = 0
        for err in errlist:
            flag = flag + 1
            err_total = 0
            tmp_dict = {'err_type': err}
            for win in data.keys():
                if flag == 1:
                    tablehead.append({'name': win, 'label': win, 'width': 200})
                print('data[win]=',data[win])
                num = data[win].get(err, 0)
                tmp_dict[win] = num
                err_total = err_total + num
            tmp_dict['total'] = err_total
            tabledata.append(tmp_dict)
        tablehead.append({'name': "total", 'label': "合计", 'width': 200})
        cur.close()
        return tablehead,tabledata

    alldict = {}
    proitems = [
        {
            'name': 'protest',
            'label': '产测'
        }, {
            'name': 'meter',
            'label': '抄表'
        }, {
            'name': 'snid',
            'label': '装壳'
        }, {
            'name': 'box',
            'label': '装箱'
        }
    ]
    activename = 'protest'

    # 产测信息
    pro_test_data = {}
    pro_test_sql1 = "SELECT Platform_Num,Test_Value,COUNT(Test_Value) as fail_num from yw_project_product_test_info " \
                    "WHERE DATE_FORMAT(insert_date,'%%Y-%%m-%%d')>=%s AND DATE_FORMAT(insert_date,'%%Y-%%m-%%d')<=%s and Batch_Num = %s AND " \
                    "prod_line = %s and Test_Result = 'Fail' GROUP BY Test_Value,Platform_Num"
    pro_test_sql2 = "SELECT Platform_Num,Test_Value,COUNT(Test_Value) as fail_num from yw_project_product_test_info " \
                    "WHERE DATE_FORMAT(insert_date,'%%Y-%%m-%%d')>=%s AND DATE_FORMAT(insert_date,'%%Y-%%m-%%d')<=%s AND " \
                    "prod_line = %s and Test_Result = 'Fail' GROUP BY Test_Value,Platform_Num"
    pro_test_tablehead,pro_test_tabledata = getformdata(pro_test_sql1,pro_test_sql2)
    alldict['protest'] = {
        'tablehead': pro_test_tablehead,
        'tabledata': pro_test_tabledata
    }

    # 抄表信息
    meter_data = {}
    meter_sql1 = "SELECT Platform_Num,Test_Value,COUNT(Test_Value) as fail_num from yw_project_meterread_test_info " \
                 "WHERE DATE_FORMAT(insert_date,'%%Y-%%m-%%d')>=%s AND DATE_FORMAT(insert_date,'%%Y-%%m-%%d')<=%s and Batch_Num = %s " \
                 "AND prod_line = %s and Test_Result = 'Fail' GROUP BY Test_Value,Platform_Num"
    meter_sql2 = "SELECT Platform_Num,Test_Value,COUNT(Test_Value) as fail_num from yw_project_meterread_test_info " \
                 "WHERE DATE_FORMAT(insert_date,'%%Y-%%m-%%d')>=%s AND DATE_FORMAT(insert_date,'%%Y-%%m-%%d')<=%s " \
                 "AND prod_line = %s and Test_Result = 'Fail' GROUP BY Test_Value,Platform_Num"
    meter_tablehead,meter_tabledata = getformdata(meter_sql1,meter_sql2)
    alldict['meter'] = {
        'tablehead': meter_tablehead,
        'tabledata': meter_tabledata
    }

    # 装壳信息
    snid_sql1 = "SELECT win_id,CONCAT(err_code,'-',err_msg) as errs,COUNT(err_code) FROM yw_project_snid_detail_error " \
               "WHERE DATE_FORMAT(tran_date,'%%Y-%%m-%%d')>=%s AND DATE_FORMAT(tran_date,'%%Y-%%m-%%d')<=%s AND order_id=%s " \
               "AND prod_line =%s GROUP BY win_id,err_code"
    snid_sql2 = "SELECT win_id,CONCAT(err_code,'-',err_msg) as errs,COUNT(err_code) FROM yw_project_snid_detail_error " \
                "WHERE DATE_FORMAT(tran_date,'%%Y-%%m-%%d')>=%s AND DATE_FORMAT(tran_date,'%%Y-%%m-%%d')<=%s " \
                "AND prod_line =%s GROUP BY win_id,err_code"
    snid_tablehead, snid_tabledata = getformdata(snid_sql1, snid_sql2)
    alldict['snid'] = {
        'tablehead': snid_tablehead,
        'tabledata': snid_tabledata
    }

    # snid_data = {}
    # cur = connection.cursor()
    # if orderid:
    #     cur.execute(snid_sql1,(begin_date,end_date,orderid,prodline))
    #     snid_rows = cur.fetchall()
    # else:
    #     cur.execute(snid_sql2, (begin_date, end_date, prodline))
    #     snid_rows = cur.fetchall()
    # snid_err = []
    # if snid_rows:
    #     for item in snid_rows:
    #         snid_data[item[0]] = {}
    #         snid_err.append(item[1])
    #     for item in snid_rows:
    #         snid_data[item[0]][item[1]] = item[2]
    # snid_err = list(set(snid_err))
    # snid_tablehead = [{'name': "err_type",'label': "错误类型",'width': 200}]
    # snid_tabledata = []
    # snid_flag = 0
    # for err in snid_err:
    #     snid_flag = snid_flag + 1
    #     err_total = 0
    #     tmp_dict = {'err_type':err}
    #     for win in snid_data.keys():
    #         if snid_flag==1:
    #             snid_tablehead.append({'name': win,'label': win,'width': 200})
    #         num = snid_data[win].get(err,0)
    #         tmp_dict[win] = num
    #         err_total = err_total +num
    #     tmp_dict['total'] = err_total
    #     snid_tabledata.append(tmp_dict)
    # snid_tablehead.append({'name': "total",'label': "合计",'width': 200})
    # cur.close()



    # 装箱信息

    box_sql1 = "SELECT win_id,CONCAT(err_code,'-',err_msg) as errs,COUNT(err_code) FROM yw_project_boxing_info_error " \
               "WHERE DATE_FORMAT(tran_date,'%%Y-%%m-%%d')>=%s AND DATE_FORMAT(tran_date,'%%Y-%%m-%%d')<=%s AND order_id=%s " \
               "AND prod_line =%s GROUP BY win_id,err_code"
    box_sql2 = "SELECT win_id,CONCAT(err_code,'-',err_msg) as errs,COUNT(err_code) FROM yw_project_boxing_info_error " \
               "WHERE DATE_FORMAT(tran_date,'%%Y-%%m-%%d')>=%s AND DATE_FORMAT(tran_date,'%%Y-%%m-%%d')<=%s " \
               "AND prod_line =%s GROUP BY win_id,err_code"
    box_tablehead, box_tabledata = getformdata(box_sql1, box_sql2)
    alldict['box'] = {
        'tablehead': box_tablehead,
        'tabledata': box_tabledata
    }

    jsondata['alldict'] = alldict
    jsondata['proitems'] = proitems
    jsondata['activename'] = activename
    jsondata['fileurl'] = ''

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------mesapp_getproform_end---------------------------')
    return HttpResponse(s)


#nse(s)


