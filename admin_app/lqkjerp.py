from django.shortcuts import HttpResponse
from django.db import connection
import json
from admin_app import public
from admin_app import models
import datetime
import pymssql
from docxtpl import DocxTemplate
import os
import random
import base64
import shutil

def main(request):
    log = public.logger
    log.info('----------------------admin_lqkjerp_begin---------------------------')

    if request.method == "POST": #POST请求
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        reqest_body=json.loads(tmp)

        trantype=reqest_body['trantype']

        log.info('trantype=[%s]' % trantype)
        if  trantype == 'get_productlist':  #获取BOM产品信息列表
            resp = get_productlist(request, reqest_body)
        elif trantype == 'get_CriticalCompModel':  # 获取关键元器件清单列表
            resp = get_CriticalCompModel(request, reqest_body)
        elif trantype == 'get_CriticalCompList':  #获取关键元器件清单列表
            resp = get_CriticalCompList(request, reqest_body)
        elif trantype == 'CriticalCompList_print':  #关键元器件清单打印或导出
            resp = CriticalCompList_print(request, reqest_body)
        elif trantype == 'CriticalCompList_add':  # 关键元器件清单模板新增
            resp = CriticalCompList_add(request, reqest_body)


        elif trantype=='CriticalCompList_templist':#获取关键元器件清单模板列表
            resp=CriticalCompList_templist(request, reqest_body)
        elif trantype=='CriticalCompList_search':#关键元器件清单查询
            resp=CriticalCompList_search(request, reqest_body)
        elif trantype == 'CriticalCompList_toword':  #关键元器件清单导出word
            resp = CriticalCompList_toword(request, reqest_body)


        elif trantype == 'get_ProduceList':  # 获取投产排队信息
            resp = get_ProduceList(request, reqest_body)
        elif trantype == 'calc_ProduceList':  # 计算投产排队信息
            resp = calc_ProduceList(request, reqest_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error! lqkjerp!"})
            resp = HttpResponse(s)
    elif request.method == "GET": #GET请求
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    log.info('----------------------admin_lqkjerp_end---------------------------')

    return resp

#获取BOM物品资料信息
def get_CriticalCompModel(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_get_productlist_begin---------------------------')

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "ModelList": []
    }

    cur = connection.cursor()  # 创建游标
    sql = "select distinct model_type,model_name from yw_lqerp_bom_criticalcomplist_head " \
          "where model_type is not NULL and (plan_no is NULL or plan_no='')"
    log.info("查找标准关键元器件清单:" + sql)
    cur.execute(sql)
    rows = cur.fetchall()

    for item in rows:
        tempdict = {}
        tempdict["model_type"] = item[0]
        tempdict["model_typename"] = item[1]
        jsondata["ModelList"].append(tempdict)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_get_productlist_begin---------------------------')
    return HttpResponse(s)


#获取BOM物品资料信息
def get_productlist(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_get_productlist_begin---------------------------')

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "productlist": []
    }

    model_type=reqest_body.get('model_type',None)

    cur = connection.cursor()  # 创建游标
    sql = "select bom_no,bom_name,bom_spc from yw_lqerp_bom_criticalcomplist_head " \
          "where model_type='%s' and (plan_no is NULL or plan_no='')" % (model_type)
    log.info("查找标准关键元器件清单:" + sql)
    cur.execute(sql)
    rows = cur.fetchall()

    for item in rows:
        tempdict = {}
        templist = []
        templist.append(item[1])
        templist.append(item[2])
        tempdict[item[0]]=templist
        jsondata["productlist"].append(tempdict)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_get_productlist_begin---------------------------')
    return HttpResponse(s)

#获取关键元器件清单列表
def get_CriticalCompList(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_get_CriticalCompList_begin---------------------------')

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "CriticalCompList": [ ]
    }



    plan_no=reqest_body.get('plan_no', None)

    cur = connection.cursor()  # 创建游标
    if plan_no:
        sql = "select id, bom_no,bom_name,bom_spc,plan_no,use_zone,writer,model_type,model_name " \
              "from yw_lqerp_bom_criticalcomplist_head where plan_no='%s'" % (plan_no)
    else:
        bom_no = reqest_body.get('bom_no', None)
        model_type = reqest_body.get('model_type', None)
        if bom_no == None:
            s = public.setrespinfo({"respcode": "600101", "respmsg": "BOM选择错误!"})
            return HttpResponse(s)

        sql = "select id, bom_no,bom_name,bom_spc,plan_no,use_zone,writer,model_type,model_name " \
              "from yw_lqerp_bom_criticalcomplist_head where bom_no= '%s' and model_type='%s' and (plan_no is NULL or plan_no='') " % (bom_no, model_type)
    log.info("获取关键元器件清单headid:" + sql)
    cur.execute(sql)
    row=cur.fetchone()
    headid=row[0]
    jsondata['bom_no']=row[1]
    jsondata['bom_name'] = row[2]
    jsondata['bom_spc'] = row[3]
    jsondata['plan_no'] = row[4]
    if jsondata['plan_no']==None:
        jsondata['plan_no']=''
    jsondata['use_zone'] = row[5]
    if jsondata['use_zone']==None:
        jsondata['use_zone']=''
    jsondata['writer'] = row[6]
    if jsondata['writer']==None:
        jsondata['writer']=''
    jsondata['model_type'] = row[7]
    if jsondata['model_type']==None:
        jsondata['model_type']=''
    jsondata['model_typename'] = row[8]
    if jsondata['model_typename']==None:
        jsondata['model_typename']=''


    sql = "select seq_no,prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_body " \
          "where head_id = '%s' order by seq_no ASC " % (headid)
    log.info("获取关键元器件清单列表:" + sql)
    cur.execute(sql)
    rows = cur.fetchall()

    if rows:
        for item in rows:
            tempdict = {}
            tempdict["seq_no"]=item[0] # 序号
            tempdict["prd_no"] = item[1] # 物料号码
            tempdict["prd_name"] = item[2] # 元器件名称
            tempdict["prd_made"] = item[3] # 生产厂商
            tempdict["prd_type"] = item[4] # 型号
            tempdict["prd_spc"] = item[5] # 规格
            tempdict["prd_nature"] = item[6] # 主要性能
            if tempdict["prd_spc"] == '-' or tempdict["prd_made"]=='-':
                tempdict["prd_level"] = "-"  # 品级
            elif tempdict["prd_no"] in ['99999998','99999999']:
                tempdict["prd_level"] = ""
            else:
                tempdict["prd_level"] = "工业级" # 品级
            jsondata['CriticalCompList'].append(tempdict)
    else:
        #空数据需要添加
        jsondata['CriticalCompList'] = [
            {"seq_no": "1", "prd_no": "30018221", "prd_name": "电源", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": "工业级" },
            {"seq_no": "2", "prd_no": "30018222", "prd_name": "主控CPU", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": "工业级"},
            {"seq_no": "3", "prd_no": "30018223", "prd_name": "存储器", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": "工业级"},
            {"seq_no": "4", "prd_no": "30018224", "prd_name": "超级电容", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": "工业级"},
            {"seq_no": "5", "prd_no": "30018225", "prd_name": "电解电容", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": "工业级"},
            {"seq_no": "6", "prd_no": "30018226", "prd_name": "晶振", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": "工业级"},
            {"seq_no": "7", "prd_no": "30018227", "prd_name": "片式二极管", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": "工业级"},
            {"seq_no": "8", "prd_no": "30018228", "prd_name": "光耦", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": "工业级"},
            {"seq_no": "9", "prd_no": "99999998", "prd_name": "", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": ""},
            {"seq_no": "10", "prd_no": "99999999", "prd_name": "", "prd_made": "", "prd_type": "", "prd_spc": "", "prd_nature": "", "prd_level": ""},
        ]

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_get_CriticalCompList_end---------------------------')
    return HttpResponse(s)

#关键元器件清单打印或导出
def CriticalCompList_print(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_CriticalCompList_print_begin---------------------------')

    bom_no=reqest_body.get('bom_no',None)
    plan_no = reqest_body.get('plan_no', None)
    if bom_no==None:
        s = public.setrespinfo( {"respcode": "600101", "respmsg": "bom号异常!"} )
        return HttpResponse(s)

    cur = connection.cursor()  # 创建游标

    #删除原来的打印信息
    if plan_no:
        # 删除原来的数据
        sql = "delete from yw_lqerp_bom_criticalcomplist_body where head_id in " \
              "(select id from yw_lqerp_bom_criticalcomplist_head where plan_no='%s')" % plan_no
        log.info("删除原来的body数据:" + sql)
        cur.execute(sql)

        sql = "delete from yw_lqerp_bom_criticalcomplist_head where plan_no='%s'" % plan_no
        log.info("删除原来的head数据:" + sql)
        cur.execute(sql)

    # 登记打印head表
    sql = "insert into yw_lqerp_bom_criticalcomplist_head(model_type,model_name,bom_no,bom_name,bom_spc,plan_no,use_zone,writer) " \
          "values('%s','%s','%s','%s','%s','%s','%s','%s')" % \
          (reqest_body.get('model_type',None), reqest_body.get('model_typename',None),reqest_body.get('bom_no',None), reqest_body.get('bom_name',None),
           reqest_body.get('bom_spc',None), reqest_body.get('plan_no', None), reqest_body.get('use_zone', None), reqest_body.get('writer', None))
    log.info("登记打印head表:" + sql)
    cur.execute(sql)

    # 获取head表的登记id
    sql = "select id from yw_lqerp_bom_criticalcomplist_head where plan_no='%s'" % ( reqest_body.get('plan_no', None) )
    log.info("获取head表的登记id:" + sql)
    cur.execute(sql)
    row=cur.fetchone()
    headid=row[0]

    #登记打印明细表
    CriticalCompList = reqest_body.get('CriticalCompList', None)
    for item in CriticalCompList:
        sql = "insert into yw_lqerp_bom_criticalcomplist_body(head_id,seq_no,prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature) " \
              "values('%s','%s','%s','%s','%s','%s','%s','%s')" % (headid, item.get('seq_no',None),item.get('prd_no',None),
                                                              item.get('prd_name',None),item.get('prd_made',None),
                                                              item.get('prd_type', None), item.get('prd_spc', None),
                                                              item.get('prd_nature', None)
                                                              )
        log.info("登记打印明细表:" + sql)
        cur.execute(sql)

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_CriticalCompList_print_begin---------------------------')
    return HttpResponse(s)


#关键元器件清单模板新增
def CriticalCompList_add(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_CriticalCompList_add_begin---------------------------')

    bom_no=reqest_body.get('bom_no',None)
    if bom_no==None:
        s = public.setrespinfo( {"respcode": "600101", "respmsg": "bom号异常!"} )
        return HttpResponse(s)

    cur = connection.cursor()  # 创建游标

    # 登记打印head表
    sql = "insert into yw_lqerp_bom_criticalcomplist_head(model_type,model_name,bom_no,bom_name,bom_spc,use_zone,writer) " \
          "values('%s','%s','%s','%s','%s','%s','%s')" % \
          (reqest_body.get('model_type',None), reqest_body.get('model_typename',None),reqest_body.get('bom_no',None), reqest_body.get('bom_name',None),
           reqest_body.get('bom_spc',None),  reqest_body.get('use_zone', None), reqest_body.get('writer', None))
    log.info("登记打印head表:" + sql)
    cur.execute(sql)

    # 获取head表的登记id
    sql = "select id from yw_lqerp_bom_criticalcomplist_head where bom_no='%s' and model_type='%s' and (plan_no is NULL or plan_no='')" \
          % ( reqest_body.get('bom_no',None), reqest_body.get('model_type',None) )
    log.info("获取head表的登记id:" + sql)
    cur.execute(sql)
    row=cur.fetchone()
    headid=row[0]
    log.info("headid=" + str(headid) )

    #登记打印明细表
    CriticalCompList = reqest_body.get('CriticalCompList', None)
    for item in CriticalCompList:
        sql = "insert into yw_lqerp_bom_criticalcomplist_body(head_id,seq_no,prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature) " \
              "values('%s','%s','%s','%s','%s','%s','%s','%s')" % (headid, item.get('seq_no',None),item.get('prd_no',None),
                                                              item.get('prd_name',None),item.get('prd_made',None),
                                                              item.get('prd_type', None), item.get('prd_spc', None),
                                                              item.get('prd_nature', None)
                                                              )
        log.info("登记打印明细表:" + sql)
        cur.execute(sql)

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_CriticalCompList_add_begin---------------------------')
    return HttpResponse(s)

#获取投产排队信息
def get_ProduceList(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_get_ProduceList_begin---------------------------')

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "heads":[],
        "tableData":[],
    }
    jsondata['heads']=[
        {'name': 'seq_no', 'label': '排序序号', 'width': '80'},
        {'name': 'plan_no', 'label': '计划号', 'width': '120'},
        {'name': 'cust_name', 'label': '客户名称', 'width': ''},
        {'name': 'product_name', 'label': '产品名称', 'width': ''},
        {'name': 'product_num', 'label': '订单数量', 'width': '100'},
        {'name': 'use_zone', 'label': '使用地区', 'width': '100'},
        {'name': 'begin_date', 'label': '投产日期', 'width': '120'},
        {'name': 'end_date', 'label': '缴货日期', 'width': '120'},
    ]

    jsondata['tableData'] =[
        {
            "seq_no": "1", "plan_no": "JH1908A026", "cust_name": "河南许继仪表有限公司",
            "product_name": "单相宽带载波模块(带停电上报+psram)","product_num":"50000.00","use_zone":"四川",
            "begin_date":"","end_date":"",
        },
        {
            "seq_no": "2", "plan_no": "JH1907A026", "cust_name": "河南许继仪表有限公司",
            "product_name": "三相宽带载波模块", "product_num": "120000.00", "use_zone": "四川",
            "begin_date": "", "end_date": "",
        },
        {
            "seq_no": "3", "plan_no": "JH1909A011", "cust_name": "杭天中电",
            "product_name": "集中器宽带载波模块(带停电上报+psram)", "product_num": "2000.00", "use_zone": "四川",
            "begin_date": "", "end_date": "",
        },
        {
            "seq_no": "4", "plan_no": "JH1908A099", "cust_name": "河南许继仪表有限公司",
            "product_name": "单相宽带载波模块(带停电上报+psram)", "product_num": "9000.00", "use_zone": "河南",
            "begin_date": "", "end_date": "",
        },
        {
            "seq_no": "5", "plan_no": "JH1910A001", "cust_name": "河南许继仪表有限公司",
            "product_name": "单相宽带载波模块(带停电上报+psram)", "product_num": "20000.00", "use_zone": "河南",
            "begin_date": "", "end_date": "",
        },
        {
            "seq_no": "6", "plan_no": "JH1910A021", "cust_name": "河南许继仪表有限公司",
            "product_name": "II采宽带载波模块", "product_num": "80000.00", "use_zone": "河南",
            "begin_date": "", "end_date": "",
        },
    ]

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_get_ProduceList_begin---------------------------')
    return HttpResponse(s)


#计算投产排队信息
def calc_ProduceList(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_calc_ProduceList_begin---------------------------')

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "heads":[],
        "tableData":[],
    }
    jsondata['heads']=[
        {'name': 'seq_no', 'label': '排序序号', 'width': '80'},
        {'name': 'plan_no', 'label': '计划号', 'width': '120'},
        {'name': 'cust_name', 'label': '客户名称', 'width': ''},
        {'name': 'product_name', 'label': '产品名称', 'width': ''},
        {'name': 'product_num', 'label': '订单数量', 'width': '100'},
        {'name': 'use_zone', 'label': '使用地区', 'width': '100'},
        {'name': 'begin_date', 'label': '投产日期', 'width': '120'},
        {'name': 'end_date', 'label': '缴货日期', 'width': '120'},
    ]

    jsondata['tableData'] =[
        {
            "seq_no": "1", "plan_no": "JH1908A026", "cust_name": "河南许继仪表有限公司",
            "product_name": "单相宽带载波模块(带停电上报+psram)","product_num":"50000.00","use_zone":"四川",
            "begin_date":"2019-10-29","end_date":"2019-11-03",
        },
        {
            "seq_no": "2", "plan_no": "JH1907A026", "cust_name": "河南许继仪表有限公司",
            "product_name": "三相宽带载波模块", "product_num": "120000.00", "use_zone": "四川",
            "begin_date": "2019-11-04", "end_date": "2019-11-14",
        },
        {
            "seq_no": "3", "plan_no": "JH1909A011", "cust_name": "杭天中电",
            "product_name": "集中器宽带载波模块(带停电上报+psram)", "product_num": "2000.00", "use_zone": "四川",
            "begin_date": "2019-11-15", "end_date": "2019-11-15",
        },
        {
            "seq_no": "4", "plan_no": "JH1908A099", "cust_name": "河南许继仪表有限公司",
            "product_name": "单相宽带载波模块(带停电上报+psram)", "product_num": "9000.00", "use_zone": "河南",
            "begin_date": "2019-11-15", "end_date": "2019-11-16",
        },
        {
            "seq_no": "5", "plan_no": "JH1910A001", "cust_name": "河南许继仪表有限公司",
            "product_name": "单相宽带载波模块(带停电上报+psram)", "product_num": "20000.00", "use_zone": "河南",
            "begin_date": "2019-11-16", "end_date": "2019-11-18",
        },
        {
            "seq_no": "6", "plan_no": "JH1910A021", "cust_name": "河南许继仪表有限公司",
            "product_name": "II采宽带载波模块", "product_num": "80000.00", "use_zone": "河南",
            "begin_date": "2019-11-18", "end_date": "2019-11-22",
        },
    ]

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_calc_ProduceList_begin---------------------------')
    return HttpResponse(s)




#获取关键元器件清单模板列表
def CriticalCompList_templist(request, reqest_body):
    log = public.logger
    log.info('----------------------CriticalCompList_temp_begin---------------------------')

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    jsondata['templist'] = [
        {'label': '默认模板', 'temp_id': '1'},
    ]

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------CriticalCompList_temp_end---------------------------')
    return HttpResponse(s)


#根据id查询关键元器件清单
def CriticalCompList_search(request, reqest_body):
    log = public.logger
    log.info('----------------------CriticalCompList_search_begin---------------------------')

    bom_no = reqest_body.get('bom_no')
    temp_id = reqest_body.get('temp_id')

    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "CriticalCompList": [],
    }

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
            s = public.setrespinfo({"respcode": "672722", "respmsg": "配方号不存在!"})
            return HttpResponse(s)

        if row[2]:
            db_cls_date = row[2].strftime("%Y-%m-%d")
        else:
            db_cls_date = '2000-01-01'

        #递归 查询节点层级
        sql = " WITH CTE AS ( SELECT *,1 AS [Level] FROM TF_BOM WHERE id_no is not null and BOM_NO='%s' " \
              " UNION ALL " \
              " SELECT G.*,CTE.Level+1 FROM TF_BOM as G JOIN CTE ON CTE.ID_NO =G.BOM_NO ) " \
              " SELECT a.prd_no, b.name, b.SPC, a.id_no,level FROM CTE a, prdt b where a.prd_no=b.prd_no" % (bom_no)
        log.info(sql)
        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            sqlserver_conn.close()
            s = public.setrespinfo({"respcode": "672722", "respmsg": "配方号不存在!"})
            return HttpResponse(s)

        bom_dict={}
        for item in rows:
            bom_dict[ item[0] ] = [item[1], item[2]]

        jsondata['bom_no'] = bom_no
        # jsondata['bom_name'] = ''
        # jsondata['bom_spc'] = ''
        # jsondata['plan_no'] = ''
        # jsondata['use_zone'] = ''
        # jsondata['writer'] = ''

    except Exception as ex:
        sqlserver_conn.close()
        log.info(str(ex))
        # log.info('连接远程数据库成功:' + str(datetime.datetime.now()))
    sqlserver_conn.close()

    cur = connection.cursor()  # 创建游标
    #开始对元器件清单赋值:
    # sql="select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg " \
    #     "where prd_name='电源' order by insert_time desc"
    if db_cls_date > '2020-11-23':  # 在这个日期之前的电源芯片是时科的，之后的是钰泰的
        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg " \
              "where prd_name='电源' order by insert_time desc"
    else:
        sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg " \
              "where prd_name='电源' order by insert_time asc"

    cur.execute(sql)
    rows = cur.fetchall()
    flag=False
    temdict = None
    for item in rows:
        if item[0] in bom_dict.keys():
            temdict={"seq_no": 1, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                     "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级" }
            if '钰泰' in item[2] and db_cls_date > '2020-11-23':  # 在这个日期之前的电源芯片是时科的，之后的是钰泰的
                flag = True
                break
    if temdict:
        jsondata['CriticalCompList'].append(temdict)
    else:
        temdict = {"seq_no": 1, "prd_no": "1", "prd_name": "电源", "prd_made": "-", "prd_type": "-",
                   "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
        jsondata['CriticalCompList'].append(temdict)

    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='主控CPU'"
    cur.execute(sql)
    rows = cur.fetchall()
    flag = False
    for item in rows:
        if item[0] in bom_dict.keys():
            flag = True
            temdict = {"seq_no": 2, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                       "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级"}
            jsondata['CriticalCompList'].append(temdict)
            break
    if flag == False:
        temdict = {"seq_no": 2, "prd_no": "2", "prd_name": "主控CPU", "prd_made": "-", "prd_type": "-",
                   "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
        jsondata['CriticalCompList'].append(temdict)

    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='存储器'"
    cur.execute(sql)
    rows = cur.fetchall()
    flag = False
    for item in rows:
        if item[0] in bom_dict.keys():
            flag = True
            temdict = {"seq_no": 3, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                       "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级"}
            jsondata['CriticalCompList'].append(temdict)
            break
    if flag == False:
        temdict = {"seq_no": 3, "prd_no": "3", "prd_name": "存储器", "prd_made": "-", "prd_type": "-",
                   "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
        jsondata['CriticalCompList'].append(temdict)

    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='超级电容'"
    cur.execute(sql)
    rows = cur.fetchall()
    flag = False
    for item in rows:
        if item[0] in bom_dict.keys():
            flag = True
            temdict = {"seq_no": 4, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                       "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级"}
            jsondata['CriticalCompList'].append(temdict)
            break
    if flag == False:
        temdict = {"seq_no": 4, "prd_no": "4", "prd_name": "超级电容", "prd_made": "-", "prd_type": "-",
                   "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
        jsondata['CriticalCompList'].append(temdict)

    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='电解电容'"
    cur.execute(sql)
    rows = cur.fetchall()
    flag = False
    for item in rows:
        if item[0] in bom_dict.keys():
            flag = True
            temdict = {"seq_no": 5, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                       "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级"}
            jsondata['CriticalCompList'].append(temdict)
            break
    if flag == False:
        temdict = {"seq_no": 5, "prd_no": "5", "prd_name": "电解电容", "prd_made": "-", "prd_type": "-",
                   "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
        jsondata['CriticalCompList'].append(temdict)

    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='晶振'"
    cur.execute(sql)
    rows = cur.fetchall()
    flag = False
    for item in rows:
        if item[0] in bom_dict.keys():
            flag = True
            temdict = {"seq_no": 6, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                       "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级"}
            jsondata['CriticalCompList'].append(temdict)
            break
    if flag == False:
        temdict = {"seq_no": 6, "prd_no": "6", "prd_name": "晶振", "prd_made": "-", "prd_type": "-",
                   "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
        jsondata['CriticalCompList'].append(temdict)

    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='片式二极管'"
    cur.execute(sql)
    rows = cur.fetchall()
    flag = False
    for item in rows:
        if item[0] in bom_dict.keys():
            flag = True
            temdict = {"seq_no": 7, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                       "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级"}
            jsondata['CriticalCompList'].append(temdict)
            break
    if flag == False:
        temdict = {"seq_no": 7, "prd_no": "7", "prd_name": "片式二极管", "prd_made": "-", "prd_type": "-",
                   "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
        jsondata['CriticalCompList'].append(temdict)


    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_name='光耦'"
    cur.execute(sql)
    rows = cur.fetchall()
    flag = False
    for item in rows:
        if item[0] in bom_dict.keys():
            flag = True
            temdict = {"seq_no": 8, "prd_no": item[0], "prd_name": item[1], "prd_made": item[2], "prd_type": item[3],
                       "prd_spc": item[4], "prd_nature": item[5], "prd_level": "工业级"}
            jsondata['CriticalCompList'].append(temdict)
            break
    if flag == False:
        temdict = {"seq_no": 8, "prd_no": "8", "prd_name": "光耦", "prd_made": "-", "prd_type": "-",
                   "prd_spc": "-", "prd_nature": "-", "prd_level": "-"}
        jsondata['CriticalCompList'].append(temdict)

    dz_fz,dz_gg,dr_fz,dr_gg = getdzdrinfo(bom_dict)

    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_no='99999998'" #片式电阻
    cur.execute(sql)
    rows = cur.fetchone()
    temdict = {"seq_no": 9, "prd_no": rows[0], "prd_name": rows[1], "prd_made": rows[2], "prd_type": "%s" % (dz_fz),
               "prd_spc":  "%s" % ( dz_gg ), "prd_nature": rows[5], "prd_level": "工业级"}
    jsondata['CriticalCompList'].append(temdict)

    sql = "select prd_no,prd_name,prd_made,prd_type,prd_spc,prd_nature from yw_lqerp_bom_criticalcomplist_cfg where prd_no='99999999'" #片式电容
    cur.execute(sql)
    rows = cur.fetchone()
    temdict = {"seq_no": 10, "prd_no": rows[0], "prd_name": rows[1], "prd_made": rows[2], "prd_type":  "%s" % ( dr_fz ),
               "prd_spc":  "%s" % ( dr_gg ), "prd_nature": rows[5], "prd_level": "工业级"}
    jsondata['CriticalCompList'].append(temdict)
    jsondata['Otherinfo'] = {
        'writer':'关欣',
        'proof_user':'徐明明',
        'audit_user':'吴德葆',
        'jointly_sign':'卢亚平  魏振兴 刘兴旺'
    }

    cur.close()

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------CriticalCompList_search_end---------------------------')
    return HttpResponse(s)

def getdzdrinfo( bom_dict={ } ):
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

                if  'K' not in tempgg and  'M' not in tempgg :  #是最小单位
                    if  'K' not in dz_maxgg and  'M' not in dz_maxgg:#也是最小单位
                        if float(dz_maxgg) < float(tempgg):
                            dz_maxgg = tempgg
                    if  'K' not in dz_mingg and  'M' not in dz_mingg:#也是最小单位
                        if float(dz_mingg) > float(tempgg):
                            dz_mingg = tempgg
                    else:
                        dz_mingg = tempgg
                elif tempgg[-1] in ['K']: #当前规格的单位是K
                    if  'K' not in dz_maxgg and  'M' not in dz_maxgg:#最大规格是K或者M
                        dz_maxgg = tempgg
                    elif  'K' in dz_maxgg: #最大规格都是K
                        if float(dz_maxgg[:-1]) < float(tempgg[:-1]):
                            dz_maxgg = tempgg

                    if 'K' in dz_mingg:
                        if float(dz_mingg[:-1]) > float(tempgg[:-1]):
                            dz_mingg = tempgg
                    elif 'M' in dz_mingg:
                        dz_mingg = tempgg

                elif  tempgg[-1] in ['M']:
                    if 'M' not in dz_maxgg:  # 最大规格不是M
                        dz_maxgg = tempgg
                    elif 'M' in  dz_maxgg: #最大规格都是M
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
                        or ( dr_maxgg[-2:] == 'nf' and tempgg[-2:] == 'uf'):
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
        log.info("获取电阻电容数据失败："+str(ex) +"，原数据:"+itemtemp, exc_info = True)

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
            dzgg = dz_maxgg+'Ω'
        else:
            dzgg = dz_mingg+'Ω' + '-' + dz_maxgg+'Ω'
    if dr_maxgg and dr_mingg:
        if dr_maxgg == dr_mingg:
            drgg = dr_maxgg
        else:
            drgg = dr_mingg  + '-' + dr_maxgg

    return dzfz,dzgg,drfz,drgg


#根据评审单号获取年月
def getPsYearMonth(ps_id):
    year = '20%s' % ps_id[2:4]
    month = ps_id[4:6].lstrip('0')
    return year,month

#根据评审单号获取计划号
def getPlanidByPsid(ps_id):
    cur = connection.cursor()
    sql = "select plan_number from yw_bill_review_form_head where head_id='%s'" % ps_id
    cur.execute(sql)
    row = cur.fetchone()
    if row:
        return row[0]
    return None

#将一个文件夹下的文件全部移到另一个文件夹下（保留子路径） 例：movePath('./dir/b','./dir/a')
def movePath(fromPath,toPath):

    if not os.path.exists(fromPath) or not os.path.exists(toPath):
        return
    filelist=os.listdir(fromPath)
    for filename in filelist:
        fromFile=fromPath+'/'+filename
        toFile=toPath+'/'+filename
        if os.path.exists(toFile):#重复
            if os.path.isdir(fromFile):#是文件夹
                movePath(fromFile,toFile)
                os.system('rm -rf %s'%fromFile)
        else:
            shutil.move(fromPath+'/'+filename,toPath)
    os.system('rm -rf %s' % fromPath)



#将计划号关联的评审单号移入计划号文件夹下
def movePs2Plan(log,plan_id,ps_id):
    root = '/home/admin/lqkj_admin/SVN/项目外来文件'
    year, month = getPsYearMonth(ps_id)
    # 根据计划号反查评审单号
    cur = connection.cursor()
    sql = "select head_id from yw_bill_review_form_head where plan_number='%s'" % plan_id
    cur.execute(sql)
    rows = cur.fetchall()
    ps_ids = []
    if rows:
        for row in rows:
            ps_ids.append(row[0])
    # 将评审单号下的文件移入计划单号下
    new_path = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, plan_id)
    if not os.path.exists(new_path):  # 路径不存在则创建
        os.mkdir(new_path)
    log.info('ps_ids=%s' % ps_ids)
    for pid in ps_ids:
        old_path = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, pid)
        movePath(old_path[:-1],new_path[:-1])
        # filelist = os.listdir(old_path)
        # for fileitem in filelist:
        #     movefilepath = old_path + fileitem
        #     log.info('移动文件：%s->%s' % (movefilepath, new_path))
        #     shutil.move(movefilepath, new_path)
        # # 删除目录
        # os.system('rm -rf %s' % old_path[:-1])

#根据ps_id获取附件路径
def getPathByPsid(ps_id):
    root = '/home/admin/lqkj_admin/SVN/项目外来文件'
    year, month = getPsYearMonth(ps_id)
    plan_id = getPlanidByPsid(ps_id)
    if plan_id[0:2]!='JH':
        filepath = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, ps_id)
    else:
        filepath = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, plan_id)
    return filepath

def CriticalCompList_toword(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_CriticalCompList_toword_begin---------------------------')
    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "filename":'',
        "data":None
    }

    billid=reqest_body.get('billid')
    temp_id=reqest_body.get('temp_id')
    bom_no = reqest_body.get('bom_no')
    bom_name=reqest_body.get('bom_name')
    bom_spc=reqest_body.get('bom_spc')
    plan_no = reqest_body.get('plan_no')
    use_zone=reqest_body.get('use_zone')
    writer=reqest_body.get('writer')
    CriticalCompList=reqest_body.get('CriticalCompList')
    otherinfo=reqest_body.get('otherinfo',{})

    # todo 登记信息

    #生成word
    data_dic = {
        'bom_name': bom_name,
        'bom_spc': bom_spc,
        'data_table': CriticalCompList,
        'plan_no': plan_no,
        'use_zone': use_zone,
        'writer':otherinfo.get('writer',''),
        'proof_user':otherinfo.get('proof_user',''),
        'audit_user':otherinfo.get('audit_user',''),
        'jointly_sign':otherinfo.get('jointly_sign','')
    }
    temp_path=os.path.join(public.localhome,'main_comp_list_temp','temp1.docx')
    if billid:
        file_name="关键元器件清单_"+billid+".docx"
    else:
        file_name = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + str(random.randint(100, 999)) + '.docx'
    # save_path=os.path.join(public.localhome,'main_comp_list_result',file_name)

    root = '/home/admin/lqkj_admin/SVN/项目外来文件'
    year, month = getPsYearMonth(billid)
    save_path = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, billid)
    # save_path=getPsFileUri(billid)
    if not os.path.exists(save_path):  # 如果路径不存在
        os.makedirs(save_path)

    save_path=save_path+file_name

    log.info('temp_path='+temp_path)
    doc = DocxTemplate(temp_path)  # 加载模板文件
    doc.render(data_dic)  # 填充数据
    doc.save(save_path)  # 保存目标文件
    log.info('save_path='+save_path)
    file = open(save_path, 'rb')
    jsondata['filename'] = file_name
    jsondata['data'] = base64.b64encode(file.read()).decode()

    #如果有计划号，移动文件到计划号文件夹
    plan_id = getPlanidByPsid(billid)
    if plan_id[0:2] != 'JH':
        plan_id = None
    if plan_id:
        movePs2Plan(log, plan_id, billid)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_CriticalCompList_toword_end---------------------------')
    return HttpResponse(s)