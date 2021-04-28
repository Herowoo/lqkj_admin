from django.shortcuts import HttpResponse
import json
import datetime
from admin_app import public
from admin_app import models
from django.db import connection, transaction
import pymssql

try:
    sqlserver_conn=pymssql.connect(server='192.168.2.222', user='sa', password='Lqiot.com', database="lq_hplc", timeout=20, autocommit=True)  # 获取连接  #sqlserver数据库链接句柄
except:
    pass

##联桥科技扫码配对工装的接口
def main(request):
    if request.method == "POST":
        log = public.logger
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        reqest_body=json.loads(tmp)

        trantype=reqest_body['trantype']
        # print('-'*20,trantype,'-'*20)
        log.info('trantype=[%s]' % trantype)
        if trantype == 'getprojectinfo':  #预览-返回url打开新页面
            resp = getprojectinfo(request, reqest_body)
        elif trantype == 'register_snid':  #扫码配对工装登记扫码信息
            resp = register_snid(request, reqest_body)
        elif trantype == 'getprojectinfo':  #提交-发交易到后台
            resp = getprojectinfo(request, reqest_body)
        elif trantype=='boxing':
            resp=boxing(request,reqest_body)#装箱
        elif trantype=='get_gwid':
            resp=get_gwid(request,reqest_body)#获取国网id
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp


#获取项目信息列表
def getprojectinfo(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjsmpd-getprojectinfo-begin---------------------------')

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "projectinfo": []
    }

    cur = connection.cursor() #创建游标
    #根据制令单号获取计划号
    time_now = datetime.datetime.now().strftime('%Y-%m-%d')
    sql = "select order_id, plan_id from yw_project_plan_info where DATE_FORMAT(begin_date,'%%Y-%%m-%%d') <='%s'" \
          " and DATE_FORMAT(end_date,'%%Y-%%m-%%d') >='%s'" % ( time_now, time_now )
    log.info("查询今日计划和昨日生产量:" + sql)
    cur.execute(sql)
    rows = cur.fetchall()
    if len(rows)==0:
        cur.close()
        s = public.setrespinfo({"respcode": "500498", "respmsg": "无当日生产计划!"})
        return HttpResponse(s)

    for item in rows:
        log.info( str(item) )
        projinfo = {}
        orderid=item[0]
        planid=item[1]
        projinfo["order_id"] = orderid

        #根据计划号获取生产信息
        sql = "select order_id,spc_name,begin_id,end_id from yw_project_info where plan_id='%s' " % planid
        log.info( sql )
        cur.execute( sql )
        row = cur.fetchone()
        if row:
            projinfo["plan_id"]=planid
            projinfo["order_msg"]=row[1]
            projinfo["begin_id"]=row[2]
            projinfo["end_id"]=row[3]
            jsondata["projectinfo"].append(projinfo)

    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjsmpd-getprojectinfo-end---------------------------')
    return HttpResponse(s)

