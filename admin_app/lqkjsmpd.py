from django.shortcuts import HttpResponse
import json
import datetime
from admin_app import public
from admin_app import models
from django.db import connection, transaction
import pymssql

global db218
db218=None



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
        elif trantype == 'register_snid_check':  # 扫码配对工装-检查时只管登记一下
            resp = register_snid_check(request, reqest_body)
        elif trantype == 'getprojectinfo':  #提交-发交易到后台
            resp = getprojectinfo(request, reqest_body)
        elif trantype=='boxing':
            resp=boxing(request,reqest_body)#装箱
        elif trantype=='get_gwid':
            resp=get_gwid(request,reqest_body)#获取国网id
        elif trantype=='getBoxInfo':
            resp=getBoxInfo(request,reqest_body)
        elif trantype=='stand_alone_login':
            resp=stand_alone_login(request,reqest_body)
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
    sql = "select order_id, IFNULL(plan_id, 'XX'), gwid_flag, prod_type,IFNULL(msg_info, 'XX') from yw_project_plan_info " \
          "where DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s' and state='1'" % ( time_now )
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
        projinfo["gwid_flag"] = item[2]
        projinfo["order_id"] = orderid
        projinfo["prod_type"] = item[3]
        ordermsginfo = item[4]

        #根据计划号获取生产信息
        sql = "select order_id,spc_name,begin_id,end_id from yw_project_info where order_id='%s' " % orderid
        log.info( sql )
        cur.execute( sql )
        row = cur.fetchone()
        if row:
            projinfo["plan_id"]=planid
            projinfo["order_msg"]=row[1]
            projinfo["begin_id"]=row[2]
            projinfo["end_id"]=row[3]
            jsondata["projectinfo"].append(projinfo)
        else:
            projinfo["plan_id"] = planid
            projinfo["order_msg"] = ordermsginfo
            projinfo["begin_id"] = ''
            projinfo["end_id"] = ''
            jsondata["projectinfo"].append(projinfo)
    #增加线体参数获取-add by litz, 2020.10.22
    sql = "select DICT_CODE,DICT_TARGET from sys_ywty_dict where DICT_NAME='YW_PROJECT_PLAN_INFO.PROD_LINE'"
    log.info("查询线别信息:" + sql)
    cur.execute(sql)
    rows = cur.fetchall()
    line_list = []
    for item in rows:
        line_list.append({
                'name':item[1],
                'value':item[0]
            })
    jsondata["line_list"] = line_list

    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------Lqkjsmpd-getprojectinfo-end---------------------------')
    return HttpResponse(s)

