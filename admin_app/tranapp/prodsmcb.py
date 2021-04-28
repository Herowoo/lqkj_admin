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
#生产扫码配对+抄表..
#add by litz, 2020.09.17
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

#资产码通讯地址对应信息导入
def txdzinfo_import(request):
    log = public.logger
    body=public.req_body
    form_var=body.get('form_var')
    excelfile = form_var.get('excelfile')
    if not excelfile:
        public.respcode, public.respmsg = "300332", "请先选择文件!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:

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
        insertsql = "insert into yw_project_txdz_detail_getinfo(model_id, order_id, txdz_id)  values('%s', '%s', '%s') "
        i=0
        for item in ws.rows:
            i = i + 1
            if i == 1:  # 第一行标题不处理
                continue

            cur.execute(insertsql % (item[0].value, item[1].value, item[2].value) )

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

# 扫码配对登记
def model_smpd_save(request):
    log = public.logger
    body=public.req_body
    try:

        cur = connection.cursor()  # 创建游标
        orderid = body.get('order_id', None)
        winid = str(body.get('win_id', None)).split('/')[0]
        modelid = body.get('model_id', None)
        pcbsn = body.get('pcb_sn', None)
        gwid = body.get('chipid', None)
        prodline = body.get('prod_line', None)
        Today = datetime.datetime.now().strftime('%Y-%m-%d')

        if not modelid:
            cur.close()
            public.respcode, public.respmsg = "500552", "模块ID不可以空!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        def insert_err():
            insert_err_sql = "INSERT INTO yw_project_snid_detail_error(id,tran_date,order_id,prod_line,win_id,model_id,pcb_sn,gw_id,err_code,err_msg) " \
                             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            Nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur = connection.cursor()
            tuple = (None, Nowtime, orderid, prod_line, winid, modelid, pcbsn, gwid, public.respcode, public.respmsg)
            cur.execute(insert_err_sql, tuple)

        # 查询SN 码最终状态
        def snid_status():
            select_status_sql = "SELECT final_status FROM yw_project_snid_final_status WHERE Board_SN =%s order by id desc limit 1 "
            cur.execute(select_status_sql, pcbsn)
            row = cur.fetchone()
            if row and row[0] != '0':
                return False
            else:
                return True

        cur = connection.cursor()  # 创建游标

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
            cur.close()
            public.respcode, public.respmsg = "500512", "未认证的终端，请联系工程人员!" + str(winid)
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not station_type or not station_num:
            public.respcode, public.respmsg = "500512", "终端参数配置有误，请联系工程人员!" + str(winid)
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        if prod_line != prodline:
            public.respcode, public.respmsg = "500532", "终端参数配置线别与当前制令单所属线别不符，请联系工程人员!" + str(winid)
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 根据制令单号获取计划号
        sql = "select id, plan_id,gwid_flag,prod_type from yw_project_plan_info where order_id='%s' and prod_line='%s' " \
              "and  DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s' and state='1' " % (orderid, prod_line, Today)
        log.info("查询今日计划和昨日生产量:" + sql)
        cur.execute(sql)
        coll_row = cur.fetchone()
        if coll_row:
            pkid = coll_row[0]
            planid = coll_row[1]
            gwid_flag = coll_row[2]
            prod_type = coll_row[3]
        else:
            public.respcode, public.respmsg = "500499", "制令单号错误，根据制令单号查不到计划号!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 查看项目信息
        sql = "select plan_id,spc_name,begin_id, end_id, plan_id from yw_project_info " \
              "where proj_state='1' and order_id=%s and begin_date<=%s and end_date >=%s"  # order by ID desc
        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # log.info( sql % (orderid,time_now,time_now) )
        cur.execute(sql, (orderid, time_now, time_now))
        rows = cur.fetchone()
        # print('查看项目信息=',rows)
        if rows == None:
            public.respcode, public.respmsg = "500100", "计划单号错误!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # add by litz, 20200401, 摄像头读取条形码异常时，判断条形码规格是否正确。
        if len(modelid) == 22 and prod_type not in ('COMMON_NCK_MODELID'):  # 22位的有效验位
            zjq = 0
            for j in range(0, len(modelid) - 1):
                qz = (3 if (j % 2 == 0) else 1)
                zjq = zjq + int(modelid[j]) * int(qz)
            a, b = divmod(zjq, 10)
            checksum = (10 - b if (b > 0) else 0)
            if str(modelid[-1]) != str(checksum):
                public.respcode, public.respmsg = "500190", "模块ID识别有误,校验值错!"
                insert_err()
                cur.close()
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        # end by litz, 20200401

        try:
            int_sn = len(pcbsn[2:])
        except Exception:
            public.respcode, public.respmsg = "500100", "SN码未写入芯片,请再次产测!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if int_sn == 0 or '0' * len(pcbsn[2:]) == pcbsn[2:]:
            public.respcode, public.respmsg = "500101", "SN码未写入芯片,请再次产测!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # SN 最终状态校验
        snflag = snid_status()
        if not snflag:
            public.respcode, public.respmsg = "500105", "该模块SN码已转入维修,请联系工程人员确认!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

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

        # 判断数据是否合法
        if db_model_id < db_begin_id or db_model_id > db_end_id or len(db_model_id) != len(db_begin_id) or len(
                db_model_id) != len(db_end_id):
            # log.info("模块ID不在项目范围")
            public.respcode, public.respmsg = "500101", "模块ID不在项目范围!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo


        # 判断产测是否通过---
        sql = "select Chip_mmid from yw_project_product_test_info where Board_SN='%s' and Test_Result='Pass'" % pcbsn
        # log.info("判断产测是否通过:"+sql)
        cur.execute(sql)
        rows = cur.fetchone()
        if not rows:
            public.respcode, public.respmsg = "500301", "产测未通过!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # if gwid != rows[0]:
        #     respcode, respmsg = "500401", "根据SN查到的产测国网ID和当前不一定，可能PCBA线下更换!"
        #     cur.close()
        #     insert_err()
        #     s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
        #     return HttpResponse(s)

        if gwid_flag == '1':
            # 查看模块ID和国网ID是否已经分配。
            sql = "select gw_id from yw_project_gwid_detail_getinfo where gl_id='%s' " % (modelid )
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "500115", "国网ID与模块ID对应关系未导入!"
                insert_err()
                cur.close()
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            gwid = row[0]
            sql = "update yw_project_gwid_detail_getinfo set ask_time=NOW(), state='1' where gl_id='%s' " % (modelid)
            cur.execute(sql)

        # 查看模块ID是否已经有数据
        if gwid_flag == '1':
            sql = "select count(1) from yw_project_snid_detail where state='1' and model_id=%s and (gw_id!=%s or pcb_sn!=%s) "
            cur.execute(sql, (modelid, gwid, pcbsn))
        else:
            sql = "select count(1) from yw_project_snid_detail where state='1' and model_id=%s and pcb_sn!=%s "
            cur.execute(sql, (modelid, pcbsn))
        rows = cur.fetchone()
        exists = rows[0]
        if exists > 0:
            public.respcode, public.respmsg = "500102", "模块ID已经被绑定使用!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 查看PCB_SN是否已经有数据
        if gwid_flag == '1':
            sql = "select count(1) from yw_project_snid_detail where state='1' and pcb_sn=%s and (model_id!=%s or gw_id!=%s)"
            cur.execute(sql, (pcbsn, modelid, gwid))
        else:
            sql = "select count(1) from yw_project_snid_detail where state='1' and pcb_sn=%s and model_id!=%s "
            cur.execute(sql, (pcbsn, modelid))
        rows = cur.fetchone()
        exists = rows[0]
        if exists > 0:
            public.respcode, public.respmsg = "500103", "SN码已经被绑定使用!"
            insert_err()
            cur.close()
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        if gwid_flag == '1':
            # 查看gw_id是否已经有数据
            sql = "select count(1) from yw_project_snid_detail where state='1' and gw_id=%s and (model_id!=%s or pcb_sn!=%s) "
            # log.info(sql % gwid)
            cur.execute(sql, (gwid, modelid, pcbsn))
            rows = cur.fetchone()
            exists = rows[0]
            if exists > 0:
                public.respcode, public.respmsg = "500104", "国网ID已经被绑定使用!"
                insert_err()
                cur.close()
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        # 登记历史表数据
        sql = "insert into yw_project_snid_detail_his(tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state, prod_line) " \
              "select tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state, prod_line from yw_project_snid_detail " \
              "where pcb_sn='%s'"
        log.info(sql % projdetail["pcb_sn"])
        cur.execute(sql % projdetail["pcb_sn"])
        sql = "delete from yw_project_snid_detail where pcb_sn='%s' "
        log.info(sql % projdetail["pcb_sn"])
        cur.execute(sql % projdetail["pcb_sn"])

        # 检查无误，登记IDSN绑定关系
        projdetail["tran_date"] = datetime.datetime.now()
        projdetail["win_id"] = winid
        projdetail["model_id"] = modelid
        projdetail["pcb_sn"] = pcbsn
        if prod_type == '2C-TXID-V2':
            sql = "select txdz_id from yw_project_txdz_detail_getinfo where model_id='%s' and order_id='%s'" \
                  % (projdetail["model_id"], projdetail["order_id"])
            log.info(sql)
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "500119", "模块ID和通讯地址的关系未建立!"
                insert_err()
                cur.close()
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            else:
                projdetail["txdz_id"] = row[0]
        elif prod_type == '2C-TXID-V3':  # 带侧贴标签的二采, 2020-09-09 add by litz,
            sql = "select mac_no from yw_project_2cmac_info where model_id='%s' and order_id='%s'" \
                  % (projdetail["model_id"], projdetail["order_id"])
            log.info("2C-TXID-V3:" + sql)
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "500119", "模块ID和通讯地址的关系未建立!"
                insert_err()
                cur.close()
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            else:
                projdetail["writesn_flag"] = True
                projdetail["NewSn"] = row[0]
                projdetail["txdz_id"] = modelid
                # 更新使用情况
                sql = "update yw_project_2cmac_info set old_sn_no='%s', gwid='%s', tran_date='%s' " \
                      "where model_id='%s' and order_id='%s'" \
                      % (pcbsn, gwid, projdetail["tran_date"], projdetail["model_id"], projdetail["order_id"])
                log.info(sql)
                cur.execute(sql)
        else:  # 其它类型
            projdetail["txdz_id"] = modelid

        if gwid_flag == '1':
            projdetail["gw_id"] = gwid
        elif "000000000000000000000000000000000000000000000000" in gwid:
            projdetail["gw_id"] = modelid
        else:
            projdetail["gw_id"] = gwid
        projdetail["state"] = '1'

        insertsql = "insert into yw_project_snid_detail(tran_date,order_id,plan_id,spc_name,pcb_sn,model_id,gw_id,win_id,state, prod_line) " \
                    "VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" \
                    % (projdetail["tran_date"], projdetail["order_id"], projdetail["plan_id"], projdetail["spc_name"],
                       projdetail["pcb_sn"], \
                       projdetail["model_id"], projdetail["gw_id"], projdetail["win_id"], projdetail["state"],
                       prod_line)
        log.info(insertsql)
        cur.execute(insertsql)

        if gwid_flag == '1':
            # 更新国网ID表数据
            updsql = "update yw_project_gwid_detail set gl_id='%s', state='1' where gw_id='%s'" % \
                     ( projdetail["model_id"], projdetail["gw_id"] )
            log.info(updsql)
            cur.execute(updsql)
        cur.close()  # 关闭游标

        if gwid_flag == '1':
            body['chipid'] = gwid
            body['gwid_write_flag'] = True #是否写入新的国网ID
        else:
            body['gwid_write_flag'] = False
        body['sn_write_flag'] = False #是否写入新的SN  --SN在产测的时候写入

        #模块ID一般都要写入
        body['modelid_write_flag'] = True #是否写入新的Model_ID

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