#扫码配对工装登记扫码信息
def register_snid(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjsmpd-register_snid-begin---------------------------')

    orderid=reqest_body.get('order_id',None)
    winid = reqest_body.get('win_id', None)
    modelid = reqest_body.get('model_id', None)
    pcbsn = reqest_body.get('pcb_sn', None)
    gwid = reqest_body.get('gw_id', None)

    try:
        int_sn=int(pcbsn[2:])
    except Exception:
        s = public.setrespinfo({"respcode": "500100", "respmsg": "SN码未写入芯片,请再次产测!"})
        return HttpResponse(s)
    if int_sn==0:
        s = public.setrespinfo({"respcode": "500100", "respmsg": "SN码未写入芯片,请再次产测!"})
        return HttpResponse(s)

    cur = connection.cursor() #创建游标

    #根据制令单号获取计划号
    sql = "select id, plan_id from yw_project_plan_info where order_id='%s' " % (orderid)
    log.info("查询今日计划和昨日生产量:" + sql)
    cur.execute(sql)
    coll_row = cur.fetchone()
    if coll_row:
        pkid = coll_row[0]
        planid = coll_row[1]
    else:
        cur.close()
        s = public.setrespinfo({"respcode": "500499", "respmsg": "制令单号错误，根据制令单号查不到计划号!"})
        return HttpResponse(s)

    #查看项目信息
    sql = "select plan_id,spc_name,begin_id,end_id, plan_id from yw_project_info " \
          "where proj_state='1' and plan_id=%s and begin_date<=%s and end_date >=%s"  # order by ID desc
    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log.info( sql % (planid,time_now,time_now) )
    cur.execute( sql, (planid,time_now,time_now) )
    rows = cur.fetchone()
    # print('查看项目信息=',rows)
    if rows==None:
        cur.close()
        s = public.setrespinfo({"respcode": "500100", "respmsg": "计划单号错误!"})
        return HttpResponse(s)

    projdetail = {}
    projdetail["order_id"] = orderid
    projdetail["plan_id"] = planid
    projdetail["spc_name"] = rows[1]
    db_begin_id = rows[2]
    db_end_id = rows[3]
    db_model_id = modelid
    if db_begin_id[-1] == 'X' and db_end_id[-1] == 'X':
        db_begin_id = db_begin_id[0:-1]
        db_end_id = db_end_id[0:-1]
        db_model_id = modelid[0:-1]
    cur.close()

    #判断数据是否合法
    if db_model_id < db_begin_id or db_model_id > db_end_id or len(db_model_id)!=len(db_begin_id) or len(db_model_id)!=len(db_end_id):
        # log.info("模块ID不在项目范围")
        s = public.setrespinfo({"respcode": "500101", "respmsg": "模块ID不在项目范围!"})
        return HttpResponse(s)

    #判断是否重复绑定，如果是重复绑定，登记历史表
    cur = connection.cursor()
    sql = "select count(1) from yw_project_snid_detail where state='1' and model_id=%s and pcb_sn=%s and gw_id=%s"
    log.info(sql % (modelid,pcbsn,gwid) )
    cur.execute(sql, (modelid,pcbsn,gwid) )
    rows = cur.fetchone()
    exist_flag = rows[0]
    cur.close()
    if exist_flag > 0:
        #重复绑定流程

        #登记历史表数据
        insertsql = "insert into yw_project_snid_detail_his(tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state) " \
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        log.info(insertsql % (datetime.datetime.now(), projdetail["order_id"], projdetail["plan_id"], projdetail["spc_name"],
                              pcbsn, modelid, gwid, winid, "1"))
        cur = connection.cursor()
        cur.execute(insertsql, (datetime.datetime.now(), projdetail["order_id"], projdetail["plan_id"], projdetail["spc_name"],
                              pcbsn, modelid, gwid, winid, "1"))
        cur.close()

        #更新扫码配对工装
        ret, retmsg=sendtosqlserver(planid, modelid, gwid, pcbsn)
        if ret < 0:
            s = public.setrespinfo({"respcode": "010101", "respmsg": retmsg})
            return HttpResponse(s)
        #不好用，不再使用，通过异步同步方式解决问题

    else:
        #查看芯片ID是否是这一个计划之内的
        cur = connection.cursor()
        # log.info('gwid, projdetail["order_id"]'+str(gwid)+str(projdetail["order_id"]) )
        sql = "select count(1) from yw_project_gwid_detail where gw_id='%s' and proj_id='%s'"  % (gwid, projdetail["plan_id"])
        log.info(sql )
        cur.execute(sql)
        rows = cur.fetchone()
        exists = rows[0]
        cur.close()
        if exists <= 0:
            s = public.setrespinfo({"respcode": "500109", "respmsg": "芯片ID不在本批次内!"})
            return HttpResponse(s)

        #查看模块ID是否已经有数据
        cur = connection.cursor()
        sql = "select count(1) from yw_project_snid_detail where state='1' and model_id=%s"
        log.info(sql % modelid)
        cur.execute(sql, modelid)
        rows = cur.fetchone()
        exists=rows[0]
        cur.close()
        if exists>0:
            s = public.setrespinfo({"respcode": "500102", "respmsg": "模块ID已经被绑定使用!"})
            return HttpResponse(s)

        #查看PCB_SN是否已经有数据
        cur = connection.cursor()
        sql = "select count(1) from yw_project_snid_detail where state='1' and pcb_sn=%s"
        log.info(sql % pcbsn)
        cur.execute(sql, pcbsn)
        rows = cur.fetchone()
        exists=rows[0]
        cur.close()
        if exists>0:
            s = public.setrespinfo({"respcode": "500103", "respmsg": "SN码已经被绑定使用!"})
            return HttpResponse(s)

        #查看gw_id是否已经有数据
        cur = connection.cursor()
        sql = "select count(1) from yw_project_snid_detail where state='1' and gw_id=%s"
        log.info(sql % gwid)
        cur.execute(sql, gwid)
        rows = cur.fetchone()
        exists=rows[0]
        cur.close()
        if exists>0:
            s = public.setrespinfo({"respcode": "500104", "respmsg": "国网ID已经被绑定使用!"})
            return HttpResponse(s)

        #检查无误，登记IDSN绑定关系
        projdetail["tran_date"]=datetime.datetime.now()
        projdetail["win_id"] = winid
        projdetail["model_id"] = modelid
        projdetail["pcb_sn"] = pcbsn
        projdetail["gw_id"]=gwid
        projdetail["state"] = '1'
        insertsql= "insert into yw_project_snid_detail(tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state) " \
                   "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        log.info(insertsql % (projdetail["tran_date"],projdetail["order_id"], projdetail["plan_id"],projdetail["spc_name"],
                              projdetail["pcb_sn"],projdetail["model_id"],projdetail["gw_id"],projdetail["win_id"],projdetail["state"]))
        cur = connection.cursor()
        cur.execute(insertsql, (projdetail["tran_date"],projdetail["order_id"], projdetail["plan_id"],projdetail["spc_name"],
                                projdetail["pcb_sn"],projdetail["model_id"],projdetail["gw_id"],projdetail["win_id"],projdetail["state"]) )
        cur.close()

        #登记历史表数据
        insertsql = "insert into yw_project_snid_detail_his(tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state) " \
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        log.info(insertsql % (projdetail["tran_date"],projdetail["order_id"], projdetail["plan_id"],projdetail["spc_name"],
                              projdetail["pcb_sn"],projdetail["model_id"], projdetail["gw_id"],projdetail["win_id"],projdetail["state"]))
        cur = connection.cursor()
        cur.execute(insertsql, (projdetail["tran_date"],projdetail["order_id"], projdetail["plan_id"],projdetail["spc_name"],
                                projdetail["pcb_sn"],projdetail["model_id"],projdetail["gw_id"],projdetail["win_id"],projdetail["state"]) )
        cur.close()

        #更新国网ID表数据
        updsql = "update yw_project_gwid_detail set gl_id='%s', state='1' where gw_id='%s'" % (projdetail["model_id"], projdetail["gw_id"])
        log.info(updsql)
        cur = connection.cursor()
        cur.execute(updsql)
        cur.close()

        #更新扫码配对工装
        ret, retmsg=sendtosqlserver(planid, modelid, gwid, pcbsn)
        if ret < 0:
            s = public.setrespinfo({"respcode": "010101", "respmsg": retmsg})
            return HttpResponse(s)

    #返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjsmpd-register_snid-end---------------------------')
    return HttpResponse(s)

