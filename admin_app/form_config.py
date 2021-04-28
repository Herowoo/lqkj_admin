from django.shortcuts import HttpResponse
from django.db import connection
import json
from admin_app import public
from admin_app import models
import datetime


def main(request):
    log = public.logger
    log.info('----------------------form_config-begin---------------------------')
    if request.method == "POST": #POST请求
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        request_body=json.loads(tmp)
        trantype=request_body['trantype']
        log.info('trantype=[%s]' % trantype)
        fun_name = trantype
        if globals().get(fun_name):
            resp = globals()[fun_name](request, request_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error! lqkjerp!"})
            resp = HttpResponse(s)
    elif request.method == "GET": #GET请求
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)
    log.info('----------------------form_config-end---------------------------')
    return resp

#函数装饰器
def func_wrapper(func):
    def wrapper(request, request_body,*args,**kwargs):
        log = public.logger
        fun_name=func.__name__
        log.info('----------------------form_config-%s-begin---------------------------'%fun_name)
        jsondata = {
            "respcode": "000000",
            "respmsg": "交易成功",
            "trantype": request_body.get('trantype', None),
        }
        res=func(jsondata,log,request, request_body,*args,**kwargs)
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
        log.info(s)
        log.info('----------------------form_config-%s-end---------------------------'%fun_name)
        return HttpResponse(s)
    return wrapper


#根据menu_id获取app_id
@func_wrapper
def get_app_id(jsondata,log,request, request_body):
    menu_id=request_body.get('menu_id')
    if not menu_id:
        jsondata['respcode'] = '400000'
        jsondata['respmsg'] = '缺少必要参数'
        return
    cursor=connection.cursor()
    sql='select menu_path,app_id from irsadmin_menu where MENU_ID=%s'
    log.info(sql%menu_id)
    cursor.execute(sql%menu_id)
    row=cursor.fetchone()
    if row:
        jsondata['menu_path']=row[0]
        jsondata['app_id']=row[1]
    else:
        jsondata['respcode'] = '400002'
        jsondata['respmsg'] = 'menu_id不存在'

#获取表单配置信息
@func_wrapper
def get_form_config(jsondata,log,request, request_body):
    form_id=request_body.get('form_id')
    if not form_id:
        jsondata['respcode']='400000'
        jsondata['respmsg']='缺少必要参数'
        return
    sql = "select form_json,now_id,value_json,form_name,form_desc,tran_api,data_api from irsadmin_db_form_config where form_id=%s"
    cursor = connection.cursor()
    log.info(sql % form_id)
    cursor.execute(sql,form_id)
    row = cursor.fetchone()
    if row:
        jsondata['form_json'] = row[0]
        jsondata['now_id'] = row[1]
        jsondata['value_json'] = row[2]
        jsondata['page_info']={
            'form_id':form_id,
            'form_name':row[3],
            'form_desc':row[4],
            'tran_api':row[5],
            'data_api': row[6]
        }
    else:
        jsondata['respcode'] = '400001'
        jsondata['respmsg'] = 'form_id不存在'
        # default={"type":"column","id":0,"data":[{"id":1,"type":"label","data":"start"}]}
        # jsondata['form_json'] = json.dumps(default)
        # jsondata['now_id'] = 1

#新建表单配置
@func_wrapper
def create_form_config(jsondata,log,request, request_body):
    default = {"type": "column", "id": 0, "data": [{"id": 1, "type": "label", "data": "start"}]}
    form_data = json.dumps(default)
    now_id=1
    now_datetime = datetime.datetime.now()
    cursor = connection.cursor()
    sql = "insert into irsadmin_db_form_config(form_json,now_id,create_time,update_time) value(%s,%s,%s,%s)"
    log.info(sql % (form_data, now_id, now_datetime, now_datetime))
    cursor.execute(sql, (form_data, now_id, now_datetime,now_datetime))
    jsondata['form_id']=cursor.lastrowid


#更新表单配置信息
@func_wrapper
def update_form_config(jsondata,log,request, request_body):
    page_info=request_body.get('page_info')
    form_data = request_body.get('form_data')
    value_json = request_body.get('value_json')
    now_id = request_body.get('now_id')
    now_datetime = datetime.datetime.now()
    if page_info:
        form_id=page_info.get('form_id')
        form_name=page_info.get('form_name')
        form_desc=page_info.get('form_desc')
        tran_api=page_info.get('tran_api')
        data_api = page_info.get('data_api')

    if page_info and form_data and now_id and form_id:
        pass
    else:
        jsondata['respcode'] = '400000'
        jsondata['respmsg'] = '缺少必要参数'
        return


    cursor = connection.cursor()
    sql = "update irsadmin_db_form_config set form_json=%s,value_json=%s,now_id=%s,update_time=%s,form_name=%s,form_desc=%s,tran_api=%s,data_api=%s where form_id=%s"
    log.info(sql % (form_data, value_json, now_id, now_datetime,form_name,form_desc,tran_api,data_api,form_id))
    cursor.execute(sql,(form_data, value_json, now_id, now_datetime,form_name,form_desc,tran_api,data_api,form_id))




@func_wrapper
def test_data_api1(jsondata,log,request, request_body):
    jsondata['data']={
        "billdata": [
            {
                "name": "硬件版本（*）",
                "value": [
                    "",
                    "",
                    "",
                    "",
                    ""
                ],
                "cltime": [
                    "",
                    "",
                    "",
                    "",
                    ""
                ],
                "wctime": [
                    "",
                    "",
                    "",
                    "",
                    ""
                ]
            },
            {
                "name": "软件版本（*）",
                "value": [
                    ""
                ],
                "cltime": [
                    ""
                ],
                "wctime": [
                    ""
                ]
            },
            {
                "name": "关键元器件清单",
                "value": [
                    "见附件"
                ],
                "cltime": [
                    ""
                ],
                "wctime": [
                    ""
                ]
            }
        ]
    }


@func_wrapper
def test_tran_api1(jsondata,log,request, request_body):
    print(request_body)