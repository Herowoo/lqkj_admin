#coding:utf-8
# -*- coding: utf-8 -*-

import json
import requests
import random
import datetime

#获取工装项目信息
def getprojectinfo():
    postdata={
        "trantype": "getprojectinfo",  #扫码配对工装获取项目信息
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjsmpd'
    req = requests.post(url, postdata)
    print(req.text)
# getprojectinfo()

#装箱
def boxing():
    postdata={
        "trantype": "boxing",
        "MENU_ID": "10",
        "uid": "38",
        "checksum": "11223355",
        "win_id": "DESKTOP-BIE22N5",
        "order_id": "JH2001A015-4",
        "plan_id":  "JH2001A015-4",
        "prod_line":  "AutoLine1",
        "box_id": "1",
        "model_list": ["3730054190000099241896"]
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjsmpd'
    req = requests.post(url, postdata)
    print(req.text)
# boxing()


#扫码配对工装登记扫码信息
def register_snid():
    postdata={
        "trantype": "register_snid",  #扫码配对工装登记扫码信息
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        'win_id': "litz",  # 窗口号
        'order_id': 'MO1909A080',  # 订单号 #
        'model_id': '11112',  # 模块id
        'pcb_sn': 'ff981822',  # 芯片sn
        'gw_id': '2222222222222222'  # 国网id
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjsmpd'
    req = requests.post(url, postdata)
    print(req.text)
# register_snid()

#多个文件上传,前端敏捷开发上传
def files_upload():
    postdata={
        "trantype":"files_upload",
        "file_list":[ #文件列表
            {
                "file_name":"fdsa.doc",
                "file_content":"qwertyuiop",#文件内容，二进制
            },

        ],
        "MENU_ID":122,
        "uid":38,
        "checksum":"11223355",
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/filedue'
    req = requests.post(url, postdata)
    print(req.text)

#发发发
def register_snid():
    postdata={
        "trantype": "register_snid",
        "MENU_ID": "10",
        "uid": "38",
        "checksum": "11223355",
        "win_id": "DESKTOP-D05G65A",
        "order_id": "MO1909A080",
        "model_id": "6230054000000040974594",
        "pcb_sn": "ff4138071613",
        "gw_id": "01029c01c1fb02485a4830000025dcd47a72fd89cccec796"
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjsmpd'
    req = requests.post(url, postdata)
    print(req.text)
# register_snid()

#获取领料情况
def getmaterialinfo():
    postdata={
        "trantype": "getmaterialinfo",  #扫码配对工装获取项目信息
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        'order_id': 'MO1909A080',  # 制令单号
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# getmaterialinfo()

#获取每小时产出情况
def gethourinfo():
    postdata={
        "trantype": "gethourinfo",  #扫码配对工装获取项目信息
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        'order_id': 'MO1909A080',  # 制令单号
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# gethourinfo()

#获取当日制程数据
def getprocinfo():
    postdata={
        "trantype": "getprocinfo",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        'order_id': 'MO1909A080',  # 制令单号
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# getprocinfo()

#获取看板数据
def getprojlist():
    postdata={
        "trantype":"getprojlist",
        "uid":"111111",
        "checksum":"11223355",
        "typevalues":["automaticline","flexibleline_one","flexibleline_two"]
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    url = 'http://192.168.2.240:8000/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# getprojlist()

#随机获取一个国网ID
def get_gwid():
    postdata={
        "trantype": "get_gwid",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        'order_id': 'MO1909A095',  # 制令单号
        "model_id":"2330054192232900010017"
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjsmpd'
    req = requests.post(url, postdata)
    print(req.text)
# get_gwid()

#获取BOM产品信息列表
def get_productlist():
    postdata={
        "trantype": "get_productlist",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        "model_type":"MODEL_111"
    }
    postdata = json.dumps(postdata)
    print(postdata)
    # url='http://192.168.2.174/api/admin/lqkjerp'
    url = 'http://192.168.2.240:8000/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# get_productlist()

#获取关键元器件清单列表
def get_CriticalCompModel():
    postdata={
        "trantype": "get_CriticalCompModel",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjerp'
    url = 'http://192.168.2.223:8000/api/admin/lqkjerp'
    req = requests.post(url, postdata)
    print(req.text)
# get_CriticalCompModel()

#获取关键元器件清单列表
def get_CriticalCompList():
    postdata={
        "trantype": "get_CriticalCompList",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        # "bom_no":"559911",
        "plan_no":"1"
    }
    postdata = json.dumps(postdata)
    print(postdata)
    # url='http://192.168.2.174/api/admin/lqkjerp'
    url = 'http://192.168.2.223:8000/api/admin/lqkjerp'
    req = requests.post(url, postdata)
    print(req.text)
# get_CriticalCompList()

#关键元器件清单模板新增
def CriticalCompList_add():
    postdata={
        "trantype": "CriticalCompList_add",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        "bom_no":"559912",
        "model_type":"mode1123",
        "model_typename":"fdsafdsa",
        "bom_name":"单样测试",
        "bom_spc": "单样测试spc",
        "use_zone": "四川",
        "CriticalCompList": [
            {
                "seq_no":"1", #序号
                "prd_no":"30018221", #物料名称
                "prd_name":"电源", #元器件名称
                "prd_made":"银行微", #生产厂商
                "prd_type":"78M12", #型号
                "prd_spc":"TO-252",  #规格
                "prd_nature":"78M12系列，输入上限35V,输出12V/500mA", #主要性能
                "prd_level":"工业级" #品级
            },
            {
                "seq_no": "2",  # 序号
                "prd_no": "30018222",  # 物料名称
                "prd_name": "主控CPU",  # 元器件名称
                "prd_made": "航天中电",  # 生产厂商
                "prd_type": "HZ3001",  # 型号
                "prd_spc": "QFN64",  # 规格
                "prd_nature": "工作频率（0.7-12）MHz；通读方式：OFDM;通讯速率:0.1-5Mbps;支持多阶中继功能;电力线升级",  # 主要性能
                "prd_level": "工业级"  # 品级
            },
            {
                "seq_no": "3",  # 序号
                "prd_no": "30018223",  # 物料名称
                "prd_name": "存储器",  # 元器件名称
                "prd_made": "来扬科技",  # 生产厂商
                "prd_type": "LY68S3200/6400",  # 型号
                "prd_spc": "SO-8",  # 规格
                "prd_nature": "32Mbit/64Mbit容量FLASH存储器",  # 主要性能
                "prd_level": "工业级"  # 品级
            },
            {
                "seq_no": "4",  # 序号
                "prd_no": "30018224",  # 物料名称
                "prd_name": "超级电容",  # 元器件名称
                "prd_made": "凹克",  # 生产厂商
                "prd_type": "2.7V/10F",  # 型号
                "prd_spc": "10*25mm",  # 规格
                "prd_nature": "工作电压2.7V,容量10F",  # 主要性能
                "prd_level": "工业级"  # 品级
            },
            {
                "seq_no": "5",  # 序号
                "prd_no": "30018225",  # 物料名称
                "prd_name": "电解电容",  # 元器件名称
                "prd_made": "青岛三莹",  # 生产厂商
                "prd_type": "220uF/25V",  # 型号
                "prd_spc": "6.3*11m",  # 规格
                "prd_nature": "漏电流小于55uA,105℃寿命:5000小时",  # 主要性能
                "prd_level": "工业级"  # 品级
            },
            {
                "seq_no": "6",  # 序号
                "prd_no": "30018226",  # 物料名称
                "prd_name": "晶振",  # 元器件名称
                "prd_made": "奥泰克",  # 生产厂商
                "prd_type": "25MHz±10PPM",  # 型号
                "prd_spc": "SMD3225",  # 规格
                "prd_nature": "9.5pF,300μW",  # 主要性能
                "prd_level": "工业级"  # 品级
            },
            {
                "seq_no": "7",  # 序号
                "prd_no": "30018227",  # 物料名称
                "prd_name": "片式二极管",  # 元器件名称
                "prd_made": "先科",  # 生产厂商
                "prd_type": "SS14",  # 型号
                "prd_spc": "DO-214AC/SMAF",  # 规格
                "prd_nature": "1A/40V",  # 主要性能
                "prd_level": "工业级"  # 品级
            },
            {
                "seq_no": "8",  # 序号
                "prd_no": "30018228",  # 物料名称
                "prd_name": "光耦",  # 元器件名称
                "prd_made": "光宝",  # 生产厂商
                "prd_type": "LTV-817S-C",  # 型号
                "prd_spc": "SOP4",  # 规格
                "prd_nature": "隔离电压:≥5kV;导通时间:≤3μS;Vceo:≥80V",  # 主要性能
                "prd_level": "工业级"  # 品级
            },
            {
                "seq_no": "9",  # 序号
                "prd_no": "99999998",  # 物料名称
                "prd_name": "贴片电阻",  # 元器件名称
                "prd_made": "",  # 生产厂商
                "prd_type": "",  # 型号
                "prd_spc": "",  # 规格
                "prd_nature": "",  # 主要性能
                "prd_level": ""  # 品级
            },
            {
                "seq_no": "10",  # 序号
                "prd_no": "99999999",  # 物料名称
                "prd_name": "贴片电容",  # 元器件名称
                "prd_made": "",  # 生产厂商
                "prd_type": "",  # 型号
                "prd_spc": "",  # 规格
                "prd_nature": "",  # 主要性能
                "prd_level": ""  # 品级
            },
        ]
    }

#    postdata={"trantype":"CriticalCompList_print","MENU_ID":"152","uid":"111112","checksum":"11223355","bom_no":"559911","plan_no":"JH1909A037","use_zone":"\xe5\x9b\x9b\xe5\xb7\x9d","CriticalCompList":[{"seq_no":"1","prd_no":"30018221","prd_name":"\xe7\x94\xb5\xe6\xba\x90","prd_made":"\xe9\x93\xb6\xe8\xa1\x8c\xe5\xbe\xae","prd_type":"78M12","prd_spc":"TO-252","prd_nature":"78M12\xe7\xb3\xbb\xe5\x88\x97\xef\xbc\x8c\xe8\xbe\x93\xe5\x85\xa5\xe4\xb8\x8a\xe9\x99\x9035V,\xe8\xbe\x93\xe5\x87\xba12V/500mA","prd_level":"\xe5\xb7\xa5\xe4\xb8\x9a\xe7\xba\xa7"},{"seq_no":"2","prd_no":"30018222","prd_name":"\xe4\xb8\xbb\xe6\x8e\xa7CPU","prd_made":"\xe8\x88\xaa\xe5\xa4\xa9\xe4\xb8\xad\xe7\x94\xb5","prd_type":"HZ3001","prd_spc":"QFN64","prd_nature":"\xe5\xb7\xa5\xe4\xbd\x9c\xe9\xa2\x91\xe7\x8e\x87\xef\xbc\x880.7-12\xef\xbc\x89MHz\xef\xbc\x9b\xe9\x80\x9a\xe8\xaf\xbb\xe6\x96\xb9\xe5\xbc\x8f\xef\xbc\x9aOFDM;\xe9\x80\x9a\xe8\xae\xaf\xe9\x80\x9f\xe7\x8e\x87:0.1-5Mbps;\xe6\x94\xaf\xe6\x8c\x81\xe5\xa4\x9a\xe9\x98\xb6\xe4\xb8\xad\xe7\xbb\xa7\xe5\x8a\x9f\xe8\x83\xbd;\xe7\x94\xb5\xe5\x8a\x9b\xe7\xba\xbf\xe5\x8d\x87\xe7\xba\xa7","prd_level":"\xe5\xb7\xa5\xe4\xb8\x9a\xe7\xba\xa7"},{"seq_no":"3","prd_no":"30018223","prd_name":"\xe5\xad\x98\xe5\x82\xa8\xe5\x99\xa8","prd_made":"\xe6\x9d\xa5\xe6\x89\xac\xe7\xa7\x91\xe6\x8a\x80","prd_type":"LY68S3200/6400","prd_spc":"SO-8","prd_nature":"32Mbit/64Mbit\xe5\xae\xb9\xe9\x87\x8fFLASH\xe5\xad\x98\xe5\x82\xa8\xe5\x99\xa8","prd_level":"\xe5\xb7\xa5\xe4\xb8\x9a\xe7\xba\xa7"},{"seq_no":"4","prd_no":"30018224","prd_name":"\xe8\xb6\x85\xe7\xba\xa7\xe7\x94\xb5\xe5\xae\xb9","prd_made":"\xe5\x87\xb9\xe5\x85\x8b","prd_type":"2.7V/10F","prd_spc":"10*25mm","prd_nature":"\xe5\xb7\xa5\xe4\xbd\x9c\xe7\x94\xb5\xe5\x8e\x8b2.7V,\xe5\xae\xb9\xe9\x87\x8f10F","prd_level":"\xe5\xb7\xa5\xe4\xb8\x9a\xe7\xba\xa7"},{"seq_no":"5","prd_no":"30018225","prd_name":"\xe7\x94\xb5\xe8\xa7\xa3\xe7\x94\xb5\xe5\xae\xb9","prd_made":"\xe9\x9d\x92\xe5\xb2\x9b\xe4\xb8\x89\xe8\x8e\xb9","prd_type":"220uF/25V","prd_spc":"6.3*11m","prd_nature":"\xe6\xbc\x8f\xe7\x94\xb5\xe6\xb5\x81\xe5\xb0\x8f\xe4\xba\x8e55uA,105\xe2\x84\x83\xe5\xaf\xbf\xe5\x91\xbd:5000\xe5\xb0\x8f\xe6\x97\xb6","prd_level":"\xe5\xb7\xa5\xe4\xb8\x9a\xe7\xba\xa7"},{"seq_no":"6","prd_no":"30018226","prd_name":"\xe6\x99\xb6\xe6\x8c\xaf","prd_made":"\xe5\xa5\xa5\xe6\xb3\xb0\xe5\x85\x8b","prd_type":"25MHz\xc2\xb110PPM","prd_spc":"SMD3225","prd_nature":"9.5pF,300\xce\xbcW","prd_level":"\xe5\xb7\xa5\xe4\xb8\x9a\xe7\xba\xa7"},{"seq_no":"7","prd_no":"30018227","prd_name":"\xe7\x89\x87\xe5\xbc\x8f\xe4\xba\x8c\xe6\x9e\x81\xe7\xae\xa1","prd_made":"\xe5\x85\x88\xe7\xa7\x91","prd_type":"SS14","prd_spc":"DO-214AC/SMAF","prd_nature":"1A/40V","prd_level":"\xe5\xb7\xa5\xe4\xb8\x9a\xe7\xba\xa7"},{"seq_no":"8","prd_no":"30018228","prd_name":"\xe5\x85\x89\xe8\x80\xa6","prd_made":"\xe5\x85\x89\xe5\xae\x9d","prd_type":"LTV-817S-C","prd_spc":"SOP4","prd_nature":"\xe9\x9a\x94\xe7\xa6\xbb\xe7\x94\xb5\xe5\x8e\x8b:\xe2\x89\xa55kV;\xe5\xaf\xbc\xe9\x80\x9a\xe6\x97\xb6\xe9\x97\xb4:\xe2\x89\xa43\xce\xbcS;Vceo:\xe2\x89\xa580V","prd_level":"\xe5\xb7\xa5\xe4\xb8\x9a\xe7\xba\xa7"},{"seq_no":"9","prd_no":"99999998","prd_name":"\xe8\xb4\xb4\xe7\x89\x87\xe7\x94\xb5\xe9\x98\xbb","prd_made":"","prd_type":"","prd_spc":"","prd_nature":"","prd_level":""},{"seq_no":"10","prd_no":"99999999","prd_name":"\xe8\xb4\xb4\xe7\x89\x87\xe7\x94\xb5\xe5\xae\xb9","prd_made":"","prd_type":"","prd_spc":"","prd_nature":"","prd_level":""}]}


    postdata = json.dumps(postdata)
    print(postdata)
    # url='http://192.168.2.174/api/admin/lqkjerp'
    url = 'http://192.168.2.223:8000/api/admin/lqkjerp'
    req = requests.post(url, postdata)
    print(req.text)
# CriticalCompList_add()

#获取投产排队信息
def get_ProduceList():
    postdata={
        "trantype": "get_ProduceList",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
    }

    postdata = json.dumps(postdata)
    print(postdata)
    # url='http://192.168.2.174/api/admin/lqkjerp'
    url = 'http://192.168.2.223:8000/api/admin/lqkjerp'
    req = requests.post(url, postdata)
    print(req.text)
# get_ProduceList()

#计算投产排队信息
def calc_ProduceList():
    postdata={
        "trantype": "calc_ProduceList",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
    }

    postdata = json.dumps(postdata)
    print(postdata)
    # url='http://192.168.2.174/api/admin/lqkjerp'
    url = 'http://192.168.2.223:8000/api/admin/lqkjerp'
    req = requests.post(url, postdata)
    print(req.text)
# calc_ProduceList()

#计算投产排队信息
def CriticalCompList_search():
    postdata={
        "trantype": "CriticalCompList_search",
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        "bom_no":"550032->50135011",
        "temp_id":"1"
    }

    postdata = json.dumps(postdata)
    print(postdata)
    # url='http://192.168.2.174/api/admin/lqkjerp'
    url = 'http://192.168.2.5:8000/api/admin/lqkjerp'
    req = requests.post(url, postdata)
    print(req.text)
# CriticalCompList_search()

#产测结果上传
def Product_Test():
    postdata = {
        "trantype": "Product_Test",  # 交易类型
        "Info": {
            "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},
            "Chip_mmid": {"Result": "Pass", "Value": "01029c01c1fb02485a4830000023a591fac86f80496a1989"},  # 国网ID
            "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
            "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 产测结果
            "Aging_Test_Period": {"Result": "Pass", "Value": "Before"},  # 老化前/老化后
            "Hw_Version": {"Result": "Pass", "Value": "50.13.5.0"},  # 硬件版本号
            "Fw_Version": {"Result": "Pass", "Value": "<CCO> <11.3.2.10>"},  # 软件版本号
            "Vendor_id": {"Result": "Pass", "Value": "TH"},  # 厂商代码
            "chip_id": {"Result": "Pass", "Value": "48-55-5c-03-cf-fd"},  # 芯片唯一识别码
        },
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://222.89.181.194:8212/api/admin/made'
    req = requests.post(url, postdata)
    print(req.text)
# Product_Test()

#校表结果上传
def MeterRead_Test():
    postdata = {"Info": {"chip_id": {"Result": "Pass", "Value": "COM6"}, "Hw_Version": {"Result": "Pass", "Value": "-1.-1.-1.-1"}, "Chip_mmid": {"Result": "Pass", "Value": "000000000000000000000000000000000000000000000000"}, "Platform_Num": {"Result": "Pass", "Value": "2"}, "Vendor_id": {"Result": "Pass", "Value": "TH"}, "Fw_Version": {"Result": "Pass", "Value": "11.4.4.63"}, "Batch_Num": {"Result": "Pass", "Value": "10"}, "Module_ID": {"Result": "Pass", "Value": "0000000000000000000000"}, "Test_Result": {"Result": "Pass", "Value": "Pass"}, "Board_SN": {"Result": "Pass", "Value": "ED34955C5548"}}, "trantype": "MeterRead_Test"}
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/api/admin/made'
    req = requests.post(url, postdata)
    print(req.text)
MeterRead_Test()

#产测结果上传
def filedeal():
    postdata = {
        "MENU_ID": "10",
        "uid": "38",
        "checksum": "11223355",
        "trantype": "filedeal",  # 交易类型
        "fileinfo": {
            "filename" : "litztest.xlsx",
            "sheetname": "Sheet1",
            "menuid" : "185",  #导入的菜单ID，非当前菜单ID
            "filerows": "1223",  #文件记录数，不带表头
            "dealtype":"3",#处理方式,3-有错误退出
            "fieldlist":[#字段对应关系
                {
                    "tablefield":"model_id",   #数据库表字段
                    "tablefieldname": "模块ID", #数据库表字段名
                    "filefield": "2", #文件字段(第几列)
                    "filefieldname": "模块ID", #文件字段名(excel文件中的标题)
                },
                {
                    "tablefield": "gw_id",  # 数据库表字段
                    "tablefieldname": "国网ID",  # 数据库表字段名
                    "filefield": "1",  # 文件字段(第几列)
                    "filefieldname": "芯片ID",  # 文件字段名(excel文件中的标题)
                },
                {
                    "tablefield": "status",  # 数据库表字段
                    "tablefieldname": "状态",  # 数据库表字段名
                    "filefield": "3",  # 文件字段(第几列)
                    "filefieldname": "状态",  # 文件字段名(excel文件中的标题)
                }
            ],
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    # url = 'http://192.168.2.26:8000/api/admin/fileup'
    url = 'http://192.168.2.174/api/admin/fileup'
    req = requests.post(url, postdata)
    print(req.text)
# filedeal()

#获取文件处理进度
def getdegree():
    postdata = {
        "MENU_ID": "10",
        "uid": "38",
        "checksum": "11223355",
        "trantype": "getdegree",  # 交易类型
        "fileinfo": {
            "fileid" : "119",
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/api/admin/fileup'
    req = requests.post(url, postdata)
    print(req.text)
# getdegree()

#文件资源上传,OA评审单上的文件，上传到指定目录
def PsFilesUpload():
    postdata = {
        "MENU_ID": "10",
        "uid": "38",
        "checksum": "11223355",
        "trantype": "PsFilesUpload",  # 交易类型
        "ps_no":"PS20203121",#评审单号
        "plan_no": "JH2001A015",  # 计划号
        "file_list": [  # 文件列表
            {
                "file_name": "fdsa.doc",
                "file_content": "qwertyuiop",  # 文件内容，二进制
            },
            {
                "file_name": "fds22a.doc",
                "file_content": "qwertyuiop",  # 文件内容，二进制
            },
        ],
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/api/admin/lqkjoa'
    req = requests.post(url, postdata)
    print(req.text)
# PsFilesUpload()