#扫码配对工装登记扫码信息
def register_snid(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjsmpd-register_snid-begin---------------------------')
    orderid=reqest_body.get('order_id',None)
    winid = str(reqest_body.get('win_id', None)).split('/')[0]
    modelid = reqest_body.get('model_id', None)
    pcbsn = reqest_body.get('pcb_sn', None)
    gwid = reqest_body.get('gw_id', None)
    Today = datetime.datetime.now().strftime('%Y-%m-%d')

    if not modelid:
        respcode, respmsg = "500552", "模块ID不可以空!"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)

    def insert_err():
        insert_err_sql = "INSERT INTO yw_project_snid_detail_error(id,tran_date,order_id,prod_line,win_id,model_id,pcb_sn,gw_id,err_code,err_msg) " \
                         "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        Nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur = connection.cursor()
        tuple = (None, Nowtime, orderid, prod_line, winid, modelid, pcbsn, gwid, respcode, respmsg)
        cur.execute(insert_err_sql,tuple)
        cur.close()

    # 查询SN 码最终状态
    def snid_status():
        select_status_sql = "SELECT final_status FROM yw_project_snid_final_status WHERE Board_SN =%s order by id desc limit 1 "
        cur.execute(select_status_sql,pcbsn)
        row = cur.fetchone()
        if row and row[0]!='0':
            return False
        else:
            return True



    cur = connection.cursor() #创建游标

    # 获取线别信息
    select_sql = "select prod_line,station_type,station_num from yw_project_prodline_term " \
                 "where Platform_win_num='%s'" % str(winid)
    cur.execute(select_sql)
    row = cur.fetchone()
    if row:
        prod_line = row[0]
        station_type = row[1]
        station_num = row[2]
    else:
        respcode, respmsg = "500512", "未认证的终端，请联系工程人员!"+str(winid)
        cur.close()
        # insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)
    if not station_type or not station_num:
        respcode, respmsg = "500512", "终端参数配置有误，请联系工程人员!" + str(winid)
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)


    #根据制令单号获取计划号
    sql = "select id, plan_id,gwid_flag,prod_type from yw_project_plan_info where order_id='%s' and prod_line='%s' " \
          "and  DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s' and state='1' " % (orderid, prod_line, Today)
    # log.info("查询今日计划和昨日生产量:" + sql)
    cur.execute(sql)
    coll_row = cur.fetchone()
    if coll_row:
        pkid = coll_row[0]
        planid = coll_row[1]
        gwid_flag = coll_row[2]
        prod_type = coll_row[3]
    else:
        respcode, respmsg = "500499", "制令单号错误，根据制令单号查不到计划号!"
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)

    #查看项目信息
    sql = "select plan_id,spc_name,begin_id, end_id, plan_id from yw_project_info " \
          "where proj_state='1' and order_id=%s and begin_date<=%s and end_date >=%s"  # order by ID desc
    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # log.info( sql % (orderid,time_now,time_now) )
    cur.execute( sql, (orderid,time_now,time_now) )
    rows = cur.fetchone()
    # print('查看项目信息=',rows)
    if rows==None:
        respcode, respmsg = "500100", "计划单号错误!"
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)


    # add by litz, 20200401, 摄像头读取条形码异常时，判断条形码规格是否正确。
    if len(modelid)==22  and prod_type not in ('COMMON_NCK_MODELID'): #22位的有效验位
        zjq = 0
        for j in range(0, len(modelid) - 1):
            qz = (3 if (j % 2 == 0) else 1)
            zjq = zjq + int(modelid[j]) * int(qz)
        a, b = divmod(zjq, 10)
        checksum = (10 - b if (b > 0) else 0)
        if str(modelid[-1]) != str(checksum):
            respcode,respmsg = "500190","模块ID识别有误,校验值错!"
            insert_err()
            s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
            return HttpResponse(s)
    # end by litz, 20200401

    try:
        int_sn=len(pcbsn[2:])
    except Exception:
        respcode, respmsg = "500100", "SN码未写入芯片,请再次产测!"
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)
    if int_sn==0 or '0'*len(pcbsn[2:])==pcbsn[2:]:
        respcode, respmsg = "500100", "SN码未写入芯片,请再次产测!"
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)

    # SN 最终状态校验
    snflag = snid_status()
    if not snflag:
        respcode, respmsg = "500105", "该模块SN码已转入维修,请联系工程人员确认!"
        insert_err()
        cur.close()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)

    projdetail = {}
    projdetail["order_id"] = orderid
    projdetail["plan_id"] = planid
    projdetail["spc_name"] = rows[1]
    projdetail["pcb_sn"] = pcbsn
    db_begin_id = rows[2]
    db_end_id = rows[3]
    db_model_id = modelid
    if db_begin_id[-1] == 'X' and db_end_id[-1] == 'X':
        db_begin_id = db_begin_id[0:-1]
        db_end_id = db_end_id[0:-1]
        db_model_id = modelid[0:-1]

    #判断数据是否合法
    if db_model_id < db_begin_id or db_model_id > db_end_id or len(db_model_id)!=len(db_begin_id) or len(db_model_id)!=len(db_end_id):
        # log.info("模块ID不在项目范围")
        respcode, respmsg = "500101", "模块ID不在项目范围!"
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)

    #判断产测是否通过---
    sql = "select Chip_mmid from yw_project_product_test_info where Board_SN='%s' and Test_Result='Pass'" % pcbsn
    # log.info("判断产测是否通过:"+sql)
    cur.execute(sql)
    rows = cur.fetchone()
    if not rows:
        respcode, respmsg = "500301", "产测未通过!"
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)
    # if gwid != rows[0]:
    #     respcode, respmsg = "500401", "根据SN查到的产测国网ID和当前不一定，可能PCBA线下更换!"
    #     cur.close()
    #     insert_err()
    #     s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    #     return HttpResponse(s)

    if gwid_flag == '1':
        #查看芯片ID是否是这一个计划之内的
        # log.info('gwid, projdetail["order_id"]'+str(gwid)+str(projdetail["order_id"]) )
        sql = "select count(1) from yw_project_gwid_detail where gw_id='%s' and proj_id='%s'"  % (gwid, projdetail["order_id"])
        # log.info(sql )
        cur.execute(sql)
        rows = cur.fetchone()
        exists = rows[0]
        if exists <= 0:
            respcode, respmsg = "500109", "芯片ID不在本批次内!"
            cur.close()
            insert_err()
            s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
            return HttpResponse(s)

    #查看模块ID是否已经有数据
    if gwid_flag == '1':
        sql = "select count(1) from yw_project_snid_detail where state='1' and model_id=%s and (gw_id!=%s or pcb_sn!=%s) "
        cur.execute(sql, (modelid, gwid, pcbsn))
    else:
        sql = "select count(1) from yw_project_snid_detail where state='1' and model_id=%s and pcb_sn!=%s "
        cur.execute(sql, (modelid, pcbsn))
    rows = cur.fetchone()
    exists=rows[0]
    if exists>0:
        respcode, respmsg = "500102", "模块ID已经被绑定使用!"
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)

    #查看PCB_SN是否已经有数据
    if gwid_flag == '1':
        sql = "select count(1) from yw_project_snid_detail where state='1' and pcb_sn=%s and (model_id!=%s or gw_id!=%s)"
        cur.execute(sql, (pcbsn, modelid, gwid))
    else:
        sql = "select count(1) from yw_project_snid_detail where state='1' and pcb_sn=%s and model_id!=%s "
        cur.execute(sql, (pcbsn, modelid))
    rows = cur.fetchone()
    exists=rows[0]
    if exists>0:
        respcode, respmsg = "500103", "SN码已经被绑定使用!"
        cur.close()
        insert_err()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)

    if gwid_flag == '1':
        #查看gw_id是否已经有数据
        sql = "select count(1) from yw_project_snid_detail where state='1' and gw_id=%s and (model_id!=%s or pcb_sn!=%s) "
        # log.info(sql % gwid)
        cur.execute(sql, (gwid, modelid, pcbsn))
        rows = cur.fetchone()
        exists=rows[0]
        if exists>0:
            respcode, respmsg = "500104", "国网ID已经被绑定使用!"
            cur.close()
            insert_err()
            s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
            return HttpResponse(s)

    # 登记历史表数据
    sql = "insert into yw_project_snid_detail_his(tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state, prod_line) " \
                "select tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state, prod_line from yw_project_snid_detail " \
                "where pcb_sn='%s'"
    log.info(sql % projdetail["pcb_sn"])
    cur.execute(sql % projdetail["pcb_sn"] )
    sql = "delete from yw_project_snid_detail where pcb_sn='%s' "
    log.info(sql % projdetail["pcb_sn"] )
    cur.execute(sql % projdetail["pcb_sn"] )
    if gwid_flag == '1':
        # 查看模块ID和国网ID是否已经分配。
        sql = "select gl_id, gw_id from yw_project_gwid_detail_getinfo where gl_id is not null " \
              "and (gl_id = '%s' or gw_id = '%s') " % (modelid, gwid)
        log.info("查看模块ID和国网ID是否已经分配:" + sql)
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            if item[0] and (item[0] != modelid or item[1] != gwid):
                respcode, respmsg = "500115", "国网ID或模块ID错误!"
                cur.close()
                insert_err()
                s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
                return HttpResponse(s)

    #检查无误，登记IDSN绑定关系
    projdetail["tran_date"]=datetime.datetime.now()
    projdetail["win_id"] = winid
    projdetail["model_id"] = modelid
    projdetail["pcb_sn"] = pcbsn
    if prod_type == '2C-TXID-V2':
        sql = "select txdz_id from yw_project_txdz_detail_getinfo where model_id='%s' and order_id='%s'" \
                    % (projdetail["model_id"], projdetail["order_id"])
        log.info('2C-TXID-V2:'+sql)
        cur.execute(sql)
        row=cur.fetchone()
        if not row:
            respcode, respmsg = "500119", "模块ID和通讯地址的关系未建立!"
            cur.close()
            insert_err()
            s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
            return HttpResponse(s)
        else:
            projdetail["txdz_id"] = row[0]
    elif prod_type == '2C-TXID-V3': #带侧贴标签的二采, 2020-09-09 add by litz,
        sql = "select mac_no from yw_project_2cmac_info where model_id='%s' and order_id='%s'" \
                    % (projdetail["model_id"], projdetail["order_id"])
        log.info("2C-TXID-V3:"+sql)
        cur.execute(sql)
        row=cur.fetchone()
        if not row:
            respcode, respmsg = "500119", "模块ID和通讯地址的关系未建立!"
            cur.close()
            insert_err()
            s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
            return HttpResponse(s)
        else:
            projdetail["writesn_flag"] = True
            projdetail["NewSn"] = row[0]
            projdetail["txdz_id"] = modelid
            #更新使用情况
            sql = "update yw_project_2cmac_info set old_sn_no='%s', gwid='%s', tran_date='%s' " \
                  "where model_id='%s' and order_id='%s'" \
                  % ( pcbsn, gwid, projdetail["tran_date"], projdetail["model_id"], projdetail["order_id"] )
            log.info(sql)
            cur.execute(sql)
    else: #其它类型
        projdetail["txdz_id"] = modelid

    if gwid_flag == '1':
        projdetail["gw_id"] = gwid
    elif "000000000000000000000000000000000000000000000000" in gwid:
        projdetail["gw_id"] = modelid
    else:
        projdetail["gw_id"] = gwid
    projdetail["state"] = '1'

    insertsql= "insert into yw_project_snid_detail(tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state, prod_line) " \
               "VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" \
    % (projdetail["tran_date"],projdetail["order_id"], projdetail["plan_id"], projdetail["spc_name"], projdetail["pcb_sn"],\
       projdetail["model_id"], projdetail["gw_id"], projdetail["win_id"], projdetail["state"], prod_line)
    log.info(insertsql)
    cur.execute(insertsql)

    if gwid_flag == '1':
        #更新国网ID表数据
        updsql = "update yw_project_gwid_detail set gl_id='%s', state='1' where gw_id='%s'" % (projdetail["model_id"], projdetail["gw_id"])
        log.info(updsql)
        cur.execute(updsql)

    cur.close()

    #返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "projdetail":{
            "txdz_id": projdetail["txdz_id"],
            "writesn_flag": projdetail.get('writesn_flag'),
            "NewSn":projdetail.get("NewSn"),
        },
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------Lqkjsmpd-register_snid-end---------------------------')
    return HttpResponse(s)

