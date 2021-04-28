#coding:utf-8
# -*- coding: utf-8 -*-

import json
import requests
import random
import datetime
import string


def Proc_test(request, reqest_body):
    print( 'I am Main_Proc!' )

# # func_test.Main_Proc('1','2')
# a = 'func_test.Main_Proc'
# from admin_app.test import func_test
# d='from admin_app.test import func_test'
# exec(d)
# b=eval(a)
# b('1','2')

#用户使用密码登陆
def LoginByPass():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "LoginByPass",
            "check_sum": "11223355",
            "req_seq": req_seq,
        },
        "BODY":{
            'password': 'MO1909A080',  # 制令单号
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://localhost:8000/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# LoginByPass()

#from表单配置查询
def form_cfg_create():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "form_cfg_create",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            'form_name': '表单新增测试',  # 制令单号
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formcfg'
    req = requests.post(url, postdata)
    print(req.text)
# form_cfg_create()

#from表单配置查询
def form_cfg_select():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "form_cfg_select",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            'form_id': '10007',
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formcfg'
    req = requests.post(url, postdata)
    print(req.text)
# form_cfg_select()

#from表单配置更新
def form_cfg_update():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "form_cfg_update",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            'form_id': '10002',
            'form_cfg': '2222',
            'form_var': '33333',
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formcfg'
    req = requests.post(url, postdata)
    print(req.text)
# form_cfg_update()

#from表单渲染
def form_cfg_show():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "form_cfg_show",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            'form_id': '10013',
            'form_data':{'ID': '1'},
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formcfg'
    req = requests.post(url, postdata)
    print(req.text)
# form_cfg_show()

#from表单列表查询
def form_cfg_list():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "form_cfg_list",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            'form_id': '10013',
            'form_data':{'ID': '1'},
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formcfg'
    req = requests.post(url, postdata)
    print(req.text)
# form_cfg_list()

#from表单-个性化交易提交
def from_student_add():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "from_student_add",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            'form_id': '10003',
            'form_data':[
                {'id': '1101'},
                {'name': ''},
                {'class': ''},
                {'pass_flag': ''},
            ],
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/tranapp/button'
    req = requests.post(url, postdata)
    print(req.text)
# from_student_add()

#增删改查配置-获取数据库中的所有表名
def get_table_list():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "get_table_list",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{ },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/crudcfg'
    req = requests.post(url, postdata)
    print(req.text)
# get_table_list()

#增删改查配置-获取配置列表
def get_crud_list():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "get_crud_list",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{ },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/crudcfg'
    req = requests.post(url, postdata)
    print(req.text)
# get_crud_list()


#增删改查配置-获取增删改查字段配置信息
def get_crud_info():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "get_crud_info",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            "app_id":"142",
            # "table_name":"sys_crud_cfg_head",
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/crudcfg'
    req = requests.post(url, postdata)
    print(req.text)
# get_crud_info()

#增删改查配置-增删改查配置创建
def crud_cfg_create():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "10",
            "uid": "38",
            "tran_type": "crud_cfg_create",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":
            {
                "crud_info":
                    {
                        "APP_ID": 142,
                        "APP_NAME": "新交易测试",
                        "TRAN_ID": "",
                        "WHERE_CTRL": "",
                        "ORDER_CTRL": "order by id desc",
                        "TABLE_NAME": "YW_PROJECT_PRODUCT_TEST_INFO",
                        "DATA_SOURCE": "",
                        "MAIN_CONTROL": "",
                        "SELECT_ABLE": True,
                        "INSERT_ABLE": False,
                        "UPDATE_ABLE": False,
                        "DELETE_ABLE": False,
                        "EXPORT_ABLE": True,
                        "IMPORT_ABLE": False,
                        "INSERT_FORMID": "",
                        "UPDATE_FORMID": "",
                        "DELETE_FORMID": "",
                        "EXPORT_FORMID": "",
                        "IMPORT_FORMID": "",
                        "SNOTE": "SNOTE"
                    },
                "crud_field": [
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "id", "FIELD_NAME": "主键", "STATE": True, "DATA_TYPE": "int", "UI_TYPE": "auto_increment", "ALLOW_BLANK": False, "IS_KEY": True, "SEARCH_TYPE": "", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 1, "SNOTE": "", "FIELD_LENGTH": 4, "MAX_LENGTH": 1, "DEF_VALUE": 999},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "insert_date", "FIELD_NAME": "登记时间", "STATE": True, "DATA_TYPE": "datetime", "UI_TYPE": "datetime", "ALLOW_BLANK": False, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 2, "SNOTE": "", "FIELD_LENGTH": 12},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Batch_Num", "FIELD_NAME": "批号", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": False, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 3, "SNOTE": "", "FIELD_LENGTH": 6},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Ser_Num", "FIELD_NAME": "端口号", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": False, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 4, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Platform_Num", "FIELD_NAME": "机台名称", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 5, "SNOTE": "", "FIELD_LENGTH": 6},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Test_Result", "FIELD_NAME": "产测结果", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_STATUS.PASS_FAIL'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 6, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Test_Value", "FIELD_NAME": "产测Value", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_VALUE.FAIL_MSG'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 7, "SNOTE": "", "FIELD_LENGTH": 14},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Board_SN_Result", "FIELD_NAME": "SN码产测结果", "STATE": False, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_STATUS.PASS_FAIL'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 8, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Board_SN", "FIELD_NAME": "SN码", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 9, "SNOTE": "", "FIELD_LENGTH": 12},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Chip_mmid_Result", "FIELD_NAME": "国网ID产测结果", "STATE": False, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_STATUS.PASS_FAIL'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 10, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Chip_mmid", "FIELD_NAME": "国网ID", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 11, "SNOTE": "", "FIELD_LENGTH": 16},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Aging_Test_Period_Result", "FIELD_NAME": "老化产测结果", "STATE": False, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_STATUS.PASS_FAIL'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 12, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Aging_Test_Period", "FIELD_NAME": "老化", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 13, "SNOTE": "", "FIELD_LENGTH": 6},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Hw_Version_Result", "FIELD_NAME": "硬件版本号产测结果", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_STATUS.PASS_FAIL'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 14, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Hw_Version", "FIELD_NAME": "硬件版本号", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 15, "SNOTE": "", "FIELD_LENGTH": 12},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Fw_Version_Result", "FIELD_NAME": "软件版本号产测结果", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_STATUS.PASS_FAIL'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 16, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Fw_Version", "FIELD_NAME": "软件版本号", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 17, "SNOTE": "", "FIELD_LENGTH": 12},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Vendor_id_Result", "FIELD_NAME": "厂商代码产测结果", "STATE": False, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_STATUS.PASS_FAIL'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 18, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "Vendor_id", "FIELD_NAME": "厂商代码", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 19, "SNOTE": "", "FIELD_LENGTH": 6},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "chip_id_Result", "FIELD_NAME": "芯片唯一识别码测试结果", "STATE": False, "DATA_TYPE": "varchar", "UI_TYPE": "list", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "select dict_code,dict_target from irs_ywty_dict where dict_name='YW_PROJECT_PRODUCT_STATUS.PASS_FAIL'", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 20, "SNOTE": "", "FIELD_LENGTH": 8},
                    {"APP_ID": 137, "TRAN_ID": "", "FIELD_ID": "chip_id", "FIELD_NAME": "芯片唯一识别码", "STATE": True, "DATA_TYPE": "varchar", "UI_TYPE": "text", "ALLOW_BLANK": True, "IS_KEY": False, "SEARCH_TYPE": "like", "SEARCH_EXTS": "", "EDIT_ABLE": False, "DEF_VALUE": "", "ORDER_ID": 21, "SNOTE": "", "FIELD_LENGTH": 12}
                ]
            },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/crudcfg'
    req = requests.post(url, postdata)
    print(req.text)
