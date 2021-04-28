#coding:utf-8
# -*- coding: utf-8 -*-

#联桥科技，产测、抄表等工装数据上传。

from django.shortcuts import HttpResponse
import json
import datetime
from admin_app import public
from admin_app import models
from django.db import connection, transaction

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
        if trantype == 'Product_Test':  #产测结果上传
            resp = Product_Test(request, reqest_body)
        elif trantype == 'MeterRead_Test':  #抄表结果上传
            resp = MeterRead_Test(request, reqest_body)
        elif trantype == 'Flash_Burn':  #烧录数据上传
            resp = Flash_Burn(request, reqest_body)
        elif trantype == 'SN_Laser_Carving_Save':  # SN码镭雕上传
            resp = SN_Laser_Carving_Save(request, reqest_body)
        elif trantype == 'Get_SN_Cfg':  # 获取SN码镭雕配置信息
            resp = Get_SN_Cfg(request, reqest_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp

#产测结果上传
def Product_Test(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjprod-getprojectinfo-begin---------------------------')

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    info=reqest_body.get('Info', None)
    if not info:
        s = public.setrespinfo({"respcode": "500511", "respmsg": "上传数据错误!"})
        return HttpResponse(s)

    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    Batch_Num = info['Batch_Num']['Value']
    Ser_Num = info['Ser_Num']['Value']
    Platform_Num = info['Platform_Num']['Value']
    Test_Result = info['Test_Result']['Result']
    Test_Value = info['Test_Result']['Value']

    Board_SN_Result = info['Board_SN']['Result']
    Board_SN = info['Board_SN']['Value']
    Chip_mmid_Result = info['Chip_mmid']['Result']
    Chip_mmid = info['Chip_mmid']['Value']
    Aging_Test_Period_Result = info['Aging_Test_Period']['Result']
    Aging_Test_Period = info['Aging_Test_Period']['Value']
    Hw_Version_Result = info['Hw_Version']['Result']
    Hw_Version = info['Hw_Version']['Value']
    Fw_Version_Result = info['Fw_Version']['Result']
    Fw_Version = info['Fw_Version']['Value']
    Vendor_id_Result = info['Vendor_id']['Result']
    Vendor_id = info['Vendor_id']['Value']
    chip_id_Result = info['Chip_id']['Result']
    chip_id = info['Chip_id']['Value']
    prod_line = '' ## 线别

    cur = connection.cursor()  # 创建游标

    # 获取线别信息
    select_sql = "select prod_line from yw_project_prodline_term where Platform_win_num='%s'" % str(Platform_Num)
    cur.execute(select_sql)
    row = cur.fetchone()
    if row:
        prod_line = row[0]
    else:
        s = public.setrespinfo({"respcode": "500512", "respmsg": "未认证的终端，请联系工程人员!"})
        return HttpResponse(s)



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
            cur.execute(snfail_sql,Board_SN)
            row = cur.fetchone()
            if row:
                snfail_tuple= (None,Board_SN,nowTime,'产测',0,'0')
                cur.execute(insert_snfial_sql,snfail_tuple)
        else:
            cur.execute(snfail_sql, Board_SN)
            row = cur.fetchone()
            # SN 最终状态表中有记录
            if row:
                count = row[4] + 1
                if count==3:
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
                                    Chip_mmid, Vendor_id, None, None, None,None, None, None, '9')
                    cur.execute(repain_insert,repair_tuple)
                elif count<3:
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


    #先把重复数据放入历史表
    sql="insert into yw_project_product_test_info_his select * from yw_project_product_test_info where Board_SN='%s' " % (Board_SN)
    cur.execute(sql)
    sql="delete from yw_project_product_test_info where Board_SN='%s' " % (Board_SN)
    cur.execute(sql)

    insert_sql = "INSERT INTO yw_project_product_test_info (insert_date, Batch_Num, Ser_Num, Platform_Num, Test_Result,Test_Value, Board_SN_Result, Board_SN, " \
                 "Chip_mmid_Result, Chip_mmid, Aging_Test_Period_Result, Aging_Test_Period, Hw_Version_Result, Hw_Version, Fw_Version_Result, Fw_Version," \
                 "Vendor_id_Result, Vendor_id, chip_id_Result, chip_id,prod_line) VALUES ( %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"



    insert_tuple = (nowTime,Batch_Num,Ser_Num,Platform_Num,Test_Result,Test_Value,Board_SN_Result,Board_SN,
                    Chip_mmid_Result,Chip_mmid,Aging_Test_Period_Result,Aging_Test_Period,Hw_Version_Result,
                    Hw_Version,Fw_Version_Result,Fw_Version,Vendor_id_Result,Vendor_id,chip_id_Result,chip_id,prod_line)
    cur.execute(insert_sql,insert_tuple)
    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjprod-getprojectinfo-end---------------------------')
    return HttpResponse(s)

#抄表结果上传
def MeterRead_Test(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjprod-MeterRead_Test-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    def InstData( info ):
        cur = connection.cursor()  # 创建游标
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        Platform_Num = info['Platform_Num']['Value']
        Batch_Num = info['Batch_Num']['Value']
        Test_Result = info['Test_Result']['Result']
        Test_Result_Value = info['Test_Result']['Value']
        Board_SN_Result = info['Board_SN']['Result']
        Board_SN = info['Board_SN']['Value']
        Chip_mmid_Result = info['Chip_mmid']['Result']
        Chip_mmid = info['Chip_mmid']['Value']
        Module_ID_Result = info['Module_ID']['Result']
        Module_ID = info['Module_ID']['Value']
        Hw_Version_Result = info['Hw_Version']['Result']
        Hw_Version = info['Hw_Version']['Value']
        Fw_Version_Result = info['Fw_Version']['Result']
        Fw_Version = info['Fw_Version']['Value']
        Vendor_id_Result = info['Vendor_id']['Result']
        Vendor_id = info['Vendor_id']['Value']
        
        # 获取线别信息
        select_sql = "SELECT prod_line FROM yw_project_prodline_term WHERE Platform_win_num='%s'" % str(Platform_Num)
        cur.execute(select_sql)
        row = cur.fetchone()
        if row:
            prod_line = row[0]
        else:
            return "500512", "未认证的终端，请联系工程人员!"

        #手工线的SN码送上来的是两两反序的，需要调整
        if prod_line not in ('AutoLine1','AutoLine2'):
            temp = ""
            for i in range(int(len(Board_SN) / 2)):
                temp += Board_SN[i * 2:i * 2 + 2][::-1]
            Board_SN = temp[::-1]

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
            return "500530","测试已连续失败超过3次,该SN码对应模块已转入维修 !"




        # 先把重复数据放入历史表
        sql = "INSERT INTO yw_project_meterread_test_info_his SELECT * FROM yw_project_meterread_test_info WHERE Board_SN='%s' " \
              % ( Board_SN )
        log.info(sql)
        cur.execute(sql)
        sql = "DELETE FROM yw_project_meterread_test_info WHERE Board_SN='%s' " % (Board_SN)
        log.info(sql)
        cur.execute(sql)

        insert_sql = "INSERT INTO yw_project_meterread_test_info (insert_date, Platform_Num, Batch_Num, " \
                     "Test_Result, Test_Value, Board_SN_Result, Board_SN, Chip_mmid_Result, Chip_mmid, Model_ID_Resut, " \
                     "Module_ID, Hw_Version_Result, Hw_Version, Fw_Version_Result, Fw_Version, Vendor_id_Result, " \
                     "Vendor_id,prod_line) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        insert_tuple = (nowTime, Platform_Num, Batch_Num, Test_Result, Test_Result_Value, Board_SN_Result, Board_SN,
                        Chip_mmid_Result, Chip_mmid, Module_ID_Result, Module_ID, Hw_Version_Result,
                        Hw_Version, Fw_Version_Result, Fw_Version, Vendor_id_Result, Vendor_id, prod_line)
        log.info(insert_sql % insert_tuple)
        cur.execute(insert_sql, insert_tuple)
        cur.close()
        return "000000", "登记成功!"

    Info=reqest_body.get('Info', None)
    if isinstance(Info,list):
        #自动线，一次上传多个
        for info in Info:
            respcode, respmsg = InstData(info)
            if respcode != "000000":
                s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
                return HttpResponse(s)
    elif isinstance(Info,dict):
        #手工线，一次上传一个
        info = Info
        respcode, respmsg = InstData(info)
        if respcode != "000000":
            s = public.setrespinfo({"respcode": respcode, "respmsg": respmsg})
            return HttpResponse(s)
    else:
        s = public.setrespinfo({"respcode": "500511", "respmsg": "上传数据错误!"})
        return HttpResponse(s)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjprod-MeterRead_Test-end---------------------------')
    return HttpResponse(s)


#烧录数据上传
def Flash_Burn(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjprod-Flash_Burn-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    if not reqest_body.get('Info', ''):
        s = public.setrespinfo({"respcode": "500511", "respmsg": "上传数据错误!"})
        return HttpResponse(s)

    cur = connection.cursor()  # 创建游标

    for info in reqest_body.get('Info', ''):
        Platform_Num = info['Platform_Num']['Value']
        Batch_Num = info['Batch_Num']['Value']
        Test_Result = info['Test_Result']['Value']
        Board_SN = info['Board_SN']['Value']
        chip_id = info['chip_id']['Value']

        # 先把重复数据放入历史表
        sql = "INSERT INTO yw_project_flash_burn_info_his SELECT * FROM yw_project_flash_burn_info WHERE Board_SN='%s' " % (Board_SN)
        log.info(sql)
        cur.execute(sql)
        sql = "DELETE FROM yw_project_flash_burn_info WHERE Board_SN='%s' " % (Board_SN)
        cur.execute(sql)

        insert_sql = "INSERT INTO yw_project_flash_burn_info (Batch_Num, prod_line, Platform_Num, Board_SN, Test_Result, chip_id) " \
                     "VALUES (%s, %s, %s, %s, %s, %s)"

        #获取线别信息
        select_sql = "SELECT prod_line FROM yw_project_prodline_term WHERE Platform_win_num='%s'" % str(Platform_Num)
        cur.execute(select_sql)
        row = cur.fetchone()
        if row:
            prod_line = row[0]
        else:
            s = public.setrespinfo({"respcode": "500512", "respmsg": "未认证的终端，请联系工程人员!"})
            return HttpResponse(s)

        insert_tuple = (Batch_Num, prod_line, Platform_Num, Board_SN, Test_Result, chip_id)
        cur.execute(insert_sql, insert_tuple)
    cur.close()

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjprod-Flash_Burn-end---------------------------')
    return HttpResponse(s)

#SN码镭雕上传
def SN_Laser_Carving_Save(request, reqest_body):
    log = public.logger
    log.info('----------------------Lqkjprod-SN_Laser_Carving_Save-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    if not reqest_body.get('Info', ''):
        s = public.setrespinfo({"respcode": "500511", "respmsg": "上传数据错误!"})
        return HttpResponse(s)

    cur = connection.cursor()  # 创建游标
    info = reqest_body.get('Info', '')
    
    Platform_Num = info.get('Platform_Num')
    Prod_Line = info.get('Prod_line')
    Batch_Num = info.get('Batch_Num')
    Plan_No = info.get('Plan_No')
    Prd_No = info.get('Prd_No')
    SN_NO = info.get('SN_NO')
    Entirety = info.get('Entirety')
    Entirety_Location = info.get('Entirety_Location')

    #先插历史表
    sql = "insert into yw_project_carving_info_his select * from yw_project_carving_info " \
          "where Entirety='%s' and Entirety_Location='%s'" % (Entirety, Entirety_Location)
    cur.execute(sql)
    sql = "delete from yw_project_carving_info where Entirety='%s' and Entirety_Location='%s'" % (Entirety, Entirety_Location)
    cur.execute(sql)

    insert_sql="insert into yw_project_carving_info(insert_date, Platform_Num, Prod_Line, Batch_Num, Plan_No, Prd_No, SN_NO, Entirety, Entirety_Location)" \
        "values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    insert_tuple = (datetime.datetime.now(),Platform_Num, Prod_Line, Batch_Num, Plan_No, Prd_No, SN_NO, Entirety, Entirety_Location)
    cur.execute(insert_sql, insert_tuple)

    cur.close()

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjprod-SN_Laser_Carving_Save-end---------------------------')
    return HttpResponse(s)

# 获取SN码镭雕配置信息
def Get_SN_Cfg(request, reqest_body):

    # 十六进制 to 十进制
    def hex2dec(string_num):
        return str(int(string_num.upper(), 16))

    # 十进制到十六进制
    def dec2hex(string_num):
        return hex(int(string_num)).split('0x')[1].upper()

    log = public.logger
    log.info('----------------------Lqkjprod-Get_SN_Cfg-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "prd_no": "",
        "prd_name": "",
        "plan_num": "",
        "plan_no": "",
        "Hw_Version": "",
        "Fw_Version": "",
        "Vendor_id": "",
        "cus_no": "",
        "cus_name": "",
        "prd_spc": "",
        "SN_info":[],
        "Entirety": "200805000001",
    }

    if not reqest_body.get('Info', ''):
        s = public.setrespinfo({"respcode": "500511", "respmsg": "上传数据错误!"})
        return HttpResponse(s)

    cur = connection.cursor()  # 创建游标
    info = reqest_body.get('Info', '')

    Platform_Num = info.get('Platform_Num')
    Prod_Line = info.get('Prod_line')
    Batch_Num = info.get('Batch_Num')
    SN_num = info.get('SN_num', 10)
    nowdate=datetime.datetime.now().strftime('%Y-%m-%d')

    #使用进程同步锁


    #先获取一个拼板号
    sql = "select Entirety_Seq from yw_project_carving_enseq where tran_date='%s' for update"  % (nowdate)
    log.info(sql)
    cur.execute(sql)
    row = cur.fetchone()
    if not row:
        Entirety = None
    else:
        Entirety = datetime.datetime.now().strftime('%Y%m%d')[2:8]+ str(row[0]).zfill(6)
    log.info('Entirety='+str(Entirety))

    if Entirety:
        sql = "update yw_project_carving_enseq set Entirety_Seq=Entirety_Seq+1 where tran_date='%s' " % (nowdate)
        cur.execute(sql)
    else:
        sql = "insert into yw_project_carving_enseq(tran_date, Entirety_Seq) values('%s', 1) " % (nowdate)
        cur.execute(sql)
        Entirety = datetime.datetime.now().strftime('%Y%m%d')[2:8] + '0000001'
    jsondata['Entirety']=Entirety

    #查询SN码配置信息
    sql = "select prod_line_num, sn_ds, sn_param, sn_beginid, sn_endid from yw_project_carving_sncfg " \
          "where order_id='%s' and Prod_Line = '%s' order by insert_date desc " % (Batch_Num, Prod_Line)
    log.info(sql)
    cur.execute(sql)
    rows=cur.fetchall()
    existflag=False
    for item in rows:
        if existflag:
            cur.close()
            s = public.setrespinfo({"respcode": "500542", "respmsg": "制令单号对应的SN码配置信息有多条，不确定选择哪个配置!"})
            return HttpResponse(s)
        cfg_prod_line_num = item[0]
        cfg_sn_ds = item[1]
        cfg_sn_param = item[2]
        cfg_sn_beginid = item[3]
        cfg_sn_endid = item[4]
        existflag = True

    if not existflag:
        cur.close()
        s = public.setrespinfo({"respcode": "500539", "respmsg": "制令单号对应的SN码配置信息不存在!"})
        return HttpResponse(s)

    if '[FF][YY][L]' not in cfg_sn_param and (not cfg_sn_beginid or not cfg_sn_beginid):
        cur.close()
        s = public.setrespinfo({"respcode": "500540", "respmsg": "个性化时,SN码号段必须配置!"})
        return HttpResponse(s)

    # 根据制令单号获取明细。
    sql = "select prd_no, prd_name, plan_num, plan_id, Hw_Version, Fw_Version, Vendor_id  from yw_project_plan_info " \
          "where order_id=%s and prod_line=%s order by prod_date DESC"
    cur.execute(sql, (Batch_Num, Prod_Line))
    row = cur.fetchone()
    if not row:
        cur.close()
        s = public.setrespinfo({"respcode": "500531", "respmsg": "生产计划不存在!"})
        return HttpResponse(s)

    jsondata['prd_no'] = row[0]  # 货品代号
    jsondata['prd_name'] = row[1]  # 货品名称
    jsondata['plan_num'] = row[2]  # 计划生产数量
    jsondata['plan_no'] = row[3]  # 计划单号
    jsondata['Hw_Version'] = row[4]  # 硬件版本号
    jsondata['Fw_Version'] = row[5]  # 软件版本号
    jsondata['Vendor_id'] = row[6]  # 厂商代码

    # 查询评审单客户编号和客户名称
    sql = "select h.customer_name,h.specification from yw_bill_review_form_head h, yw_bill_review_form_body b " \
          "where h.head_id=b.head_id and b.require_name like '产品母配方%%' " \
          "and h.plan_number='%s' and b.require_value like '%s%%' order by h.id desc limit 1" \
          % (jsondata['plan_no'], jsondata['prd_no'])
    log.info(sql)
    cur.execute(sql)
    row = cur.fetchone()
    if row:
        jsondata['cus_no'] = ""  # 客户编码
        jsondata['cus_name'] = row[0]  # 客户名称
        jsondata['prd_spc'] = row[1]  # 货品规格
    else:
        jsondata['cus_no'] = ""  # 客户编码
        jsondata['cus_name'] = ""  # 客户名称
        jsondata['prd_spc'] = ""  # 货品规格

    if  cfg_sn_param[0:11] == '[FF][YY][L]':
        yearwork = datetime.datetime.now().strftime('%y')
        sn_flag = 'FF'+ str(yearwork) + str(cfg_prod_line_num)
        sql = "select max(sn_no) from yw_project_carving_info where DATE_FORMAT(insert_date,'%%y')='%s' " \
              "and Prod_Line = '%s' and sn_no like '%s%%'" % ( yearwork, Prod_Line, sn_flag )
        log.info("获取当前最大的16进制SN码SQL:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        if not row or not row[0]:
            maxsn =  'FF'+ str(yearwork) + str(cfg_prod_line_num) + '0000001'
            if cfg_sn_beginid and maxsn < cfg_sn_beginid:
                maxsn = cfg_sn_beginid
        else:
            db_nowmaxsn = row[0]
            log.info('nowmaxsn='+db_nowmaxsn)
            nowmaxsn = db_nowmaxsn[5:12]
            log.info('nowmaxsn=' + nowmaxsn)
            if cfg_sn_ds == 'hex': #16进制递增
                nextsn = int(hex2dec(nowmaxsn)) + 1
                log.info('nextsn=' + str(nextsn))
                maxsn = 'FF'+ str(yearwork) + str(cfg_prod_line_num) + dec2hex(str(nextsn)).zfill(7)
                log.info('maxsn, 16=' + maxsn)
            else: #10进制递增
                nextsn = int(nowmaxsn) + 1
                maxsn = 'FF' + str(yearwork) + str(cfg_prod_line_num) + str(nextsn).zfill(7)
                log.info('maxsn, 10=' + maxsn)

        if maxsn < cfg_sn_beginid:
            maxsn = cfg_sn_beginid
        if cfg_sn_endid and maxsn > cfg_sn_endid:  # 生成的SN码不在指定区间
            cur.close()
            s = public.setrespinfo({"respcode": "500566", "respmsg": "SN码超过指定参数的结束号段!当前值:" + str(maxsn)+"号段结束值："+str(cfg_sn_endid)})
            return HttpResponse(s)
        jsondata['SN_info'].append( {"1": maxsn})
        for i in range(2, SN_num+1):
            nowmaxsn = maxsn[5:12]
            if cfg_sn_ds == 'hex': #16进制递增
                nextsn = int(hex2dec(nowmaxsn)) + 1
                log.info('nextsn=' + str(nextsn))
                maxsn = 'FF'+ str(yearwork) + str(cfg_prod_line_num) + dec2hex(str(nextsn)).zfill(7)
                log.info('maxsn, 16=' + maxsn)
            else: #10进制递增
                nextsn = int(nowmaxsn) + 1
                maxsn = 'FF' + str(yearwork) + str(cfg_prod_line_num) + str(nextsn).zfill(7)
                log.info('maxsn, 10=' + maxsn)
            jsondata['SN_info'].append({ str(i): maxsn})
            if cfg_sn_endid and maxsn > cfg_sn_endid:  # 生成的SN码不在指定区间
                cur.close()
                s = public.setrespinfo({"respcode": "500586", "respmsg": "SN码超过指定参数的结束号段!当前值:" + str(maxsn)+"号段结束值:"+str(cfg_sn_endid)})
                return HttpResponse(s)

    else: #其它个性化SN码，暂时不写代码
        sn_pre, sn_seq = cfg_sn_param.split('[')[1].split(']')
        yearwork = datetime.datetime.now().strftime('%y')
        sql = "select max(sn_no) from yw_project_carving_info where Batch_Num='%s' " % ( Batch_Num )
        log.info("获取当前最大的16进制SN码SQL:" + sql)
        cur.execute(sql)
        row = cur.fetchone()
        if not row or not row[0]:
            maxsn = cfg_sn_beginid
        else:
            db_nowmaxsn = row[0]
            log.info('nowmaxsn=' + db_nowmaxsn)
            nowmaxsn = db_nowmaxsn[len(sn_pre):len(sn_pre)+len(sn_seq)]
            log.info('nowmaxsn=' + nowmaxsn)
            if cfg_sn_ds == 'hex':  # 16进制递增
                nextsn = int(hex2dec(nowmaxsn)) + 1
                log.info('nextsn=' + str(nextsn))
                maxsn = sn_pre + dec2hex(str(nextsn)).zfill(len(sn_seq))
                log.info('maxsn, 16=' + maxsn)
            else:  # 10进制递增
                nextsn = int(nowmaxsn) + 1
                maxsn = sn_pre + str(nextsn).zfill(len(sn_seq))
                log.info('maxsn, 10=' + maxsn)

        if maxsn < cfg_sn_beginid:
            maxsn = cfg_sn_beginid
        if cfg_sn_endid and maxsn > cfg_sn_endid:  # 生成的SN码不在指定区间
            cur.close()
            s = public.setrespinfo({"respcode": "500569", "respmsg": "SN码超过指定参数的结束号段!当前值:" + str(maxsn)+"号段结束值:"+str(cfg_sn_endid)})
            return HttpResponse(s)
        jsondata['SN_info'].append({"1": maxsn})
        for i in range(2, SN_num + 1):
            nowmaxsn = maxsn[len(sn_pre):len(sn_pre)+len(sn_seq)]
            if cfg_sn_ds == 'hex':  # 16进制递增
                nextsn = int(hex2dec(nowmaxsn)) + 1
                log.info('nextsn=' + str(nextsn))
                maxsn = sn_pre + dec2hex(str(nextsn)).zfill(len(sn_seq))
                log.info('maxsn, 16=' + maxsn)
            else:  # 10进制递增
                nextsn = int(nowmaxsn) + 1
                maxsn =sn_pre + str(nextsn).zfill(len(sn_seq))
                log.info('maxsn, 10=' + maxsn)
            jsondata['SN_info'].append({str(i): maxsn})
            if cfg_sn_endid and maxsn > cfg_sn_endid:  # 生成的SN码不在指定区间
                cur.close()
                s = public.setrespinfo({"respcode": "500596", "respmsg": "SN码超过指定参数的结束号段!当前值:" + str(maxsn)+"号段结束值:"+str(cfg_sn_endid)})
                return HttpResponse(s)

    #判断SN是否重复
    list_sn = []
    for item in jsondata['SN_info']:
        for value in item.values():
            list_sn.append(value)

    for item in list_sn:
        sql = "select sn_no from yw_project_carving_info where SN_NO='%s' " % (item)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            cur.close()
            s = public.setrespinfo( {"respcode": "500596", "respmsg": "SN码重复!值:"+str(row[0]) } )
            return HttpResponse(s)

    cur.close()

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Lqkjprod-Get_SN_Cfg-end---------------------------')
    return HttpResponse(s)