# 扫码配对装箱SQL
# planid-计划号; modelid-外壳条码; gw_id-芯片ID; nowtime-当前时间; pcb_sn-芯片SN码
def sendtosqlserver(planid, modelid, gw_id, pcb_sn):
    log = public.logger
    global sqlserver_conn
    try:
        sqlserver_conn=sqlserver_dbtest( sqlserver_conn )
        cursor = sqlserver_conn.cursor()  # 获取光标

        # nowtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 更新语句
        updsql = "UPDATE TOP (1) T_barCode SET bc_shellCode = '%s', bc_chipID  = '%s', bc_zhuangKeDateTime = GETDATE(), bc_productionStatus = '20' WHERE bc_barCode = '%s'"
        sql= "BEGIN TRANSACTION;" + updsql % (modelid, gw_id, pcb_sn) + ";COMMIT TRANSACTION;"
        log.info(sql)
        result =cursor.execute(sql)
        log.info("更新语句执行结果"+str(result))

        # 插入语句
        inssql = "INSERT INTO T_RealTimeProduceMX(rtpnmx_dateTime,rtpnmx_status,rtpnmx_code, rj_jiHuaDanHao) VALUES(GETDATE(), '20', '%s', '%s')"
        sql = "BEGIN TRANSACTION;" + inssql % (modelid, planid) + ";COMMIT TRANSACTION;"
        log.info(sql)
        result=cursor.execute(sql)
        log.info("插入语句执行结果" + str(result))
        cursor.close()
        sqlserver_conn.commit()
        # sqlserver_conn.close()
        return 0, '同步成功'
    except Exception as e:
        log.info( str(e) )
        if 'unique index' in str(e):
            return -1, '芯片ID重复!'
        else:
            return -1, '更新生产原数据库表失败!'