#获取192.168.2.18数据库连接信息
def get_db218():
    global db218
    log = public.logger
    def db_connect():
        try:
            log.info('开始连接远程数据库:' + str(datetime.datetime.now()))
            db = pymssql.connect(server='10.10.1.250', user='sa', password='luyao123KEJI', database="MEStest",
                                 timeout=20, autocommit=True)  # 获取连接
            log.info('连接远程数据库成功:' + str(datetime.datetime.now()))
        except Exception as e:
            log.info(str(e))
        else:
            return db
    if db218 is None:
        db218 = db_connect()
        return db218
    else:
        try:
            cursor = db218.cursor()  # 获取光标
            cursor.execute("select getdate()")
            cursor.close()
            return db218
        except Exception as e:
            log.info(str(e))
            db218=db_connect()
            return db218


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
#自定义异常6-重复条码
class SelectException6(Exception):
    pass
#自定义异常7-条码不存在
class SelectException7(Exception):
    pass
#自定义异常8-条码不连号
class SelectException8(Exception):
    pass
#自定义异常9-制令单号不存在
class SelectException9(Exception):
    pass
#自定义异常10-未抄表
class SelectException10(Exception):
    pass
#自定义异常11-未产测
class SelectException11(Exception):
    pass
#自定义异常12-硬件版本错误
class SelectException12(Exception):
    pass