# crud_cfg_create()

#增删改查配置-界面渲染
def crud_cfg_show():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "212",
            "uid": "38",
            "tran_type": "crud_cfg_show",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{},
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/crudcfg'
    req = requests.post(url, postdata)
    print(req.text)
# crud_cfg_show()

#增删改查配置-数据查询
def get_crud_data():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "212",
            "uid": "38",
            "tran_type": "get_crud_data",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            "search":[]
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/crudcfg'
    req = requests.post(url, postdata)
    print(req.text)
# get_crud_data()

#增删改查配置-获取穿梭框数据
def gettransferdata():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "214",
            "uid": "111111",
            "tran_type": "gettransferdata",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            "data":{
                "USER_ID":"111111",
            }
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/cruddata'
    req = requests.post(url, postdata)
    print(req.text)
# gettransferdata()

#增删改查配置-自定义按钮
def form_data_testadd():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        'HEAD': {
            'tran_type': 'form_data_testadd',
            'req_seq': req_seq,
            'mid': '215',
            'uid': '111112',
            'checksum': '9ad1a9126e5a94e2b2bd7977ab5e7460'
        },
        'BODY': {}
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formdata'
    req = requests.post(url, postdata)
    print(req.text)
# form_data_testadd()

#用户权限管理-新增或修改角色
def auth_role_create():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "214",
            "uid": "111111",
            "tran_type": "auth_role_create",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            "ROLE_ID":"testrole1",
            "ROLE_NAME": "测试角色22",
            "ROLE_ABOVE_ID": "administrator",
            "SNOTE":"for 测试"
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/userauth'
    req = requests.post(url, postdata)
    print(req.text)