#判断数据库的连接状态，如果连接失败，则重新发起连接
def sqlserver_dbtest( conn ):
    log = public.logger
    try:
        cursor = conn.cursor()  # 获取光标
        cursor.execute("select GETDATE()")
        cursor.close()
        return conn
    except Exception as e:
        log.info(str(e))
        log.info('开始连接远程数据库:' + str(datetime.datetime.now()))
        try:
            conn = pymssql.connect(server='192.168.2.222', user='sa', password='Lqiot.com', database="lq_hplc", timeout=20, autocommit=True)  # 获取连接
        except Exception as ex:
            log.info(str(ex))
        log.info('连接远程数据库成功:' + str(datetime.datetime.now()))
        return conn

#自定义异常1-未扫码配对
class SelectException1(Exception):
    pass
#自定义异常2-已经装箱过
class SelectException2(Exception):
    pass
#自定义异常3-箱号有误
class SelectException3(Exception):
    pass
#自定义异常4-制订单号有误
class SelectException4(Exception):
    pass
#自定义异常5-计划号有误
class SelectException5(Exception):
    pass
#装箱记录
@transaction.atomic()
def boxing(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjsmpd-boxing-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    model_list=reqest_body.get('model_list')
    # model_id = reqest_body.get('model_id')
    box_id=reqest_body.get('box_id')
    order_id = reqest_body.get('order_id')
    plan_id=reqest_body.get('plan_id')
    win_id = reqest_body.get('win_id')
    tran_date=datetime.datetime.now()
    state='1'

    cur = connection.cursor()  # 创建游标
    # try:
    # 设置事务保存点
    SuccessFlag = True
    s1 = transaction.savepoint()
    try:
        for model_id in model_list:
            # 查询模块是否已经扫码配对
            sql = "select count(1) from yw_project_snid_detail where model_id='%s' and  state='1'" % model_id
            log.info(sql)
            cur.execute(sql)
            isexist = cur.fetchone()[0]
            if isexist==0:
                raise SelectException1

            # #查询模块是否已经装箱
            # sql = "select box_id from yw_project_boxing_info where model_id='%s' and  state='1'" % model_id
            # log.info(sql)
            # cur.execute( sql )
            # row=cur.fetchone()
            # if row:
            #     boxid=row[0]
            #     if boxid:
            #         raise SelectException2

            # 查询模块装箱信息
            sql = "select box_id,order_id,plan_id,state from yw_project_boxing_info where model_id='%s'" % model_id
            log.info(sql)
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                s_box_id, s_order_id, s_plan_id, s_state=row
                if s_state=='1':
                    raise SelectException2
                if s_box_id!=box_id:
                    raise SelectException3
                if s_order_id!=order_id:
                    raise SelectException4
                if s_plan_id!=plan_id:
                    raise SelectException5



            # #登记装箱信息
            # sql = "insert into yw_project_boxing_info (model_id,box_id,order_id,plan_id,win_id,tran_date,state) value('%s','%s','%s','%s','%s','%s','%s')" \
            #       % (model_id, box_id, order_id, plan_id, win_id, tran_date, state)
            # log.info(sql)
            # cur.execute(sql)

            # 更新装箱信息
            sql = "update yw_project_boxing_info set win_id='%s',tran_date='%s',state='%s' where model_id='%s'" % (win_id, tran_date, state,model_id)
            log.info(sql)
            cur.execute(sql)

        #查询当前装箱信息
        all_count,now_count=0,0
        sql="select count(*) from yw_project_boxing_info where box_id='%s'"%box_id
        log.info(sql)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            all_count=row[0]

        sql = "select count(*) from yw_project_boxing_info where box_id='%s' and state='1'" % box_id
        log.info(sql)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            now_count = row[0]
        jsondata['all_count']=all_count
        jsondata['now_count']=now_count
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    except SelectException1 as e:
        SuccessFlag = False
        log.info("模块ID没有扫码配对:" + str(model_id) )
        s = public.setrespinfo({"respcode": "367001", "respmsg": "模块ID没有扫码配对:" + str(model_id)})
    except SelectException2 as e:
        SuccessFlag = False
        log.info("模块ID已经装入箱子:" + str(s_box_id) )
        s = public.setrespinfo({"respcode": "367001", "respmsg": "模块ID已经装入箱子:" + str(s_box_id)})
    except SelectException3 as e:
        SuccessFlag = False
        log.info("箱号有误:" + str(box_id) )
        s = public.setrespinfo({"respcode": "367001", "respmsg": "箱号有误:" + str(box_id)})
    except SelectException4 as e:
        SuccessFlag = False
        log.info("制订单号有误:" + str(order_id) )
        s = public.setrespinfo({"respcode": "367001", "respmsg": "制订单号有误:" + str(order_id)})
    except SelectException5 as e:
        SuccessFlag = False
        log.info("计划号有误:" + str(plan_id) )
        s = public.setrespinfo({"respcode": "367001", "respmsg": "计划号有误:" + str(plan_id)})
    except Exception as e:
        SuccessFlag = False
        log.info("登记装箱信息失败:" + str(e))
        s = public.setrespinfo({"respcode": "999999", "respmsg": '登记装箱信息失败' + str(e) } )
    except:
        SuccessFlag=False
        log.info('error!')
    finally:
        cur.close()

    if SuccessFlag:
        # 提交事务 (如果没有异常,就提交事务)
        transaction.savepoint_commit(s1)
    else:
        # 事务回滚 (如果发生异常,就回滚事务)
        transaction.savepoint_rollback(s1)

    # s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjsmpd-boxing-end---------------------------')
    return HttpResponse(s)


#获取国网id
def get_gwid(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjsmpd-get_gwid-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    orderid=reqest_body.get('order_id')
    modelid = reqest_body.get('model_id', None)

    if orderid:
        pass
    else:
        s = public.setrespinfo({"respcode": "500510", "respmsg": "缺少参数"})
        return HttpResponse(s)
    cur = connection.cursor()  # 创建游标

    #先判断modelid是不是自动化线已经关联过的
    if modelid:
        sql = "select ks_id, ks_keyid from yw_project_keyidshellbarcode where ks_shell_barcode='%s' " % (modelid)
        log.info("先判断modelid是不是自动化线已经关联过的:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            jsondata['gw_id'] = row[1]
            s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
            log.info(s)

            log.info('----------------------Lqkjsmpd-get_gwid-end---------------------------')
            return HttpResponse(s)


    # 根据制令单号获取计划号
    sql = "select id, plan_id from yw_project_plan_info where order_id='%s' " % (orderid)
    log.info("据制令单号获取计划号:" + sql)
    cur.execute(sql)
    coll_row = cur.fetchone()
    if coll_row:
        pkid = coll_row[0]
        planid = coll_row[1]
    else:
        cur.close()
        s = public.setrespinfo({"respcode": "500499", "respmsg": "制令单号错误，根据制令单号查不到计划号!"})
        return HttpResponse(s)
    #查询空闲国网id
    randstr=public.genRandomString(8)
    sql = "update yw_project_gwid_detail_getinfo set ask_time=NOW(), randstr='%s',gl_id='%s' where proj_id='%s' and state='0' and ask_time is null limit 1" % ( randstr, modelid, planid )
    log.info("锁定一个空闲国网id:" + sql)
    res = cur.execute(sql)
    if res > 0:
        # 更新成功 返回国网id
        sql = "select gw_id from yw_project_gwid_detail_getinfo where randstr='%s'" % randstr
        log.info("查询空闲国网id:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        gw_id = row[0]
        jsondata['gw_id'] = gw_id
    else:
        jsondata['respcode']='111111'
        jsondata['respmsg']='没有可用国网id了'
        jsondata['gw_id']=''

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjsmpd-get_gwid-end---------------------------')
    return HttpResponse(s)