#自定义异常13-软件版本错误
class SelectException13(Exception):
    pass
#自定义异常14-厂商代码错误
class SelectException14(Exception):
    pass
#自定义异常15-国网ID重复
class SelectException15(Exception):
    pass


#装箱记录
# @transaction.atomic()
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
    box_id=reqest_body.get('box_id', '')
    order_id = reqest_body.get('order_id', '')
    plan_id=reqest_body.get('plan_id', '')
    win_id = reqest_body.get('win_id', '')
    prod_line = reqest_body.get('prod_line', '')
    tran_date=datetime.datetime.now()
    state='1'

    def insert_err2(log):
        tuple2 = (None, tran_date, order_id, plan_id, win_id, prod_line, str(model_list), box_id, respcode, respmsg)
        insert_err_sql = "INSERT INTO yw_project_boxing_info_error(id,tran_date,order_id,plan_id,win_id,prod_line,model_id,box_id,err_code,err_msg) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur = connection.cursor()
        try:
            cur.execute(insert_err_sql, tuple2)
        except:
            log.info('sql错误')
        # transaction.savepoint_commit(s2)
        # connection.commit()
        # cur.close()

    cur = connection.cursor()  # 创建游标

    # 获取线别信息
    select_sql = "select prod_line,station_type,station_num from yw_project_prodline_term " \
                 "where Platform_win_num='%s'" % str(win_id)
    cur.execute(select_sql)
    row = cur.fetchone()
    if row:
        db_prod_line = row[0]
        station_type = row[1]
        station_num = row[2]
    else:
        respcode, respmsg = "500512", "未认证的终端，请联系工程人员!" + str(win_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)
    if not db_prod_line or not station_type or not station_num:
        respcode, respmsg = "500512", "终端参数配置有误，请联系工程人员!" + str(win_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)
    if db_prod_line != prod_line:
        respcode, respmsg = "500512", "终端线别不一致，请联系工程人员!" + str(win_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)
    # try:
    # 设置事务保存点
    SuccessFlag = True
    s1 = transaction.savepoint()
    try:
        #判断连号情况
        if len(model_list)>1:
            model_list.sort(key=lambda x: x[:-1])
            if int(model_list[-1][:-1])-int(model_list[0][:-1])==len(model_list)-1:
                pass
            else:
                raise SelectException8

        #根据制令单号获取线别和芯片ID配置信息
        Today = datetime.datetime.now().strftime('%Y-%m-%d')
        sql = "select prod_line, gwid_flag, prd_name, Hw_Version, Fw_Version, Vendor_id, prod_type from yw_project_plan_info " \
              "where order_id='%s' and prod_line='%s' and DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s'" \
              % (order_id, prod_line, Today)
        log.info(sql)
        cur.execute(sql)
        row = cur.fetchone()
        auto_flag = False #是否自动化线生产,默认否
        man_flag = False #是否手工线生产,默认否
        smpd_check_flag = False #是否检查芯片ID, 有些无芯片ID，装箱时不需要判断绑定关系
        if row:
            if  row[0] in ['AutoLine1']:
                auto_flag = True
            else:
                man_flag = True
            if row[1] == '1':
                smpd_check_flag = True
            prd_name = row[2]  #产品名称
            hw_version=row[3]  #硬件版本号
            fw_version=row[4]  #软件版本号
            vendor_id =row[5]  #厂商代码
            prod_type = row[6] #生产类型
        else:
            raise SelectException9

        for model_id in model_list:
            # add by litz, 20200401, 摄像头读取条形码异常时，判断条形码规格是否正确。
            if len(model_id) == 22  and prod_type not in ('COMMON_NCK_MODELID'):  # 22位的有效验位
                zjq = 0
                for j in range(0, len(model_id) - 1):
                    qz = (3 if (j % 2 == 0) else 1)
                    zjq = zjq + int(model_id[j]) * int(qz)
                a, b = divmod(zjq, 10)
                checksum = (10 - b if (b > 0) else 0)
                if str(model_id[-1]) != str(checksum):
                    respcode,respmsg = "500190","模块ID识别有误,校验值错!"
                    insert_err2(log)
                    s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
                    return HttpResponse(s)
            # end by litz, 20200401

            # 查询模块装箱信息
            sql = "select box_id,order_id,plan_id,state,gw_id, pcb_sn from yw_project_boxing_info where model_id='%s'" % model_id
            log.info(sql)
            cur.execute(sql)
            row = cur.fetchone()
            # 校验装箱状态 箱号 订单号 计划号
            if row:
                s_box_id, s_order_id, s_plan_id, s_state, s_gw_id, s_pcb_sn = row
                if s_order_id != order_id:
                    raise SelectException4
                if s_plan_id != plan_id:
                    raise SelectException5
                if s_box_id != box_id:
                    raise SelectException3
                if s_state == '1':
                    raise SelectException2
            else:#装箱初始数据未配置
                raise SelectException7

            # 芯片ID校验结果
            if smpd_check_flag:
                check_result_success=False #芯片ID校验结果
                if auto_flag:  #先查自动线，因为自动线生产的生产的快
                    # 自动化线的产测数据,经过自动化线的有数据之后才能装箱
                    sql2 = "SELECT ks_KeyID, ks_SN  FROM [dbo].[T_KeyIDShellBarCode] WHERE ks_shell_barcode = '%s'" % model_id
                    log.info(sql2)
                    db218 = get_db218()
                    cursor218 = db218.cursor()
                    cursor218.execute(sql2)
                    row2 = cursor218.fetchone()
                    if row2:
                        gw_id, pcb_sn = row2
                        check_result_success = True
                    cursor218.close()
                    db218.close()
                if man_flag and not check_result_success: #可能有自动线也有手工线做同一批模块的情况，避免重复查询
                # if not check_result_success:
                    # 查询手工线模块扫码配对信息
                    # sql = "select count(1) from yw_project_snid_detail where model_id='%s' and  state='1'" % model_id
                    sql = "select gw_id, pcb_sn from yw_project_snid_detail where model_id='%s' and state='1'" % model_id
                    log.info(sql)
                    cur.execute(sql)
                    row2=cur.fetchone()
                    if row2:
                        gw_id, pcb_sn = row2
                        check_result_success = True
                if not check_result_success:
                    # 条码未经过自动化线或手工线产测工站
                    raise SelectException1
                gw_id = gw_id.upper() #将国网id全部转大写
            else: #无芯片ID，装箱时不需要判断绑定关系,也得不到芯片ID和SN码
                gw_id, pcb_sn = '0','0'

            # 必须扫码配对对
            if prod_type in ['2C-TXID-V2']:
                sql = "select gw_id, pcb_sn from yw_project_snid_detail where model_id='%s' and state='1'" % model_id
                log.info(sql)
                cur.execute(sql)
                row2 = cur.fetchone()
                if row2:
                    gw_id, pcb_sn = row2
                else:
                    # 条码未经过自动化线或手工线产测工站
                    raise SelectException1

            # substrflag = prd_name.find('集中器', 0, len(prd_name))
            # if substrflag == -1:
            #     # 未抄表不可以装箱, add by litz, 20200416
            #     sql = "select Test_Result,Hw_Version,Fw_Version,Vendor_id from yw_project_meterread_test_info where Module_ID='%s' " % model_id
            #     log.info(sql)
            #     cur.execute(sql)
            #     row = cur.fetchone()
            #     if not row:
            #         #未抄表，不允许装箱
            #         raise SelectException10
            #     if row[0] != 'Pass':
            #         # 抄表失败，不允许装箱
            #         raise SelectException11
            #
            #     #判断软件版本号、硬件版本号和厂商代码是否正确 add by litz, 20200430
            #     if hw_version :
            #         if hw_version != row[1]:
            #             raise SelectException12  # 硬件版本号错误
            #     if fw_version :
            #         if fw_version != row[2]:
            #             raise SelectException13  # 软件版本号错误
            #     if vendor_id :
            #         if vendor_id != row[3]:
            #             raise SelectException14  # 厂商代码错误

            #查询模块是否已经装箱
            sql = "select box_id from yw_project_boxing_info where model_id='%s' and  state='1'" % model_id
            log.info(sql)
            cur.execute( sql )
            row=cur.fetchone()
            if row:
                boxid=row[0]
                if boxid:
                    raise SelectException2

            # 判断国网ID是否重复
            if len(gw_id)> 10:
                sql = "select model_id from yw_project_boxing_info where gw_id='%s' " %  gw_id
                log.info(sql)
                cur.execute(sql)
                row=cur.fetchone()
                if row:
                    db_modelid = row[0]
                    if db_modelid != model_id:
                        raise SelectException15

            # 更新装箱信息
            if gw_id:
                sql = "update yw_project_boxing_info set win_id='%s',tran_date='%s',state='%s',gw_id='%s',pcb_sn='%s', prod_line='%s' where model_id='%s'" \
                      % ( win_id, tran_date, state, gw_id, pcb_sn, prod_line, model_id)
            else:
                sql = "update yw_project_boxing_info set win_id='%s',tran_date='%s',state='%s',gw_id=null,pcb_sn='%s', prod_line='%s' where model_id='%s'" \
                      % ( win_id, tran_date, state, pcb_sn, prod_line, model_id)
            log.info(sql)
            cur.execute(sql)


        #查询当前装箱信息数量
        all_count, now_count=0,0
        sql="select count(*) from yw_project_boxing_info where box_id='%s' and order_id='%s' and plan_id='%s'"%(box_id,order_id,plan_id)
        log.info(sql)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            all_count=row[0]

        sql = "select count(*) from yw_project_boxing_info where box_id='%s' and state='1' and order_id='%s' and plan_id='%s'" %(box_id,order_id,plan_id)
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
        respcode, respmsg = "367001", "模块ID没有扫码配对:" + str(model_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException2 as e:
        SuccessFlag = False
        log.info("模块ID已经装入箱子:" + str(s_box_id) )
        respcode, respmsg = "367002", "模块ID已经装入箱子:" + str(s_box_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException3 as e:
        SuccessFlag = False
        log.info("箱号有误:%s,应为：%s"%(box_id,s_box_id) )
        respcode, respmsg = "367003", "箱号有误:%s,应为：%s"%(box_id,s_box_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException4 as e:
        SuccessFlag = False
        log.info("制令单号有误:%s，应为：%s"%(order_id, s_order_id))
        respcode, respmsg = "367004", "制令单号有误:%s，应为：%s"%(order_id,s_order_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException5 as e:
        SuccessFlag = False
        log.info("计划号有误:%s，应为：%s"%(plan_id,s_plan_id))
        respcode, respmsg = "367005", "计划号有误:%s，应为：%s"%(plan_id,s_plan_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException6 as e:
        SuccessFlag = False
        log.info("重复条码:" + str(model_id) )
        respcode, respmsg = "367006", "重复条码:" + str(plan_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException7 as e:
        SuccessFlag = False
        log.info("条码不存在:" + str(model_id) )
        respcode, respmsg = "367007", "条码不存在:" + str(model_id)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException8 as e:
        SuccessFlag = False
        log.info("条码不连号")
        respcode, respmsg = "367008", "条码不连号"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException9 as e:
        SuccessFlag = False
        log.info("制令单号对应的线体不存在!")
        respcode, respmsg = "367009", "制令单号对应的线体不存在!"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException10 as e:
        SuccessFlag = False
        log.info("未抄表-不允许装箱!")
        respcode, respmsg = "367010", "未抄表-不允许装箱!"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException11 as e:
        SuccessFlag = False
        log.info("抄表失败-不允许装箱!")
        respcode, respmsg = "367011", "抄表失败-不允许装箱!"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException12 as e:
        SuccessFlag = False
        log.info("硬件版本错误-不允许装箱!")
        respcode, respmsg = "367012", "硬件版本错误-不允许装箱!"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException13 as e:
        SuccessFlag = False
        log.info("软件版本错误-不允许装箱!")
        respcode, respmsg = "367013", "软件版本错误-不允许装箱!"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException14 as e:
        SuccessFlag = False
        log.info("厂商代码错误-不允许装箱!")
        respcode, respmsg = "367014", "厂商代码错误-不允许装箱!"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except SelectException15 as e:
        SuccessFlag = False
        log.info("国网ID重复-不允许装箱!")
        respcode, respmsg = "367015", "国网ID重复-不允许装箱!"
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
    except Exception as e:
        SuccessFlag = False
        log.info("登记装箱信息失败:" + str(e))
        respcode, respmsg = "999999", '登记装箱信息失败' + str(e)
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
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


        tuple2 = (None, tran_date, order_id, plan_id, win_id, prod_line, str(model_list), box_id, respcode, respmsg)
        log.info('开始插入错误信息8')
        s2 = transaction.savepoint()
        insert_err2(log)
        transaction.savepoint_commit(s2)

    # s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

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
    pcbsn = reqest_body.get('sn', None)
    if orderid:
        pass
    else:
        s = public.setrespinfo({"respcode": "500510", "respmsg": "缺少参数"})
        return HttpResponse(s)

    cur = connection.cursor()  # 创建游标

    if pcbsn:
        # 判断产测是否通过---
        sql = "select Chip_mmid from yw_project_product_test_info where Board_SN='%s' and Test_Result='Pass'" % pcbsn
        log.info("判断产测是否通过:"+sql)
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            respcode, respmsg = "500301", "产测未通过!"
            cur.close()
            s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
            return HttpResponse(s)

    #根据制令单号获取计划号
    Today = datetime.datetime.now().strftime('%Y-%m-%d')
    sql = "select id, plan_id,gwid_flag,prod_type from yw_project_plan_info where order_id='%s' " \
          "and  DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s' and state='1' limit 1 " % (orderid, Today)
    log.info("根据制令单号获取计划号:" + sql)
    cur.execute(sql)
    coll_row = cur.fetchone()
    if coll_row:
        pkid = coll_row[0]
        planid = coll_row[1]
        gwid_flag = coll_row[2]
        prod_type = coll_row[3]
    else:
        respcode, respmsg = "500499", "制令单号错误，根据制令单号查不到计划号!"
        cur.close()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)


    # add by litz, 20200401, 摄像头读取条形码异常时，判断条形码规格是否正确。
    if len(modelid) == 22  and prod_type not in ('COMMON_NCK_MODELID'):  # 22位的有效验位
        zjq = 0
        for j in range(0, len(modelid) - 1):
            qz = (3 if (j % 2 == 0) else 1)
            zjq = zjq + int(modelid[j]) * int(qz)
        a, b = divmod(zjq, 10)
        checksum = (10 - b if (b > 0) else 0)
        if str(modelid[-1]) != str(checksum):
            respcode, respmsg = "500190", "模块ID识别有误,校验值错!"
            s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
            return HttpResponse(s)
    # end by litz, 20200401

    # 查看项目信息
    sql = "select plan_id,spc_name,begin_id, end_id, plan_id from yw_project_info " \
          "where proj_state='1' and order_id=%s and begin_date<=%s and end_date >=%s"  # order by ID desc
    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # log.info( sql % (orderid,time_now,time_now) )
    cur.execute(sql, (orderid, time_now, time_now))
    row = cur.fetchone()
    # print('查看项目信息=',rows)
    if row == None:
        respcode, respmsg = "500100", "计划单号错误!"
        cur.close()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)
    db_begin_id = row[2]
    db_end_id = row[3]
    # 判断数据是否合法
    if modelid < db_begin_id or modelid > db_end_id or len(modelid) != len(db_begin_id) or len(modelid) != len(db_end_id):
        # log.info("模块ID不在项目范围")
        respcode, respmsg = "500101", "模块ID不在项目范围!"
        cur.close()
        s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        return HttpResponse(s)


    #先判断modelid是不是自动化线已经关联过的
    if modelid:
        sql = "select ks_id, ks_keyid from yw_project_keyidshellbarcode where ks_shell_barcode='%s' " % (modelid)
        log.info("先判断modelid是不是自动化线已经关联过的:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            jsondata['gw_id'] = row[1]
            cur.close()
            s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
            log.info('----------------------Lqkjsmpd-get_gwid-end---------------------------')
            return HttpResponse(s)

    # 根据制令单号获取计划号
    # sql = "select id, plan_id from yw_project_plan_info where order_id='%s' order by id desc" % (orderid)
    # log.info("据制令单号获取计划号:" + sql)
    # cur.execute(sql)
    # coll_row = cur.fetchone()
    # if coll_row:
    #     pkid = coll_row[0]
    #     planid = coll_row[1]
    # else:
    #     cur.close()
    #     s = public.setrespinfo({"respcode": "500499", "respmsg": "制令单号错误，根据制令单号查不到计划号!"})
    #     return HttpResponse(s)

    #先判断modelid是不是已经关联， add by litz, 20200417
    if modelid:
        sql = "select gw_id from yw_project_gwid_detail_getinfo where gl_id='%s' " % (modelid)
        log.info("先判断modelid是不是已经关联:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            jsondata['gw_id'] = row[0]

            sql = "update yw_project_gwid_detail_getinfo set ask_time=NOW(), state='1' " \
                  "where gl_id='%s' and proj_id='%s'" % (modelid, orderid)
            log.info("更新modelid:" + sql)
            cur.execute(sql)
            cur.close()
            s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
            log.info('----------------------Lqkjsmpd-get_gwid-end---------------------------')
            return HttpResponse(s)

    #查询空闲国网id
    randstr=public.genRandomString(8)
    sql = "update yw_project_gwid_detail_getinfo set ask_time=NOW(), randstr='%s',gl_id='%s', state='1' where proj_id='%s' and gl_id is null " \
          "and state='0' and ask_time is null limit 1" % ( randstr, modelid, orderid )
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
        jsondata['respmsg']='没有可用国网ID'
        jsondata['gw_id']=''

    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------Lqkjsmpd-get_gwid-end---------------------------')
    return HttpResponse(s)


#扫码配对--检查时只管登记一下，不判断处理，应对于手工维护某些产品时的处理。
def register_snid_check(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjsmpd-register_snid_check-begin---------------------------')

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

    # 获取线别信息
    select_sql = "select prod_line,station_type,station_num from yw_project_prodline_term where Platform_win_num='%s'" % str(winid)
    cur.execute(select_sql)
    row = cur.fetchone()
    if row:
        prod_line = row[0]
        station_type = row[1]
        station_num = row[2]
    else:
        s = public.setrespinfo({"respcode": "500512", "respmsg": "未认证的终端，请联系工程人员!"+str(winid)})
        return HttpResponse(s)
    if not prod_line or not station_type or not station_num:
        s = public.setrespinfo({"respcode": "500513", "respmsg": "终端参数配置有误，请联系工程人员!"+str(winid)})
        return HttpResponse(s)

    #登记历史检查表数据
    insertsql = "insert into yw_project_snid_detail_check(tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state, prod_line) " \
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"  % (datetime.datetime.now(), orderid, '', '', pcbsn, modelid, gwid, winid, "1", prod_line)
    # log.info(insertsql)
    cur.execute(insertsql)
    cur.close()

    #返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------Lqkjsmpd-register_snid_check-end---------------------------')
    return HttpResponse(s)



#根据计划号 制订单号 箱号 获取箱子信息（箱号 已装箱条码数 该箱条码总数 已装箱条码列表）
def getBoxInfo(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjsmpd-getBoxInfo-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    order_id = reqest_body.get('order_id')
    plan_id = reqest_body.get('plan_id')
    box_id=reqest_body.get('box_id')


    if order_id and plan_id and box_id:
        pass
    else:
        s = public.setrespinfo({"respcode": "500510", "respmsg": "缺少参数"})
        return HttpResponse(s)

    cur = connection.cursor()  # 创建游标
    sql = "select model_id,box_code,state from yw_project_boxing_info where box_id='%s' and order_id='%s' and plan_id='%s'" % (box_id, order_id, plan_id)
    log.info(sql)
    cur.execute(sql)
    rows = cur.fetchall()
    all_count=len(rows)
    now_count=0
    model_list=[]
    box_code=''
    if all_count>0:
        box_code=rows[0][1]
    for row in rows:
        if row[2]=='1':
            now_count+=1
            model_list.append(row[0])

    jsondata['detail']={
        "all_count":all_count,
        "now_count":now_count,
        "box_code":box_code,
        "model_list":model_list
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------Lqkjsmpd-getBoxInfo-end---------------------------')
    return HttpResponse(s)

# 扫码配对，单机版登录验证
def stand_alone_login(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjsmpd-stand_alone_login-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    userid = reqest_body.get('userid')
    password = reqest_body.get('password')


    if userid and password:
        pass
    else:
        s = public.setrespinfo({"respcode": "220025", "respmsg": "用户名或密码错误！"})
        return HttpResponse(s)
    # 查找管理台用户信息表权限
    try:
        AdminUser = models.IrsadminUser.objects.get(user_id=userid, passwd=password)
    except models.IrsadminUser.DoesNotExist:
        # 找不到时，有可能使用手机号登陆的
        try:
            AdminUser = models.IrsadminUser.objects.get(tel=userid, passwd=password)
        except models.IrsadminUser.DoesNotExist:
            s = public.setrespinfo({"respcode": "220025", "respmsg": "用户名或密码错误!"})
            return HttpResponse(s)



    jsondata['uid'] = AdminUser.user_id


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)

    log.info('----------------------Lqkjsmpd-stand_alone_login-end---------------------------')
    return HttpResponse(s)