# auth_role_create()

#用户权限管理-角色查询
def auth_role_select():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "214",
            "uid": "111111",
            "tran_type": "auth_role_select",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            "ROLE_ID":"testrole",
            "ROLE_NAME": "测试角色",
            "ROLE_ABOVE_ID": "administrator",
            "SNOTE":"for 测试"
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/userauth'
    req = requests.post(url, postdata)
    print(req.text)
# auth_role_select()

#用户权限管理-角色删除
def auth_role_delete():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD":{
            "mid": "214",
            "uid": "111111",
            "tran_type": "auth_role_delete",
            "checksum": "11223355",
            "req_seq": req_seq, #前端流水号
        },
        "BODY":{
            "ROLE_ID":"testrole1",
        },
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/userauth'
    req = requests.post(url, postdata)
    print(req.text)
# auth_role_delete()

#用户权限管理-角色新增
def role_cfg_create():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        'HEAD': {'tran_type': 'role_cfg_create', 'req_seq': req_seq, 'mid': '225', 'uid': '111112', 'checksum': '11223355'},
        'BODY': {'form_id': '10023', 'form_var': {'role_id': 'testlalaa', 'role_name': 'testlalaa', 'root_role': 'root', 'role_desc': 'testlalaa', 'root_role_option': [{'key': 'root', 'value': '超级管理员'}], 'selectedKeys': ['223', '223-3']}, 'button_id': 'iqoqqznjlgle'}
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formdata'
    req = requests.post(url, postdata)
    print(req.text)
# role_cfg_create()

