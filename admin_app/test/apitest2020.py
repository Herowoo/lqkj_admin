#coding:utf-8
# -*- coding: utf-8 -*-

import json
import string
import requests
import random
import datetime

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
    postdata={"trantype":"gethourinfo","order_id":"MO2004A059","plan_id":"JH2003A033","prod_line":"ManLine2","begin_date":"2020-04-22","end_date":"2020-04-22","uid":"111131","checksum":"11223355"}
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
        "plan_id": "JH2003A005",
        "order_id": "MO2003A033",
        "prod_line": "ManLine2",
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
        "typevalues":['ManLine1','ManLine2','ManLine3']
    }

    postdata = json.dumps(postdata)
    print(datetime.datetime.now(), postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    # url = 'http://192.168.2.240:8000/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(datetime.datetime.now(), req.text)
# getprojlist()

#获取昨日生产情况，今年生产情况
def getcollectinfo():
    postdata={
        "trantype":"getcollectinfo",
        "uid":"57",
        "checksum":"11223355",

        "plan_id": "SB2003A004",
        "order_id": "MO2004A025",
        "prod_line": "ManLine3",

    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    # url = 'http://192.168.2.240:8000/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# getcollectinfo()

#获取项目信息
def getprojinfo():
    postdata={
        "trantype":"getprojinfo",
        "uid":"57",
        "checksum":"11223355"
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    # url = 'http://192.168.2.240:8000/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# getprojinfo()

#根据时间段获取获取项目信息
def getprojectlist():
    postdata={
        "trantype":"getprojectlist",
        "uid":"57",
        "checksum":"11223355",
        "begin_date": "2020-04-01",
        "end_date": "2020-04-11",
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    # url = 'http://192.168.2.240:8000/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# getprojectlist()

#获取各工站生产情况
def getstationinfo():
    postdata={
        "trantype": "getstationinfo",  #扫码配对工装获取项目信息
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        # "plan_id": "SB2003A004",
        "order_id": "MO2004A029",
        "prod_line": "ManLine2",
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/api/admin/lqkjmes'
    req = requests.post(url, postdata)
    print(req.text)
# getstationinfo()

#烧录数据上传
def Flash_Burn():
    postdata={
        "trantype": "Flash_Burn",  #烧录数据上传
        "MENU_ID":"10",
        "uid":"38",
        "checksum":"11223355",
        "Info": [
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM11"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM12"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM13"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM14"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM15"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM16"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM17"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM18"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM19"}  # 串口号
            },
            {
                "Board_SN": {"Result": "Pass", "Value": "ff4140036386"},  # SN码
                "Platform_Num": {"Result": "Pass", "Value": "10"},  # 机台名称
                "Test_Result": {"Result": "Pass", "Value": "Pass"},  # 抄表结果
                "Batch_Num": {"Result": "Pass", "Value": "MO2001A031"},  # 制令号
                "chip_id": {"Result": "Pass", "Value": "COM11"}  # 串口号
            }
        ]
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://222.89.181.194:7080/api/admin/made'
    req = requests.post(url, postdata)
    print(req.text)
# Flash_Burn()

#抄表测试数据上传
def MeterRead_Test():
    postdata = {
        "trantype":"MeterRead_Test",
        "Info":[
            {"Board_SN":{"Result":"","Value":"11111"},"Platform_Num": {"Result": "Pass", "Value": "2"},"Chip_mmid":{"Result":"","Value":""},"Batch_Num":{"Result":"","Value":"zhiling"},"chip_id":{"Result":"","Value":"1"},"Module_ID":{"Result":"","Value":""},"Test_Result":{"Result":"","Value":"zhiling"},"Fw_Version":{"Result":"","Value":""},"Hw_Version":{"Result":"","Value":""},"Vendor_id":{"Result":"","Value":None}},
            {"Board_SN":{"Result":"","Value":"11112"},"Platform_Num": {"Result": "Pass", "Value": "2"},"Chip_mmid":{"Result":"","Value":""},"Batch_Num":{"Result":"","Value":"zhiling"},"chip_id":{"Result":"","Value":"2"},"Module_ID":{"Result":"","Value":""},"Test_Result":{"Result":"","Value":"zhiling"},"Fw_Version":{"Result":"","Value":""},"Hw_Version":{"Result":"","Value":""},"Vendor_id":{"Result":"","Value":None}}
        ]
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://222.89.181.194:7080/api/admin/made'
    req = requests.post(url, postdata)
    print(req.text)
# MeterRead_Test()


#客户CTO订单信息上传
def custorder_ctoinfo_save():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {
            "mid": "223",
            "uid": "111112",
            "tran_type": "custorder_ctoinfo_save",
            "checksum": "11223355",
            "req_seq": req_seq,
            "respcode": "000000",
            "respmsg": "交易成功!"
        },
        "BODY": {
            "order_head": {
                "head_id":"", #修改时使用，主键ID，新增时为空或无此变量
                "order_date": "2020-07-15",   #订单发出版本日期
                "cust_orderid": "tc-2093",    #重庆客户订单编号
                "term_orderid": "83d11",      #终端客户订单编号
                "checker": "张三",      #审核人
                "undertaker": "李四",      #承办
                "order_info":[ #订单信息
                    {
                        "seq_no":"1", #项次
                        "ch_no":"CH-0530", #出货单号
                        "tc_no":"TC-0521", #投产单号
                        "cust_name":"海兴", #客户名称
                        "hard_version":"313033", #硬件版本号
                        "prod_name":"集中器模块", #产品名称
                        "prod_spc":"规格型号", #规格型号
                        "prod_num":"5", #订单数量
                        "prod_wb":"南网", #网别
                        "use_zone":"广西", #目的区域
                     },
                ],
                "order_specinfo":"", #订单特别要求
                #收货信息
                "delivery_addr":"浙江省杭州市拱墅区莫干山路1418-35号海兴电力科技仓储部", #收货地址
                "delivery_person":"徐素兰", #联系人
                "delivery_phone":"15968165872", #联系方式
            },
            "tech_info": [ #技术信息
                {
                    "ship_logo": "",  #芯片标示要求
                    "ship_id": "", #芯片ID
                    "ship_id_file": [331], #芯片ID文件
                    "ship_mac": "", #mac地址
                    "ship_mac_begin_id": "",
                    "ship_mac_end_id": "",
                    "ship_note": "",
                    "shell_cad": "",
                    "shell_cad_file":[336],#外壳CAD文件
                    "shell_supplier": "", #外壳供货厂家
                    "shell_name": "", #模块名称
                    "shell_spc": "",  #规格型号
                    "shell_fn": "",  #出厂编号
                    "shell_fn_file": [332],  #出厂编号
                    "shell_barcode": "",  #资产条码
                    "shell_barcode_file": [333],
                    "shel_note": "", #外壳信息备注
                    "soft_in_ver": "", #内部版本信息
                    "soft_in_file": [334],#内部版本文件
                    "soft_ex_ver": "", #外部版本信息
                    "soft_hardcode": "", #硬件识别码
                    "soft_spec": "", #固件特殊要求
                    "soft_note": "", #软件信息备注
                    "pack_specs": "", #包装规范
                    "pack_specs_file": "", #包装规范特殊要求文件
                    "pack_delivery": "", #送货单
                    "pack_devliver_file": [335],#专用送货单文件
                    "pack_note":"", #包装信息备注
                }
            ]
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/tranapp/custorder'
    req = requests.post(url, postdata)
    print(req.text)
# custorder_ctoinfo_save()

#客户CTO订单信息确认
def custorder_ctoinfo_confirm():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {
            "mid": "223",
            "uid": "111112",
            "tran_type": "custorder_ctoinfo_confirm",
            "checksum": "11223355",
            "req_seq": req_seq,
            "respcode": "000000",
            "respmsg": "交易成功!"
        },
        "BODY": {
            "order_head": {
                "id":"16", #修改时使用，主键ID，新增时为空或无此变量
            }
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/tranapp/custorder'
    req = requests.post(url, postdata)
    print(req.text)
# custorder_ctoinfo_confirm()

#客户CTO订单信息撤消
def custorder_ctoinfo_cancel():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {
            "mid": "223",
            "uid": "111112",
            "tran_type": "custorder_ctoinfo_cancel",
            "checksum": "11223355",
            "req_seq": req_seq,
            "respcode": "000000",
            "respmsg": "交易成功!"
        },
        "BODY": {
            "order_head": {
                "id":"16", #修改时使用，主键ID，新增时为空或无此变量
            }
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/tranapp/custorder'
    req = requests.post(url, postdata)
    print(req.text)
# custorder_ctoinfo_cancel()


#客户CTO订单信息详情查询
def custorder_ctoinfo_getlist():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {
            "mid": "223",
            "uid": "111112",
            "tran_type": "custorder_ctoinfo_getlist",
            "checksum": "11223355",
            "req_seq": req_seq,
            "respcode": "000000",
            "respmsg": "交易成功!"
        },
        "BODY": { }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/tranapp/custorder'
    req = requests.post(url, postdata)
    print(req.text)
# custorder_ctoinfo_getlist()


#客户CTO订单信息获取详情
def custorder_ctoinfo_getinfo():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {
            "mid": "223",
            "uid": "111112",
            "tran_type": "custorder_ctoinfo_getinfo",
            "checksum": "11223355",
            "req_seq": req_seq,
            "respcode": "000000",
            "respmsg": "交易成功!"
        },
        "BODY": {
            "order_head": {
                "head_id":"145", #修改时使用，主键ID，新增时为空或无此变量
            }
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/tranapp/custorder'
    req = requests.post(url, postdata)
    print(req.text)
# custorder_ctoinfo_getinfo()

#扫码配对登记
def model_smpd_save():
    req_seq = 'PROD_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        'HEAD': {
            'mid': '223',
            'uid': '57',
            'tran_type': 'model_smpd_save',
            'checksum': '11223355',
            'req_seq': 'PROD_114330096096_36'
        },
        'BODY': {
            'order': 'MO2999A001',
            'model_id': '3300038383883821123',
            'win_id': '100',
            'prod_line': 'ManLine1',
            'sn': 'FF20600305AC',
            'chipid': '000000000000000000000000000000000000000000000000'
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/tranapp/prodsmcb'
    req = requests.post(url, postdata)
    print(req.text)
# model_smpd_save()

#抄表登记
def model_meterread_save():
    req_seq = 'PROD_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    # postdata = {
    #     "HEAD": {
    #         "mid": "223",
    #         "uid": "57",
    #         "tran_type": "model_meterread_save",
    #         "checksum": "11223355",
    #         "req_seq": req_seq,
    #         "respcode": "000000",
    #         "respmsg": "交易成功!"
    #     },
    #     "BODY": {
    #         "order_id": "MO2999A001",  # 制令号
    #         "model_id": "0000000000000000000000",
    #         "chipid": "000000000000000000000000000000000000000000000000",
    #         "sn": "FF20600305AC",
    #         "hw_version": "255.255.255.255",
    #         "fw_version": "11.5.2.48",
    #         "vendor_code": "WT",
    #         "MeterRead_Result": "Pass",
    #         "prod_line": "ManLine1",
    #         "win_id": "LQ123"
    #     }
    # }
    postdata = {'HEAD': {'mid': '223', 'uid': '57', 'tran_type': 'model_meterread_save', 'checksum': '11223355',
              'req_seq': req_seq},
     'BODY': {'chipid': '000000000000000000000000000000000000000000000000', 'sn': 'FF4230139269',
              'hw_version': '255.255.255.255', 'fw_version': '11.4.2.51', 'vendor_code': 'HT',
              'MeterRead_Result': 'Pass', 'prod_line': 'AutoLine2', 'win_id': 'LQ-ZZ', 'order_id': 'MO2009A063',
              'model_id': '201909000000421'}}

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://10.10.10.174/interface/tranapp/prodsmcb'
    req = requests.post(url, postdata)
    print(req.text)
model_meterread_save()


#自动装箱-获取装箱信息
def get_autobox_info():
    req_seq = 'PROD_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {
            "mid": "223",
            "uid": "57",
            "tran_type": "get_autobox_info",
            "checksum": "11223355",
            "req_seq": req_seq,
        },
        "BODY": {
            "win_id": "computer_name",  # 机台名称
            "prod_line": "AutoLine2",  # 生产线别 ManLine1-柔性线1
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://10.10.10.174/interface/tranapp/prodbox'
    req = requests.post(url, postdata)
    print(req.text)
# get_autobox_info()

#自动装箱-获取装箱信息
def put_autobox_info():
    req_seq = 'PROD_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {
            "mid": "223",
            "uid": "57",
            "tran_type": "put_autobox_info",
            "checksum": "11223355",
            "req_seq": req_seq,
        },
        "BODY": {
            "win_id": "computer_name",  # 机台名称
            "prod_line": "AutoLine2",  # 生产线别 ManLine1-柔性线1
            "order_id": "MO9999A001",
            "model_info": [
                {"place_id": 1, "model_id": "9807016"},
                {"place_id": 2, "model_id": "3300038383883821123"},
                {"place_id": 3, "model_id": "9807017"},
                {"place_id": 4, "model_id": "3300038383883821123"},
                {"place_id": 5, "model_id": "3300038383883821123"},
                {"place_id": 6, "model_id": "3300038383883821123"},
                {"place_id": 7, "model_id": "3300038383883821123"},
                {"place_id": 8, "model_id": "3300038383883821123"},
            ]
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://10.10.10.174/interface/tranapp/prodbox'
    req = requests.post(url, postdata)
    print(req.text)
# put_autobox_info()

#手动装箱-手工一次性一托盘的装箱验证方式
def put_manbox_info():
    req_seq = 'PROD_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {
            "mid": "223",
            "uid": "57",
            "tran_type": "put_manbox_info", #手工一次性一托盘的装箱方式
            "checksum": "11223355",
            "req_seq": req_seq,
        },
        "BODY": {
            "win_id": "computer_name",  # 机台名称
            "prod_line": "AutoLine2",  # 生产线别 ManLine1-柔性线1
            "order_id": "MO9999A001",
            "model_info": [
                {"place_id": 1, "model_id": "9807016"},
                {"place_id": 2, "model_id": "3300038383883821123"},
                {"place_id": 3, "model_id": "9807017"},
                {"place_id": 4, "model_id": "3300038383883821123"},
                {"place_id": 5, "model_id": "3300038383883821123"},
                {"place_id": 6, "model_id": "3300038383883821123"},
                {"place_id": 7, "model_id": "3300038383883821123"},
                {"place_id": 8, "model_id": "3300038383883821123"},
            ]
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://10.10.10.174/interface/tranapp/prodbox'
    req = requests.post(url, postdata)
    print(req.text)
# put_autobox_info()