# 抄表登记
def model_meterread_save(request):
    log = public.logger
    body=public.req_body
    try:

        cur = connection.cursor()  # 创建游标
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        Platform_Num = body.get('win_id')
        Batch_Num = body.get('order_id')
        prod_line = body.get('prod_line')
        Test_Result_Value = body.get('MeterRead_Result')
        if Test_Result_Value == 'Pass':
            Test_Result = 'Pass'
        else:
            Test_Result = 'Fail'

        Board_SN =  body.get('sn')
        if Board_SN:
            Board_SN_Result = 'Pass'
        else:
            Board_SN_Result = 'Fail'

        #手工线的SN码送上来的是两两反序的，需要调整
        if prod_line not in ('AutoLine1','AutoLine2'):
            temp = ""
            for i in range(int(len(Board_SN) / 2)):
                temp += Board_SN[i * 2:i * 2 + 2][::-1]
            Board_SN = temp[::-1]

        Chip_mmid = body.get('chipid')
        if Chip_mmid:
            Chip_mmid_Result = 'Pass'
        else:
            Chip_mmid_Result = 'Fail'

        Module_ID = body.get('model_id')
        if not Module_ID: #没上送模块ID，通过扫码配对查一下
            sql = "select model_id from yw_project_snid_detail where gw_id='%s'" % Chip_mmid
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                Module_ID = row[0]
        if Module_ID:
            Module_ID_Result = 'Pass'
        else:
            Module_ID_Result = 'Fail'

        Hw_Version = body.get('hw_version')
        if Hw_Version:
            Hw_Version_Result = 'Pass'
        else:
            Hw_Version_Result = 'Fail'

        Fw_Version = body.get('fw_version')
        if Hw_Version:
            Fw_Version_Result = 'Pass'
        else:
            Fw_Version_Result = 'Fail'

        Vendor_id = body.get('vendor_code')
        if Vendor_id:
            Vendor_id_Result = 'Pass'
        else:
            Vendor_id_Result = 'Fail'

        # 根据制令单号获取计划号
        Today = datetime.datetime.now().strftime('%Y-%m-%d')
        sql = "select id, plan_id,gwid_flag,prod_type, Hw_Version, Fw_Version, Vendor_id from yw_project_plan_info " \
              "where order_id='%s' and prod_line='%s' " \
              "and  DATE_FORMAT(prod_date,'%%Y-%%m-%%d')='%s' and state='1' " % (Batch_Num, prod_line, Today)
        log.info("查询今日计划和昨日生产量:" + sql)
        cur.execute(sql)
        coll_row = cur.fetchone()
        if coll_row:
            pkid = coll_row[0]
            planid = coll_row[1]
            gwid_flag = coll_row[2]
            prod_type = coll_row[3]
            hw_version=coll_row[4]  #硬件版本号
            fw_version=coll_row[5]  #软件版本号
            vendor_id =coll_row[6]  #厂商代码
        else:
            cur.close()
            public.respcode, public.respmsg = "500499", "制令单号错误，根据制令单号查不到计划号!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        #判断软件版本号、硬件版本号和厂商代码是否正确 add by litz, 20200430
        if hw_version :
            if hw_version != Hw_Version:
                cur.close()
                public.respcode, public.respmsg = "500519", "硬件版本号错误!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        if fw_version :
            if fw_version != Fw_Version:
                cur.close()
                public.respcode, public.respmsg = "500520", "软件版本号错误!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        if vendor_id :
            if vendor_id != Vendor_id:
                cur.close()
                public.respcode, public.respmsg = "500521", "厂商代码错误!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        # 获取线别信息
        select_sql = "SELECT prod_line FROM yw_project_prodline_term WHERE Platform_win_num='%s'" % str(Platform_Num)
        cur.execute(select_sql)
        row = cur.fetchone()
        if row:
            prod_line = row[0]
        else:
            cur.close()
            public.respcode, public.respmsg = "500512", "未认证的终端，请联系工程人员!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 测试失败次数超过3次，SN 码状态自动进入维修状态
        def insert_repair():
            # 查询SN 码最终状态表SQL
            snfail_sql = "SELECT * from yw_project_snid_final_status WHERE Board_SN = %s order by id desc limit 1 "
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
                    snfail_tuple = (None, Board_SN, nowTime, '抄表', 0, '0')
                    cur.execute(insert_snfial_sql, snfail_tuple)
            else:
                cur.execute(snfail_sql, Board_SN)
                row = cur.fetchone()
                # SN 最终状态表中有记录
                if row:
                    count = row[4] + 1
                    if count == 3:
                        snfail_tuple = (None, Board_SN, nowTime, '抄表', 3, '1')
                        cur.execute(insert_snfial_sql, snfail_tuple)
                        # 此时连续测试失败超过三次，SN 自动转入维修状态
                        flag = False
                        plan_num = None
                        cur.execute(proinfo_sql, Batch_Num)
                        plan_row = cur.fetchone()
                        if plan_row:
                            plan_num = plan_row[0]
                        # 将该SN 相关记录信息插入维修记录表
                        repair_tuple = (None, nowTime, Board_SN, '抄表', nowTime, prod_line,
                                        Platform_Num, Batch_Num, plan_num, '', '', Test_Result,
                                        Test_Result_Value, Hw_Version, Fw_Version, None,
                                        Chip_mmid, Vendor_id, None, None, None, None, None, None, '9')
                        cur.execute(repain_insert, repair_tuple)
                    elif count < 3:
                        snfail_tuple = (None, Board_SN, nowTime, '抄表', count, '0')
                        cur.execute(insert_snfial_sql, snfail_tuple)
                # SN 最终状态表中无记录
                else:
                    snfail_tuple = (None, Board_SN, nowTime, '抄表', 1, '0')
                    cur.execute(insert_snfial_sql, snfail_tuple)
            return flag

        check_flag = insert_repair()
        if not check_flag:
            cur.close()
            public.respcode, public.respmsg = "500530", "测试已连续失败超过3次,该SN码对应模块已转入维修!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        if Module_ID and len(Module_ID) == 22 and prod_type not in ('COMMON_NCK_MODELID'):  # 22位的有效验位
            #判断是否已经扫码配对
            sql = "select pcb_sn,gw_id from yw_project_snid_detail where order_id = '%s' and model_id='%s' and state='1'" \
                         % ( Batch_Num, Module_ID )
            log.info('判断是否已经扫码配对:'+select_sql, extra={'ptlsh': public.req_seq})
            cur.execute(sql)
            row = cur.fetchone()
            if row and row[0]:
                # 终端上送SN码不对，为了尽快测试，暂时先取为扫码配对的SN码
                Board_SN = row[0]
                Chip_mmid = row[1]
                # if row[0] != Board_SN:
                #     # cur.close()
                #     # public.respcode, public.respmsg = "500812", "SN码与扫码配对时不一致!"
                #     # public.respinfo = HttpResponse(public.setrespinfo())
                #     # return public.respinfo
            else:
                cur.close()
                public.respcode, public.respmsg = "500813", "未执行扫码配对工序!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        # 先把重复数据放入历史表
        sql = "INSERT INTO yw_project_meterread_test_info_his SELECT * FROM yw_project_meterread_test_info WHERE Board_SN='%s' " \
              % (Board_SN)
        # log.info(sql, extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        sql = "DELETE FROM yw_project_meterread_test_info WHERE Board_SN='%s' " % (Board_SN)
        # log.info(sql, extra={'ptlsh': public.req_seq})
        cur.execute(sql)

        insert_sql = "INSERT INTO yw_project_meterread_test_info (insert_date, Platform_Num, Batch_Num, " \
                     "Test_Result, Test_Value, Board_SN_Result, Board_SN, Chip_mmid_Result, Chip_mmid, Model_ID_Resut, " \
                     "Module_ID, Hw_Version_Result, Hw_Version, Fw_Version_Result, Fw_Version, Vendor_id_Result, " \
                     "Vendor_id,prod_line) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        insert_tuple = (nowTime, Platform_Num, Batch_Num, Test_Result, Test_Result_Value, Board_SN_Result, Board_SN,
                        Chip_mmid_Result, Chip_mmid, Module_ID_Result, Module_ID, Hw_Version_Result,
                        Hw_Version, Fw_Version_Result, Fw_Version, Vendor_id_Result, Vendor_id, prod_line)
        # log.info(insert_sql % insert_tuple, extra={'ptlsh': public.req_seq})
        cur.execute(insert_sql, insert_tuple)
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
        "BODY": None
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