#用户权限管理-角色权限查询
def role_cfg_select():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={'HEAD':
                  {'tran_type': 'role_cfg_select', 'req_seq':req_seq, 'mid': '225', 'uid': '111112', 'checksum': '11223355'},
              'BODY': {
                  'form_id': '10023',
                  'form_var': {'role_id': '', 'role_name': '', 'root_role_option': [{'key': 'root', 'value': '超级管理员'}], 'root_role': 'root', 'role_desc': '', 'tree_data': [{'label': '目录1', 'children': [{'label': '菜单1', 'children': [{'label': '添加权限'}, {'label': '删除权限'}, {'label': '修改权限'}, {'label': '查询权限'}], 'field_power': [{'name': 'id', 'label': 'ID', 'power': []}, {'name': 'name', 'label': '姓名', 'power': []}, {'name': 'sex', 'label': '性别', 'power': []}, {'name': 'age', 'label': '年龄', 'power': []}, {'name': 'tel', 'label': '手机号', 'power': []}]}]}, {'label': '菜单2', 'children': [{'label': '添加权限'}, {'label': '删除权限'}, {'label': '修改权限'}, {'label': '查询权限'}], 'field_power': [{'name': 'id', 'label': 'ID', 'power': []}, {'name': 'name', 'label': '姓名', 'power': []}, {'name': 'sex', 'label': '性别', 'power': []}, {'name': 'age', 'label': '年龄', 'power': []}, {'name': 'tel', 'label': '手机号', 'power': []}]}]},
                  'select_key': 'root'
              }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formdata'
    req = requests.post(url, postdata)
    print(req.text)
# role_cfg_select()

#用户权限管理-角色菜单字段权限查询
def role_fieldcfg_select():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        'HEAD': {
            'tran_type': 'role_fieldcfg_select',
            'req_seq': req_seq,
            'mid': '225',
            'uid': '111112',
            'checksum': '11223355'
        },
        'BODY': {'role_id': 'testefds', 'cfg_id': '225-1', 'app_id': 153, 'form_id': '10023'}
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formdata'
    req = requests.post(url, postdata)
    print(req.text)
# role_fieldcfg_select()

#用户权限管理-角色菜单字段权限查询
def role_fieldcfg_select():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        'HEAD': {
            'tran_type': 'role_fieldcfg_select',
            'req_seq': req_seq,
            'mid': '225',
            'uid': '111112',
            'checksum': '11223355'
        },
        'BODY': {
            "role_id": "root",
            'cfg_id': '225-1',
            "app_id": 150,
            "form_id": "10023",
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formdata'
    req = requests.post(url, postdata)
    print(req.text)
# role_fieldcfg_select()

#用户权限管理-角色菜单字段权限添加
def role_fieldcfg_create():
    req_seq = 'TEST_'+datetime.datetime.now().strftime('%H%M%S%f')+"_"+''.join(random.sample(string.digits, 2))
    postdata={
        "HEAD": {"mid": "225", "uid": "111112", "tran_type": "role_fieldcfg_create", "checksum": "11223355", "req_seq":req_seq, "respcode": "000000", "respmsg": "角色添加成功!"},
        "BODY": {"cfg_id": "225-1", "cfg_data": [{"name": "id", "label": "主键", "power": ["显示", "置灰"]}, {"name": "tran_date", "label": "交易日期", "power": ["显示", "置灰"]}, {"name": "name", "label": "姓名", "power": ["显示", "置灰"]}], "role_id": "ss", "app_id": 150, "form_id": "10023"}
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url='http://192.168.2.174/interface/sys/formdata'
    req = requests.post(url, postdata)
    print(req.text)
# role_fieldcfg_create()

#获取用户消息列表
def user_message_list():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "111112", "tran_type": "user_message_list", "checksum": "11223355", "req_seq": req_seq},
        "BODY": {}
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# user_message_list()

#获取用户消息详情
def user_message_info():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "111112", "tran_type": "user_message_info", "checksum": "11223355", "req_seq": req_seq},
        "BODY": {
            "id":"1"
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# user_message_info()

#获取用户首页信息显示
def user_index_msg_list():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "111112", "tran_type": "user_index_msg_list", "checksum": "11223355",
                 "req_seq": req_seq},
        "BODY": {
            "id": "111"
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# user_index_msg_list()

#使用密码登陆系统
def user_login_bypasswd():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": None, "tran_type": "user_login_bypasswd", "checksum": "",
                 "req_seq": req_seq},
        "BODY": {
            "login_name": "15303747326",
            "login_pswd":"75e266f182b4fa3625d4a4f4f779af54"
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# user_login_bypasswd()

#获取用户信息
def get_user_info():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "57", "tran_type": "get_user_info", "checksum": "11223355",
                 "req_seq": req_seq},
        "BODY": { }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# get_user_info()

#修改用户信息
def update_user_info():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "57", "tran_type": "update_user_info", "checksum": "11223355",
                 "req_seq": req_seq},
        "BODY": {
            "user_name": "天正",
            "station": "新扫码登陆用户",
            "certi_type": '',
            "certi": '',
            "sex": "1",
            "address": "郑州",
            "tel": "15303747326",
            "email": '',
            "state": "1",
            "head_imgurl": "http://qukufile2.qianqian.com/data2/pic/7cafa0e31cb50e083c72dd9f21ed2cc4/585027323/585027323.jpg@s_2,w_300,h_300",
            "snote": "修改用户信息测试"
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# update_user_info()

#修改密码
def update_user_info():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "57", "tran_type": "update_user_info", "checksum": "11223355",
                 "req_seq": req_seq},
        "BODY": {
            "passwd_old": "111111111111111111",
            "passwd_new": "222222222222222222",
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# update_user_info()

#新增用户信息
def add_user_info():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "57", "tran_type": "add_user_info", "checksum": "11223355",
                 "req_seq": req_seq},
        "BODY": {
            "user_name": "天正",
            "station": "新扫码登陆用户",
            "certi_type": '',
            "certi": '',
            "sex": "1",
            "address": "郑州",
            "tel": "15303747326",
            "email": '',
            "state": "1",
            "head_imgurl": "http://qukufile2.qianqian.com/data2/pic/7cafa0e31cb50e083c72dd9f21ed2cc4/585027323/585027323.jpg@s_2,w_300,h_300",
            "snote": "修改用户信息测试"
        }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/useract'
    req = requests.post(url, postdata)
    print(req.text)
# add_user_info()

#获取用户菜单列表
def get_menu_list():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "57", "tran_type": "get_menu_list", "checksum": "11223355",
                 "req_seq": req_seq},
        "BODY": {}
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/menucfg'
    req = requests.post(url, postdata)
    print(req.text)
# get_menu_list()

#获取菜单详情
def get_menu_info():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "57", "tran_type": "get_menu_info", "checksum": "11223355",
                 "req_seq": req_seq},
        "BODY": {
            "menu_id":224,
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/menucfg'
    req = requests.post(url, postdata)
    print(req.text)
# get_menu_info()

#保存菜单配置
def save_menu_info():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "57", "tran_type": "save_menu_info", "checksum": "11223355",
                 "req_seq": req_seq},
        "BODY": {
            "menuinfo":
            {
                "menu_id":"",
                "menu_name":"通用表单设计2",
                "menu_desc":"通用表单设计2",
                "menu_seq":"123333",
                "menu_appid":"",
                "menu_tranid":"",
                "menu_type":"formConfigSelect",
                "menu_path":"formConfigSelect",
                "menu_icon":"aa",
                "is_active":True,
                "above_menu_id":"224"
            }
        }
    }
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.174/interface/sys/menucfg'
    req = requests.post(url, postdata)
    print(req.text)
# save_menu_info()

#流程审批管理-查询审批明细
def get_workflow_info():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {
        "HEAD": {"mid": "225", "uid": "57", "tran_type": "get_workflow_info", "checksum": "11223355", "req_seq": req_seq},
        "BODY": {
            "node_id": 11,
         }
    }

    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/sys/workflow'
    req = requests.post(url, postdata)
    print(req.text)
# get_workflow_info()

def gen_diary_report():
    req_seq = 'TEST_' + datetime.datetime.now().strftime('%H%M%S%f') + "_" + ''.join(random.sample(string.digits, 2))
    postdata = {"HEAD": {"mid": "250", "uid": "111112", "tran_type": "gen_diary_report", "checksum": "11223355", "req_seq": req_seq}, "BODY": {"form_var": {"prod_date": "2020-05-20T16:00:00.000Z", "tableData": []}, "button_id": "adtvmwrcypjt"}}
    postdata = json.dumps(postdata)
    print(postdata)
    url = 'http://192.168.2.175/interface/tranapp/prodinfo'
    req = requests.post(url, postdata)
    print(req.text)
gen_diary_report()
